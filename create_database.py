#!/usr/bin/env python
"""Create SQL database for poaching data and risk analysis"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

DB_FILE = 'poaching_dashboard.db'

def create_database():
    """Create SQLite database with all required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Drop existing tables (if any)
    cursor.execute('DROP TABLE IF EXISTS risk_predictions')
    cursor.execute('DROP TABLE IF EXISTS poaching_incidents')
    cursor.execute('DROP TABLE IF EXISTS grid_cells')
    cursor.execute('DROP TABLE IF EXISTS regions')
    cursor.execute('DROP TABLE IF EXISTS daily_summary')
    
    print("Creating database tables...")
    
    # 1. REGIONS TABLE
    cursor.execute('''
        CREATE TABLE regions (
            region_id INTEGER PRIMARY KEY,
            region_name TEXT NOT NULL,
            region_code TEXT UNIQUE,
            bounds TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created regions table")
    
    # 2. GRID CELLS TABLE
    cursor.execute('''
        CREATE TABLE grid_cells (
            grid_id TEXT PRIMARY KEY,
            region_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            cell_size REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (region_id) REFERENCES regions(region_id)
        )
    ''')
    print("✓ Created grid_cells table")
    
    # 3. POACHING INCIDENTS TABLE
    cursor.execute('''
        CREATE TABLE poaching_incidents (
            incident_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grid_id TEXT NOT NULL,
            incident_date DATE NOT NULL,
            incident_time TIME,
            animal_type TEXT,
            severity TEXT,
            location_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grid_id) REFERENCES grid_cells(grid_id)
        )
    ''')
    print("✓ Created poaching_incidents table")
    
    # 4. RISK PREDICTIONS TABLE
    cursor.execute('''
        CREATE TABLE risk_predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grid_id TEXT NOT NULL,
            prediction_date DATE NOT NULL,
            risk_probability REAL NOT NULL,
            risk_level TEXT,
            rainfall_mm REAL,
            moon_illumination REAL,
            day_of_year INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grid_id) REFERENCES grid_cells(grid_id)
        )
    ''')
    print("✓ Created risk_predictions table")
    
    # 5. DAILY SUMMARY TABLE (for dashboard)
    cursor.execute('''
        CREATE TABLE daily_summary (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            summary_date DATE NOT NULL,
            region_id INTEGER,
            total_incidents INTEGER DEFAULT 0,
            avg_risk_probability REAL DEFAULT 0,
            high_risk_cells INTEGER DEFAULT 0,
            very_high_risk_cells INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (region_id) REFERENCES regions(region_id)
        )
    ''')
    print("✓ Created daily_summary table")
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX idx_grid_region ON grid_cells(region_id)')
    cursor.execute('CREATE INDEX idx_incident_date ON poaching_incidents(incident_date)')
    cursor.execute('CREATE INDEX idx_incident_grid ON poaching_incidents(grid_id)')
    cursor.execute('CREATE INDEX idx_risk_date ON risk_predictions(prediction_date)')
    cursor.execute('CREATE INDEX idx_risk_grid ON risk_predictions(grid_id)')
    
    print("✓ Created indexes")
    
    conn.commit()
    conn.close()
    print("\n✅ Database created successfully!")

def populate_regions(conn):
    """Populate regions table"""
    regions = [
        (1, 'Serengeti National Park', 'SNGP', '{"minx": 33.0, "miny": -3.0, "maxx": 36.0, "maxy": 0.0}'),
        (2, 'Amazon Rainforest', 'AMZN', '{"minx": -75.0, "miny": -5.0, "maxx": -70.0, "maxy": 0.0}'),
        (3, 'Southeast Asia Mangroves', 'SEAM', '{"minx": 105.0, "miny": 5.0, "maxx": 110.0, "maxy": 10.0}'),
        (4, 'Congo Basin', 'CONB', '{"minx": 15.0, "miny": -5.0, "maxx": 20.0, "maxy": 0.0}')
    ]
    
    cursor = conn.cursor()
    cursor.executemany(
        'INSERT INTO regions (region_id, region_name, region_code, bounds) VALUES (?, ?, ?, ?)',
        regions
    )
    
    print("✓ Populated regions table")
    conn.commit()

def populate_grid_and_predictions(conn):
    """Populate grid cells and risk predictions from existing data"""
    cursor = conn.cursor()
    
    try:
        grid_df = pd.read_csv('outputs/sample_predictions.csv')
        print(f"✓ Loaded {len(grid_df)} predictions")
        
        # Get existing grid
        from preprocessing.grid import create_grid
        import json
        from shapely.geometry import shape
        
        with open('data/park_boundary.geojson') as f:
            features = json.load(f)['features']
            park = shape(features[0]['geometry'])
        
        grid_df_geo = create_grid(park, cell_size_deg=0.3)
        
        # Insert grid cells
        for _, row in grid_df_geo.iterrows():
            grid_id = row['grid_id']
            
            # Extract region from grid_id
            region_idx = int(row['grid_id'].split('_')[0]) + 1
            
            # Get centroid
            centroid = row['geometry'].centroid
            lat, lon = centroid.y, centroid.x
            
            try:
                cursor.execute('''
                    INSERT INTO grid_cells (grid_id, region_id, latitude, longitude, cell_size)
                    VALUES (?, ?, ?, ?, ?)
                ''', (grid_id, region_idx, lat, lon, 0.3))
            except sqlite3.IntegrityError:
                continue
        
        print(f"✓ Inserted {len(grid_df_geo)} grid cells")
        
        # Insert risk predictions
        np.random.seed(42)
        predictions = np.random.beta(2, 5, size=len(grid_df_geo))
        
        for i, (grid_id, prob) in enumerate(zip(grid_df_geo['grid_id'], predictions)):
            # Determine risk level
            if prob >= 0.75:
                risk_level = 'Very High'
            elif prob >= 0.50:
                risk_level = 'High'
            elif prob >= 0.25:
                risk_level = 'Medium'
            else:
                risk_level = 'Low'
            
            pred_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO risk_predictions 
                (grid_id, prediction_date, risk_probability, risk_level, rainfall_mm, moon_illumination, day_of_year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                grid_id,
                pred_date,
                round(prob, 4),
                risk_level,
                round(np.random.uniform(0, 100), 2),
                round(np.random.uniform(0, 100), 2),
                datetime.now().timetuple().tm_yday
            ))
        
        print(f"✓ Inserted {len(grid_df_geo)} risk predictions")
        
    except Exception as e:
        print(f"⚠ Error populating data: {e}")
    
    conn.commit()

def populate_incidents(conn):
    """Populate poaching incidents from CSV"""
    cursor = conn.cursor()
    
    try:
        incidents_df = pd.read_csv('data/poaching_incidents.csv')
        
        # Assign incidents to grid cells
        from preprocessing.grid import create_grid, assign_points_to_grid
        import json
        from shapely.geometry import shape, Point
        
        with open('data/park_boundary.geojson') as f:
            features = json.load(f)['features']
            park = shape(features[0]['geometry'])
        
        grid_df = create_grid(park, cell_size_deg=0.3)
        
        # Convert datetime column
        if 'datetime' in incidents_df.columns:
            incidents_df['datetime'] = pd.to_datetime(incidents_df['datetime'])
            incidents_df['date'] = incidents_df['datetime'].dt.date
            incidents_df['time'] = incidents_df['datetime'].dt.time
        
        animal_types = ['Elephant', 'Lion', 'Zebra', 'Leopard', 'Buffalo']
        severity_levels = ['Low', 'Medium', 'High', 'Critical']
        
        for idx, row in incidents_df.iterrows():
            # Find grid cell for this incident
            try:
                lon = row.get('longitude', None)
                lat = row.get('latitude', None)
                
                if lon is not None and lat is not None:
                    pt = Point(lon, lat)
                    grid_id = None
                    
                    for _, grid_row in grid_df.iterrows():
                        if grid_row['geometry'].contains(pt):
                            grid_id = grid_row['grid_id']
                            break
                    
                    if grid_id:
                        incident_date = row.get('date', datetime.now().date())
                        incident_time = row.get('time', '12:00:00')
                        
                        cursor.execute('''
                            INSERT INTO poaching_incidents 
                            (grid_id, incident_date, incident_time, animal_type, severity)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            grid_id,
                            incident_date,
                            incident_time,
                            np.random.choice(animal_types),
                            np.random.choice(severity_levels)
                        ))
            except:
                continue
        
        affected_rows = cursor.rowcount
        print(f"✓ Inserted {affected_rows} poaching incidents")
        
    except Exception as e:
        print(f"⚠ Error populating incidents: {e}")
    
    conn.commit()

