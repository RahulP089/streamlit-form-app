import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
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

# --- Tab Names for Equipment Workbook ---
HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"

# -------------------- UTILITIES --------------------
def parse_date(s):
    """Safely parses a string into a date object."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    for fmt in ("%d/%m/%Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).split(' ')[0], fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def badge_expiry(d, expiry_days=10):
    """Creates a visual badge for expiry dates."""
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%d %B %Y')
    if d < today:
        return f"🚨 Expired ({date_str})"
    elif d <= today + timedelta(days=expiry_days):
        return f"⚠️ Expires Soon ({date_str})"
    else:
        return f"✅ Valid ({date_str})"

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600) # Cache for 10 minutes
def get_sheets():
    """Connects to Google Sheets and returns worksheet objects."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    def get_or_create(workbook, ws_title, headers=None):
        try:
            ws = workbook.worksheet(ws_title)
            if not ws.get_all_values() and headers:
                 ws.append_row(headers)
        except gspread.exceptions.WorksheetNotFound:
            ws = workbook.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws
    
    obs_headers = [
        "DATE", "WELL NO", "AREA", "OBSERVER NAME", "OBSERVATION DETAILS",
        "RECOMMENDED SOLUTION/ACTION TAKEN", "SUPERVISOR NAME", "DISCIPLINE",
        "CATEGORY", "CLASSIFICATION", "STATUS"
    ]
    permit_headers = [
        "DATE", "DRILL SITE", "PERMIT NO", "TYPE OF PERMIT", "ACTIVITY", "PERMIT RECEIVER", "PERMIT ISSUER"
    ]
    heavy_equip_headers = [
        "Equipment type", "Make", "Palte No.", "Asset code", "Owner", "T.P inspection date", "T.P Expiry date",
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

    obs_wb = client.open_by_url(OBSERVATION_URL)
    permit_wb = client.open_by_url(PERMIT_URL)
    equip_wb = client.open_by_url(EQUIPMENT_URL)

    obs_sheet = get_or_create(obs_wb, "Sheet1", headers=obs_headers)
    permit_sheet = get_or_create(permit_wb, "Sheet1", headers=permit_headers)
    heavy_equip_sheet = get_or_create(equip_wb, HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(equip_wb, HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)

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
        menu_options = [
            "🏠 Home", "📝 Observation Form", "🛠️ Permit Form",
            "🏗️ Equipments", "📊 Dashboard", "🚪 Logout"
        ]
        menu = st.selectbox("Go to", menu_options, key="main_menu")

        if menu == "🏗️ Equipments":
            sub_menu = st.selectbox("Select Equipment", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"], key="equip_sub")
            return sub_menu
        return menu

# -------------------- FORMS --------------------
def show_equipment_form(sheet):
    st.header("🚜 Heavy Equipment Entry Form")
    # This form's code is correct and remains unchanged
    
def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    # This form's code is correct and remains unchanged

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    
    # --- NEW: List of Permit Receivers ---
    PERMIT_RECEIVERS = [
        "MD MEHEDI HASAN NAHID", "JEFFREY VERBO YOSORES", "RAMESH KOTHAPALLY BHUMAIAH",
        "ALAA ALI ALI ALQURAISHI", "VALDIMIR FERNANDO", "PRINCE BRANDON LEE RAJU",
        "JEES RAJ RAJAN ALPHONSA", "BRAYAN DINESH", "EZBORN NGUNYI MBATIA",
        "AHILAN THANKARAJ", "MOHAMMAD FIROZ ALAM", "PRAVEEN SAHANI",
        "KANNAN GANESAN", "ARUN MANAYATHU ANANDH", "ANANDHU SASIDHARAN",
        "NINO URSAL CANON", "REJIL RAVI", "SIVA PRAVEEN SUGUMARAN",
        "AKHIL ASHOKAN", "OMAR MAHUSAY DATANGEL", "MAHAMMAD SINAN",
        "IRSHAD ALI MD QUYOOM", "RAISHKHA IQBALKHA PATHAN", "ABHILASH AMBAREEKSHAN",
        "SHIVKUMAR MANIKAPPA MANIKAPPA", "VAMSHIKRISHNA POLASA", "NIVIN PRASAD",
        "DHAVOUTH SULAIMAN JEILANI", "WINDY BLANCASABELLA", "MAHTAB ALAM",
        "BERIN ROHIN JOSEPH BENZIGER", "NEMWEL GWAKO", "RITHIC SAI",
        "SHAIK KHADEER", "SIMON GACHAU MUCHIRI", "JARUZELSKI MELENDES PESINO",
        "HAIDAR NASSER MOHAMMED ALKHALAF", "JEYARAJA JAYAPAL", "HASHEM ABDULMAJEED ALBAHRANI",
        "PRATHEEP RADHAKRISHNAN", "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC",
        "SHAHWAZ KHAN"
    ]
    PERMIT_RECEIVERS.sort() # Sort the list alphabetically

    with st.form("permit_form", clear_on_submit=True):
        data = {
            "DATE": st.date_input("Date").strftime("%d/%m/%Y"),
            "DRILL SITE": st.text_input("Drill Site"),
            "PERMIT NO": st.text_input("Permit No"),
            "TYPE OF PERMIT": st.selectbox("Type of Permit", ["HOT", "COLD"]),
            "ACTIVITY": st.text_area("Activity"),
            # --- UPDATED: Changed text_input to selectbox ---
            "PERMIT RECEIVER": st.selectbox("Permit Receiver", PERMIT_RECEIVERS),
            "PERMIT ISSUER": st.text_input("Permit Issuer"),
        }
        if st.form_submit_button("Submit"):
            try:
                sheet.append_row(list(data.values()))
                st.success("✅ Permit submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")
    # This form's code is correct and remains unchanged

# -------------------- ADVANCED DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])
    
    def safe_get_dataframe(sheet):
        try:
            data = sheet.get_all_values()
            if not data:
                return pd.DataFrame()
            
            headers = [str(header).strip() for header in data[0]]
            
            if len(data) > 1:
                return pd.DataFrame(data[1:], columns=headers)
            else:
                return pd.DataFrame(columns=headers)
                
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load data from Google Sheets: {e}")
            return pd.DataFrame()

    # --- OBSERVATION DASHBOARD TAB ---
    with tab_obs:
        st.subheader("Observation Analytics")
        df_obs = safe_get_dataframe(obs_sheet)
        if df_obs.empty:
            st.info("No observation data available to display.")
        else:
            # ... dashboard code ...
            st.dataframe(df_obs, use_container_width=True)

    # --- PERMIT DASHBOARD TAB ---
    with tab_permit:
        st.subheader("Permit Log Analytics")
        df_permit = safe_get_dataframe(permit_sheet)
        if df_permit.empty:
            st.info("No permit data available to display.")
        else:
            if 'DATE' not in df_permit.columns:
                st.error("Permit sheet is missing the 'DATE' column.")
            else:
                # ... dashboard code ...
                st.dataframe(df_permit, use_container_width=True)

    # --- EQUIPMENT DASHBOARD TAB ---
    with tab_eqp:
        st.subheader("Heavy Equipment Analytics")
        df_equip = safe_get_dataframe(heavy_equip_sheet)
        if df_equip.empty:
            st.info("No Heavy Equipment data available to display.")
        else:
            # ... dashboard code ...
            st.dataframe(df_equip, use_container_width=True)


# -------------------- MAIN APP --------------------
def main():
    st.set_page_config(page_title="Onsite Reporting System", layout="wide")
    if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
        login()
        return

    obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet = get_sheets()
    choice = sidebar()

    if choice == "🏠 Home":
        st.title("📋 Onsite Reporting System")
        st.write(f"Welcome, **{st.session_state.get('username')}**!")
        st.info("Select an option from the sidebar to begin.")

    elif choice == "📝 Observation Form":
        show_observation_form(obs_sheet)

    elif choice == "🛠️ Permit Form":
        show_permit_form(permit_sheet)

    elif choice == "📊 Dashboard":
        if st.session_state.get("role") == "admin":
            show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet)
        else:
            st.warning("🚫 Access Denied: This page is for admins only.")

    elif choice == "🚜 Heavy Equipment":
        show_equipment_form(heavy_equip_sheet)

    elif choice == "🚚 Heavy Vehicle":
        show_heavy_vehicle_form(heavy_vehicle_sheet)

    elif choice == "🚪 Logout":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
