import os
import json
import math
import uuid
import re
import statistics
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
import urllib.request
import urllib.parse
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify, send_from_directory
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='.', template_folder='.')

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# ====================================================================
# Pure Python Supabase Direct REST Client (Zero C-Extension Dependency)
# ====================================================================
def query_supabase(table="civic_complaints", method="GET", body=None, params=None):
    if not SUPABASE_URL or not SUPABASE_KEY or "supabase.co" not in SUPABASE_URL:
        return None
        
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    if params:
        url += f"?{urllib.parse.urlencode(params)}"
        
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    try:
        req_data = json.dumps(body).encode('utf-8') if body else None
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body) if res_body else []
    except Exception as e:
        # Fallback cleanly to local in-memory store
        return None

# ====================================================================
# Seed Dataset (Matching Supabase Schema Exactly)
# ====================================================================
def get_initial_complaints():
    now = datetime.now(timezone.utc)
    return [
        {
            "id": "CMP-1001",
            "category": "Water Supply",
            "title": "Yellow muddy water flowing from municipal tap",
            "description": "Since this morning 6 AM, tap water in Block B Sector 4 is dark yellow with bad smell. Cannot drink or cook.",
            "upvotes": 34,
            "timestamp": (now - timedelta(minutes=45)).isoformat(),
            "sla_hours": 12,
            "longitude": 77.2195,
            "latitude": 28.6328,
            "severity": 5,
            "department": "Water & Sewage Board",
            "status": "Escalated",
            "citizen_name": "Aarav Sharma",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1002",
            "category": "Water Supply",
            "title": "Severe pipeline rupture leaking sewage into drinking line",
            "description": "Main water pipeline burst near Sector 4 community center. Dirty gutter water entering drinking pipes.",
            "upvotes": 42,
            "timestamp": (now - timedelta(minutes=75)).isoformat(),
            "sla_hours": 12,
            "longitude": 77.2180,
            "latitude": 28.6340,
            "severity": 5,
            "department": "Water & Sewage Board",
            "status": "In Progress",
            "citizen_name": "Pooja Verma",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1003",
            "category": "Water Supply",
            "title": "No water pressure and brown muddy sediment",
            "description": "Water supply pressure dropped to zero and whatever little water comes is muddy with thick silt in Sector 4.",
            "upvotes": 28,
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "sla_hours": 12,
            "longitude": 77.2210,
            "latitude": 28.6315,
            "severity": 4,
            "department": "Water & Sewage Board",
            "status": "Pending",
            "citizen_name": "Rajesh Kulkarni",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1004",
            "category": "Water Supply",
            "title": "Drinking water contaminated causing stomach illness",
            "description": "Three kids in our lane fell sick after drinking municipal tap water in Sector 4. Urgent water test needed.",
            "upvotes": 56,
            "timestamp": (now - timedelta(hours=2, minutes=30)).isoformat(),
            "sla_hours": 8,
            "longitude": 77.2190,
            "latitude": 28.6335,
            "severity": 5,
            "department": "Water & Sewage Board",
            "status": "Escalated",
            "citizen_name": "Dr. Meenakshi Sundaram",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1005",
            "category": "Water Supply",
            "title": "Foul smelling water coming from main valve",
            "description": "Sector 4 pocket 2 water valve is mixing with open drain overflow. Immediate inspection required.",
            "upvotes": 19,
            "timestamp": (now - timedelta(hours=3)).isoformat(),
            "sla_hours": 12,
            "longitude": 77.2225,
            "latitude": 28.6350,
            "severity": 4,
            "department": "Water & Sewage Board",
            "status": "Pending",
            "citizen_name": "Sunil Rawat",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1006",
            "category": "Water Supply",
            "title": "Underground reservoir polluted by broken pipe",
            "description": "Broken main inlet pipe overflowing next to street 5 underground tank in Sector 4.",
            "upvotes": 23,
            "timestamp": (now - timedelta(hours=3, minutes=45)).isoformat(),
            "sla_hours": 12,
            "longitude": 77.2175,
            "latitude": 28.6305,
            "severity": 5,
            "department": "Water & Sewage Board",
            "status": "In Progress",
            "citizen_name": "Kavita Chawla",
            "locality": "Sector 4"
        },
        # SPIKE 2: Civil Lines Electricity Hazard
        {
            "id": "CMP-1007",
            "category": "Electricity",
            "title": "Transformer sparking and loud explosion sounds",
            "description": "11kV transformer on Pole 42 sparking intensely with smoke emitting. Power fluctuated and tripped 20 houses in Civil Lines.",
            "upvotes": 47,
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
            "sla_hours": 6,
            "longitude": 77.2280,
            "latitude": 28.6750,
            "severity": 5,
            "department": "Electricity Distribution Board",
            "status": "Escalated",
            "citizen_name": "Virender Gill",
            "locality": "Civil Lines"
        },
        {
            "id": "CMP-1008",
            "category": "Electricity",
            "title": "Live dangling wire touching metal road railing",
            "description": "Overhead electrical wire snapped due to fallen branch near Civil Lines metro station gate 2.",
            "upvotes": 51,
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "sla_hours": 4,
            "longitude": 77.2295,
            "latitude": 28.6735,
            "severity": 5,
            "department": "Electricity Distribution Board",
            "status": "In Progress",
            "citizen_name": "Amitabh Sengupta",
            "locality": "Civil Lines"
        },
        {
            "id": "CMP-1009",
            "category": "Electricity",
            "title": "Area blackout and burning plastic smell near substation",
            "description": "Entire Civil Lines block C plunged into darkness. Transformer smoke visible from distance.",
            "upvotes": 38,
            "timestamp": (now - timedelta(hours=1, minutes=45)).isoformat(),
            "sla_hours": 8,
            "longitude": 77.2260,
            "latitude": 28.6765,
            "severity": 4,
            "department": "Electricity Distribution Board",
            "status": "Pending",
            "citizen_name": "Neha Singhal",
            "locality": "Civil Lines"
        },
        {
            "id": "CMP-1010",
            "category": "Electricity",
            "title": "Severe voltage fluctuation burning home appliances",
            "description": "Voltage jumping between 140V and 310V in Civil Lines sector. AC and refrigerator compressor tripped.",
            "upvotes": 29,
            "timestamp": (now - timedelta(hours=2, minutes=15)).isoformat(),
            "sla_hours": 8,
            "longitude": 77.2275,
            "latitude": 28.6740,
            "severity": 4,
            "department": "Electricity Distribution Board",
            "status": "Pending",
            "citizen_name": "Mohd. Tariq",
            "locality": "Civil Lines"
        },
        # SPIKE 3: Road & Potholes (South Extension)
        {
            "id": "CMP-1011",
            "category": "Road & Potholes",
            "title": "Massive crater pothole causing bike accidents",
            "description": "Deep 1.5 ft pothole on Ring Road flyover descent near South Extension. Two motorcyclists skid and suffered injuries today.",
            "upvotes": 65,
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "sla_hours": 18,
            "longitude": 77.2215,
            "latitude": 28.5720,
            "severity": 5,
            "department": "Public Works Department",
            "status": "Escalated",
            "citizen_name": "Gaurav Batra",
            "locality": "South Extension"
        },
        {
            "id": "CMP-1012",
            "category": "Road & Potholes",
            "title": "Caved-in asphalt creating dangerous trench",
            "description": "Left lane of Ring Road near South Ex market caved in after water tanker passed.",
            "upvotes": 33,
            "timestamp": (now - timedelta(hours=3, minutes=10)).isoformat(),
            "sla_hours": 24,
            "longitude": 77.2230,
            "latitude": 28.5745,
            "severity": 4,
            "department": "Public Works Department",
            "status": "In Progress",
            "citizen_name": "Rohit Menghani",
            "locality": "South Extension"
        },
        {
            "id": "CMP-1013",
            "category": "Road & Potholes",
            "title": "Loose gravel and crater spread over 50 meters",
            "description": "Unfinished road patch left open with sharp gravel and big pits on South Ex underpass.",
            "upvotes": 22,
            "timestamp": (now - timedelta(hours=4)).isoformat(),
            "sla_hours": 24,
            "longitude": 77.2200,
            "latitude": 28.5705,
            "severity": 3,
            "department": "Public Works Department",
            "status": "Pending",
            "citizen_name": "Ananya Deshmukh",
            "locality": "South Extension"
        },
        # Other Solid Waste, Sewage, Streetlight Complaints
        {
            "id": "CMP-1014",
            "category": "Waste Management",
            "title": "Overflowing garbage bin blocking pedestrian walkway",
            "description": "Community dumper not cleared for 5 days in Hauz Khas. Garbage spilled onto road creating biohazard and foul stench.",
            "upvotes": 18,
            "timestamp": (now - timedelta(hours=6)).isoformat(),
            "sla_hours": 24,
            "longitude": 77.2090,
            "latitude": 28.5450,
            "severity": 3,
            "department": "Solid Waste Management",
            "status": "Pending",
            "citizen_name": "Priya Nambiar",
            "locality": "Hauz Khas"
        },
        {
            "id": "CMP-1015",
            "category": "Waste Management",
            "title": "Illegal dumping of construction debris on sidewalk",
            "description": "Tractor dumped 4 tons of concrete rubble and bricks blocking entry to Hauz Khas market.",
            "upvotes": 14,
            "timestamp": (now - timedelta(hours=8)).isoformat(),
            "sla_hours": 36,
            "longitude": 77.2065,
            "latitude": 28.5430,
            "severity": 3,
            "department": "Solid Waste Management",
            "status": "In Progress",
            "citizen_name": "Karan Johar",
            "locality": "Hauz Khas"
        },
        {
            "id": "CMP-1016",
            "category": "Street Lighting",
            "title": "All streetlights non-functional in residential avenue",
            "description": "Dark stretch of 800 meters from Lane 3 to Lane 9 in Tilak Marg. High risk of theft and harassment at night.",
            "upvotes": 35,
            "timestamp": (now - timedelta(hours=9)).isoformat(),
            "sla_hours": 24,
            "longitude": 77.2340,
            "latitude": 28.6180,
            "severity": 3,
            "department": "Electrical Maintenance",
            "status": "Pending",
            "citizen_name": "Swati Saxena",
            "locality": "Tilak Marg"
        },
        {
            "id": "CMP-1017",
            "category": "Sewage & Drainage",
            "title": "Open manhole cover missing on busy market street",
            "description": "Heavy cast iron manhole cover stolen or broken in Karol Bagh. Open 10ft drain posing fatal danger to pedestrians.",
            "upvotes": 72,
            "timestamp": (now - timedelta(hours=4, minutes=30)).isoformat(),
            "sla_hours": 6,
            "longitude": 77.1850,
            "latitude": 28.6520,
            "severity": 5,
            "department": "Drainage & Sewerage Board",
            "status": "Escalated",
            "citizen_name": "Manoj Agarwal",
            "locality": "Karol Bagh"
        },
        {
            "id": "CMP-1018",
            "category": "Sewage & Drainage",
            "title": "Black sewage overflowing into front yards of houses",
            "description": "Main sewer line clogged with plastic waste in Karol Bagh. Gutter water backing up through house drains.",
            "upvotes": 31,
            "timestamp": (now - timedelta(hours=10)).isoformat(),
            "sla_hours": 18,
            "longitude": 77.1890,
            "latitude": 28.6500,
            "severity": 4,
            "department": "Drainage & Sewerage Board",
            "status": "In Progress",
            "citizen_name": "Geeta Gupta",
            "locality": "Karol Bagh"
        },
        # Historical Baseline records
        {
            "id": "CMP-1019",
            "category": "Water Supply",
            "title": "Low pressure during morning hours",
            "description": "Water arrives only for 20 minutes with low pressure in Sector 4.",
            "upvotes": 8,
            "timestamp": (now - timedelta(days=1, hours=4)).isoformat(),
            "sla_hours": 48,
            "longitude": 77.2185,
            "latitude": 28.6330,
            "severity": 2,
            "department": "Water & Sewage Board",
            "status": "Resolved",
            "citizen_name": "Suresh Menon",
            "locality": "Sector 4"
        },
        {
            "id": "CMP-1020",
            "category": "Road & Potholes",
            "title": "Small cracks on colony road",
            "description": "Surface bitumen wearing off near park perimeter in South Extension.",
            "upvotes": 5,
            "timestamp": (now - timedelta(days=2, hours=6)).isoformat(),
            "sla_hours": 72,
            "longitude": 77.2220,
            "latitude": 28.5730,
            "severity": 2,
            "department": "Public Works Department",
            "status": "Resolved",
            "citizen_name": "Anita Sen",
            "locality": "South Extension"
        },
        {
            "id": "CMP-1021",
            "category": "Electricity",
            "title": "Flickering street lamp outside house 14",
            "description": "Sodium vapor lamp turning on and off repeatedly in Civil Lines.",
            "upvotes": 4,
            "timestamp": (now - timedelta(days=3, hours=2)).isoformat(),
            "sla_hours": 48,
            "longitude": 77.2270,
            "latitude": 28.6745,
            "severity": 1,
            "department": "Electricity Distribution Board",
            "status": "Resolved",
            "citizen_name": "Tanuja Trivedi",
            "locality": "Civil Lines"
        },
        {
            "id": "CMP-1022",
            "category": "Public Transport",
            "title": "Bus queue shelter roof glass shattered",
            "description": "Bus shelter glass broken by vandals near metro pillar 128 in Lajpat Nagar.",
            "upvotes": 12,
            "timestamp": (now - timedelta(days=3, hours=8)).isoformat(),
            "sla_hours": 48,
            "longitude": 77.2020,
            "latitude": 28.5800,
            "severity": 2,
            "department": "Transport Corporation",
            "status": "Resolved",
            "citizen_name": "Akhil Roy",
            "locality": "Lajpat Nagar"
        },
        {
            "id": "CMP-1023",
            "category": "Public Safety",
            "title": "Encroachment by unauthorized vendors blocking emergency exit",
            "description": "Vegetable carts blocking fire brigade emergency access lane in Karol Bagh market.",
            "upvotes": 29,
            "timestamp": (now - timedelta(days=4, hours=1)).isoformat(),
            "sla_hours": 24,
            "longitude": 77.1860,
            "latitude": 28.6530,
            "severity": 4,
            "department": "Municipal Enforcement",
            "status": "Resolved",
            "citizen_name": "Ashok Singla",
            "locality": "Karol Bagh"
        },
        {
            "id": "CMP-1024",
            "category": "Water Supply",
            "title": "Water meter leakage at main connection",
            "description": "Meter joint leaking clean water on sidewalk in Sector 4.",
            "upvotes": 6,
            "timestamp": (now - timedelta(days=4, hours=14)).isoformat(),
            "sla_hours": 48,
            "longitude": 77.2198,
            "latitude": 28.6322,
            "severity": 2,
            "department": "Water & Sewage Board",
            "status": "Resolved",
            "citizen_name": "Vandana Joshi",
            "locality": "Sector 4"
        }
    ]

