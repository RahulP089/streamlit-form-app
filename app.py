import streamlit as st # for web
import pandas as pd # For JSON file
import gspread # Link spread sheet
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
import plotly.express as px # fore pie
import base64 # Added for image encoding
import os # Added for file path checking

# -------------------- USER LOGIN --------------------
USER_CREDENTIALS = {
    "Rahul": {"password": "1234", "role": "admin"},
    "user": {"password": "user", "role": "user"}
}

# -------------------- GOOGLE SHEET LINKS --------------------
# ⚠️ ACTION: These are the URLs you provided. 
OBSERVATION_URL = "https://docs.google.com/spreadsheets/d/1i3f5ixYfRjfHeHXbuV0Gpx-gtRvJ6oKT2gaaUBMSLEE/edit"
PERMIT_URL = "https://docs.google.com/spreadsheets/d/1Xam9P0t-BZq6OcLDSYizLhpvbpj2spWgT2fncHpHjcU/edit"
# This matches the screenshot you shared (Equipment Master)
EQUIPMENT_URL = "https://docs.google.com/spreadsheets/d/1KbjDWkdG4Ce9fSDs3tCZskyoSGgIpSzFb5I7rMOAS3w/edit"

HEAVY_EQUIP_TAB = "Heavy Equipment"
HEAVY_VEHICLE_TAB = "Heavy Vehicles"

# --- MASTER SITE LIST ---
ALL_SITES = [
    "1858", "1969", "1972", "2433", "2447", "2485",
    "2534", "2549", "2553", "2516", "2556", "2575", "2566","2570","HRDH Laydown","2595"
]
# ------------------------

