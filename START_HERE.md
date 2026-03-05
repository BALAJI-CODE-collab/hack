# 🎬 PRESENTATION PACKAGE - START HERE

## WHAT YOU HAVE

Your complete 3-minute presentation system is ready:

✅ **Interactive Map** - 4 regions, color-coded risk
✅ **SQL Database** - 967 grid cells with poaching data  
✅ **Analytics Dashboard** - Hotspot detection & analysis
✅ **3-Minute Script** - Ready to present

---

## QUICK START - 3 STEPS

### STEP 1: OPEN THE MAP (0-55 seconds)
```bash
# Open in web browser:
C:\Project\outputs\risk_map.html
```
**What you'll see:**
- 4 forest regions with colored boundaries
- Red zones = urgent poaching risk
- Orange zones = high risk
- Yellow zones = medium risk
- Blue zones = low risk
- Professional title at top
- Full legend on the right

**What to point out during presentation:**
- "This is Serengeti with these red hotspots here..."
- "This is Amazon with mixed risk colors..."
- "This is Mangroves and Congo Basin..."
- Zoom in to show detail, zoom out to show all 4

---

### STEP 2: RUN THE DASHBOARD (55-165 seconds)
```bash
cd C:\Project
streamlit run dashboard_fixed.py
```

**Opens at:** http://localhost:8501

**What you'll see:**
- Top metrics: Total incidents, average risk, high risk areas
- Bar chart: Which region has most incidents
- Pie chart: Risk distribution across colors
- **Hotspots table** - THE KEY FEATURE
  - Top 15 grid cells by incident count
  - Shows exact latitude/longitude
  - Shows incident counts
  - Shows risk percentage
  - Rangers use this to know WHERE to patrol

**What to point out during presentation:**
- "This grid cell here had 8 incidents - that's our #1 hotspot"
- "Coordinates are 5.2°S, 31.4°E - rangers go there first"
- "This cell is 78% risk probability - Very High danger"
- "The table automatically shows the top priority locations"

---

### STEP 3: DELIVER SCRIPT (165-180 seconds)
Use **PRESENTATION_3MIN_READY.md** while presenting

**What to say:**
- Opening: Introduce system (10 seconds)
- Challenge: Why this matters (20 seconds)  
- Solution: How it works (40 seconds)
- Impact: Results and benefits (30 seconds)

---

## FILES IN ORDER

### FOR VIDEO RECORDING:
1. **PRESENTATION_3MIN_READY.md** ← **USE THIS**
   - SAY column = what to speak
   - SHOW column = what to display
   - Exact 180-second timing

### FOR REFERENCE:
2. SCRIPT_3MIN.md (longer version with details)
3. SAY_AND_SHOW_3MIN.md (previous version)

### FOR RUNNING:
4. **outputs/risk_map.html** ← Open in browser
5. **dashboard_fixed.py** ← Run with streamlit

### FOR SUBMISSION:
6. INNOVATION_SUBMISSION_TITLES.md (title suggestions)
7. All Python source files (models/, preprocessing/, etc.)

---

## EXACT PRESENTATION SEQUENCE

### TIME 0:00-0:25 (Intro)
```
YOU: Say opening line
SCREEN: Show risk_map.html with all 4 regions visible
SHOW: Zoom/pan across map to display regions
```

### TIME 0:25-0:55 (Challenge)
```
YOU: Describe problem statement
SCREEN: Keep map visible, point to red zones
SHOW: Zoom to Serengeti hotspots (show red clearly)
```

### TIME 0:55-1:50 (How It Works)
```
YOU: Explain AI system and regions
SCREEN: Zoom around to each region
SHOW: Amazon (red zones), Mangroves (red zones), Congo (red zones)
SHOW: Zoom out to display all 4 together
```

### TIME 1:50-2:45 (Dashboard)
```
YOU: Explain dashboard and hotspots
SCREEN: Switch to browser with dashboard running
SHOW: Top metrics visible
SHOW: Scroll to Hotspots table
SHOW: Point to top grid cells with coordinates
SHOW: Show incident counts and risk percentages
```