complaints_db = get_initial_complaints()

def get_all_complaints():
    global complaints_db
    # Attempt to fetch from Supabase if active
    sb_data = query_supabase("civic_complaints", "GET")
    if sb_data and isinstance(sb_data, list) and len(sb_data) > 0:
        return sb_data
    return complaints_db

# ====================================================================
# Pure Python NLP Classifier & Taxonomy
# ====================================================================
CATEGORY_TAXONOMY = {
    "Water Supply": {
        "keywords": ["water", "pipe", "pipeline", "leak", "tap", "drinking", "smell", "yellow", "muddy", "sediment", "pressure", "tank", "contamination", "chlorine", "borewell", "supply", "pani"],
        "department": "Water & Sewage Board",
        "default_sla": 12
    },
    "Electricity": {
        "keywords": ["transformer", "spark", "sparking", "wire", "power", "blackout", "voltage", "substation", "current", "shock", "phase", "meter", "bijli", "short circuit", "pole"],
        "department": "Electricity Distribution Board",
        "default_sla": 8
    },
    "Road & Potholes": {
        "keywords": ["pothole", "crater", "road", "asphalt", "tar", "flyover", "divider", "traffic", "accident", "gravel", "trench", "caved", "skid", "sadak", "gaddha"],
        "department": "Public Works Department",
        "default_sla": 24
    },
    "Waste Management": {
        "keywords": ["garbage", "trash", "waste", "dumper", "bin", "stench", "rotting", "debris", "plastic", "kachra", "cow", "cattle", "rubble", "litter", "dump"],
        "department": "Solid Waste Management",
        "default_sla": 24
    },
    "Sewage & Drainage": {
        "keywords": ["sewage", "drain", "gutter", "manhole", "overflow", "waterlogging", "clogged", "stinking", "nala", "backflow", "silt", "drainage", "flood"],
        "department": "Drainage & Sewerage Board",
        "default_sla": 12
    },
    "Street Lighting": {
        "keywords": ["streetlight", "lamp", "dark", "light", "bulb", "darkness", "pole", "flickering", "night", "avenue", "lane", "harassment"],
        "department": "Electrical Maintenance",
        "default_sla": 24
    },
    "Public Transport": {
        "keywords": ["bus", "shelter", "stop", "metro", "auto", "stand", "route", "conductor", "transit", "station"],
        "department": "Transport Corporation",
        "default_sla": 48
    },
    "Public Safety": {
        "keywords": ["encroachment", "illegal", "vendor", "fire", "emergency", "theft", "hazard", "threat", "danger", "police", "blocked exit"],
        "department": "Municipal Enforcement",
        "default_sla": 12
    }
}

