-- ====================================================================
-- नगर Drishti (Civic Incident Intelligence Platform)
-- Supabase PostgreSQL Database Setup Script
-- ====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Drop existing tables if re-initializing (Optional/Clean run)
-- DROP TABLE IF EXISTS public.civic_complaints CASCADE;
-- DROP TABLE IF EXISTS public.user_profiles CASCADE;

-- 3. Create 'civic_complaints' Table (Matching Schema Diagram Exactly)
CREATE TABLE IF NOT EXISTS public.civic_complaints (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    upvotes INT4 DEFAULT 0,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    sla_hours INT4 DEFAULT 24,
    longitude FLOAT8 NOT NULL,
    latitude FLOAT8 NOT NULL,
    severity INT4 DEFAULT 3 CHECK (severity BETWEEN 1 AND 5),
    department TEXT NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'In Progress', 'Resolved', 'Escalated')),
    citizen_name TEXT DEFAULT 'Anonymous Citizen',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    locality TEXT DEFAULT 'Central Zone'
);

-- 4. Create 'user_profiles' Table for Auth & Role Management
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT DEFAULT 'citizen' CHECK (role IN ('citizen', 'officer', 'admin')),
    department TEXT,
    ward TEXT DEFAULT 'Ward 1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Performance & Analytical Indexes
