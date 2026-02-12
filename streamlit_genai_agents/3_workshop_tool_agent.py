# -------------------------------------------------------------
# app.py – Water‑Infrastructure Asset Management Dashboard
# -------------------------------------------------------------
import os
import pandas as pd
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from ollama import Client

# -------------------------------------------------------------
# Load environment variables (for Ollama API)
# -------------------------------------------------------------
load_dotenv()
ollama_api_key = os.getenv("ollama_api_key")
ollama_url = os.getenv("ollama_url", "https://ollama.com")

# -------------------------------------------------------------
# Streamlit page configuration
# -------------------------------------------------------------
st.set_page_config(
    page_title="Water‑Infrastructure Asset Manager",
    page_icon="💧",
    layout="wide",
)

# -------------------------------------------------------------
# Header & description
# -------------------------------------------------------------
st.header("💧 Water‑Infrastructure Asset Management Portal")
st.markdown(
    """
    A unified dashboard for **asset inventory, maintenance history, site overview and real‑time sensor data** of the water‑works network.  

    **Features**  
    - 📦 Asset catalogue – search, filter, view technical specs  
    - 🔧 Maintenance logs – filter by date, type, technician, export CSV  
    - 📍 Site dashboard – assets per site, cost per site, status breakdown  
    - 🛰️ **IoT sensor data** – time‑series visualisation, summary stats, export  
    - 🧾 AI‑generated maintenance summary – let Ollama draft a professional report  
    - 📥 Export tools – download any table as CSV  

    _Demo mode – all data are read from the CSV files in the `data/` folder._
    """
)

# -------------------------------------------------------------
# Utility: read CSV files (cached)
# -------------------------------------------------------------
@st.cache_data
def load_csv(file_path: str) -> pd.DataFrame:
    """Read a CSV, handling a possible UTF‑8 BOM."""
    try:
        return pd.read_csv(file_path, encoding="utf-8-sig")
    except FileNotFoundError:
        st.error(f"File not found: `{file_path}` – please check the `data/` folder.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading `{file_path}`: {e}")
        return pd.DataFrame()


# -------------------------------------------------------------
# Load all datasets
# -------------------------------------------------------------
inventory_df = load_csv("data/workshop_agent_data/csv/Inventory Catalogue.csv")
asset_df     = load_csv("data/workshop_agent_data/csv/Asset Registar.csv")
maint_df     = load_csv("data/workshop_agent_data/csv/Maintenance History.csv")
site_df      = load_csv("data/workshop_agent_data/csv/Site Registar.csv")
iot_df       = load_csv("data/workshop_agent_data/csv/IoT Senor Data.csv").head(5000)   # <-- new file


# -------------------------------------------------------------
# Basic cleaning / type conversion
# -------------------------------------------------------------
if not maint_df.empty:
    maint_df["Maintenance Date"] = pd.to_datetime(maint_df["Maintenance Date"], errors="coerce")
    maint_df["Cost (£)"] = pd.to_numeric(maint_df["Cost (£)"], errors="coerce").fillna(0)

if not asset_df.empty:
    asset_df["Installation Date"] = pd.to_datetime(asset_df["Installation Date"], errors="coerce")
    asset_df["Warranty End Date"] = pd.to_datetime(asset_df["Warranty End Date"], errors="coerce")

if not iot_df.empty:
    # Remove hidden BOM from first column name, strip whitespace from all columns
    iot_df.columns = iot_df.columns.str.replace("\ufeff", "", regex=False).str.strip()
    # Ensure column names are exactly what we expect (they already are after the replace)
    # Parse timestamps
    iot_df["Timestamp"] = pd.to_datetime(iot_df["Timestamp"], errors="coerce")

# -------------------------------------------------------------
# Session state – keep generated reports & message history
# -------------------------------------------------------------
if "report_history" not in st.session_state:
    st.session_state.report_history = []

if "current_report" not in st.session_state:
    st.session_state.current_report = ""

# -------------------------------------------------------------
# ==== 1️⃣ Asset Catalogue =================================================
# -------------------------------------------------------------
st.divider()
st.subheader("📦 Asset Catalogue")