CRITICAL_KEYWORDS = ["sparking", "explosion", "fire", "accident", "fatal", "hospital", "kids sick", "illness", "poison", "live wire", "open manhole", "caved in", "danger", "burst", "urgent"]
HIGH_KEYWORDS = ["yellow", "muddy", "blackout", "crater", "overflowing", "clogged", "darkness", "tripped", "biohazard", "stench", "severe", "contaminated"]

def classify_text_nlp(text):
    text_lower = text.lower()
    scores = {}
    for cat, data in CATEGORY_TAXONOMY.items():
        score = 0
        for kw in data["keywords"]:
            if kw in text_lower:
                score += 3 if len(kw) > 5 else 1.5
        scores[cat] = score
        
    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        best_category = "Public Safety"
        
    department = CATEGORY_TAXONOMY[best_category]["department"]
    base_sla = CATEGORY_TAXONOMY[best_category]["default_sla"]
    
    severity = 3
    if any(kw in text_lower for kw in CRITICAL_KEYWORDS):
        severity = 5
        base_sla = max(4, int(base_sla * 0.4))
    elif any(kw in text_lower for kw in HIGH_KEYWORDS):
        severity = 4
        base_sla = max(8, int(base_sla * 0.7))
    elif len(text.split()) < 6:
        severity = 2
        base_sla = int(base_sla * 1.5)
        
    return {
        "category": best_category,
        "department": department,
        "severity": severity,
        "sla_hours": base_sla,
        "confidence": min(0.98, 0.65 + (scores[best_category] * 0.05))
    }

