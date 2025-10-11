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
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        return None

def badge_expiry(date_str: str):
    d = parse_date(date_str)
    if d is None:
        return date_str
    return ("🚨 " if d < date.today() else "✅ ") + d.strftime("%Y-%m-%d")

def expiry_status(date_str: str):
    """Returns 'Expired' or 'Valid' for chart grouping."""
    d = parse_date(date_str)
    if d is None:
        return "Unknown"
    return "Expired" if d < date.today() else "Valid"

# -------------------- GOOGLE SHEETS CONNECTION --------------------
def get_sheets():
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
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
        "Equipment type", "Make", "Plate No.", "Asset code", "Owner", "T.P inspection date", "T.P Expiry date",
        "Insurance expiry date", "Operator Name", "Iqama NO", "T.P Card type", "T.P Card Number",
        "T.P Card expiry date", "Q.R code", "PWAS status", "F.E TP expiry",
        "FA box Status", "Documents"
    ]

    heavy_vehicle_headers = [
        "Vehicle Type", "Make", "Plate No", "Asset Code", "Owner", "MVPI Expiry date", "Insurance Expiry",
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
        make = st.text_input("Make")
        plate_no = st.text_input("Plate No.")
        asset_code = st.text_input("Asset code")
        owner = st.text_input("Owner")
        tp_insp_date = st.date_input("T.P inspection date").strftime("%Y-%m-%d")
        tp_expiry = st.date_input("T.P Expiry date").strftime("%Y-%m-%d")
        insurance_expiry = st.date_input("Insurance expiry date").strftime("%Y-%m-%d")
        operator_name = st.text_input("Operator Name")
        iqama_no = st.text_input("Iqama NO")
        tp_card_type = st.selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_number = st.text_input("T.P Card Number")
        tp_card_expiry = st.date_input("T.P Card expiry date").strftime("%Y-%m-%d")
        qr_code = st.text_input("Q.R code")
        pwas_status = st.selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        fe_tp_expiry = st.date_input("F.E TP expiry").strftime("%Y-%m-%d")
        fa_box_status = st.text_input("FA box Status")
        documents = st.text_input("Documents")

        data = {
            "Equipment type": equipment_type,
            "Make": make,
            "Plate No.": plate_no,
            "Asset code": asset_code,
            "Owner": owner,
            "T.P inspection date": tp_insp_date,
            "T.P Expiry date": tp_expiry,
            "Insurance expiry date": insurance_expiry,
            "Operator Name": operator_name,
            "Iqama NO": iqama_no,
            "T.P Card type": tp_card_type,
            "T.P Card Number": tp_card_number,
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

# -------------------- DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs(["📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"])

    with tab_eqp:
        df = pd.DataFrame(heavy_equip_sheet.get_all_records())
        st.subheader("🚜 Heavy Equipment Overview")

        if df.empty:
            st.info("No Heavy Equipment data available.")
        else:
            # Clean data
            for col in ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]:
                if col in df.columns:
                    df[col] = df[col].astype(str)

            # Summary metrics
            st.metric("Total Equipments", len(df))
            st.metric("Unique Equipment Types", df["Equipment type"].nunique())

            # Graph 1: Equipment type count
            fig1 = px.bar(df["Equipment type"].value_counts().reset_index(),
                          x="index", y="Equipment type",
                          labels={"index": "Equipment Type", "Equipment type": "Count"},
                          title="Equipment Type Count")
            st.plotly_chart(fig1, use_container_width=True)

            # Graph 2: T.P Expiry Status
            df["T.P Status"] = df["T.P Expiry date"].apply(expiry_status)
            fig2 = px.pie(df, names="T.P Status", title="T.P Expiry Status")
            st.plotly_chart(fig2, use_container_width=True)

            # Graph 3: Insurance Expiry Status
            df["Insurance Status"] = df["Insurance expiry date"].apply(expiry_status)
            fig3 = px.pie(df, names="Insurance Status", title="Insurance Expiry Status")
            st.plotly_chart(fig3, use_container_width=True)

            # Graph 4: PWAS Status Distribution
            fig4 = px.bar(df["PWAS status"].value_counts().reset_index(),
                          x="index", y="PWAS status",
                          labels={"index": "PWAS Status", "PWAS status": "Count"},
                          title="PWAS Status Distribution")
            st.plotly_chart(fig4, use_container_width=True)

            # Show table with expiry badges
            for col in ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]:
                if col in df.columns:
                    df[col] = df[col].apply(badge_expiry)
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

# -------------------- PLACEHOLDER FOR OTHER FORMS --------------------
def show_observation_form(sheet):
    pass  # keep your original form code here

def show_permit_form(sheet):
    pass  # keep your original form code here

def show_heavy_vehicle_form(sheet):
    pass  # keep your original form code here

if __name__ == "__main__":
    main()