col_a, col_b = st.columns([3, 1])
with col_a:
    # Filter options
    asset_type_options = ["All"] + sorted(asset_df["Asset Type"].dropna().unique().tolist())
    status_options      = ["All"] + sorted(asset_df["Status"].dropna().unique().tolist())
    crit_options        = ["All"] + sorted(asset_df["Criticality"].dropna().unique().tolist())

    sel_type   = st.selectbox("Asset Type", asset_type_options, key="filter_type")
    sel_status = st.selectbox("Status", status_options, key="filter_status")
    sel_crit   = st.selectbox("Criticality", crit_options, key="filter_crit")

    # Apply filters
    filtered_assets = asset_df.copy()
    if sel_type != "All":
        filtered_assets = filtered_assets[filtered_assets["Asset Type"] == sel_type]
    if sel_status != "All":
        filtered_assets = filtered_assets[filtered_assets["Status"] == sel_status]
    if sel_crit != "All":
        filtered_assets = filtered_assets[filtered_assets["Criticality"] == sel_crit]

    # Show table (limit rows for performance)
    st.dataframe(
        filtered_assets[
            [
                "Asset ID",
                "Asset Type",
                "Manufacturer",
                "Model Number",
                "Status",
                "Criticality",
                "Installation Date",
                "Site Name",
            ]
        ].reset_index(drop=True),
        use_container_width=True,
        height=350,
    )
with col_b:
    # Quick asset search
    asset_ids = sorted(inventory_df["Asset ID"].dropna().unique().tolist())
    selected_id = st.selectbox("🔎 Search Asset ID", ["Select …"] + asset_ids, key="asset_search")
    if selected_id != "Select …":
        # Show combined info from all tables
        st.markdown("**📄 Asset Overview**")
        inv_row  = inventory_df[inventory_df["Asset ID"] == selected_id].iloc[0]
        spec_row = asset_df[asset_df["Asset ID"] == selected_id].iloc[0]

        st.write(f"- **Asset ID:** {selected_id}")
        st.write(f"- **Type:** {spec_row['Asset Type']}")
        st.write(f"- **Manufacturer / Model:** {spec_row['Manufacturer']} / {spec_row['Model Number']}")
        st.write(f"- **Current Site:** {inv_row['Current Site']}")
        st.write(f"- **Status:** {spec_row['Status']}")
        st.write(f"- **Criticality:** {spec_row['Criticality']}")
        st.write(
            f"- **Installed:** {spec_row['Installation Date'].date() if pd.notnull(spec_row['Installation Date']) else 'N/A'}"
        )
        st.write(
            f"- **Warranty‑ends:** {spec_row['Warranty End Date'].date() if pd.notnull(spec_row['Warranty End Date']) else 'N/A'}"
        )
        st.write(f"- **Operating Hours:** {spec_row['Operating Hours']:,}")

# -------------------------------------------------------------
# ==== 2️⃣ Maintenance History =================================================
# -------------------------------------------------------------
st.divider()
st.subheader("🔧 Maintenance History")

# ---- Filters ----
col1, col2, col3 = st.columns(3)

with col1:
    asset_filter = st.selectbox("Asset ID", ["All"] + asset_ids, key="maint_asset")
with col2:
    date_min = maint_df["Maintenance Date"].min() if not maint_df.empty else None
    date_max = maint_df["Maintenance Date"].max() if not maint_df.empty else None
    start_date = st.date_input("Start date", value=date_min, key="maint_start")
    end_date   = st.date_input("End date",   value=date_max, key="maint_end")
with col3:
    maint_type_options = ["All"] + sorted(maint_df["Maintenance Type"].dropna().unique().tolist())
    maint_type = st.selectbox("Maintenance Type", maint_type_options, key="maint_type")

# ---- Apply filters ----
filtered_maint = maint_df.copy()
if asset_filter != "All":
    filtered_maint = filtered_maint[filtered_maint["Asset ID"] == asset_filter]

if pd.notnull(start_date):
    filtered_maint = filtered_maint[filtered_maint["Maintenance Date"] >= pd.Timestamp(start_date)]