# ====================================================================
# Pure Python TF-IDF & Cosine Similarity Engine
# ====================================================================
def tokenize(text):
    return re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

def compute_cosine_similarity(text1, text2):
    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    if not tokens1 or not tokens2:
        return 0.0
        
    vec1 = Counter(tokens1)
    vec2 = Counter(tokens2)
    
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    return float(numerator) / denominator if denominator else 0.0

# ====================================================================
# Analytics & Anomaly Detection Engines
# ====================================================================
def calculate_statistical_spikes():
    complaints = get_all_complaints()
    if not complaints:
        return []

    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(hours=24)
    baseline_cutoff = now - timedelta(days=7)

    recent_complaints = []
    historical_complaints = []

    for c in complaints:
        try:
            ts_str = c['timestamp'].replace('Z', '+00:00')
            ts = datetime.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            ts = now

        if ts >= recent_cutoff:
            recent_complaints.append(c)
        elif ts >= baseline_cutoff:
            historical_complaints.append(c)

    # Group recent complaints by (locality, category)
    groups = defaultdict(list)
    for c in recent_complaints:
        groups[(c['locality'], c['category'])].append(c)

    spikes = []
    for (locality, category), items in groups.items():
        current_count = len(items)
        if current_count < 2:
            continue

        # Historical match count
        hist_match = [h for h in historical_complaints if h['locality'] == locality and h['category'] == category]
        hist_days = 6.0
        hist_daily = len(hist_match) / hist_days if hist_days > 0 else 0.5
        hist_mean = max(0.5, hist_daily)
        hist_std = max(0.4, hist_mean * 0.6)

        z_score = round((current_count - hist_mean) / (hist_std + 0.001), 2)
        surge_percentage = int(((current_count - hist_mean) / hist_mean) * 100) if hist_mean > 0 else 100
        avg_severity = round(statistics.mean([c['severity'] for c in items]), 1)
        evidence_ids = [c['id'] for c in items]

        if (z_score >= 1.8) or (current_count >= 3 and avg_severity >= 4.0):
            lats = [c['latitude'] for c in items if 'latitude' in c]
            lons = [c['longitude'] for c in items if 'longitude' in c]
            spikes.append({
                "locality": locality,
                "category": category,
                "current_count": current_count,
                "baseline_mean": round(hist_mean, 1),
                "z_score": z_score,
                "surge_percentage": max(0, surge_percentage),
                "avg_severity": avg_severity,
                "evidence_rows": evidence_ids,
                "latitude": float(statistics.mean(lats)) if lats else 28.625,
                "longitude": float(statistics.mean(lons)) if lons else 77.215,
                "status": "CRITICAL_SPIKE" if z_score >= 2.5 or avg_severity >= 4.5 else "EMERGING_SURGE",
                "sample_title": items[0]['title'],
                "sample_description": items[0]['description']
            })

    spikes.sort(key=lambda x: (x['z_score'], x['avg_severity']), reverse=True)
    return spikes