# -------------------- UTILITIES --------------------
def get_img_as_base64(file):
    """Reads an image file and returns it as a base64 encoded string."""
    if not os.path.exists(file):
        return None
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def parse_date(s):
    """Safely parses a string into a date object."""
    if pd.isna(s) or s == "":
        return None
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    
    s = str(s).strip()
    # Try ISO format first, then others
    formats = ["%Y-%m-%d", "%d-%b-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]
    
    for fmt in formats:
        try:
            # Handle cases where time is included
            return datetime.strptime(s.split(' ')[0], fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def badge_expiry(d, expiry_days=30):
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%Y-%m-%d')
    if d < today:
        return f"🚨 Expired ({date_str})"
    elif d <= today + timedelta(days=expiry_days):
        return f"⚠️ Expires Soon ({date_str})"
    else:
        return f"✅ Valid ({date_str})"

# -------------------- ROBUST GOOGLE SHEETS CONNECTION --------------------
@st.cache_resource(ttl=600)
def get_sheets():
    """Connects to Google Sheets and returns worksheet objects safely."""
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
    wb_equipment = client.open_by_url(EQUIPMENT_URL)

    # Define exact headers based on your image
    heavy_equip_headers = [
        "Equipment type", "Make", "Palte No.", "Asset code", "Owner", "T.P inspection date", "T.P Expiry date",
        "Insurance expiry date", "Operator Name", "Iqama NO", "T.P Card type", "T.P Card Number",
        "T.P Card expiry date", "Q.R code", "PWAS status", "FA box Status", "Documents"
    ]

    heavy_vehicle_headers = [
        "Vehicle Type", "Make", "Plate No", "Asset Code", "Owner", "MVPI Expiry date", "Insurance Expiry",
        "Driver Name", "Iqama No", "Licence Expiry", "Q.R code", "F.A Box", "PWAS Status", 
        "Seat belt damaged", "Tyre Condition", "Suspension Systems", "Remarks"
    ]

    # Helper to find sheet by name (case-insensitive) or create it
    def get_or_create_sheet(wb, title, headers):
        try:
            ws = wb.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            # Try finding with different casing (e.g. "heavy vehicles" vs "Heavy Vehicles")
            found = False
            for sheet in wb.worksheets():
                if sheet.title.strip().lower() == title.strip().lower():
                    ws = sheet
                    found = True
                    break
            
            if not found:
                # Create if missing
                ws = wb.add_worksheet(title=title, rows="100", cols="20")
                ws.append_row(headers)
                return ws
        
        # --- FIX FOR "DATA NOT COMING" (Row 1000 issue) ---
        # If the sheet exists but has empty rows at the bottom (common in new sheets),
        # data might be appended at row 1001. This check isn't perfect but helps.
        # We ensure the header row is correct.
        current_headers = ws.row_values(1)
        if not current_headers:
            ws.append_row(headers)
        
        return ws

    heavy_equip_sheet = get_or_create_sheet(wb_equipment, HEAVY_EQUIP_TAB, heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create_sheet(wb_equipment, HEAVY_VEHICLE_TAB, heavy_vehicle_headers)

    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet
    
# -------------------- LOGIN PAGE --------------------
def login():
    IMG_PATH = "login_bg.jpg" 
    img_base64 = get_img_as_base64(IMG_PATH)
    
    background_css = ""
    if img_base64:
        file_extension = os.path.splitext(IMG_PATH)[1].lower()
        mime_type = file_extension[1:]
        if mime_type == "jpg":
            mime_type = "jpeg"

        background_css = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/{mime_type};base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"] > .main {{
            background-color: transparent !important;
        }}
        </style>
        """

    st.markdown(f"""
    {background_css}
    <style>
    .login-container {{
        background-color: transparent; 
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
        box-shadow: none;
        max-width: 200px;
        margin: 4rem auto; 
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
    }}
    .login-title {{
        font-size: 32px; 
        font-weight: 700; 
        color: white; 
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        margin-bottom: 1.5rem;
    }}
    .login-container label {{
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
    }}
    .login-container [data-testid="stTextInput"],
    .login-container [data-testid="stPasswordInput"] {{
        margin-left: auto;
        margin-right: auto;
        width: 100%;
    }}
    .login-container .stButton > button {{
        margin: 1rem auto;
        display: block;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🛡️ Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
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
        
        # Add a refresh button to clear cache if data looks stuck
        if st.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.rerun()
            
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
        date_format = "%Y-%m-%d"
        
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime(date_format)
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime(date_format)
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime(date_format)
        tp_card_expiry = cols_dates[1].date_input("T.P Card expiry date").strftime(date_format)

        st.subheader("T.P Card & Status")
        cols_status = st.columns(2)
        tp_card_type = cols_status[0].selectbox("T.P Card Type", ["SPSP", "Aramco", "PAX", "N/A"])
        tp_card_number = cols_status[1].text_input("T.P Card Number")
        pwas_status = cols_status[0].selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        fa_box_status = cols_status[1].text_input("FA box Status")
        qr_code = cols_status[0].text_input("Q.R code")
        documents = cols_status[1].text_input("Documents")

        if st.form_submit_button("Submit", use_container_width=True):
            data = [
                equipment_type, make, plate_no, asset_code, owner, tp_insp_date, tp_expiry,
                insurance_expiry, operator_name, iqama_no, tp_card_type, tp_card_number,
                tp_card_expiry, qr_code, pwas_status, fa_box_status, documents
            ]
            try:
                sheet.append_row(data, value_input_option="USER_ENTERED")
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    OBSERVER_NAMES = [
        "AJISH", "AKHIL MOHAN", "AQIB", "ARFAN", "ASIM", "ASHRAF KHAN", "BIJO", "FELIN", "HABEEB", "ILYAS", "IRFAN", "JAMALI", 
        "JOSEPH CRUZ", "MOHSIN", "PRADEEP", "RAJSHEKAR", "RICKEN", "SHIVA KANNAN", "SHIVA SUBRAMANIYAM", "SUDISH", "VAISHAK", 
        "VARGHEESE", "WALI ALAM", "ZAHEER"
    ]
    AREAS = ["Well Head", "Flow Line", "OHPL", "Tie In", "Lay Down", "Cellar", "Remote Header"]
    CATEGORIES = [
        "Fall Protection/Personal Fall Arrest System Use/Falling Hazard", "Trenching/Excavation/Shoring",
        "Scaffolds, Ladders and Elevated work platforms", "Crane and Lifting Devices", "Heavy Equipment",
        "Vehicles / Traffic Control", "Hand/Power Tools and Electrical appliances", "Electrical Safety",
        "Hot work (Cutting/Welding/Brazing)", "Fire prevention & Protection", "Abrasive Blasting and Coating",
        "Confined Space / Restricted area", "Civil, Concrete Work", "Compressed Gases",
        "General Equipment's (Air Compressors/Power Generator etc.)", "Work Permit, Risk Assessment, JSA & other procedures",
        "Chemical Handling and Hazardous material", "Environmental / Waste Management", "Health, hygiene & welfare",
        "Radiation and NDT", "Security, Unsafe Behavior, and other project Requirements", "PPE", "House Keeping"
    ]
    SUPERVISOR_TRADE_MAP = {
"RAJA KUMAR": "CONTROLLER-EQUIPMENT", "SREEDHARAN VISWANATHAN": "SUPERVISOR-PIPING", "MANOJ THOMAS": "WELL IN CHARGE",
"ANIL KUMAR JANARDHANAN": "WELL IN CHARGE", "SIVA PRASAD PILLAI": "FOREMAN-PIPING", "JAYAN RAJAJAN": "FOREMAN-PIPING",
"MURUGAN VANNIYAPERUMAL": "COORDINATOR-NDE", "ANU MOHAN MOHANAN PILLAI": "FIELD ADMINISTRATOR", "BHARAT CHANDRABARAL": "ASSISTANT-STORE",
"SUMOD PRABHAKARA": "LAND SURVEYOR", "DHARMA RAJU UPPADA": "FOREMAN-HYDRO TEST", "JEFFREY F. TABAMO": "CONSTRUCTION SUPERVISOR-E & I",
"ORLANDO GURGUD": "SUPERVISOR-PAINTING CREW", "RICHARD REYES RIVERAL": "SUPERVISOR-PAINTING CREW", "AJIMAL SULFIKAR": "SUPERVISOR-PIPING",
"ARVIND KUMAR": "SUPERVISOR-CIVIL", "MAQSUD ALAM": "CONSTRUCTION SUPERVISOR-PIPING", "SIFAT MEHDI": "FOREMAN-INSTRUMENTATION",
"SAJU SADANANDAN": "SUPERVISOR-CIVIL", "SASIDHARA KURUP": "FOREMAN-ELECTRICAL", "ALVIN CHARLY": "CONSTRUCTION SUPERVISOR-E & I",
"PAWAN KUMAR YADAV": "FOREMAN-CIVIL", "BRIHASPATI ADAK": "FOREMAN-CIVIL", "JITHIN JOHN": "CONSTRUCTION SUPERVISOR-CIVIL",
"RAVI SINGH": "SUPERVISOR-CIVIL", "ANILKUMAR SAHADEVAN": "SUPERVISOR-CIVIL", "BALA KRISHNA": "FOREMAN-CIVIL", "SUNIL KUMARSAHU": "FOREMAN-CIVIL",
"RAJESHWAR YASOJI NARAYANA": "SUPERVISOR-SCAFFOLDING", "ASHWANI KUMAR YADAV": "FOREMAN-CIVIL", "QUAISAR ALI": "SUPERVISOR-ELECTRICAL",
"ABHISHEK REGHUVARAN": "SUPERVISOR-PIPING", "ZEESHAN YOUSUF": "SUPERVISOR-CIVIL", "MOHAMMAD RAUSHAN": "SUPERVISOR-CIVIL",
"AHAMED RIYAZ ASHRAE ALI": "SUPERVISOR-CIVIL", "ASLAM KHAN ALBAN": "FOREMAN-SCAFFOLDING", "SURESH KUMAR": "WELL IN CHARGE",
"ANOOPKUMAR": "SUPERVISOR-ELECTRICAL", "VAISHNAV VINOD SREEJA": "SUPERVISOR-PIPING", "MOHAMMED MUHANNA AL WOSAIFER": "ENGINEER-MECHANICAL",
"HISHAM IBRAHIM AL FARHAN": "ADMIN ASSISTANT", "HASSAN FAYAA MOHAMMED MASHNI": "ELECTRICAL ENGINEER", "ABDALLAH MOHAMMED ALMOTAWA": "ENGINEER-MECHANICAL",
"RAJA ALAGAPPAN": "SUPERVISOR-PAINTING CREW", "SURESHKUMAR": "CONSTRUCTION SUPERVISOR-PIPING","GOPAN": "SUPERVISOR-CIVIL","BHARATH":"STORE KEEPER",
"HAROON":"STORE KEEPER","BIVIN":"FOREMAN-PIPING"
    }
    supervisor_names = [""] + sorted(list(SUPERVISOR_TRADE_MAP.keys()))

    with st.form("obs_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            form_date = st.date_input("Date")
            area = st.selectbox("Area", AREAS)
            observer_name = st.selectbox("Observer Name", OBSERVER_NAMES)
            classification = st.selectbox("Classification", ["POSITIVE", "UNSAFE CONDITION", "UNSAFE ACT"])
            category = st.selectbox("Category", CATEGORIES)
        with col2:
            well_no = st.selectbox("Well No", ALL_SITES)
            supervisor_name = st.selectbox("Supervisor Name", supervisor_names)
            trade = SUPERVISOR_TRADE_MAP.get(supervisor_name, "")
            discipline = st.text_input("Discipline", value=trade, disabled=True)
            status = st.selectbox("Status", ["OPEN", "CLOSE"])
        obs_details = st.text_area("Observation Details")
        rec_action = st.text_area("Recommended Action")

        if st.form_submit_button("Submit"):
            data = [
                form_date.strftime("%Y-%m-%d"),
                well_no, area, observer_name, obs_details, rec_action,
                supervisor_name, discipline, category, classification, status
            ]
            try:
                sheet.append_row(data, value_input_option="USER_ENTERED")
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    WORK_LOCATIONS = ["Well Head", "OHPL", "OPTF", "E&I Skid", "Burn Pit", "Cellar", "Flow Line", "Lay down", "CP area","BD-Line"]
    PERMIT_TYPES = ["Hot", "Cold", "CSE", "EOLB"]
    PERMIT_ISSUERS = ["UNNIMON SRINIVASAN","VISHNU MOHAN"]
    PERMIT_RECEIVERS = [
        "MD MEHEDI HASAN NAHID","ALWIN", "JEFFREY VERBO YOSORES", "RAMESH KOTHAPALLY BHUMAIAH", "ALAA ALI ALI ALQURAISHI", "VALDIMIR FERNANDO",
        "PRINCE BRANDON LEE RAJU", "JEES RAJ RAJAN ALPHONSA", "BRAYAN DINESH", "EZBORN NGUNYI MBATIA", "AHILAN THANKARAJ", "MOHAMMAD FIROZ ALAM",
        "PRAVEEN SAHANI", "KANNAN GANESAN", "ARUN MANAYATHU ANANDH", "ANANDHU SASIDHARAN", "NINO URSAL CANON", "REJIL RAVI",
        "SIVA PRAVEEN SUGUMARAN", "AKHIL ASHOKAN", "OMAR MAHUSAY DATANGEL", "MAHAMMAD SINAN", "IRSHAD ALI MD QUYOOM", "RAISHKHA IQBALKHA PATHAN",
        "ABHILASH AMBAREEKSHAN", "SHIVKUMAR MANIKAPPA MANIKAPPA", "VAMSHIKRISHNA POLASA", "NIVIN PRASAD", "DHAVOUTH SULAIMAN JEILANI",
        "WINDY BLANCASABELLA", "MAHTAB ALAM", "BERIN ROHIN JOSEPH BENZIGER", "NEMWEL GWAKO", "RITHIC SAI", "SHAIK KHADEER", "SIMON GACHAU MUCHIRI",
        "DIFLIN", "JARUZELSKI MELENDES PESINO", "HAIDAR NASSER MOHAMMED ALKHALAF", "JEYARAJA JAYAPAL", "HASHEM ABDULMAJEED ALBAHRANI",
        "PRATHEEP RADHAKRISHNAN", "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC", "SHAHWAZ KHAN","PACIFICO LUBANG ICHON","ELMER","REMY E PORRAS",
    ]
    PERMIT_ACTIVITIES = [
        "--- Select Activity ---", "Mechanical Excavation", "Manual Excavation", "Fitup welding cutting and grinding", "Holiday test", "Pole erection",
        "Manual painting", "CP drilling", "Trenching and Backfilling", "Backfilling leveling and compaction", "Construction of ROW",
        "Marl mixing loading and unloading", "Construction of fence", "Cable pulling", "Cable termination and threading", "Conduit fixing",
        "Construction of Burn pit", "Loading and unloading of materials", "Abrasive blasting and painting", "Diesel refueling", "Equipment maintenance",
        "Water filling", "Surface preparation and concrete chipping", "Foam work", "Shuttering activity", "Nitrogen purging", "Berming", "Rebar works",
        "Megger test", "Marker installation", "Grouting", "Cellar construction", "Entry into CSE", "Entry into Burnpit", "Hydro test",
        "Scafolding activity", "Structure cutting", "Bolt Torquing", "Surface Prepration", "Survey", "Foundation Installation", "CAD welding",
        "Pipe Lowering", "Sand Bedding", "Radiography test", "Splicing "
    ]
    with st.form("permit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("Date")
            drill_site = st.selectbox("Drill Site", ALL_SITES)
            work_location = st.selectbox("Work Location", WORK_LOCATIONS)
            permit_receiver = st.selectbox("Permit Receiver", PERMIT_RECEIVERS)
        with col2:
            permit_no = st.text_input("Permit No")
            permit_type = st.radio("Type of Permit", PERMIT_TYPES, horizontal=True)
            permit_issuer = st.radio("Permit Issuer", PERMIT_ISSUERS, horizontal=True)
        activity = st.selectbox("Activity", PERMIT_ACTIVITIES)

        if st.form_submit_button("Submit"):
            data = [
                date_val.strftime("%Y-%m-%d"), drill_site, work_location, permit_no, permit_type,
                activity, permit_receiver, permit_issuer
            ]
            try:
                sheet.append_row(data, value_input_option="USER_ENTERED")
                st.success("✅ Permit submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_heavy_vehicle_form(sheet):
    st.header("🚚 Heavy Vehicle Entry Form")
    VEHICLE_LIST = ["Bus", "Dump Truck", "Low Bed", "Trailer", "Water Tanker", "Mini Bus", "Flat Truck"]
    with st.form("vehicle_form", clear_on_submit=True):
        st.subheader("Vehicle & Driver Information")
        c1, c2 = st.columns(2)
        vehicle_type = c1.selectbox("Vehicle Type", VEHICLE_LIST)
        make = c2.text_input("Make")
        plate_no = c1.text_input("Plate No")
        asset_code = c2.text_input("Asset Code")
        owner = c1.text_input("Owner")
        qr_code = c2.text_input("Q.R code")
        driver_name = c1.text_input("Driver Name")
        iqama_no = c2.text_input("Iqama No")

        st.subheader("Expiry Dates")
        d1, d2, d3 = st.columns(3)
        date_format = "%Y-%m-%d"
        mvpi_expiry = d1.date_input("MVPI Expiry date").strftime(date_format)
        insurance_expiry = d2.date_input("Insurance Expiry").strftime(date_format)
        licence_expiry = d3.date_input("Licence Expiry").strftime(date_format)

        st.subheader("Condition & Status")
        s1, s2 = st.columns(2)
        fa_box = s1.selectbox("F.A Box", ["Available", "Not Available", "Expired", "Inadequate Medicine"])
        pwas_status = s2.selectbox("PWAS Status", ["Working", "Not Working", "Alarm Not Audible", "Faulty Camera/Monitor", "N/A"])
        seatbelt_damaged = s1.selectbox("Seat belt damaged", ["Yes", "No", "N/A"])
        tyre_condition = s2.selectbox("Tyre Condition", ["Good", "Worn Out", "Damaged", "Needs Replacement", "N/A"])
        suspension_systems = s1.selectbox("Suspension Systems", ["Good", "Faulty", "Needs Repair", "DamDamaged", "N/A"])
        remarks = st.text_area("Remarks")

        if st.form_submit_button("Submit"):
            data = [
                vehicle_type, make, plate_no, asset_code, owner,
                mvpi_expiry, insurance_expiry,
                driver_name, iqama_no, licence_expiry,
                qr_code, fa_box,
                pwas_status, seatbelt_damaged, tyre_condition,
                suspension_systems, remarks
            ]
            try:
                sheet.append_row(data, value_input_option="USER_ENTERED")
                st.success(f"✅ Heavy Vehicle submitted successfully to '{sheet.title}'!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")
                if "403" in str(e):
                    st.error("⚠️ PERMISSION DENIED: Please share the Google Sheet with the bot email as an 'Editor'.")

# -------------------- ADVANCED DASHBOARD --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs(["📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"])
    today = date.today()
    thirty_days = today + timedelta(days=30)

    # -------------------- OBSERVATION DASHBOARD --------------------
    with tab_obs:
        st.subheader("Advanced Observation Analytics")
        try:
            df_obs = pd.DataFrame(obs_sheet.get_all_records())
            df_obs.columns = [str(col).strip().upper() for col in df_obs.columns]
        except gspread.exceptions.GSpreadException:
            st.error("Could not load observation data."); return 

        if df_obs.empty: st.info("No observation data available."); return

        if 'DATE' not in df_obs.columns: st.warning("Missing 'DATE' column."); return
        df_obs['DATE'] = pd.to_datetime(df_obs['DATE'], dayfirst=True, errors='coerce')
        df_obs.dropna(subset=['DATE'], inplace=True)
        df_obs = df_obs.sort_values(by='DATE', ascending=False)
        
        if 'CLASSIFICATION' in df_obs.columns: df_obs['CLASSIFICATION'] = df_obs['CLASSIFICATION'].str.strip().str.upper()
        if 'STATUS' in df_obs.columns: df_obs['STATUS'] = df_obs['STATUS'].str.strip().str.capitalize()

        with st.expander("Adjust Filters", expanded=True):
            col_f1, col_f2 = st.columns(2)
            min_d, max_d = df_obs['DATE'].min().date(), df_obs['DATE'].max().date()
            dr = col_f1.date_input("Date Range", (min_d, max_d), min_value=min_d, max_value=max_d, key="obs_dr")
            cls_opts = df_obs['CLASSIFICATION'].unique() if 'CLASSIFICATION' in df_obs.columns else []
            sel_cls = col_f2.multiselect("Classification", cls_opts, default=cls_opts)
            sts_opts = df_obs['STATUS'].unique() if 'STATUS' in df_obs.columns else []
            sel_sts = col_f2.multiselect("Status", sts_opts, default=sts_opts)

        s_date, e_date = dr if len(dr) == 2 else (min_d, max_d)
        mask = (df_obs['DATE'] >= pd.to_datetime(s_date)) & (df_obs['DATE'] <= pd.to_datetime(e_date))
        if sel_cls and 'CLASSIFICATION' in df_obs.columns: mask &= df_obs['CLASSIFICATION'].isin(sel_cls)
        if sel_sts and 'STATUS' in df_obs.columns: mask &= df_obs['STATUS'].isin(sel_sts)
        df_filtered = df_obs[mask]

        if df_filtered.empty: st.warning("No data matches filters."); return
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Observations", len(df_filtered))
        k2.metric("Open Issues", len(df_filtered[df_filtered['STATUS'] == 'Open']) if 'STATUS' in df_filtered.columns else 0)
        k3.metric("Total Unsafe", len(df_filtered[df_filtered['CLASSIFICATION'].isin(['UNSAFE ACT', 'UNSAFE CONDITION'])]) if 'CLASSIFICATION' in df_filtered.columns else 0)
        k4.metric("Busiest Day", df_filtered['DATE'].dt.day_name().mode()[0] if not df_filtered.empty else "N/A")
        
        st.markdown("---")
        c1, c2 = st.columns(2)
        if 'CLASSIFICATION' in df_filtered.columns:
            fig = px.pie(df_filtered, names='CLASSIFICATION', color='CLASSIFICATION', hole=0.4, 
                         color_discrete_map={'UNSAFE ACT': '#E74C3C', 'UNSAFE CONDITION': '#F39C12', 'POSITIVE': '#2ECC71'})
            c1.plotly_chart(fig, use_container_width=True)
        if 'STATUS' in df_filtered.columns:
            fig = px.pie(df_filtered, names='STATUS', color='STATUS', hole=0.4, color_discrete_map={'Open': '#E74C3C', 'Close': '#2ECC71'})
            c2.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # -------------------- PERMIT DASHBOARD --------------------
    with tab_permit:
        st.subheader("Advanced Permit Log Analytics")
        try:
            df_permit = pd.DataFrame(permit_sheet.get_all_records())
            df_permit.columns = [str(col).strip().upper() for col in df_permit.columns]
        except gspread.exceptions.GSpreadException: st.error("Could not load permit data."); return

        if df_permit.empty: st.info("No permit data."); return
        if 'DATE' not in df_permit.columns: st.warning("Missing 'DATE' column."); return
        df_permit['DATE'] = pd.to_datetime(df_permit['DATE'], dayfirst=True, errors='coerce')
        df_permit.dropna(subset=['DATE'], inplace=True)
        df_permit = df_permit.sort_values(by='DATE', ascending=False)

        with st.expander("Adjust Filters", expanded=True):
            col_f1, col_f2 = st.columns(2)
            min_d, max_d = df_permit['DATE'].min().date(), df_permit['DATE'].max().date()
            dr = col_f1.date_input("Date Range", (min_d, max_d), min_value=min_d, max_value=max_d, key="pmt_dr")
            type_opts = df_permit['TYPE OF PERMIT'].unique() if 'TYPE OF PERMIT' in df_permit.columns else []
            sel_type = col_f2.multiselect("Permit Type", type_opts, default=type_opts)

        s_date, e_date = dr if len(dr) == 2 else (min_d, max_d)
        mask = (df_permit['DATE'] >= pd.to_datetime(s_date)) & (df_permit['DATE'] <= pd.to_datetime(e_date))
        if sel_type and 'TYPE OF PERMIT' in df_permit.columns: mask &= df_permit['TYPE OF PERMIT'].isin(sel_type)
        df_filtered = df_permit[mask]

        if df_filtered.empty: st.warning("No data matches filters."); return
        k1, k2 = st.columns(2)
        k1.metric("Total Permits", len(df_filtered))
        hot_pct = (len(df_filtered[df_filtered['TYPE OF PERMIT'].str.contains("Hot", case=False)]) / len(df_filtered) * 100) if 'TYPE OF PERMIT' in df_filtered.columns and len(df_filtered) > 0 else 0
        k2.metric("Hot Permits %", f"{hot_pct:.1f}%")

        if 'DRILL SITE' in df_filtered.columns:
            fig = px.bar(df_filtered['DRILL SITE'].value_counts().reset_index(), x='DRILL SITE', y='count')
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # -------------------- EQUIPMENT DASHBOARD --------------------
    with tab_eqp:
        st.subheader("🚜 Heavy Equipment Analytics")
        try:
            df_eq = pd.DataFrame(heavy_equip_sheet.get_all_records())
            df_eq.columns = [str(col).strip().upper() for col in df_eq.columns]
        except gspread.exceptions.GSpreadException: st.error("Could not load equipment data."); return

        if df_eq.empty: st.info("No equipment data."); return

        # Process dates
        date_cols = ["T.P EXPIRY DATE", "INSURANCE EXPIRY DATE", "T.P CARD EXPIRY DATE"]
        for col in date_cols:
            if col in df_eq.columns: df_eq[col] = df_eq[col].apply(parse_date)
            
        # Expiry Logic
        id_cols = ["EQUIPMENT TYPE", "PALTE NO.", "OWNER"]
        exist_id = [c for c in id_cols if c in df_eq.columns]
        exist_dt = [c for c in date_cols if c in df_eq.columns]
        
        if exist_id and exist_dt:
            df_long = df_eq.melt(id_vars=exist_id, value_vars=exist_dt, var_name="Doc", value_name="Exp")
            df_long.dropna(subset=['Exp'], inplace=True)
            df_alerts = df_long[df_long['Exp'] <= thirty_days].copy()
            
            if not df_alerts.empty:
                df_alerts['Status'] = df_alerts['Exp'].apply(lambda d: "🚨 Expired" if d < today else "⚠️ Soon")
                df_alerts['Exp'] = df_alerts['Exp'].apply(lambda d: d.strftime('%Y-%m-%d'))
                st.write("🚨 **Document Expiry Alerts**")
                st.dataframe(df_alerts.sort_values(by="Exp"), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No upcoming expiries.")

        # Charts
        c1, c2 = st.columns(2)
        if 'EQUIPMENT TYPE' in df_eq.columns:
            fig = px.bar(df_eq['EQUIPMENT TYPE'].value_counts().reset_index(), x='EQUIPMENT TYPE', y='count')
            c1.plotly_chart(fig, use_container_width=True)
        if 'PWAS STATUS' in df_eq.columns:
            fig = px.pie(df_eq, names='PWAS STATUS', hole=0.3)
            c2.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_eq, use_container_width=True, hide_index=True)

    # -------------------- VEHICLE DASHBOARD --------------------
    with tab_veh:
        st.subheader("🚚 Heavy Vehicle Analytics")
        try:
            df_veh = pd.DataFrame(heavy_vehicle_sheet.get_all_records())
            df_veh.columns = [str(col).strip().upper() for col in df_veh.columns]
        except gspread.exceptions.GSpreadException: st.error("Could not load vehicle data."); return

        if df_veh.empty: st.info("No vehicle data."); return

        # Process dates
        date_cols_v = ["MVPI EXPIRY DATE", "INSURANCE EXPIRY", "LICENCE EXPIRY"]
        for col in date_cols_v:
            if col in df_veh.columns: df_veh[col] = df_veh[col].apply(parse_date)
            
        # Expiry Logic
        id_cols_v = ["VEHICLE TYPE", "PLATE NO", "DRIVER NAME"]
        exist_id_v = [c for c in id_cols_v if c in df_veh.columns]
        exist_dt_v = [c for c in date_cols_v if c in df_veh.columns]
        
        if exist_id_v and exist_dt_v:
            df_long_v = df_veh.melt(id_vars=exist_id_v, value_vars=exist_dt_v, var_name="Doc", value_name="Exp")
            df_long_v.dropna(subset=['Exp'], inplace=True)
            df_alerts_v = df_long_v[df_long_v['Exp'] <= thirty_days].copy()
            
            if not df_alerts_v.empty:
                df_alerts_v['Status'] = df_alerts_v['Exp'].apply(lambda d: "🚨 Expired" if d < today else "⚠️ Soon")
                df_alerts_v['Exp'] = df_alerts_v['Exp'].apply(lambda d: d.strftime('%Y-%m-%d'))
                st.write("🚨 **Document Expiry Alerts**")
                st.dataframe(df_alerts_v.sort_values(by="Exp"), use_container_width=True, hide_index=True)
            else:
                st.success("✅ No upcoming expiries.")

        # Charts
        c1, c2 = st.columns(2)
        if 'VEHICLE TYPE' in df_veh.columns:
            fig = px.bar(df_veh['VEHICLE TYPE'].value_counts().reset_index(), x='VEHICLE TYPE', y='count')
            c1.plotly_chart(fig, use_container_width=True)
        if 'TYRE CONDITION' in df_veh.columns:
            fig = px.bar(df_veh['TYRE CONDITION'].value_counts().reset_index(), x='TYRE CONDITION', y='count')
            c2.plotly_chart(fig, use_container_width=True)

        st.dataframe(df_veh, use_container_width=True, hide_index=True)

# -------------------- MAIN APP --------------------
def main():
    st.set_page_config(page_title="Onsite Reporting System", layout="wide")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login()
        return

    try:
        obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet = get_sheets()
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets. Please check your connection and secrets.")
        st.error(f"Error details: {e}")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        return

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