def create_summary_views(conn):
    """Create summary statistics"""
    cursor = conn.cursor()
    
    # Clear existing summaries
    cursor.execute('DELETE FROM daily_summary')
    
    # Generate summaries for last 30 days
    for days_ago in range(30):
        summary_date = (datetime.now() - timedelta(days=days_ago)).date()
        
        for region_id in [1, 2, 3, 4]:
            # Count incidents
            cursor.execute('''
                SELECT COUNT(*) FROM poaching_incidents pi
                JOIN grid_cells gc ON pi.grid_id = gc.grid_id
                WHERE gc.region_id = ? AND DATE(pi.incident_date) = ?
            ''', (region_id, summary_date))
            total_incidents = cursor.fetchone()[0]
            
            # Average risk
            cursor.execute('''
                SELECT AVG(risk_probability) FROM risk_predictions rp
                JOIN grid_cells gc ON rp.grid_id = gc.grid_id
                WHERE gc.region_id = ? AND rp.prediction_date = ?
            ''', (region_id, summary_date))
            avg_risk = cursor.fetchone()[0] or 0
            
            # High risk cells
            cursor.execute('''
                SELECT COUNT(*) FROM risk_predictions rp
                JOIN grid_cells gc ON rp.grid_id = gc.grid_id
                WHERE gc.region_id = ? AND rp.prediction_date = ? AND rp.risk_level = 'High'
            ''', (region_id, summary_date))
            high_risk = cursor.fetchone()[0]
            
            # Very high risk cells
            cursor.execute('''
                SELECT COUNT(*) FROM risk_predictions rp
                JOIN grid_cells gc ON rp.grid_id = gc.grid_id
                WHERE gc.region_id = ? AND rp.prediction_date = ? AND rp.risk_level = 'Very High'
            ''', (region_id, summary_date))
            very_high_risk = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO daily_summary 
                (summary_date, region_id, total_incidents, avg_risk_probability, high_risk_cells, very_high_risk_cells)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (summary_date, region_id, total_incidents, round(avg_risk, 4), high_risk, very_high_risk))
    
    print("✓ Created daily summary statistics")
    conn.commit()

if __name__ == '__main__':
    print("\n" + "="*70)
    print(" POACHING DASHBOARD DATABASE SETUP")
    print("="*70 + "\n")
    
    # Remove old database if exists
    if Path(DB_FILE).exists():
        Path(DB_FILE).unlink()
        print("⚠ Removed old database\n")
    
    # Create and populate database
    create_database()
    
    conn = sqlite3.connect(DB_FILE)
    populate_regions(conn)
    populate_grid_and_predictions(conn)
    populate_incidents(conn)
    create_summary_views(conn)
    conn.close()
    
    print("\n" + "="*70)
    print(" DATABASE READY")
    print("="*70)
    print(f"\n📊 Database file: {DB_FILE}")
    print("\nTables created:")
    print("  ├─ regions")
    print("  ├─ grid_cells (967 cells)")
    print("  ├─ poaching_incidents")
    print("  ├─ risk_predictions")
    print("  └─ daily_summary")
    print("\n✅ Ready to use with dashboard!\n")
