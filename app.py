import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime
import plotly.express as px

# -------------------- USER LOGIN --------------------
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"

HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"  

# -------------------- UTILITIES --------------------
def parse_date(s: str):
    """Safely parse YYYY-MM-DD to date, else return None."""
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        return None

def badge_expiry(date_str: str):
    """Return 🚨 if expired, ✅ if valid, keep as-is if blank/invalid."""
    d = parse_date(date_str)
    if d is None:
        return date_str
    return ("🚨 " if d < date.today() else "✅ ") + d.strftime("%Y-%m-%d")

# -------------------- GOOGLE SHEETS CONNECTION --------------------
def get_sheets():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    # observation and permit are separate spreadsheets (use first sheet)
    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1

    # equipment workbook (may contain multiple tabs)
    wb = client.open_by_url(EQUIPMENT_URL)

    def get_or_create(ws_title, headers=None):
        try:
            ws = wb.worksheet(ws_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = wb.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws

    heavy_equip_headers = [
        "Equipment type","Plate No.", "Asset code", "T.P inspection date", "T.P Expiry date",
        "Insurance expiry date", "Operator Name", "Iqama NO", "T.P Card type", "T.P Card expiry date",
        "Q.R code", "PWAS status", "F.E TP expiry", "FA box Status", "Documents"
    ]

    heavy_vehicle_headers = [
        "Vehicle Type", "Plate No", "Asset Code", "MVPI Expiry date", "Insurance Expiry",
        "Driver Name", "Iqama No", "Licence Expiry", "Q.R code", "F.A Box",
        "Fire Extinguisher T.P Expiry", "PWAS Status", "Seat belt damaged", "Tyre Condition",
        "Suspension Systems", "Remarks"
    ]

    heavy_equip_sheet = get_or_create(HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)

    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet

# -------------------- LOGIN PAGE --------------------
def login():
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px; margin: 4rem auto; padding: 2rem;
        border-radius: 12px; background-color: white;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .login-title {
        font-size: 32px; font-weight:700; color:#2c3e50;
        margin-bottom:1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🛡️ Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_btn = st.button("Login")
    st.markdown("</div>", unsafe_allow_html=True)

    if login_btn:
        user = USER_CREDENTIALS.get(username)
        if user and user["password"] == password:
            st.session_state.update(logged_in=True, username=username, role=user["role"])
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# -------------------- SIDEBAR --------------------
def sidebar():
    with st.sidebar:
        st.title("🧭 Navigation")
        menu = st.selectbox("Go to", [
            "🏠 Home",
            "📝 Observation Form",
            "🛠️ Permit Form",
            "🏗️ Equipments",
            "📊 Dashboard",
            "🚪 Logout"
        ], key="main_menu")

        if menu == "🏗️ Equipments":
            sub = st.selectbox("Select Equipment", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"], key="equip_sub")
            return sub
        return menu

# -------------------- OBSERVATION FORM --------------------
def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    well_numbers = ["2334", "2556", "1858", "2433", "2553", "2447"]
    with st.form("obs_form", clear_on_submit=True):
        form_date = st.date_input("Date")
        data = {
            "DATE": form_date.strftime("%Y-%m-%d"),
            "WELL NO": st.selectbox("Well No", well_numbers),
            "AREA": st.text_input("Area"),
            "OBSERVER NAME": st.text_input("Observer Name"),
            "OBSERVATION DETAILS": st.text_area("Observation Details"),
            "RECOMMENDED SOLUTION/ACTION TAKEN": st.text_area("Recommended Action"),
            "SUPERVISOR NAME": st.text_input("Supervisor Name"),
            "DISCIPLINE": st.text_input("Discipline"),
            "CATEGORY": st.text_input("Category"),
            "CLASSIFICATION": st.selectbox("Classification", ["POSITIVE", "UNSAFE CONDITION", "UNSAFE ACT"]),
            "STATUS": st.selectbox("Status", ["Open", "Closed"])
        }
        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

# -------------------- PERMIT FORM --------------------
def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    with st.form("permit_form", clear_on_submit=True):
        data = {
            "AREA": st.text_input("Area"),
            "DATE": st.date_input("Date").strftime("%Y-%m-%d"),
            "DRILL SITE": st.text_input("Drill Site"),
            "PERMIT NO": st.text_input("Permit No"),
            "TYPE OF PERMIT": st.text_input("Type of Permit"),
            "ACTIVITY": st.text_area("Activity"),
            "PERMIT RECEIVER": st.text_input("Permit Receiver"),
            "PERMIT ISSUER": st.text_input("Permit Issuer"),
        }
        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Permit submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

# -------------------- HEAVY EQUIPMENT FORM --------------------
def show_equipment_form(sheet):
    st.header("🚜 Heavy Equipment Entry Form")

    EQUIPMENT_LIST = [
        "Excavator", "Backhoe Loader", "Wheel Loader", "Bulldozer",
        "Motor Grader", "Compactor / Roller", "Crane", "Forklift",
        "Boom Truck", "Side Boom", "Hydraulic Drill Unit", "Telehandler", "Skid Loader"
    ]

    with st.form("equipment_form", clear_on_submit=True):  
        equipment_type = st.selectbox("Equipment type", EQUIPMENT_LIST)
        plate_no = st.text_input("Plate No.")
        asset_code = st.text_input("Asset code")
        tp_insp_date = st.date_input("T.P inspection date").strftime("%Y-%m-%d")
        tp_expiry = st.date_input("T.P Expiry date").strftime("%Y-%m-%d")
        insurance_expiry = st.date_input("Insurance expiry date").strftime("%Y-%m-%d")
        operator_name = st.text_input("Operator Name")
        iqama_no = st.text_input("Iqama NO")
        tp_card_type = st.selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_expiry = st.date_input("T.P Card expiry date").strftime("%Y-%m-%d")
        qr_code = st.text_input("Q.R code")
        pwas_status = st.selectbox(
            "PWAS Status",
            ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"]
        )
        fe_tp_expiry = st.date_input("F.E TP expiry").strftime("%Y-%m-%d")
        fa_box_status = st.text_input("FA box Status")
        documents = st.text_input("Documents")

        data = {
            "Equipment type": equipment_type,
            "Plate No.": plate_no,
            "Asset code": asset_code,
            "T.P inspection date": tp_insp_date,
            "T.P Expiry date": tp_expiry,
            "Insurance expiry date": insurance_expiry,
            "Operator Name": operator_name,
            "Iqama NO": iqama_no,
            "T.P Card type": tp_card_type,
            "T.P Card expiry date": tp_card_expiry,
            "Q.R code": qr_code,
            "PWAS status": pwas_status,
            "F.E TP expiry": fe_tp_expiry,
            "FA box Status": fa_box_status,
            "Documents": documents
        }

        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- HEAVY VEHICLE FORM --------------------
def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")

    with st.form("vehicle_form", clear_on_submit=True):
        VEHICLE_LIST = [
            "Bus", "Dump Truck", "Low Bed", "Trailer", "Water Tanker",
            "Coater/Mini Bus", "Drinking Water Tanker", "Painting Truck", "Flat Truck"
        ]

        vehicle_type = st.selectbox("Vehicle Type", VEHICLE_LIST)
        plate_no = st.text_input("Plate No")
        asset_code = st.text_input("Asset Code")
        mvpi_expiry = st.date_input("MVPI Expiry date")
        insurance_expiry = st.date_input("Insurance Expiry")
        driver_name = st.text_input("Driver Name")
        iqama_no = st.text_input("Iqama No")
        licence_expiry = st.date_input("Licence Expiry")
        qr_code = st.text_input("Q.R code")

        fa_box = st.selectbox("F.A Box", ["Available", "Not Available", "Expired", "Inadequate Medicine"])
        fire_ext_tp_expiry = st.date_input("Fire Extinguisher T.P Expiry")

        pwas_status = st.selectbox(
            "PWAS Status",
            ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"]
        )
        seatbelt_damaged = st.selectbox("Seat belt damaged", ["Yes", "No", "N/A"])
        tyre_condition = st.selectbox("Tyre Condition", ["Good", "Worn Out", "Damaged", "Needs Replacement", "N/A"])
        suspension_systems = st.selectbox("Suspension Systems", ["Good", "Faulty", "Needs Repair", "Damaged", "N/A"])
        remarks = st.text_input("Remarks")

        data = {
            "Vehicle Type": vehicle_type,
            "Plate No": plate_no,
            "Asset Code": asset_code,
            "MVPI Expiry date": mvpi_expiry.strftime("%Y-%m-%d"),
            "Insurance Expiry": insurance_expiry.strftime("%Y-%m-%d"),
            "Driver Name": driver_name,
            "Iqama No": iqama_no,
            "Licence Expiry": licence_expiry.strftime("%Y-%m-%d"),
            "Q.R code": qr_code,
            "F.A Box": fa_box,
            "Fire Extinguisher T.P Expiry": fire_ext_tp_expiry.strftime("%Y-%m-%d"),
            "PWAS Status": pwas_status,
            "Seat belt damaged": seatbelt_damaged,
            "Tyre Condition": tyre_condition,
            "Suspension Systems": suspension_systems,
            "Remarks": remarks
        }

        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Heavy Vehicle submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- DASHBOARD (ALL SECTIONS) --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")

    # Tabs for all dashboards
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])

    # ---------- Observation Dashboard ----------
    with tab_obs:
        df = pd.DataFrame(obs_sheet.get_all_records())
        if df.empty:
            st.info("No Observation data.")
        else:
            st.subheader("Observation Records")
            st.dataframe(df)

    # ---------- Permit Dashboard ----------
    with tab_permit:
        df = pd.DataFrame(permit_sheet.get_all_records())
        if df.empty:
            st.info("No Permit data.")
        else:
            st.subheader("Permit Records")
            st.dataframe(df)

    # ---------- Heavy Equipment Dashboard ----------
    with tab_eqp:
        df = pd.DataFrame(heavy_equip_sheet.get_all_records())
        st.subheader("Heavy Equipment Overview")

        if df.empty:
            st.info("No Heavy Equipment data.")
        else:
            # KPIs
            st.metric("Total Equipment", len(df))

            # Count by Equipment type (header: 'Equipment type')
            if "Equipment type" in df.columns:
                cnt = df["Equipment type"].value_counts().reset_index()
                cnt.columns = ["Equipment type", "Count"]
                fig = px.bar(cnt, x="Equipment type", y="Count", title="Count by Equipment Type")
                st.plotly_chart(fig, use_container_width=True)

            # Expiry alerts (use headers from equipment tab)
            for col in ["T.P Expiry date", "Insurance expiry date", "F.E TP expiry", "T.P Card expiry date"]:
                if col in df.columns:
                    df[col] = df[col].apply(badge_expiry)

            with st.expander("📋 Show Equipment Data (with Expiry Alerts)"):
                st.dataframe(df)

    # ---------- Heavy Vehicle Dashboard ----------
    with tab_veh:
        df = pd.DataFrame(heavy_vehicle_sheet.get_all_records())
        st.subheader("Heavy Vehicle Overview")

        if df.empty:
            st.info("No Heavy Vehicle data.")
        else:
            # KPIs
            st.metric("Total Vehicles", len(df))

            # Count by Vehicle type
            if "Vehicle Type" in df.columns:
                cntv = df["Vehicle Type"].value_counts().reset_index()
                cntv.columns = ["Vehicle Type", "Count"]
                fig2 = px.bar(cntv, x="Vehicle Type", y="Count", title="Count by Vehicle Type")
                st.plotly_chart(fig2, use_container_width=True)

            # Pie charts if columns exist
            if "PWAS Status" in df.columns:
                st.plotly_chart(px.pie(df, names="PWAS Status", title="PWAS Status"), use_container_width=True)
            if "Tyre Condition" in df.columns:
                st.plotly_chart(px.pie(df, names="Tyre Condition", title="Tyre Condition"), use_container_width=True)
            if "Suspension Systems" in df.columns:
                st.plotly_chart(px.pie(df, names="Suspension Systems", title="Suspension Systems"), use_container_width=True)

            # Expiry alerts
            for col in ["MVPI Expiry date", "Insurance Expiry", "Licence Expiry", "Fire Extinguisher T.P Expiry"]:
                if col in df.columns:
                    df[col] = df[col].apply(badge_expiry)

            with st.expander("📋 Show Vehicle Data (with Expiry Alerts)"):
                st.dataframe(df)

# -------------------- MAIN APP --------------------
def main():
    if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
        login()
        return

    obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet = get_sheets()
    choice = sidebar()

    if choice == "🏠 Home":
        st.title("📋 Onsite Reporting System")

    elif choice == "📝 Observation Form":
        show_observation_form(obs_sheet)

    elif choice == "🛠️ Permit Form":
        show_permit_form(permit_sheet)

    elif choice == "📊 Dashboard":
        if st.session_state.get("role") == "admin":
            show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet)
        else:
            st.warning("🚫 Access Denied: Admin only.")

    elif choice == "🚜 Heavy Equipment":
        show_equipment_form(heavy_equip_sheet)

    elif choice == "🚚 Heavy Vehicle":
        show_heavy_vehicle_form(heavy_vehicle_sheet)

    elif choice == "🚪 Logout":
        st.session_state.logged_in = False
        st.rerun()

if __name__ == "__main__":
    main()




