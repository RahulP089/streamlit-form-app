import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime, timedelta

# -------------------- USER LOGIN --------------------
# A dictionary to store user credentials (in a real app, use a more secure method)
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
# Replace with your actual Google Sheet URLs
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"

# Define tab names for clarity
HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"

# -------------------- UTILITIES --------------------
def parse_date(s: str):
    """Safely converts a string to a date object, returning None on failure."""
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def badge_expiry(date_str: str):
    """Creates a visual badge (🚨 or ✅) based on the expiry date."""
    d = parse_date(date_str)
    if d is None:
        return date_str
    # Use an emoji to indicate status
    status_emoji = "🚨" if d < date.today() else "✅"
    return f"{status_emoji} {d.strftime('%Y-%m-%d')}"

def expiry_status(date_str: str):
    """Categorizes a date string into 'Expired', 'Valid', or 'Unknown' for charts."""
    d = parse_date(date_str)
    if d is None:
        return "Unknown"
    return "Expired" if d < date.today() else "Valid"

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource
def get_sheets():
    """Establishes a connection to Google Sheets using Streamlit secrets."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
    wb = client.open_by_url(EQUIPMENT_URL)

    def get_or_create(ws_title, headers=None):
        """Gets a worksheet by title, or creates it with headers if it doesn't exist."""
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
    """Displays the login interface."""
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
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🛡️ Login</div>', unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = USER_CREDENTIALS.get(username)
            if user and user["password"] == password:
                st.session_state.update(logged_in=True, username=username, role=user["role"])
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        st.markdown("</div>", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
def sidebar():
    """Displays the main navigation sidebar."""
    with st.sidebar:
        st.title("🧭 Navigation")
        menu_options = [
            "🏠 Home", "📝 Observation Form", "🛠️ Permit Form",
            "🏗️ Equipments", "📊 Dashboard", "🚪 Logout"
        ]
        menu = st.selectbox("Go to", menu_options, key="main_menu")

        if menu == "🏗️ Equipments":
            return st.selectbox("Select Equipment", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"], key="equip_sub")
        return menu

# -------------------- HEAVY EQUIPMENT FORM --------------------
def show_equipment_form(sheet):
    """Displays the form for entering new heavy equipment data."""
    st.header("🚜 Heavy Equipment Entry Form")
    EQUIPMENT_LIST = [
        "Excavator", "Backhoe Loader", "Wheel Loader", "Bulldozer",
        "Motor Grader", "Compactor / Roller", "Crane", "Forklift",
        "Boom Truck", "Side Boom", "Hydraulic Drill Unit", "Telehandler", "Skid Loader"
    ]
    with st.form("equipment_form", clear_on_submit=True):
        cols = st.columns(2)
        equipment_type = cols[0].selectbox("Equipment type", EQUIPMENT_LIST)
        make = cols[1].text_input("Make")
        plate_no = cols[0].text_input("Plate No.")
        asset_code = cols[1].text_input("Asset code")
        owner = cols[0].text_input("Owner")
        tp_insp_date = cols[1].date_input("T.P inspection date")
        tp_expiry = cols[0].date_input("T.P Expiry date")
        insurance_expiry = cols[1].date_input("Insurance expiry date")
        operator_name = cols[0].text_input("Operator Name")
        iqama_no = cols[1].text_input("Iqama NO")
        tp_card_type = cols[0].selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_number = cols[1].text_input("T.P Card Number")
        tp_card_expiry = cols[0].date_input("T.P Card expiry date")
        qr_code = cols[1].text_input("Q.R code")
        pwas_status = cols[0].selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        fe_tp_expiry = cols[1].date_input("F.E TP expiry")
        fa_box_status = cols[0].text_input("FA box Status")
        documents = cols[1].text_input("Documents")
        
        if st.form_submit_button("Submit"):
            data = [
                equipment_type, make, plate_no, asset_code, owner,
                tp_insp_date.strftime("%Y-%m-%d"), tp_expiry.strftime("%Y-%m-%d"),
                insurance_expiry.strftime("%Y-%m-%d"), operator_name, iqama_no,
                tp_card_type, tp_card_number, tp_card_expiry.strftime("%Y-%m-%d"),
                qr_code, pwas_status, fe_tp_expiry.strftime("%Y-%m-%d"),
                fa_box_status, documents
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    """Displays the main dashboard with data visualizations and alerts."""
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs(["📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"])

    with tab_eqp:
        df = pd.DataFrame(heavy_equip_sheet.get_all_records())
        st.subheader("🚜 Heavy Equipment Overview")

        if df.empty:
            st.info("No Heavy Equipment data available.")
            return

        # --- Expiry Alerts Section ---
        st.markdown("---")
        st.subheader("⚠️ Expiry Alerts (Next 15 Days)")
        date_cols = ["T.P Expiry date", "Insurance expiry date", "T.P Card expiry date", "F.E TP expiry"]
        df_dates = df.copy()
        for col in date_cols:
            if col in df_dates.columns:
                df_dates[col] = pd.to_datetime(df_dates[col], errors='coerce').dt.date

        today = date.today()
        fifteen_days_later = today + timedelta(days=15)
        expiring_soon_records = []

        for index, row in df_dates.iterrows():
            for col in date_cols:
                if col in row and pd.notna(row[col]):
                    if today <= row[col] <= fifteen_days_later:
                        expiring_soon_records.append({
                            "Equipment Type": row["Equipment type"],
                            "Plate No.": row["Plate No."],
                            "Item Expiring": col.replace(' expiry date', '').replace(' Expiry', ''),
                            "Expiry Date": row[col].strftime("%Y-%m-%d")
                        })
        if expiring_soon_records:
            st.dataframe(pd.DataFrame(expiring_soon_records), use_container_width=True)
        else:
            st.success("✅ No items are expiring in the next 15 days.")
        st.markdown("---")

        # --- Summary Metrics and Charts ---
        col1, col2 = st.columns(2)
        col1.metric("Total Equipments", len(df))
        col2.metric("Unique Equipment Types", df["Equipment type"].nunique())

        st.plotly_chart(px.bar(df["Equipment type"].value_counts().reset_index(),
                              x="Equipment type", y="count", title="Equipment Type Count",
                              color="Equipment type"), use_container_width=True)

        col1, col2 = st.columns(2)
        df["T.P Status"] = df["T.P Expiry date"].apply(expiry_status)
        col1.plotly_chart(px.pie(df, names="T.P Status", title="T.P Expiry Status", color="T.P Status"), use_container_width=True)

        df["Insurance Status"] = df["Insurance expiry date"].apply(expiry_status)
        col2.plotly_chart(px.pie(df, names="Insurance Status", title="Insurance Expiry Status", color="Insurance Status"), use_container_width=True)

        if "PWAS status" in df.columns:
            st.plotly_chart(px.bar(df["PWAS status"].value_counts().reset_index(),
                                  x="PWAS status", y="count", title="PWAS Status Distribution",
                                  color="PWAS status"), use_container_width=True)

        # --- Full Data Table with Badges ---
        df_display = df.copy()
        for col in date_cols:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(badge_expiry)
        st.dataframe(df_display)

# -------------------- MAIN APP LOGIC --------------------
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Onsite Reporting", layout="wide")
    if not st.session_state.get("logged_in"):
        login()
        return

    obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet = get_sheets()
    choice = sidebar()

    page_map = {
        "🏠 Home": lambda: st.title("📋 Onsite Reporting System"),
        "📝 Observation Form": lambda: show_observation_form(obs_sheet),
        "🛠️ Permit Form": lambda: show_permit_form(permit_sheet),
        "🚜 Heavy Equipment": lambda: show_equipment_form(heavy_equip_sheet),
        "🚚 Heavy Vehicle": lambda: show_heavy_vehicle_form(heavy_vehicle_sheet)
    }

    if choice in page_map:
        page_map[choice]()
    elif choice == "📊 Dashboard":
        if st.session_state.get("role") == "admin":
            show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet)
        else:
            st.warning("🚫 Access Denied: Admin role required for the dashboard.")
    elif choice == "🚪 Logout":
        st.session_state.clear()
        st.rerun()

# -------------------- PLACEHOLDER FOR OTHER FORMS --------------------
def show_observation_form(sheet):
    st.header("📋 Observation Form")
    st.info("This form is under construction.")

def show_permit_form(sheet):
    st.header("🛠️ Permit Form")
    st.info("This form is under construction.")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Form")
    st.info("This form is under construction.")

if __name__ == "__main__":
    main()