if pd.notnull(end_date):
    filtered_maint = filtered_maint[filtered_maint["Maintenance Date"] <= pd.Timestamp(end_date)]

if maint_type != "All":
    filtered_maint = filtered_maint[filtered_maint["Maintenance Type"] == maint_type]

# ---- Show table & summary ----
st.write(f"**{len(filtered_maint)} records found**")
st.dataframe(
    filtered_maint[
        [
            "Asset ID",
            "Maintenance Date",
            "Maintenance Type",
            "Duration (hrs)",
            "Cost (£)",
            "Technician ID",
        ]
    ]
    .sort_values("Maintenance Date", ascending=False),
    use_container_width=True,
    height=300,
)

# ---- Cost summary ----
if not filtered_maint.empty:
    total_cost = filtered_maint["Cost (£)"].sum()
    st.metric("💰 Total cost (filtered)", f"£{total_cost:,.0f}")

# -------------------------------------------------------------
# ==== 3️⃣ Site Dashboard ====================================================
# -------------------------------------------------------------
st.divider()
st.subheader("📍 Site Overview")

if not site_df.empty:
    # Merge site name into inventory for easy aggregation
    inventory_with_site = inventory_df.merge(
        site_df[["Site Name", "Site Code"]], left_on="Current Site", right_on="Site Name", how="left"
    )
    asset_counts = inventory_with_site["Site Name"].value_counts().rename("Asset Count")
    crit_counts = asset_df["Criticality"].value_counts()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🗂️ Sites", len(site_df))
    with col2:
        st.metric("🔧 Assets total", len(asset_df))
    with col3:
        st.metric("⚠️ Critical assets", crit_counts.get("Critical", 0))

    # Bar chart – assets per site
    st.write("**Assets per site**")
    st.bar_chart(asset_counts)

    # Cost per site (filtered maintenance view)
    cost_per_site = (
        filtered_maint.merge(inventory_df[["Asset ID", "Current Site"]], on="Asset ID", how="left")
        .groupby("Current Site")["Cost (£)"]
        .sum()
        .reset_index()
        .rename(columns={"Cost (£)": "Total Cost (£)"})
    )
    if not cost_per_site.empty:
        st.write("**Maintenance cost per site (current filters)**")
        st.dataframe(cost_per_site.sort_values("Total Cost (£)", ascending=False), use_container_width=True)

# -------------------------------------------------------------
# ==== 4️⃣ IoT Sensor Data ===================================================
# -------------------------------------------------------------
st.divider()
st.subheader("🛰️ IoT Sensor Data")

if iot_df.empty:
    st.info("No IoT sensor data file found or it could not be loaded.")