def cluster_duplicate_incidents(threshold=0.45):
    complaints = get_all_complaints()
    if len(complaints) < 2:
        return []

    visited = set()
    clusters = []

    for i, c1 in enumerate(complaints):
        if c1['id'] in visited:
            continue

        cluster_members = [c1]
        visited.add(c1['id'])
        desc1 = f"{c1['title']} {c1['description']} {c1['locality']}"

        for j, c2 in enumerate(complaints[i+1:], i+1):
            if c2['id'] not in visited:
                same_loc = c1['locality'] == c2['locality']
                same_cat = c1['category'] == c2['category']
                desc2 = f"{c2['title']} {c2['description']} {c2['locality']}"
                
                sim = compute_cosine_similarity(desc1, desc2)
                effective_sim = sim + (0.25 if (same_loc and same_cat) else 0.0)

                if effective_sim >= threshold:
                    cluster_members.append(c2)
                    visited.add(c2['id'])

        if len(cluster_members) >= 2:
            root_c = max(cluster_members, key=lambda x: x['severity'])
            lats = [c['latitude'] for c in cluster_members if 'latitude' in c]
            lons = [c['longitude'] for c in cluster_members if 'longitude' in c]
            
            clusters.append({
                "cluster_id": f"CLUST-{root_c['id']}",
                "category": root_c['category'],
                "locality": root_c['locality'],
                "department": root_c['department'],
                "incident_title": root_c['title'],
                "parent_id": root_c['id'],
                "complaint_count": len(cluster_members),
                "total_upvotes": sum([c.get('upvotes', 0) for c in cluster_members]),
                "avg_severity": round(statistics.mean([c['severity'] for c in cluster_members]), 1),
                "evidence_rows": [c['id'] for c in cluster_members],
                "complaints": cluster_members,
                "latitude": float(statistics.mean(lats)) if lats else 28.625,
                "longitude": float(statistics.mean(lons)) if lons else 77.215,
                "status": "Escalated" if any(c['status'] == 'Escalated' for c in cluster_members) else "In Progress"
            })

    clusters.sort(key=lambda x: (x['complaint_count'], x['avg_severity']), reverse=True)
    return clusters

