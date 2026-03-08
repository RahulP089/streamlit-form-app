import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
import plotly.express as px
import base64
import os

# -------------------- USER LOGIN --------------------
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"

# -------------------- WPR MASTER HEADERS (SL NO REMOVED) --------------------
WPR_HEADERS = [
    "NAME", "DESIGNATION", "EMP #", "IQAMA NUMBERS", "PERMIT TYPE", 
    "SAWPR ID", "EXPIRY DATE", "SAOO EXPIRY DATE", "SAOO valid days", 
    "South Delegation Expiry Date", "South Delegation valid days", 
    "Central Expiry Date", "Central Valid Days", "MDRK", "MDRK Valid Days", 
    "Uniyzal Expiry date", "Uniyzal Deligation valid days", 
    "POD ORIENTATION", "IQAMA VALID DAYS", "IQAMA", "Document"
]

ALL_SITES = [
    "1858", "1969", "1972", "2433", "2447", "2485",
    "2534", "2549", "2553", "2516", "2556", "2575", "2566","2570","HRDH Laydown","2595"
]

# -------------------- UTILITIES --------------------
def get_img_as_base64(file):
    if not os.path.exists(file): return None
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def parse_date(s):
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try: return datetime.strptime(str(s).split(' ')[0], fmt).date()
        except (ValueError, TypeError): continue
    return None

def badge_expiry(d, expiry_days=30):
    if d is None: return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%d-%b-%Y')
    if d < today: return f"🚨 Expired ({date_str})"
    elif d <= today + timedelta(days=expiry_days): return f"⚠️ Expires Soon ({date_str})"
    else: return f"✅ Valid ({date_str})"

def ensure_headers_match(worksheet, expected_headers):
    try:
        current_header = worksheet.row_values(1)
        if current_header != expected_headers:
            worksheet.update('A1', [expected_headers])
            st.cache_resource.clear()
            st.rerun()
    except Exception as e:
        st.error(f"Header Error in {worksheet.title}: {e}")

# -------------------- GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600)
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
        try: ws = wb.worksheet(ws_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = wb.add_worksheet(title=ws_title, rows="1000", cols="40")
            if headers: ws.append_row(headers)
        return ws

    heavy_equip_sheet = get_or_create("Heavy Equipment")
    heavy_vehicle_sheet = get_or_create("Heavy Vehicles")
    wpr_sheet = get_or_create("WPR Master", headers=WPR_HEADERS)

    ensure_headers_match(wpr_sheet, WPR_HEADERS)
    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet, wpr_sheet

# -------------------- WPR FORM --------------------
def show_wpr_form(sheet):
    st.header("🆔 WPR Internal & Aramco Master Entry")
    with st.form("wpr_form_new", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Name")
            desig = st.text_input("Designation")
            emp_no = st.text_input("EMP #")
            iqama = st.text_input("Iqama Number")
            p_type = st.selectbox("Permit Type", ["Aramco", "Internal", "Both"])
            sawpr_id = st.text_input("SAWPR ID")
        
        with c2:
            exp_date = st.date_input("SAWPR Expiry Date")
            saoo_date = st.date_input("SAOO Expiry Date")
            south_date = st.date_input("South Delegation Expiry")
            central_date = st.date_input("Central Expiry Date")
            mdrk = st.text_input("MDRK")
            mdrk_date = st.date_input("MDRK Expiry Date")

        with c3:
            uniyzal_date = st.date_input("Uniyzal Expiry Date")
            pod_date = st.date_input("POD Orientation Date")
            iqama_exp = st.date_input("Iqama Valid Date")
            doc_link = st.text_input("Document Link")

        if st.form_submit_button("Submit WPR Data"):
            today = date.today()
            # Calculate Valid Days automatically
            data = [
                name, desig, emp_no, iqama, p_type, sawpr_id,
                exp_date.strftime("%d-%b-%Y"), 
                saoo_date.strftime("%d-%b-%Y"), (saoo_date - today).days,
                south_date.strftime("%d-%b-%Y"), (south_date - today).days,
                central_date.strftime("%d-%b-%Y"), (central_date - today).days,
                mdrk, (mdrk_date - today).days,
                uniyzal_date.strftime("%d-%b-%Y"), (uniyzal_date - today).days,
                pod_date.strftime("%d-%b-%Y"), (iqama_exp - today).days,
                iqama_exp.strftime("%d-%b-%Y"), doc_link
            ]
            sheet.append_row(data)
            st.success("✅ WPR Record added successfully!")

# -------------------- SIDEBAR & MAIN --------------------
def sidebar():
    with st.sidebar:
        st.title("🧭 Navigation")
        menu = st.selectbox("Go to", ["🏠 Home", "📝 Observation Form", "🛠️ Permit Form", "🆔 WPR Master", "🏗️ Equipments", "📊 Dashboard", "🚪 Logout"])
        if menu == "🏗️ Equipments":
            return st.selectbox("Select", ["🚜 Heavy Equipment", "🚚 Heavy Vehicle"])
        return menu

def main():
    st.set_page_config(page_title="NSH Haradh Reporting", layout="wide")
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    
    # Simple login check (Rahul/1234)
    if not st.session_state.logged_in:
        # (Login logic remains as per your original code)
        # Assuming you'll use your original login function here
        pass 

    obs, per, eqp, veh, wpr = get_sheets()
    choice = sidebar()

    if choice == "🏠 Home": st.title("Welcome to NSH HGUPD Haradh")
    elif choice == "🆔 WPR Master": show_wpr_form(wpr)
    elif choice == "📊 Dashboard": 
        # You can add a new tab in show_combined_dashboard for WPR
        st.write("Dashboard loading...") 
    # ... (other choices)

if __name__ == "__main__":
    main()