else:
    # ---------- Filters ----------
    asset_options = ["All"] + sorted(iot_df["Asset ID"].dropna().unique().tolist())
    selected_asset = st.selectbox("Asset ID", asset_options, key="iot_asset")

    # Date range (use the full range of the data as defaults)
    ts_min = iot_df["Timestamp"].min()
    ts_max = iot_df["Timestamp"].max()
    col_a, col_b = st.columns(2)
    with col_a:
        start_ts = st.date_input("Start date", value=ts_min.date() if pd.notnull(ts_min) else datetime.today())
    with col_b:
        end_ts   = st.date_input("End date",   value=ts_max.date() if pd.notnull(ts_max) else datetime.today())

    # ---------- Apply filters ----------
    df_iot = iot_df.copy()
    if selected_asset != "All":
        df_iot = df_iot[df_iot["Asset ID"] == selected_asset]

    start_dt = pd.Timestamp(start_ts)
    end_dt   = pd.Timestamp(end_ts) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # inclusive
    df_iot = df_iot[(df_iot["Timestamp"] >= start_dt) & (df_iot["Timestamp"] <= end_dt)]

    # ---------- Summary metrics ----------
    st.metric("Records", len(df_iot))

    if not df_iot.empty:
        # Compute key statistics (ignore NaNs)
        avg_flow      = df_iot["Flow Rate (m3/s)"].mean()
        max_pressure  = df_iot["Pressure (bar)"].max()
        avg_turbidity = df_iot["Turbidity (NTU)"].mean()
        avg_ph        = df_iot["pH Level"].mean()
        avg_temp      = df_iot["Motor Temperature (°C)"].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Flow (m³/s)", f"{avg_flow:.3f}" if pd.notnull(avg_flow) else "‑")
        with col2:
            st.metric("Max Pressure (bar)", f"{max_pressure:.2f}" if pd.notnull(max_pressure) else "‑")
        with col3:
            st.metric("Avg Turbidity (NTU)", f"{avg_turbidity:.2f}" if pd.notnull(avg_turbidity) else "‑")

        col4, col5 = st.columns(2)
        with col4:
            st.metric("Avg pH", f"{avg_ph:.2f}" if pd.notnull(avg_ph) else "‑")
        with col5:
            st.metric("Avg Motor Temp (°C)", f"{avg_temp:.1f}" if pd.notnull(avg_temp) else "‑")

        # ---------- Table ----------
        with st.expander("Show raw sensor records"):
            st.dataframe(
                df_iot[
                    [
                        "Asset ID",
                        "Timestamp",
                        "Flow Rate (m3/s)",
                        "Pressure (bar)",
                        "Turbidity (NTU)",
                        "pH Level",
                        "Motor Temperature (°C)",
                    ]
                ].sort_values("Timestamp"),
                use_container_width=True,
                height=300,
            )

        # ---------- Time‑series charts ----------
        st.write("**Time‑series visualisations**")
        chart_metrics = [
            ("Flow Rate (m³/s)", "Flow Rate (m3/s)"),
            ("Pressure (bar)", "Pressure (bar)"),
            ("Turbidity (NTU)", "Turbidity (NTU)"),
            ("pH Level", "pH Level"),
            ("Motor Temperature (°C)", "Motor Temperature (°C)"),
        ]

        for title, col_name in chart_metrics:
            st.subheader(title)
            chart_df = df_iot[["Timestamp", col_name]].set_index("Timestamp")
            st.line_chart(chart_df)

        # ---------- Export ----------
        if st.button("📥 Export filtered sensor data", key="export_iot"):
            csv = df_iot.to_csv(index=False).encode()
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="iot_sensor_data_filtered.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("No sensor records match the selected filters.")

# -------------------------------------------------------------
# ==== 5️⃣ Generate AI Maintenance Report ==================================
# -------------------------------------------------------------
st.divider()
st.subheader("📝 Generate Maintenance Status Report (AI‑powered)")

col_a, col_b = st.columns([2, 1])
with col_a:
    report_asset = st.selectbox("Asset (or All)", ["All"] + asset_ids, key="report_asset")
    report_start = st.date_input("From", value=date_min if date_min else datetime.today())
    report_end   = st.date_input("To",   value=date_max if date_max else datetime.today())

with col_b:
    if st.button("🚀 Generate Report", use_container_width=True):
        # -------------------------------------------------
        # Gather context
        # -------------------------------------------------
        if report_asset == "All":
            maint_subset = maint_df[
                (maint_df["Maintenance Date"] >= pd.Timestamp(report_start))
                & (maint_df["Maintenance Date"] <= pd.Timestamp(report_end))
            ]
            assets_considered = "all assets"
        else:
            maint_subset = maint_df[
                (maint_df["Asset ID"] == report_asset)
                & (maint_df["Maintenance Date"] >= pd.Timestamp(report_start))
                & (maint_df["Maintenance Date"] <= pd.Timestamp(report_end))
            ]
            assets_considered = f"Asset {report_asset}"

        total_maint  = len(maint_subset)
        total_cost   = maint_subset["Cost (£)"].sum()
        uniq_techs   = maint_subset["Technician ID"].nunique()

        # -------------------------------------------------
        # Build prompt for Ollama
        # -------------------------------------------------
        prompt = f"""
        You are a professional water‑works asset manager. Write a concise (2‑3 paragraphs) status report
        covering the maintenance activity for {assets_considered} between {report_start:%Y-%m-%d}
        and {report_end:%Y-%m-%d}.

        **Key numbers to embed**
        - Number of maintenance jobs: {total_maint}
        - Total cost: £{total_cost:,.0f}
        - Distinct technicians involved: {uniq_techs}

        If there are no records, say that no maintenance was performed in the period.
        Keep the tone professional and suitable for a senior manager or board audience.
        """

        # -------------------------------------------------
        # Call Ollama (if API key is set)
        # -------------------------------------------------
        if not ollama_api_key:
            st.error("⚠️ OLLAMA_API_KEY not set – add it to `.env` to enable AI generation.")
            st.session_state.current_report = "Error – missing Ollama credentials."
        else:
            try:
                client = Client(
                    host=ollama_url,
                    headers={"Authorization": f"Bearer {ollama_api_key}"},
                )
                response = client.chat(
                    model="gpt-oss:120b-cloud",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful water‑works reporting assistant. Generate concise, professional status updates.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                )
                report_text = ""
                for chunk in response:
                    if isinstance(chunk, dict) and "message" in chunk:
                        report_text += chunk["message"].get("content", "")
                st.session_state.current_report = report_text.strip()
            except Exception as e:
                st.error(f"❌ Error while contacting Ollama: {e}")
                st.session_state.current_report = f"Error generating report: {e}"

