# Final Optimised Attempt — 500,000 IoT Records
# Convert timestamps to string to reduce Excel datetime processing overhead

import pandas as pd
import random
from datetime import datetime, timedelta
import uuid

random.seed(42)

# ---------------- SITE REGISTER ----------------
sites = [
    ["SA","Small Water Works - Site A","Water Treatment Works","Cumbernauld, Scotland",55.9469,-3.9900,2500],
    ["SB","Medium Water Works - Site B","Water Treatment Works","Lanark, Scotland",55.6736,-3.7812,8000],
    ["SC","Pumping Station - Site C","Booster Pumping Station","Shotts, Scotland",55.8195,-3.7975,5000],
    ["SD","Raw Water Abstraction - Site D","River Intake & Abstraction","Wishaw, Scotland",55.7720,-3.9185,15000],
]

site_df = pd.DataFrame(sites, columns=[
    "Site Code","Site Name","Site Type","Location",
    "Latitude","Longitude","Capacity (m3/day)"
])

# ---------------- ASSET REGISTER ----------------
asset_types = ["Raw Water Pump","Booster Pump","Motor","VSD Drive","Generator",
               "Chlorine Doser","Rapid Gravity Filter","UF Membrane",
               "Flow Meter","Pressure Transmitter","Level Sensor",
               "Turbidity Sensor","pH Sensor","Control Panel","Isolation Valve"]

manufacturers = ["Grundfos","Sulzer","KSB","Wilo","Siemens","ABB","Schneider","Hach","Xylem"]

assets = []
asset_id = 1000

for site in site_df["Site Name"]:
    for _ in range(30):
        install_date = datetime.now() - timedelta(days=random.randint(1000,4000))
        assets.append([
            f"WC-{asset_id}",
            random.choice(asset_types),
            random.choice(manufacturers),
            f"MDL-{random.randint(1000,9999)}",
            f"SN-{uuid.uuid4().hex[:8].upper()}",
            install_date.date().isoformat(),
            (install_date + timedelta(days=365*5)).date().isoformat(),
            site,
            random.choice(["Operational","Standby","Under Maintenance"]),
            random.choice(["Critical","High","Medium"]),
            random.randint(5000,60000),
            random.randint(5000,250000),
            random.choice(["Excellent","Good","Fair"]),
            f"ENG-{random.randint(101,130)}"
        ])
        asset_id += 1

asset_df = pd.DataFrame(assets, columns=[
    "Asset ID","Asset Type","Manufacturer","Model Number","Serial Number",
    "Installation Date","Warranty End Date","Site Name","Status",
    "Criticality","Operating Hours","Acquisition Cost (£)",
    "Condition","Responsible Engineer"
])

# ---------------- INVENTORY ----------------
inventory = []
for _, row in asset_df.iterrows():
    origin = random.choice(site_df["Site Name"].tolist())
    inventory.append([
        row["Asset ID"],
        origin,
        row["Site Name"],
        random.randint(0,2),
        "",
        f"Transferred from {origin}. Commissioned under QA standards."
    ])

inventory_df = pd.DataFrame(inventory, columns=[
    "Asset ID","Origin Site","Current Site",
    "Transfer Count","Last Transfer Date","Notes"
])

# ---------------- MAINTENANCE ----------------
maintenance = []
for asset in asset_df["Asset ID"]:
    for _ in range(5):
        maintenance.append([
            asset,
            (datetime.now() - timedelta(days=random.randint(30,1500))).date().isoformat(),
            random.choice(["Preventive","Corrective","Inspection","Calibration"]),
            random.randint(2,16),
            random.randint(200,10000),
            f"TECH-{random.randint(201,250)}"
        ])

maintenance_df = pd.DataFrame(maintenance, columns=[
    "Asset ID","Maintenance Date","Maintenance Type",
    "Duration (hrs)","Cost (£)","Technician ID"
])

# ---------------- IoT DATA (500k) ----------------
records = 500000
start_date = datetime.now() - timedelta(days=90)
asset_sample = asset_df.sample(50)["Asset ID"].tolist()

iot_rows = []
for i in range(records):
    timestamp = (start_date + timedelta(minutes=i % 129600)).isoformat()
    iot_rows.append([
        random.choice(asset_sample),
        timestamp,
        round(random.uniform(2.5,8.5),3),
        round(random.uniform(1.0,6.0),3),
        round(random.uniform(0,10),3),
        round(random.uniform(6.5,8.5),3),
        round(random.uniform(5,40),2)
    ])

iot_df = pd.DataFrame(iot_rows, columns=[
    "Asset ID","Timestamp","Flow Rate (m3/s)","Pressure (bar)",
    "Turbidity (NTU)","pH Level","Motor Temperature (°C)"
])

# ---------------- SAVE ----------------
file_path = "data/uk_water_company_asset_model.xlsx"

with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
    # asset_df.to_excel(writer, sheet_name="Asset Register", index=False)
    inventory_df.to_excel(writer, sheet_name="Inventory Catalogue", index=False)
    # maintenance_df.to_excel(writer, sheet_name="Maintenance History", index=False)
    # site_df.to_excel(writer, sheet_name="Site Register", index=False)
    iot_df.to_excel(writer, sheet_name="IoT Sensor Data", index=False)

file_path