def generate_operations_briefing():
    complaints = get_all_complaints()
    spikes = calculate_statistical_spikes()
    clusters = cluster_duplicate_incidents()
    
    total = len(complaints)
    now = datetime.now(timezone.utc)
    
    status_counts = Counter([c.get('status', 'Pending') for c in complaints])
    cat_counts = Counter([c['category'] for c in complaints])
    loc_counts = Counter([c['locality'] for c in complaints])

    briefing_items = []
    
    # 1. Critical Spikes Item
    if spikes:
        for spike in spikes[:3]:
            briefing_items.append({
                "section": "Critical Spikes Detected",
                "priority": "HIGH" if spike['z_score'] >= 2.0 else "MEDIUM",
                "headline": f"Surge in {spike['category']} ({spike['locality']}) - Z-Score: +{spike['z_score']}",
                "detail": f"Observed {spike['current_count']} incidents in past 24h vs baseline of {spike['baseline_mean']} (+{spike['surge_percentage']}% surge). Average severity: {spike['avg_severity']}/5.",
                "action_item": f"Deploy emergency {spike['category']} rapid response unit to {spike['locality']}.",
                "evidence_rows": spike['evidence_rows']
            })
    else:
        briefing_items.append({
            "section": "System Status",
            "priority": "LOW",
            "headline": "No Anomalous Spikes Detected",
            "detail": "All municipal wards are operating within standard historical variance.",
            "action_item": "Continue regular maintenance operations.",
            "evidence_rows": []
        })

    # 2. Clustered High-Impact Incidents
    if clusters:
        for c in clusters[:2]:
            briefing_items.append({
                "section": "Deduplicated Incident Clusters",
                "priority": "HIGH" if c['avg_severity'] >= 4.0 else "MEDIUM",
                "headline": f"Unified Incident: {c['incident_title']} in {c['locality']}",
                "detail": f"{c['complaint_count']} independent citizens reported related occurrences with {c['total_upvotes']} community upvotes.",
                "action_item": f"Assign single resolution task force under {c['department']}.",
                "evidence_rows": c['evidence_rows']
            })

    # 3. SLA & Escalation Alerts
    urgent_cases = [c for c in complaints if c.get('status') != 'Resolved' and c.get('severity', 3) >= 4]
    if urgent_cases:
        top_locs = list(set([c['locality'] for c in urgent_cases]))[:3]
        briefing_items.append({
            "section": "SLA & Escalation Risk",
            "priority": "CRITICAL" if len(urgent_cases) >= 4 else "HIGH",
            "headline": f"{len(urgent_cases)} High-Severity Complaints Active",
            "detail": f"Urgent cases requiring immediate attention across {', '.join(top_locs)}.",
            "action_item": "Mandatory Superintendent review required within 2 hours.",
            "evidence_rows": [c['id'] for c in urgent_cases[:6]]
        })

    return {
        "generated_at": now.strftime("%d %b %Y, %I:%M %p UTC"),
        "total_analyzed_complaints": total,
        "active_spikes_count": len(spikes),
        "clustered_incidents_count": len(clusters),
        "status_breakdown": dict(status_counts),
        "top_categories": dict(cat_counts),
        "top_localities": dict(loc_counts),
        "briefing_items": briefing_items
    }

# ====================================================================
# Routes & API Endpoints
# ====================================================================
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/main.html')
def main_html():
    return send_from_directory('.', 'index.html')

@app.route('/auth')
@app.route('/auth.html')
def auth_page():
    return send_from_directory('.', 'auth.html')

@app.route('/logo.png')
def logo_image():
    return send_from_directory('.', 'logo.png')

@app.route('/<path:path>')
def catch_all_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({
        "status": "online",
        "service": "नगर Drishti AI Engine",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "Supabase PostgreSQL" if SUPABASE_URL and SUPABASE_KEY else "Local Data Engine",
        "records_loaded": len(get_all_complaints())
    })