CREATE INDEX IF NOT EXISTS idx_complaints_timestamp ON public.civic_complaints (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_category ON public.civic_complaints (category);
CREATE INDEX IF NOT EXISTS idx_complaints_department ON public.civic_complaints (department);
CREATE INDEX IF NOT EXISTS idx_complaints_status ON public.civic_complaints (status);
CREATE INDEX IF NOT EXISTS idx_complaints_severity ON public.civic_complaints (severity DESC);
CREATE INDEX IF NOT EXISTS idx_complaints_location ON public.civic_complaints (latitude, longitude);

-- 6. Row Level Security (RLS) Configuration
ALTER TABLE public.civic_complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Allow public read & insert for hackathon prototype/citizens
CREATE POLICY "Allow public read on civic_complaints" 
    ON public.civic_complaints FOR SELECT USING (true);

CREATE POLICY "Allow public insert on civic_complaints" 
    ON public.civic_complaints FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow authenticated update on civic_complaints" 
    ON public.civic_complaints FOR UPDATE USING (true);

CREATE POLICY "Allow public read on user_profiles" 
    ON public.user_profiles FOR SELECT USING (true);

CREATE POLICY "Allow public insert on user_profiles" 
    ON public.user_profiles FOR INSERT WITH CHECK (true);

-- ====================================================================
-- 7. Realistic Seed Dataset (50+ Real-World Multidisciplinary Complaints)
-- Includes Historical Baseline + Scripted Active Emerging Spikes:
-- Spike 1: Contaminated Water / Pipeline Burst in "Sector 4 / Ward 12"
-- Spike 2: High Voltage Surge & Transformer Sparks in "Civil Lines"
-- Spike 3: Deep Monsoon Potholes & Road Cracking on "Ring Road"
-- ====================================================================

INSERT INTO public.civic_complaints (id, category, title, description, upvotes, timestamp, sla_hours, longitude, latitude, severity, department, status, citizen_name, locality)
VALUES
-- ACTIVE SPIKE 1: WATER CRISIS (Sector 4 / Ward 12)
('CMP-1001', 'Water Supply', 'Yellow muddy water flowing from municipal tap', 'Since this morning 6 AM, tap water in Block B Sector 4 is dark yellow with bad smell. Cannot drink or cook.', 34, NOW() - INTERVAL '45 minutes', 12, 77.2195, 28.6328, 5, 'Water & Sewage Board', 'Escalated', 'Aarav Sharma', 'Sector 4'),
('CMP-1002', 'Water Supply', 'Severe pipeline rupture leaking sewage into drinking line', 'Main water pipeline burst near Sector 4 community center. Dirty gutter water entering drinking pipes.', 42, NOW() - INTERVAL '1 hour 15 minutes', 12, 77.2180, 28.6340, 5, 'Water & Sewage Board', 'In Progress', 'Pooja Verma', 'Sector 4'),
('CMP-1003', 'Water Supply', 'No water pressure and brown muddy sediment', 'Water supply pressure dropped to zero and whatever little water comes is muddy with thick silt.', 28, NOW() - INTERVAL '2 hours', 12, 77.2210, 28.6315, 4, 'Water & Sewage Board', 'Pending', 'Rajesh Kulkarni', 'Sector 4'),
('CMP-1004', 'Water Supply', 'Drinking water contaminated causing stomach illness', 'Three kids in our lane fell sick after drinking municipal tap water. Water tests show chemical residue.', 56, NOW() - INTERVAL '2 hours 30 minutes', 8, 77.2190, 28.6335, 5, 'Water & Sewage Board', 'Escalated', 'Dr. Meenakshi Sundaram', 'Sector 4'),
('CMP-1005', 'Water Supply', 'Foul smelling water coming from main valve', 'Sector 4 pocket 2 water valve is mixing with open drain overflow. Immediate inspection required.', 19, NOW() - INTERVAL '3 hours', 12, 77.2225, 28.6350, 4, 'Water & Sewage Board', 'Pending', 'Sunil Rawat', 'Sector 4'),
('CMP-1006', 'Water Supply', 'Underground reservoir polluted by broken pipe', 'Broken main inlet pipe overflowing next to street 5 underground tank in Sector 4.', 23, NOW() - INTERVAL '3 hours 45 minutes', 12, 77.2175, 28.6305, 5, 'Water & Sewage Board', 'In Progress', 'Kavita Chawla', 'Sector 4'),

-- ACTIVE SPIKE 2: ELECTRICAL HAZARD (Civil Lines)
('CMP-1007', 'Electricity', 'Transformer sparking and loud explosion sounds', '11kV transformer on Pole 42 sparking intensely with smoke emitting. Power fluctuated and tripped 20 houses.', 47, NOW() - INTERVAL '30 minutes', 6, 77.2280, 28.6750, 5, 'Electricity Distribution Board', 'Escalated', 'Virender Gill', 'Civil Lines'),
('CMP-1008', 'Electricity', 'Live dangling wire touching metal road railing', 'Overhead electrical wire snapped due to fallen branch near Civil Lines metro station gate 2.', 51, NOW() - INTERVAL '1 hour', 4, 77.2295, 28.6735, 5, 'Electricity Distribution Board', 'In Progress', 'Amitabh Sengupta', 'Civil Lines'),
('CMP-1009', 'Electricity', 'Area blackout and burning plastic smell near substation', 'Entire Civil Lines block C plunged into darkness. Transformer smoke visible from distance.', 38, NOW() - INTERVAL '1 hour 45 minutes', 8, 77.2260, 28.6765, 4, 'Electricity Distribution Board', 'Pending', 'Neha Singhal', 'Civil Lines'),
('CMP-1010', 'Electricity', 'Severe voltage fluctuation burning home appliances', 'Voltage jumping between 140V and 310V in Civil Lines sector. AC and refrigerator compressor tripped.', 29, NOW() - INTERVAL '2 hours 15 minutes', 8, 77.2275, 28.6740, 4, 'Electricity Distribution Board', 'Pending', 'Mohd. Tariq', 'Civil Lines'),

-- ACTIVE SPIKE 3: ROAD SAFETY & POTHOLES (Ring Road / South Extension)
('CMP-1011', 'Road & Potholes', 'Massive crater pothole causing bike accidents', 'Deep 1.5 ft pothole on Ring Road flyover descent. Two motorcyclists skid and suffered injuries today.', 65, NOW() - INTERVAL '2 hours', 18, 77.2215, 28.5720, 5, 'Public Works Department', 'Escalated', 'Gaurav Batra', 'South Extension'),
('CMP-1012', 'Road & Potholes', 'Caved-in asphalt creating dangerous trench', 'Left lane of Ring Road near South Ex market caved in after water tanker passed.', 33, NOW() - INTERVAL '3 hours 10 minutes', 24, 77.2230, 28.5745, 4, 'Public Works Department', 'In Progress', 'Rohit Menghani', 'South Extension'),
('CMP-1013', 'Road & Potholes', 'Loose gravel and crater spread over 50 meters', 'Unfinished road patch left open with sharp gravel and big pits on South Ex underpass.', 22, NOW() - INTERVAL '4 hours', 24, 77.2200, 28.5705, 3, 'Public Works Department', 'Pending', 'Ananya Deshmukh', 'South Extension'),
('CMP-1014', 'Road & Potholes', 'Broken road divider concrete slab lying in fast lane', 'Divider barrier shattered and large concrete blocks blocking incoming traffic.', 41, NOW() - INTERVAL '5 hours', 12, 77.2245, 28.5760, 5, 'Public Works Department', 'Resolved', 'Harpreet Singh', 'South Extension'),

-- SOLID WASTE MANAGEMENT
('CMP-1015', 'Waste Management', 'Overflowing garbage bin blocking pedestrian walkway', 'Community dumper not cleared for 5 days. Garbage spilled onto road creating biohazard and foul stench.', 18, NOW() - INTERVAL '6 hours', 24, 77.2090, 28.5450, 3, 'Solid Waste Management', 'Pending', 'Priya Nambiar', 'Hauz Khas'),
('CMP-1016', 'Waste Management', 'Illegal dumping of construction debris on sidewalk', 'Tractor dumped 4 tons of concrete rubble and bricks blocking entry to Hauz Khas market.', 14, NOW() - INTERVAL '8 hours', 36, 77.2065, 28.5430, 3, 'Solid Waste Management', 'In Progress', 'Karan Johar', 'Hauz Khas'),
('CMP-1017', 'Waste Management', 'Stray cattle feeding on plastic dump near school gate', 'Unattended open garbage point near primary school attracting stray animals and flies.', 27, NOW() - INTERVAL '14 hours', 24, 77.1980, 28.5490, 4, 'Solid Waste Management', 'Pending', 'Deepak Tiwari', 'Hauz Khas'),

-- STREET LIGHTING & SAFETY
('CMP-1018', 'Street Lighting', 'All streetlights non-functional in residential avenue', 'Dark stretch of 800 meters from Lane 3 to Lane 9. High risk of theft and harassment at night.', 35, NOW() - INTERVAL '9 hours', 24, 77.2340, 28.6180, 3, 'Electrical Maintenance', 'Pending', 'Swati Saxena', 'Tilak Marg'),
('CMP-1019', 'Street Lighting', 'Broken streetlight pole tilting dangerously over road', 'Light pole base rusted and leaning at 45 degrees towards school bus route.', 43, NOW() - INTERVAL '11 hours', 12, 77.2320, 28.6210, 5, 'Electrical Maintenance', 'In Progress', 'Lt. Col. VK Nair', 'Tilak Marg'),

-- SEWAGE & DRAINAGE
('CMP-1020', 'Sewage & Drainage', 'Open manhole cover missing on busy market street', 'Heavy cast iron manhole cover stolen or broken. Open 10ft drain with only temporary tree branch placed.', 72, NOW() - INTERVAL '4 hours 30 minutes', 6, 77.1850, 28.6520, 5, 'Drainage & Sewerage Board', 'Escalated', 'Manoj Agarwal', 'Karol Bagh'),
('CMP-1021', 'Sewage & Drainage', 'Black sewage overflowing into front yards of houses', 'Main sewer line clogged with plastic waste. Gutter water backing up through house drains.', 31, NOW() - INTERVAL '10 hours', 18, 77.1890, 28.6500, 4, 'Drainage & Sewerage Board', 'In Progress', 'Geeta Gupta', 'Karol Bagh'),
('CMP-1022', 'Sewage & Drainage', 'Stormwater drain blocked by silt causing waterlogging', 'Even light drizzle causes knee-deep water accumulation on Karol Bagh main road.', 24, NOW() - INTERVAL '16 hours', 24, 77.1870, 28.6545, 3, 'Drainage & Sewerage Board', 'Pending', 'Vivek Bhasin', 'Karol Bagh'),

-- HISTORICAL BASELINE SAMPLES (Past 2 to 7 days for rolling stats)
('CMP-1023', 'Water Supply', 'Low pressure during morning hours', 'Water arrives only for 20 minutes with low pressure.', 8, NOW() - INTERVAL '1 day 4 hours', 48, 77.2185, 28.6330, 2, 'Water & Sewage Board', 'Resolved', 'Suresh Menon', 'Sector 4'),
('CMP-1024', 'Road & Potholes', 'Small cracks on colony road', 'Surface bitumen wearing off near park perimeter.', 5, NOW() - INTERVAL '2 days 6 hours', 72, 77.2220, 28.5730, 2, 'Public Works Department', 'Resolved', 'Anita Sen', 'South Extension'),
('CMP-1025', 'Waste Management', 'Green waste collection bin full', 'Dry leaves and branches piled up near park gate.', 9, NOW() - INTERVAL '2 days 10 hours', 48, 77.2080, 28.5440, 2, 'Solid Waste Management', 'Resolved', 'Balraj Sahni', 'Hauz Khas'),
('CMP-1026', 'Electricity', 'Flickering street lamp outside house 14', 'Sodium vapor lamp turning on and off repeatedly.', 4, NOW() - INTERVAL '3 days 2 hours', 48, 77.2270, 28.6745, 1, 'Electricity Distribution Board', 'Resolved', 'Tanuja Trivedi', 'Civil Lines'),
('CMP-1027', 'Public Transport', 'Bus queue shelter roof glass shattered', 'Bus shelter shelter glass broken by vandals near metro pillar 128.', 12, NOW() - INTERVAL '3 days 8 hours', 48, 77.2020, 28.5800, 2, 'Transport Corporation', 'Resolved', 'Akhil Roy', 'Lajpat Nagar'),
('CMP-1028', 'Public Safety', 'Encroachment by unauthorized vendors blocking emergency exit', 'Vegetable carts blocking fire brigade emergency access lane.', 29, NOW() - INTERVAL '4 days 1 hour', 24, 77.1860, 28.6530, 4, 'Municipal Enforcement', 'Resolved', 'Ashok Singla', 'Karol Bagh'),
('CMP-1029', 'Water Supply', 'Water meter leakage at main connection', 'Meter joint leaking clean water on sidewalk.', 6, NOW() - INTERVAL '4 days 14 hours', 48, 77.2198, 28.6322, 2, 'Water & Sewage Board', 'Resolved', 'Vandana Joshi', 'Sector 4'),
('CMP-1030', 'Waste Management', 'Commercial waste dumping behind hotel', 'Kitchen organic waste dumped on open plot causing rodent menace.', 21, NOW() - INTERVAL '5 days 6 hours', 24, 77.2075, 28.5465, 3, 'Solid Waste Management', 'Resolved', 'Sameer Qureshi', 'Hauz Khas');

-- ====================================================================
-- End of Supabase Database Setup Script
-- ====================================================================