# ---- Show generated report & actions ----
if st.session_state.current_report:
    st.divider()
    st.subheader("🗒️ Generated Report")
    edited_report = st.text_area(
        "Edit if needed", value=st.session_state.current_report, height=250, key="editable_report"
    )
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("💾 Save to History", use_container_width=True):
            entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "asset": report_asset,
                "period": f"{report_start} – {report_end}",
                "report": edited_report,
            }
            st.session_state.report_history.append(entry)
            st.success("✅ Report saved to history!")

    with col2:
        if st.button("📋 Copy to clipboard", use_container_width=True):
            st.write(edited_report)  # Streamlit copies the last printed text automatically
            st.toast("Report copied to clipboard!", icon="📋")

    with col3:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.current_report = ""
            st.rerun()

    with col4:
        if st.button("📤 Download as txt", use_container_width=True):
            st.download_button(
                label="Download report",
                data=edited_report,
                file_name=f"maintenance_report_{datetime.now():%Y%m%d_%H%M%S}.txt",
                mime="text/plain",
                use_container_width=True,
            )

# -------------------------------------------------------------
# ==== 6️⃣ History of AI‑generated reports ================================
# -------------------------------------------------------------
st.divider()
st.subheader("📚 Report History")

if st.session_state.report_history:
    for i, entry in enumerate(reversed(st.session_state.report_history)):
        with st.expander(
            f"🗓️ {entry['timestamp']} – Asset: {entry['asset']} – Period: {entry['period']}",
            expanded=False,
        ):
            st.text(entry["report"])
            if st.button(f"🗑️ Delete (#{i})", key=f"del_report_{i}", use_container_width=True):
                st.session_state.report_history.pop(i)
                st.rerun()
else:
    st.info("No AI reports have been generated yet.")

# -------------------------------------------------------------
# ==== 7️⃣ Export raw data ==================================================
# -------------------------------------------------------------
st.divider()
st.subheader("📥 Export Raw Data")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if st.button("Export Asset Inventory", use_container_width=True):
        csv = inventory_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="Inventory_Catalogue.csv",
            mime="text/csv",
            use_container_width=True,
        )

with c2:
    if st.button("Export Asset Details", use_container_width=True):
        csv = asset_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="Asset_Registar.csv",
            mime="text/csv",
            use_container_width=True,
        )

with c3:
    if st.button("Export Maintenance History", use_container_width=True):
        csv = maint_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="Maintenance_History.csv",
            mime="text/csv",
            use_container_width=True,
        )

with c4:
    if st.button("Export Site Register", use_container_width=True):
        csv = site_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="Site_Registar.csv",
            mime="text/csv",
            use_container_width=True,
        )

with c5:
    if st.button("Export IoT Sensor Data", use_container_width=True):
        csv = iot_df.to_csv(index=False).encode()
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="IoT_Sensor_Data.csv",
            mime="text/csv",
            use_container_width=True,
        )

st.caption(
    "💧 Water‑Infrastructure Asset Manager – v1.0 | Built with Streamlit, pandas & Ollama"
)