### TIME 2:45-3:00 (Closing)
```
YOU: Impact statement and closing
SCREEN: Full map view of all 4 regions
SHOW: Return to map for final visual impact
```

---

## CRITICAL REMINDERS

### ✅ DO THIS:
- Use `dashboard_fixed.py` (not the old `dashboard.py`)
- Speak clearly, not rushed
- Pause to let visuals be seen
- Point naturally at screen
- Make eye contact with camera 1/3 of time
- Show screen 2/3 of time

### ❌ DON'T DO THIS:
- Don't read code line-by-line
- Don't show error messages
- Don't use the old `dashboard.py` (it has threading errors)
- Don't scroll too fast
- Don't use system terminal in recording (just show app)

---

## TIMING CHECK

**Your script = exactly 180 seconds**

| Section | Script Time | Plus transitions | Total |
|---------|-------------|-----------------|-------|
| Intro | 20s | +5s pause | 25s |
| Challenge | 30s | +0s | 30s |
| Ecosystems | 45s | +5s zoom | 50s |
| AI/Dashboard | 45s | +0s | 45s |
| Hotspots view | 15s | +0s | 15s |
| Closing | 10s | +5s final view | 15s |
| **TOTAL** | **165s** | **+15s** | **180s** |

---

## TECHNICAL DETAILS

### Database Status:
- ✅ Created: poaching_dashboard.db
- ✅ Tables: 5 (regions, grid_cells, incidents, predictions, summary)
- ✅ Populated: 967 grid cells across 4 regions
- ✅ Ready: Yes, fully functional

### Map Status:
- ✅ Generated: outputs/risk_map.html
- ✅ Regions: 4 (Serengeti, Amazon, Mangroves, Congo)
- ✅ Grid cells: 967 cells with color-coded risk
- ✅ Ready: Yes, open in any browser

### Dashboard Status:
- ✅ Created: dashboard_fixed.py (FIXED VERSION)
- ✅ Type: Streamlit web app
- ✅ Features: Metrics, charts, hotspots table, filters
- ✅ Ready: Yes, run with `streamlit run dashboard_fixed.py`

---

## SUBMISSION CHECKLIST

For innovation competition, include:

- [ ] SCRIPT_3MIN.md (or PRESENTATION_3MIN_READY.md)
- [ ] outputs/risk_map.html (interactive map)
- [ ] Video recording (3 minutes following script)
- [ ] dashboard_fixed.py (source code)
- [ ] poaching_dashboard.db (database)
- [ ] INNOVATION_SUBMISSION_TITLES.md (title options)
- [ ] All Python source files in models/, preprocessing/, etc.
- [ ] README.md explaining system architecture

---

## SUCCESS INDICATORS

✅ Map shows all 4 regions with distinct colors
✅ Red zones are visible in every region
✅ Dashboard displays hotspots table
✅ Dashboard shows top 15 grid cells with coordinates
✅ All metrics display correctly
✅ Script reads naturally in 3 minutes
✅ No code visible in video
✅ No error messages in video
✅ Professional appearance throughout

---

## IF YOU GET STUCK

**Map not showing?**
- Wrong: C:\Project\outputs\risk_map.html
- Right: Open in browser, not Python

**Dashboard won't run?**
- Wrong: `streamlit run dashboard.py`
- Right: `streamlit run dashboard_fixed.py`

**Script too long?**
- Cut: Reduce ecosystem details
- Trim: Remove "very" and filler words
- Combine: Merge Congo/Amazon descriptions

**No red zones showing?**
- The map uses percentile-based coloring
- Regenerate with: `python gen_map.py`
- Check: outputs/risk_map.html opens correctly

---

🎬 YOU'RE READY TO PRESENT!

**Next Step:** Record your 3-minute video using PRESENTATION_3MIN_READY.md