@app.route('/api/complaints', methods=['GET', 'POST'])
def handle_complaints():
    global complaints_db
    if request.method == 'GET':
        items = get_all_complaints()
        
        cat = request.args.get('category')
        dept = request.args.get('department')
        status = request.args.get('status')
        loc = request.args.get('locality')
        sev = request.args.get('severity')
        search = request.args.get('search', '').lower()

        filtered = []
        for c in items:
            if cat and cat != 'All' and c.get('category') != cat:
                continue
            if dept and dept != 'All' and c.get('department') != dept:
                continue
            if status and status != 'All' and c.get('status') != status:
                continue
            if loc and loc != 'All' and c.get('locality') != loc:
                continue
            if sev and sev != 'All' and str(c.get('severity')) != str(sev):
                continue
            if search:
                haystack = f"{c.get('id','')} {c.get('title','')} {c.get('description','')} {c.get('locality','')}".lower()
                if search not in haystack:
                    continue
            filtered.append(c)

        return jsonify({
            "success": True,
            "count": len(filtered),
            "complaints": filtered
        })

    elif request.method == 'POST':
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        citizen_name = data.get('citizen_name', 'Anonymous Citizen').strip()
        locality = data.get('locality', 'Sector 4').strip()
        latitude = float(data.get('latitude', 28.6328))
        longitude = float(data.get('longitude', 77.2195))

        if not title or not description:
            return jsonify({"success": False, "error": "Title and description required"}), 400

        nlp = classify_text_nlp(f"{title} {description}")
        new_id = f"CMP-{1000 + len(complaints_db) + 1}"
        new_complaint = {
            "id": new_id,
            "category": data.get('category') or nlp['category'],
            "title": title,
            "description": description,
            "upvotes": 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sla_hours": int(data.get('sla_hours') or nlp['sla_hours']),
            "longitude": longitude,
            "latitude": latitude,
            "severity": int(data.get('severity') or nlp['severity']),
            "department": data.get('department') or nlp['department'],
            "status": "Pending",
            "citizen_name": citizen_name,
            "locality": locality
        }

        # Try inserting to Supabase
        query_supabase("civic_complaints", "POST", new_complaint)
        complaints_db.insert(0, new_complaint)

        return jsonify({
            "success": True,
            "message": "Complaint submitted and AI auto-categorized successfully!",
            "complaint": new_complaint,
            "ai_classification": nlp
        }), 201

@app.route('/api/classify', methods=['POST'])
def classify_preview():
    data = request.get_json() or {}
    text = data.get('text', '')
    res = classify_text_nlp(text)
    return jsonify(res)

@app.route('/api/complaints/<id>/status', methods=['PATCH'])
def update_status(id):
    global complaints_db
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['Pending', 'In Progress', 'Resolved', 'Escalated']:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    found = False
    for c in complaints_db:
        if c['id'] == id:
            c['status'] = new_status
            found = True
            break

    query_supabase(f"civic_complaints?id=eq.{id}", "PATCH", {"status": new_status})
    return jsonify({"success": True, "message": f"Status updated to {new_status}"})

@app.route('/api/complaints/<id>/upvote', methods=['POST'])
def upvote(id):
    global complaints_db
    for c in complaints_db:
        if c['id'] == id:
            c['upvotes'] = c.get('upvotes', 0) + 1
            query_supabase(f"civic_complaints?id=eq.{id}", "PATCH", {"upvotes": c['upvotes']})
            return jsonify({"success": True, "upvotes": c['upvotes']})
    return jsonify({"success": False, "error": "Not found"}), 404

@app.route('/api/analytics/spikes')
def get_spikes():
    spikes = calculate_statistical_spikes()
    return jsonify({"success": True, "count": len(spikes), "spikes": spikes})

@app.route('/api/analytics/clusters')
def get_clusters():
    clusters = cluster_duplicate_incidents()
    return jsonify({"success": True, "count": len(clusters), "clusters": clusters})

@app.route('/api/analytics/summary')
def get_summary():
    complaints = get_all_complaints()
    spikes = calculate_statistical_spikes()
    clusters = cluster_duplicate_incidents()
    
    total = len(complaints)
    escalated = len([c for c in complaints if c.get('status') == 'Escalated'])
    in_progress = len([c for c in complaints if c.get('status') == 'In Progress'])
    resolved = len([c for c in complaints if c.get('status') == 'Resolved'])
    pending = len([c for c in complaints if c.get('status') == 'Pending'])
    
    sevs = [c.get('severity', 3) for c in complaints]
    slas = [c.get('sla_hours', 24) for c in complaints]
    avg_sev = round(statistics.mean(sevs), 1) if sevs else 3.0
    avg_sla = round(statistics.mean(slas), 1) if slas else 24.0

    return jsonify({
        "success": True,
        "metrics": {
            "total_complaints": total,
            "active_spikes": len(spikes),
            "duplicate_clusters": len(clusters),
            "escalated_count": escalated,
            "in_progress_count": in_progress,
            "resolved_count": resolved,
            "pending_count": pending,
            "avg_severity": avg_sev,
            "avg_sla_hours": avg_sla
        }
    })

