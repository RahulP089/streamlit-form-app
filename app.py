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
    try:
        return datetime.strptime(str(s).split(' ')[0], "%d %B %Y").date()
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(s).split(' ')[0], "%Y-%m-%d").date()
        except (ValueError, TypeError):
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

    # --- Helper function to get or create a worksheet ---
    def get_or_create(workbook, ws_title, headers=None):
        try:
            ws = workbook.worksheet(ws_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = workbook.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws
    
    # --- Define Headers for ALL sheets to prevent KeyErrors ---
    obs_headers = [
        "DATE", "WELL NO", "AREA", "OBSERVER NAME", "OBSERVATION DETAILS",
        "RECOMMENDED SOLUTION/ACTION TAKEN", "SUPERVISOR NAME", "DISCIPLINE",
        "CATEGORY", "CLASSIFICATION", "STATUS"
    ]
    permit_headers = [
        "DATE", "PERMIT NO", "TYPE OF PERMIT", "ACTIVITY", "PERMIT RECEIVER", "PERMIT ISSUER"
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

    # --- Open workbooks ---
    obs_wb = client.open_by_url(OBSERVATION_URL)
    permit_wb = client.open_by_url(PERMIT_URL)
    equip_wb = client.open_by_url(EQUIPMENT_URL)

    # --- Get or create all worksheets securely ---
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
    EQUIPMENT_LIST = [
        "Excavator", "Backhoe Loader", "Wheel Loader", "Bulldozer", "Motor Grader", "Compactor / Roller",
        "Crane", "Forklift", "Boom Truck", "Side Boom", "Hydraulic Drill Unit", "Telehandler", "Skid Loader"
    ]
    with st.form("equipment_form", clear_on_submit=True):
        cols = st.columns(2)
        equipment_type = cols[0].selectbox("Equipment type", EQUIPMENT_LIST)
        make = cols[1].text_input("Make")
        plate_no = cols[0].text_input("Palte No.")
        asset_code = cols[1].text_input("Asset code")
        owner = cols[0].text_input("Owner")
        operator_name = cols[1].text_input("Operator Name")
        iqama_no = cols[0].text_input("Iqama NO")

        st.subheader("Expiry Dates")
        cols_dates = st.columns(2)
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime("%d %B %Y")
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime("%d %B %Y")
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime("%d %B %Y")
        fe_tp_expiry = cols_dates[1].date_input("F.E TP expiry").strftime("%d %B %Y")
        tp_card_expiry = cols_dates[0].date_input("T.P Card expiry date").strftime("%d %B %Y")

        st.subheader("T.P Card & Status")
        cols_status = st.columns(2)
        tp_card_type = cols_status[0].selectbox("T.P Card Type", ["S
