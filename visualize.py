import folium
import branca
import json
from shapely.geometry import mapping
from folium.plugins import HeatMap, MarkerCluster

def add_forest_regions_overlay(map_obj):
    """Add forest region overlays to the map."""
    try:
        with open('data/park_boundary.geojson', 'r') as f:
            forest_data = json.load(f)
        
        region_colors = {
            'Serengeti National Park': '#27ae60',
            'Amazon Rainforest': '#2ecc71',
            'Southeast Asia Mangroves': '#16a085',
            'Congo Basin': '#3498db'
        }
        
        for feature in forest_data['features']:
            region_name = feature['properties'].get('name', 'Unknown')
            color = region_colors.get(region_name, '#95a5a6')
            
            folium.GeoJson(
                feature,
                style_function=lambda x, c=color: {
                    'fillColor': c,
                    'color': c,
                    'weight': 3,
                    'opacity': 0.8,
                    'fillOpacity': 0.3,
                    'dashArray': '5, 5'
                },
                popup=f"<b>{region_name}</b><br>Protected Forest Region",
                tooltip=region_name
            ).add_to(map_obj)
        
        print("✓ Forest regions overlay added")
    except Exception as e:
        print(f"⚠ Could not load forest regions: {e}")

def create_heatmap(grid_df, prob_col='risk_proba', park_geom=None, out_html='outputs/heatmap.html', show_regions=True):
    # center map
    if park_geom is not None:
        centroid = park_geom.centroid
    else:
        centroid = grid_df['geometry'][0].centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=12, tiles='cartodbpositron')

    minv = float(min(grid_df[prob_col].min(), 0.0))
    maxv = float(grid_df[prob_col].max())
    cmap = branca.colormap.LinearColormap(['green','yellow','red'], vmin=minv, vmax=maxv)

    for _, row in grid_df.iterrows():
        geojson = mapping(row['geometry'])
        color = cmap(row[prob_col])
        folium.GeoJson(geojson, style_function=lambda feat, color=color: {'fillColor':color,'color':'#444','weight':0.5,'fillOpacity':0.6}).add_to(m)

    # add forest regions if enabled
    if show_regions:
        add_forest_regions_overlay(m)

    # add Leaflet heatmap using centroids weighted by probability
    heat_data = []
    for _, row in grid_df.iterrows():
        cent = row['geometry'].centroid
        heat_data.append([cent.y, cent.x, float(row[prob_col])])
    if len(heat_data) > 0:
        HeatMap(heat_data, radius=25, blur=15, max_zoom=13).add_to(m)

    cmap.caption = 'Poaching risk probability'
    cmap.add_to(m)
    m.save(out_html)
    return m

def highlight_top_grids(grid_df, top_n=10, out_html='outputs/top_grids.html'):
    top = grid_df.sort_values(by='risk_proba', ascending=False).head(top_n)
    centroid = top['geometry'].iloc[0].centroid
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=13)
    for _, row in top.iterrows():
        folium.GeoJson(mapping(row['geometry']), style_function=lambda feat: {'fillColor':'red','color':'black','weight':1,'fillOpacity':0.7}).add_to(m)

    # add marker cluster for top grids centroids
    mc = MarkerCluster()
    for _, row in top.iterrows():
        c = row['geometry'].centroid
        folium.Marker(location=(c.y, c.x), popup=f"grid_id={row['grid_id']}, risk={row['risk_proba']:.3f}").add_to(mc)
    mc.add_to(m)
    m.save(out_html)
    return m

def make_simple_patrol_routes(grid_df, top_n=10, out_html='outputs/patrol_routes.html'):
    top = grid_df.sort_values(by='risk_proba', ascending=False).head(top_n)
    centroids = [g.centroid for g in top['geometry']]
    coords = [(c.y, c.x) for c in centroids]
    m = folium.Map(location=coords[0], zoom_start=13)
    folium.PolyLine(coords, color='blue', weight=3).add_to(m)
    for c in coords:
        folium.CircleMarker(location=c, radius=4, color='navy').add_to(m)
    m.save(out_html)
    return m