@app.route('/api/analytics/trends')
def get_trends():
    complaints = get_all_complaints()
    now = datetime.now(timezone.utc)
    
    time_labels = []
    current_counts = []
    baseline_counts = []
    
    for i in range(11, -1, -1):
        window_start = now - timedelta(hours=(i + 1) * 2)
        window_end = now - timedelta(hours=i * 2)
        label = window_end.strftime("%H:00")
        time_labels.append(label)
        
        cnt_curr = 0
        for c in complaints:
            try:
                ts = datetime.fromisoformat(c['timestamp'].replace('Z', '+00:00'))
                if ts.tzinfo is None: ts = ts.replace(tzinfo=timezone.utc)
                if window_start <= ts < window_end:
                    cnt_curr += 1
            except Exception:
                pass
        current_counts.append(cnt_curr)
        baseline_counts.append(round(max(0.4, (cnt_curr * 0.3) + 0.5), 1))

    return jsonify({
        "success": True,
        "labels": time_labels,
        "current_24h": current_counts,
        "historical_baseline": baseline_counts
    })

@app.route('/api/analytics/categories')
def get_categories():
    complaints = get_all_complaints()
    counts = Counter([c['category'] for c in complaints])
    return jsonify({
        "success": True,
        "categories": list(counts.keys()),
        "counts": list(counts.values())
    })

@app.route('/api/briefing/generate')
def get_briefing():
    b = generate_operations_briefing()
    return jsonify({"success": True, "briefing": b})

@app.route('/api/simulate/spike', methods=['POST'])
def simulate_spike():
    global complaints_db
    data = request.get_json() or {}
    spike_type = data.get('type', 'water_surge')
    now = datetime.now(timezone.utc)
    
    if spike_type == 'water_surge':
        items = [
            ("Water Supply", "High silt and sewage contamination in sector 4 pocket C", "Water tap outputting dark brown mud and foul chemical odor.", "Sector 4", 28.6330, 77.2188, 5, 8),
            ("Water Supply", "Water main valve fracture flooding street", "Huge water gushing out from broken joint near sector 4 park.", "Sector 4", 28.6342, 77.2201, 5, 8),
            ("Water Supply", "Contaminated muddy water reported in 12 houses", "Multiple residents tested water TDS above 800 with foul smell.", "Sector 4", 28.6320, 77.2175, 4, 12),
        ]
    elif spike_type == 'power_crisis':
        items = [
            ("Electricity", "Major substation transformer blast near main road", "Massive spark flash and burning chemical smell in Civil Lines.", "Civil Lines", 28.6755, 77.2285, 5, 4),
            ("Electricity", "Snapped electric cable sparking on pedestrian path", "11kV wire broke and sparking near vegetable market.", "Civil Lines", 28.6740, 77.2290, 5, 4),
            ("Electricity", "Surge burned elevator motor and home meters", "Instant power spike damaged electronics in apartment building.", "Civil Lines", 28.6760, 77.2270, 4, 6),
        ]
    else:
        items = [
            ("Road & Potholes", "Huge sinkhole opened on South Extension road", "Bus wheel trapped in 2-foot road collapse during morning rush hour.", "South Extension", 28.5730, 77.2220, 5, 12),
            ("Road & Potholes", "Motorbike accident due to hidden pothole filled with water", "Rider injured after hitting unbarricaded road pit.", "South Extension", 28.5740, 77.2235, 5, 12),
        ]

    injected = []
    for cat, title, desc, loc, lat, lon, sev, sla in items:
        new_id = f"CMP-{1000 + len(complaints_db) + 1}"
        c = {
            "id": new_id,
            "category": cat,
            "title": title,
            "description": desc,
            "upvotes": 20,
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
            "sla_hours": sla,
            "longitude": lon,
            "latitude": lat,
            "severity": sev,
            "department": CATEGORY_TAXONOMY[cat]["department"],
            "status": "Escalated",
            "citizen_name": f"Citizen {new_id[-3:]}",
            "locality": loc
        }
        complaints_db.insert(0, c)
        injected.append(c)

    return jsonify({
        "success": True,
        "message": f"Simulated crisis injected! {len(injected)} real-time complaints added.",
        "injected_count": len(injected)
    })

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    role = data.get('role', 'officer')

    if not email:
        return jsonify({"success": False, "error": "Email is required"}), 400

    name_part = email.split('@')[0].replace('.', ' ').title()
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "full_name": f"Officer {name_part}" if role == 'officer' else name_part,
        "role": role,
        "department": "Municipal Operations Command" if role == 'officer' else "Citizen",
        "token": f"token_{uuid.uuid4().hex[:16]}"
    }
    return jsonify({"success": True, "message": f"Welcome, {user['full_name']}!", "user": user})

@app.route('/api/auth/signup', methods=['POST'])
def auth_signup():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'citizen')
    ward = data.get('ward', 'Sector 4')

    if not email or not full_name:
        return jsonify({"success": False, "error": "Email and Full Name required"}), 400

    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "full_name": full_name,
        "role": role,
        "ward": ward,
        "department": "Public Works & Operations" if role == 'officer' else "Citizen",
        "token": f"token_{uuid.uuid4().hex[:16]}"
    }
    return jsonify({"success": True, "message": "Account created successfully!", "user": user}), 201

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"[*] Nagar Drishti Server active on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
