import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import date, datetime, timedelta
import plotly.express as px
import base64  # Added for image encoding
import os      # Added for file path checking

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

# --- MASTER SITE LIST ---
ALL_SITES = [
    "1858", "1969", "1972", "2433", "2447", "2485",
    "2534", "2549", "2553", "2556", "2566","2570","HRDH Laydown","2595"
]
# ------------------------

# -------------------- UTILITIES --------------------
def get_img_as_base64(file):
    """Reads an image file and returns it as a base64 encoded string."""
    if not os.path.exists(file):
        # st.error(f"Cannot find image file: {file}") # Optional: show error
        return None
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def parse_date(s):
    """Safely parses a string into a date object, trying multiple formats."""
    if isinstance(s, (date, datetime)):
        return s.date() if isinstance(s, datetime) else s
    # Try parsing the new format first, then fall back to the old one for existing data
    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(s).split(' ')[0], fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def badge_expiry(d, expiry_days=30):
    """Creates a visual badge for expiry dates."""
    if d is None:
        return "⚪ Not Set"
    today = date.today()
    date_str = d.strftime('%d-%b-%Y')
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

    obs_sheet = client.open_by_url(OBSERVATION_URL).sheet1
    permit_sheet = client.open_by_url(PERMIT_URL).sheet1
    wb = client.open_by_url(EQUIPMENT_URL)

    def get_or_create(ws_title, headers=None):
        try:
            ws = wb.worksheet(ws_title)
        except gspread.exceptions.WorksheetNotFound:
            ws = wb.add_workskeyt(title=ws_title, rows="1000", cols="40")
            if headers:
                ws.append_row(headers)
        return ws
    
    heavy_equip_headers = [
        "Equipment type", "Make", "Palte No.", "Asset code", "Owner", "T.P inspection date", "T.P Expiry date",
        "Insurance expiry date", "Operator Name", "Iqama NO", "T.P Card type", "T.P Card Number",
        "T.P Card expiry date", "Q.R code", "PWAS status", "F.E TP expiry",
        "FA box Status", "Documents"
    ]

    heavy_vehicle_headers = [
        "Vehicle Type", "Make", "Plate No", "Asset Code", "Owner", "MVPI Expiry date", "Insurance Expiry",
        "Driver Name", "Iqama No", "Licence Expiry", "Q.R code", "F.A Box",
        "PWAS Status", "Seat belt damaged", "Tyre Condition",
        "Suspension Systems", "Remarks"
    ]

    heavy_equip_sheet = get_or_create(HEAVY_EQUIP_TAB, headers=heavy_equip_headers)
    heavy_vehicle_sheet = get_or_create(HEAVY_VEHICLE_TAB, headers=heavy_vehicle_headers)

    return obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet
    
# -------------------- LOGIN PAGE --------------------
def login():
    
    # This assumes "login_bg.jpg" is in the SAME folder as "app.py"
    IMG_PATH = "login_bg.jpg" 

    img_base64 = get_img_as_base64(IMG_PATH) # Try to get the image
    
    background_css = ""
    if img_base64:
        # Auto-detect file type
        file_extension = os.path.splitext(IMG_PATH)[1].lower()
        mime_type = file_extension[1:] # remove the dot
        if mime_type == "jpg":
            mime_type = "jpeg"

        # Create the CSS for the background
        background_css = f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/{mime_type};base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* This makes the main content area transparent so the background shows through */
        [data-testid="stAppViewContainer"] > .main {{
            background-color: transparent !important;
        }}
        </style>
        """
    # If img_base64 is None (image not found), background_css will remain an empty string,
    # and the app will just have its default background. No error message is displayed
    # in the UI now for a cleaner user experience.

    st.markdown(f"""
    {background_css}
    <style>
    .login-container {{
        max-width: 400px; margin: 4rem auto; padding: 2rem;
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        text-align: center;
    }}
    .login-title {{
        font-size: 32px; font-weight:700; color:#2c3e50;
        margin-bottom:1.5rem;
    }}
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
        date_format = "%d-%b-%Y"
        tp_insp_date = cols_dates[0].date_input("T.P inspection date").strftime(date_format)
        tp_expiry = cols_dates[1].date_input("T.P Expiry date").strftime(date_format)
        insurance_expiry = cols_dates[0].date_input("Insurance expiry date").strftime(date_format)
        fe_tp_expiry = cols_dates[1].date_input("F.E TP expiry").strftime(date_format)
        tp_card_expiry = cols_dates[0].date_input("T.P Card expiry date").strftime(date_format)

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
                tp_card_expiry, qr_code, pwas_status, fe_tp_expiry, fa_box_status, documents
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Equipment submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

#--------------------------------------------------------------- HSE OBSERVATION FORM-----------------------------------------------------------------------------------------------
def show_observation_form(sheet):
    st.header("📋 Daily HSE Site Observation Entry Form")
    
    OBSERVER_NAMES = [
        "AJISH", "AKHIL MOHAN", "AQIB", "ARFAN", "ASIM", "ASHRAF KHAN", "BIJO",
        "FELIN", "HABEEB", "ILYAS", "IRFAN", "JAMALI", "JOSEPH CRUZ", "MOHSIN",
        "PRADEEP", "RAJSHEKAR", "RICKEN", "SHIVA KANNAN", "SHIVA SUBRAMANIYAM",
        "SUDISH", "VAISHAK", "VARGHEESE", "WALI ALAM", "ZAHEER"
    ]
    
    AREAS = [
        "Well Head", "Flow Line", "OHPL", "Tie In",
        "Lay Down", "Cellar", "Remote Header"
    ]

    CATEGORIES = [
        "Fall Protection/Personal Fall Arrest System Use/Falling Hazard",
        "Trenching/Excavation/Shoring",
        "Scaffolds, Ladders and Elevated work platforms",
        "Crane and Lifting Devices",
        "Heavy Equipment",
        "Vehicles / Traffic Control",
        "Hand/Power Tools and Electrical appliances",
        "Electrical Safety",
        "Hot work (Cutting/Welding/Brazing)",
        "Fire prevention & Protection",
        "Abrasive Blasting and Coating",
        "Confined Space / Restricted area",
        "Civil, Concrete Work",
        "Compressed Gases",
        "General Equipment's (Air Compressors/Power Generator etc.)",
        "Work Permit, Risk Assessment, JSA & other procedures",
        "Chemical Handling and Hazardous material",
        "Environmental / Waste Management",
        "Health, hygiene & welfare",
        "Radiation and NDT",
        "Security, Unsafe Behavior, and other project Requirements",
        "PPE"
    ]

    SUPERVISOR_TRADE_MAP = {
"RAJA KUMAR": "CONTROLLER-EQUIPMENT", "SREEDHARAN VISWANATHAN": "SUPERVISOR-PIPING",
"MANOJ THOMAS": "WELL IN CHARGE", "ANIL KUMAR JANARDHANAN": "WELL IN CHARGE",
"SIVA PRASAD PILLAI": "FOREMAN-PIPING", "JAYAN RAJAJAN": "FOREMAN-PIPING",
"MURUGAN VANNIYAPERUMAL": "COORDINATOR-NDE", "ANU MOHAN MOHANAN PILLAI": "FIELD ADMINISTRATOR",
"BHARAT CHANDRABARAL": "ASSISTANT-STORE", "SUMOD PRABHAKARA": "LAND SURVEYOR",
"DHARMA RAJU UPPADA": "FOREMAN-HYDRO TEST", "JEFFREY F. TABAMO": "CONSTRUCTION SUPERVISOR-E & I",
"ORLANDO GURGUD": "SUPERVISOR-PAINTING CREW", "RICHARD REYES RIVERAL": "SUPERVISOR-PAINTING CREW",
"AJIMAL SULFIKAR": "SUPERVISOR-PIPING", "ARVIND KUMAR": "SUPERVISOR-CIVIL",
"MAQSUD ALAM": "CONSTRUCTION SUPERVISOR-PIPING", "SIFAT MEHDI": "FOREMAN-INSTRUMENTATION",
"SAJU SADANANDAN": "SUPERVISOR-CIVIL", "SASIDHARA KURUP": "FOREMAN-ELECTRICAL",
"ALVIN CHARLY": "CONSTRUCTION SUPERVISOR-E & I", "PAWAN KUMAR YADAV": "FOREMAN-CIVIL",
"BRIHASPATI ADAK": "FOREMAN-CIVIL", "JITHIN JOHN": "CONSTRUCTION SUPERVISOR-CIVIL",
"RAVI SINGH": "SUPERVISOR-CIVIL", "ANILKUMAR SAHADEVAN": "SUPERVISOR-CIVIL",
"BALA KRISHNA": "FOREMAN-CIVIL", "SUNIL KUMARSAHU": "FOREMAN-CIVIL",
"RAJESHWAR YASOJI NARAYANA": "SUPERVISOR-SCAFFOLDING", "ASHWANI KUMAR YADAV": "FOREMAN-CIVIL",
"QUAISAR ALI": "SUPERVISOR-ELECTRICAL", "ABHISHEK REGHUVARAN": "SUPERVISOR-PIPING",
"ZEESHAN YOUSUF": "SUPERVISOR-CIVIL", "MOHAMMAD RAUSHAN": "SUPERVISOR-CIVIL",
"AHAMED RIYAZ ASHRAE ALI": "SUPERVISOR-CIVIL", "ASLAM KHAN ALBAN": "FOREMAN-SCAFFOLDING",
"SURESH KUMAR": "WELL IN CHARGE", "ANOOPKUMAR": "SUPERVISOR-ELECTRICAL",
"VAISHNAV VINOD SREEJA": "SUPERVISOR-PIPING", "MOHAMMED MUHANNA AL WOSAIFER": "ENGINEER-MECHANICAL",
"HISHAM IBRAHIM AL FARHAN": "ADMIN ASSISTANT", "HASSAN FAYAA MOHAMMED MASHNI": "ELECTRICAL ENGINEER",
"ABDALLAH MOHAMMED ALMOTAWA": "ENGINEER-MECHANICAL", "RAJA ALAGAPPAN": "SUPERVISOR-PAINTING CREW",
"SURESHKUMAR": "CONSTRUCTION SUPERVISOR-PIPING","GOPAN": "SUPERVISOR-CIVIL" 
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
            well_no = st.selectbox("Well No", ALL_SITES) # Uses the master ALL_SITES list
            supervisor_name = st.selectbox("Supervisor Name", supervisor_names)
            trade = SUPERVISOR_TRADE_MAP.get(supervisor_name, "")
            discipline = st.text_input("Discipline", value=trade, disabled=True)
            status = st.selectbox("Status", ["OPEN", "CLOSE"])
            
        obs_details = st.text_area("Observation Details")
        rec_action = st.text_area("Recommended Action")

        if st.form_submit_button("Submit"):
            data = [
                form_date.strftime("%d-%b-%Y"),
                well_no,
                area,
                observer_name,
                obs_details,
                rec_action,
                supervisor_name,
                discipline,
                category,
                classification,
                status
            ]
            try:
                sheet.append_row(data)
                st.success("✅ Observation submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error submitting data: {e}")

def show_permit_form(sheet):
    st.header("🛠️ Daily Internal Permit Log")
    
    WORK_LOCATIONS = [
        "Well Head", "OHPL", "E&I Skid", "Burn Pit", "Cellar",
        "Flow Line", "Lay down", "CP area","BD-Line"
    ]
    PERMIT_TYPES = ["Hot", "Cold", "CSE", "EOLB"]
    PERMIT_ISSUERS = ["UNNIMON SRINIVASAN","VISHNU MOHAN"]
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
        "HAIDAR NASSER MOHAMMED ALKHALAF", "JEYARAJA JAYAPAL",
        "HASHEM ABDULMAJEED ALBAHRANI", "PRATHEEP RADHAKRISHNAN",
        "REYNANTE CAYUMO AMOYO", "JAY MARASIGAN BONDOC", "SHAHWAZ KHAN","PACIFICO LUBANG ICHON","ELMER","REMY E PORRAS"
    ]
    
    PERMIT_ACTIVITIES = [
        "--- Select Activity ---",
        "Mechanical Excavation",
        "Fitup welding cutting and grinding",
        "Holiday test",
        "Manual painting",
        "CP drilling",
        "Trenching and Backfilling",
        "Backfilling leveling and compaction",
        "Construction of ROW",
        "Marl mixing loading and unloading",
        "Construction of fence",
        "Cable pulling",
        "Cable termination and threading",
        "Conduit fixing",
        "Construction of Burn pit",
        "Loading and unloading of materials",
        "Abrasive blasting and painting",
        "Diesel refueling",
        "Equipment maintenance",
        "Water filling",
        "Surface preparation and concrete chipping",
        "Foam work",
        "Shuttering activity",
        "Nitrogen purging",
        "Berming",
        "Marker installation",
        "Grouting",
        "Cellar construction",
        "Entry into CSE",
        "Entry into Burnpit",
        "Hydro test",
        "Scafolding activity",
        "Structure cutting",
        "Bolt Torquing",
        "Surface Prepration",
        "Survey",
        "Foundation Installation",
        "CAD welding",
        "Pipe Lowering"
        "Sand Bedding",
        "Radiography test",
        "Splicing "
    ]

    with st.form("permit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date_val = st.date_input("Date")
            drill_site = st.selectbox("Drill Site", ALL_SITES) # Uses the master ALL_SITES list
            work_location = st.selectbox("Work Location", WORK_LOCATIONS)
            permit_receiver = st.selectbox("Permit Receiver", PERMIT_RECEIVERS)

        with col2:
            permit_no = st.text_input("Permit No")
            permit_type = st.radio("Type of Permit", PERMIT_TYPES, horizontal=True)
            permit_issuer = st.radio("Permit Issuer", PERMIT_ISSUERS, horizontal=True)

        activity = st.selectbox("Activity", PERMIT_ACTIVITIES)

        if st.form_submit_button("Submit"):
            data = [
                date_val.strftime("%d-%b-%Y"), # Column A: DATE
                drill_site,                   # Column B: DRILL SITE
                work_location,                # Column C: WORK LOCATION
                permit_no,                    # Column D: PERMIT NO
                permit_type,                  # Column E: TYPE OF PERMIT
                activity,                     # Column F: ACTIVITY
                permit_receiver,              # Column G: PERMIT RECEIVER
                permit_issuer                 # Column H: PERMIT ISSUER
            ]
            try:
                sheet.append_row(data)
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
        d1, d2 = st.columns(2)
        date_format = "%d-%b-%Y"
        mvpi_expiry = d1.date_input("MVPI Expiry date").strftime(date_format)
        insurance_expiry = d2.date_input("Insurance Expiry").strftime(date_format)
        licence_expiry = d1.date_input("Licence Expiry").strftime(date_format)

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
                sheet.append_row(data)
                st.success("✅ Heavy Vehicle submitted successfully!")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# -------------------- ADVANCED DASHBOARD (MODIFIED) --------------------
def show_combined_dashboard(obs_sheet, permit_sheet, heavy_equip_sheet, heavy_vehicle_sheet):
    st.header("📊 Dashboard")
    tab_obs, tab_permit, tab_eqp, tab_veh = st.tabs([
        "📋 Observation", "🛠️ Permit", "🚜 Heavy Equipment", "🚚 Heavy Vehicle"
    ])

    today = date.today()
    thirty_days = today + timedelta(days=30)

    # -------------------- OBSERVATION TAB --------------------
    with tab_obs:
        st.subheader("Advanced Observation Analytics")
        try:
            df_obs = pd.DataFrame(obs_sheet.get_all_records())
            df_obs.columns = [str(col).strip().upper() for col in df_obs.columns]
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load observation data from Google Sheets: {e}")
            return # Use return to stop execution of this tab only

        if df_obs.empty:
            st.info("No observation data available to display.")
            return

        # --- Data Cleaning and Preparation ---
        if 'DATE' not in df_obs.columns:
            st.warning("The 'DATE' column is missing from the Observation Log sheet.")
            return

        df_obs['DATE'] = pd.to_datetime(df_obs['DATE'], errors='coerce')
        df_obs.dropna(subset=['DATE'], inplace=True)
        df_obs = df_obs.sort_values(by='DATE', ascending=False)
        
        if 'CLASSIFICATION' in df_obs.columns:
             df_obs['CLASSIFICATION'] = df_obs['CLASSIFICATION'].str.strip().str.upper()
        if 'STATUS' in df_obs.columns:
             df_obs['STATUS'] = df_obs['STATUS'].str.strip().str.capitalize()


        # --- Interactive Filters ---
        st.markdown("#### Filter & Explore")
        with st.expander("Adjust Filters", expanded=True):
            col_filter1_obs, col_filter2_obs = st.columns(2)

            with col_filter1_obs:
                min_date_obs = df_obs['DATE'].min().date()
                max_date_obs = df_obs['DATE'].max().date()
                date_range_obs = st.date_input(
                    "Select Date Range",
                    (min_date_obs, max_date_obs),
                    min_value=min_date_obs,
                    max_value=max_date_obs,
                    key="obs_date_range"
                )

            with col_filter2_obs:
                class_options = df_obs['CLASSIFICATION'].unique() if 'CLASSIFICATION' in df_obs.columns else []
                selected_class = st.multiselect("Filter by Classification", options=class_options, default=class_options)

                status_options = df_obs['STATUS'].unique() if 'STATUS' in df_obs.columns else []
                selected_status = st.multiselect("Filter by Status", options=status_options, default=status_options)

        # --- Apply Filters to DataFrame ---
        start_date_obs, end_date_obs = date_range_obs if len(date_range_obs) == 2 else (min_date_obs, max_date_obs)
        start_datetime_obs = pd.to_datetime(start_date_obs)
        end_datetime_obs = pd.to_datetime(end_date_obs)

        mask_obs = (df_obs['DATE'] >= start_datetime_obs) & (df_obs['DATE'] <= end_datetime_obs)
        if selected_class and 'CLASSIFICATION' in df_obs.columns:
            mask_obs &= df_obs['CLASSIFICATION'].isin(selected_class)
        if selected_status and 'STATUS' in df_obs.columns:
            mask_obs &= df_obs['STATUS'].isin(selected_status)

        df_filtered_obs = df_obs[mask_obs]

        if df_filtered_obs.empty:
            st.warning("No data matches the selected filters.")
            return

        # --- High-Level KPIs ---
        st.markdown("---")
        st.markdown("#### Key Metrics Overview")

        total_obs = len(df_filtered_obs)
        open_issues = 0
        if 'STATUS' in df_filtered_obs.columns:
            open_issues = df_filtered_obs[df_filtered_obs['STATUS'] == 'Open'].shape[0]

        total_unsafe = 0
        if 'CLASSIFICATION' in df_filtered_obs.columns:
            total_unsafe = df_filtered_obs[df_filtered_obs['CLASSIFICATION'].isin(['UNSAFE ACT', 'UNSAFE CONDITION'])].shape[0]

        busiest_day_obs = df_filtered_obs['DATE'].dt.day_name().mode()[0] if not df_filtered_obs.empty else "N/A"

        kpi1_obs, kpi2_obs, kpi3_obs, kpi4_obs = st.columns(4)
        kpi1_obs.metric("Total Observations", f"{total_obs}")
        kpi2_obs.metric("Open Issues", f"{open_issues}")
        kpi3_obs.metric("Total Unsafe (Acts + Cond.)", f"{total_unsafe}")
        kpi4_obs.metric("Busiest Day", busiest_day_obs)
        st.markdown("---")

        # --- Visualizations ---
        st.markdown("#### Visual Insights")
        col_viz1_obs, col_viz2_obs = st.columns(2)

        with col_viz1_obs:
            if 'CLASSIFICATION' in df_filtered_obs.columns:
                st.write("**Observation Classification**")
                color_map = {'UNSAFE ACT': '#E74C3C', 'UNSAFE CONDITION': '#F39C12', 'POSITIVE': '#2ECC71'}
                
                class_counts = df_filtered_obs['CLASSIFICATION'].value_counts().reset_index()
                
                fig_class_pie = px.pie(
                    class_counts,
                    values='count',
                    names='CLASSIFICATION',
                    hole=0.4,
                    color='CLASSIFICATION',
                    color_discrete_map=color_map
                )
                fig_class_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_class_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_class_pie, use_container_width=True)

            if 'CATEGORY' in df_filtered_obs.columns:
                st.write("**Top 10 Observation Categories**")
                cat_counts = df_filtered_obs['CATEGORY'].value_counts().nlargest(10).reset_index()
                fig_cat_bar = px.bar(
                    cat_counts,
                    y='CATEGORY', x='count', orientation='h', text_auto=True,
                    labels={'count': 'Count', 'CATEGORY': 'Category'}
                )
                fig_cat_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_cat_bar, use_container_width=True)

        with col_viz2_obs:
            if 'STATUS' in df_filtered_obs.columns:
                st.write("**Observation Status**")
                status_color_map = {'Open': '#E74C3C', 'Close': '#2ECC71'} # Adjusted "CLOSE" to "Close"
                status_counts = df_filtered_obs['STATUS'].value_counts().reset_index()

                fig_status_pie = px.pie(
                    status_counts,
                    values='count',
                    names='STATUS',
                    hole=0.4,
                    color='STATUS',
                    color_discrete_map=status_color_map
                )
                fig_status_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_status_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_status_pie, use_container_width=True)

            if 'OBSERVER NAME' in df_filtered_obs.columns:
                st.write("**Top 10 Observers**")
                observer_counts = df_filtered_obs['OBSERVER NAME'].value_counts().nlargest(10).reset_index()
                fig_obs_bar = px.bar(
                    observer_counts,
                    y='OBSERVER NAME', x='count', orientation='h', text_auto=True,
                    labels={'count': 'Count', 'OBSERVER NAME': 'Observer'}
                )
                fig_obs_bar.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_obs_bar, use_container_width=True)
        
        # --- Time Series Analysis ---
        st.markdown("---")
        st.write("#### Observation Trend Over Time")
        obs_by_day = df_filtered_obs.groupby(df_filtered_obs['DATE'].dt.date).size().reset_index(name='count')
        
        fig_time_obs = px.area(
            obs_by_day, x='DATE', y='count', markers=True,
            labels={'DATE': 'Date', 'count': 'Number of Observations'}
        )
        fig_time_obs.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_time_obs, use_container_width=True)
        
        # --- Supervisor Analysis ---
        if 'SUPERVISOR NAME' in df_filtered_obs.columns and 'CLASSIFICATION' in df_filtered_obs.columns:
            st.write("#### Unsafe Observations by Supervisor")
            df_unsafe = df_filtered_obs[df_filtered_obs['CLASSIFICATION'].isin(['UNSAFE ACT', 'UNSAFE CONDITION'])]
            
            if not df_unsafe.empty:
                unsafe_counts = df_unsafe.groupby(['SUPERVISOR NAME', 'CLASSIFICATION']).size().reset_index(name='count')
                
                top_supervisors = df_unsafe['SUPERVISOR NAME'].value_counts().nlargest(15).index
                unsafe_counts_top = unsafe_counts[unsafe_counts['SUPERVISOR NAME'].isin(top_supervisors)]

                fig_sup_bar = px.bar(
                    unsafe_counts_top,
                    x='SUPERVISOR NAME',
                    y='count',
                    color='CLASSIFICATION',
                    title="Unsafe Acts/Conditions by Supervisor (Top 15)",
                    barmode='stack',
                    labels={'count': 'Total Unsafe Observations', 'SUPERVISOR NAME': 'Supervisor', 'CLASSIFICATION': 'Type'},
                    color_discrete_map={'UNSAFE ACT': '#E74C3C', 'UNSAFE CONDITION': '#F39C12'}
                )
                fig_sup_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_sup_bar, use_container_width=True)
            else:
                st.info("No 'Unsafe Act' or 'Unsafe Condition' observations found in the selected filter range.")


        # --- Full Data Table ---
        st.markdown("---")
        st.markdown("#### Detailed Observation Log (Filtered)")
        df_display_obs = df_filtered_obs.copy()
        df_display_obs['DATE'] = df_display_obs['DATE'].dt.strftime('%d-%b-%Y')
        st.dataframe(df_display_obs, use_container_width=True, hide_index=True)

    # -------------------- PERMIT TAB --------------------
    with tab_permit:
        st.subheader("Advanced Permit Log Analytics")
        try:
            df_permit = pd.DataFrame(permit_sheet.get_all_records())
            df_permit.columns = [str(col).strip().upper() for col in df_permit.columns]
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load permit data from Google Sheets: {e}")
            return

        if df_permit.empty:
            st.info("No permit data available to display.")
            return

        # --- Data Cleaning and Preparation ---
        if 'DATE' not in df_permit.columns:
            st.warning("The 'DATE' column is missing from the Permit Log sheet.")
            return

        df_permit['DATE'] = pd.to_datetime(df_permit['DATE'], errors='coerce')
        df_permit.dropna(subset=['DATE'], inplace=True)
        df_permit = df_permit.sort_values(by='DATE', ascending=False)

        # --- Interactive Filters ---
        st.markdown("#### Filter & Explore")
        with st.expander("Adjust Filters", expanded=True):
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                min_date = df_permit['DATE'].min().date()
                max_date = df_permit['DATE'].max().date()
                date_range = st.date_input(
                    "Select Date Range",
                    (min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="permit_date_range"
                )

            with col_filter2:
                permit_types = df_permit['TYPE OF PERMIT'].unique() if 'TYPE OF PERMIT' in df_permit.columns else []
                selected_types = st.multiselect("Filter by Permit Type", options=permit_types, default=permit_types)

                issuers = df_permit['PERMIT ISSUER'].unique() if 'PERMIT ISSUER' in df_permit.columns else []
                selected_issuers = st.multiselect("Filter by Permit Issuer", options=issuers, default=issuers)

        # --- Apply Filters to DataFrame ---
        start_date, end_date = date_range if len(date_range) == 2 else (min_date, max_date)
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)

        mask = (df_permit['DATE'] >= start_datetime) & (df_permit['DATE'] <= end_datetime)
        if selected_types and 'TYPE OF PERMIT' in df_permit.columns:
            mask &= df_permit['TYPE OF PERMIT'].isin(selected_types)
        if selected_issuers and 'PERMIT ISSUER' in df_permit.columns:
            mask &= df_permit['PERMIT ISSUER'].isin(selected_issuers)

        df_filtered = df_permit[mask]

        if df_filtered.empty:
            st.warning("No data matches the selected filters.")
            return

        # --- High-Level KPIs ---
        st.markdown("---")
        st.markdown("#### Key Metrics Overview")

        total_permits = len(df_filtered)
        hot_permits_count = 0
        if 'TYPE OF PERMIT' in df_filtered.columns:
            hot_permits_count = df_filtered[df_filtered['TYPE OF PERMIT'].str.contains("Hot", case=False)].shape[0]

        hot_permits_perc = (hot_permits_count / total_permits * 100) if total_permits > 0 else 0
        busiest_day = df_filtered['DATE'].dt.day_name().mode()[0] if not df_filtered.empty else "N/A"
        active_receivers = df_filtered['PERMIT RECEIVER'].nunique() if 'PERMIT RECEIVER' in df_filtered.columns else 0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Total Permits (in range)", f"{total_permits}")
        kpi2.metric("Hot Permits %", f"{hot_permits_perc:.1f}%")
        kpi3.metric("Busiest Day", busiest_day)
        kpi4.metric("Active Permit Receivers", f"{active_receivers}")
        st.markdown("---")

        # --- Visualizations ---
        st.markdown("#### Visual Insights")
        col_viz1, col_viz2 = st.columns(2)

        with col_viz1:
            if 'TYPE OF PERMIT' in df_filtered.columns:
                st.write("**Permit Type Distribution**")
                fig_type_pie = px.pie(
                    df_filtered, names='TYPE OF PERMIT', hole=0.4,
                )
                fig_type_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_type_pie.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_type_pie, use_container_width=True)

            if 'DRILL SITE' in df_filtered.columns and 'TYPE OF PERMIT' in df_filtered.columns:
                st.write("**Permit Composition by Drill Site**")
                
                site_permit_counts = df_filtered.groupby(['DRILL SITE', 'TYPE OF PERMIT']).size().reset_index(name='count')
                
                site_permit_counts['DRILL SITE'] = pd.Categorical(
                    site_permit_counts['DRILL SITE'],
                    categories=ALL_SITES,
                    ordered=True
                )
                site_permit_counts = site_permit_counts.dropna(subset=['DRILL SITE'])

                fig_site_stacked = px.bar(
                    site_permit_counts,
                    x='DRILL SITE',
                    y='count',
                    color='TYPE OF PERMIT',
                    title="Permit Type Breakdown per Site",
                    text_auto=True,
                    labels={
                        'count': 'Total Permits',
                        'DRILL SITE': 'Drill Site',
                        'TYPE OF PERMIT': 'Permit Type'
                    }
                )
                fig_site_stacked.update_layout(
                    barmode='stack',
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_site_stacked, use_container_width=True)
            
            elif 'DRILL SITE' in df_filtered.columns:
                st.write("**Total Permits by Drill Site**")
                site_counts = df_filtered['DRILL SITE'].value_counts().reset_index()

                site_counts['DRILL SITE'] = pd.Categorical(
                    site_counts['DRILL SITE'],
                    categories=ALL_SITES,
                    ordered=True
                )
                site_counts = site_counts.dropna(subset=['DRILL SITE'])

                fig_site = px.bar(
                    site_counts, x='DRILL SITE', y='count', text_auto=True,
                    title="Total Permits per Drill Site",
                    labels={'count': 'Count', 'DRILL SITE': 'Drill Site'}
                )
                fig_site.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_site, use_container_width=True)

        with col_viz2:
            if 'PERMIT ISSUER' in df_filtered.columns:
                st.write("**Permit Count by Issuer**")
                issuer_counts = df_filtered['PERMIT ISSUER'].value_counts().reset_index()
                fig_issuer_bar = px.bar(
                    issuer_counts,
                    x='PERMIT ISSUER',
                    y='count',
                    text_auto=True,
                    labels={'count': 'Number of Permits', 'PERMIT ISSUER': 'Issuer Name'}
                )
                fig_issuer_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_issuer_bar, use_container_width=True)

            if 'PERMIT RECEIVER' in df_filtered.columns:
                st.write("**Top 10 Permit Receivers**")
                receiver_counts = df_filtered['PERMIT RECEIVER'].value_counts().nlargest(10).reset_index()
                fig_receiver = px.bar(
                    receiver_counts, y='PERMIT RECEIVER', x='count', orientation='h', text_auto=True,
                    labels={'count': 'Count', 'PERMIT RECEIVER': 'Receiver Name'}
                )
                fig_receiver.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=30, b=20))
                st.plotly_chart(fig_receiver, use_container_width=True)
                
        # --- Time Series Analysis ---
        st.markdown("---")
        st.write("#### Permit Trend Over Time")
        permits_by_day = df_filtered.groupby(df_filtered['DATE'].dt.date).size().reset_index(name='count')
        
        fig_time = px.area(
            permits_by_day, x='DATE', y='count', markers=True,
            labels={'DATE': 'Date', 'count': 'Number of Permits'}
        )
        
        fig_time.update_traces(
            fill='tozeroy',
            fillcolor='rgba(220, 240, 220, 0.7)',
            line=dict(color='rgba(34, 139, 34, 1)')
        )
        
        fig_time.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_time, use_container_width=True)

        # --- Full Data Table ---
        st.markdown("---")
        st.markdown("#### Detailed Permit Log (Filtered)")
        df_display_permit = df_filtered.copy()
        df_display_permit['DATE'] = df_display_permit['DATE'].dt.strftime('%d-%b-%Y')
        st.dataframe(df_display_permit, use_container_width=True, hide_index=True)

    # -------------------- HEAVY EQUIPMENT TAB --------------------
    with tab_eqp:
        st.subheader("🚜 Heavy Equipment Analytics")
        try:
            df_equip = pd.DataFrame(heavy_equip_sheet.get_all_records())
            df_equip.columns = [str(col).strip().upper() for col in df_equip.columns]
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load data from Google Sheets: {e}")
            return

        if df_equip.empty:
            st.info("No Heavy Equipment data available to display.")
            return

        date_cols_eq = ["T.P EXPIRY DATE", "INSURANCE EXPIRY DATE", "T.P CARD EXPIRY DATE", "F.E TP EXPIRY"]
        for col in date_cols_eq:
                if col in df_equip.columns:
                        df_equip[col] = df_equip[col].apply(parse_date)

        # --- EXPIRY TRACKING TABLE ---
        st.subheader("🚨 Equipment Document Expiry Alerts")

        id_cols_eq = ["EQUIPMENT TYPE", "PALTE NO.", "OWNER", "OPERATOR NAME"]
        
        existing_id_cols_eq = [c for c in id_cols_eq if c in df_equip.columns]
        existing_date_cols_eq = [c for c in date_cols_eq if c in df_equip.columns]

        if not existing_date_cols_eq or not existing_id_cols_eq:
            st.warning("Could not generate alerts. Key identifier or date columns are missing from the sheet.")
        else:
            df_long_eq = df_equip.melt(
                id_vars=existing_id_cols_eq,
                value_vars=existing_date_cols_eq,
                var_name="Document Type",
                value_name="Expiry Date"
            )

            df_long_eq.dropna(subset=['Expiry Date'], inplace=True)
            df_alerts_eq = df_long_eq[df_long_eq['Expiry Date'] <= thirty_days].copy()

            if df_alerts_eq.empty:
                st.success("✅ No equipment documents are expired or expiring within 30 days.")
            else:
                df_alerts_eq['Status'] = df_alerts_eq['Expiry Date'].apply(
                    lambda d: "🚨 Expired" if d < today else "⚠️ Expiring Soon"
                )
                
                df_alerts_eq['Expiry Date'] = df_alerts_eq['Expiry Date'].apply(lambda d: d.strftime('%d-%b-%Y'))
                
                df_alerts_eq = df_alerts_eq.sort_values(by=["Status", "Expiry Date"])
                
                display_cols_eq = [
                    "EQUIPMENT TYPE", "PALTE NO.", "Document Type",
                    "Expiry Date", "Status", "OPERATOR NAME", "OWNER"
                ]
                
                final_cols_eq = [col for col in display_cols_eq if col in df_alerts_eq.columns]
                
                st.dataframe(df_alerts_eq[final_cols_eq], use_container_width=True, hide_index=True)
        # --- END OF TABLE ---

        st.markdown("---")

        total_equipment = len(df_equip)
        expired_count = 0
        expiring_soon_count = 0

        for col in existing_date_cols_eq:
            expired_count += df_equip.loc[df_equip[col] < today].shape[0]
            expiring_soon_count += df_equip.loc[(df_equip[col] >= today) & (df_equip[col] <= thirty_days)].shape[0]

        kpi1_eq, kpi2_eq, kpi3_eq = st.columns(3)
        kpi1_eq.metric(label="Total Equipment", value=total_equipment)
        kpi2_eq.metric(label="Total Expired Items", value=expired_count, delta="Action Required", delta_color="inverse")
        kpi3_eq.metric(label="Expiring in 30 Days", value=expiring_soon_count, delta="Monitor Closely", delta_color="off")
        
        st.markdown("---")
        
        st.subheader("Visual Insights")
        c1_eq, c2_eq = st.columns(2)

        with c1_eq:
            if 'EQUIPMENT TYPE' in df_equip.columns:
                fig_type_eq = px.bar(
                    df_equip['EQUIPMENT TYPE'].value_counts().reset_index(),
                    x='EQUIPMENT TYPE', y='count', title='Equipment Distribution by Type',
                    labels={'count': 'Number of Units', 'EQUIPMENT TYPE': 'Type'},
                    text_auto=True
                )
                fig_type_eq.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_type_eq, use_container_width=True)

        with c2_eq:
            if 'PWAS STATUS' in df_equip.columns:
                fig_pwas = px.pie(
                    df_equip, names='PWAS STATUS', title='PWAS Status Overview',
                    hole=0.3
                )
                st.plotly_chart(fig_pwas, use_container_width=True)
                
        if 'OWNER' in df_equip.columns:
            fig_owner = px.bar(
                df_equip['OWNER'].value_counts().nlargest(10).reset_index(),
                x='OWNER', y='count', title='Top 10 Equipment Owners',
                labels={'count': 'Number of Units', 'OWNER': 'Owner Name'},
                text_auto=True
            )
            st.plotly_chart(fig_owner, use_container_width=True)
        
        st.markdown("---")
        
        st.subheader("Full Heavy Equipment Data")
        df_display_eq = df_equip.copy()
        for col in existing_date_cols_eq:
            df_display_eq[col] = df_display_eq[col].apply(badge_expiry, expiry_days=30)
        
        st.dataframe(df_display_eq, use_container_width=True, hide_index=True)

    # -------------------- START: NEW HEAVY VEHICLE TAB --------------------
    with tab_veh:
        st.subheader("🚚 Heavy Vehicle Analytics")
        try:
            df_veh = pd.DataFrame(heavy_vehicle_sheet.get_all_records())
            df_veh.columns = [str(col).strip().upper() for col in df_veh.columns]
        except gspread.exceptions.GSpreadException as e:
            st.error(f"Could not load data from Google Sheets: {e}")
            return

        if df_veh.empty:
            st.info("No Heavy Vehicle data available to display.")
            return

        # --- Data Cleaning ---
        date_cols_veh = ["MVPI EXPIRY DATE", "INSURANCE EXPIRY", "LICENCE EXPIRY"]
        for col in date_cols_veh:
            if col in df_veh.columns:
                df_veh[col] = df_veh[col].apply(parse_date)
        
        cat_cols_veh = ["PWAS STATUS", "TYRE CONDITION", "SUSPENSION SYSTEMS", "F.A BOX", "SEAT BELT DAMAGED", "VEHICLE TYPE"]
        for col in cat_cols_veh:
             if col in df_veh.columns:
                 df_veh[col] = df_veh[col].str.strip().str.capitalize()

        # --- Filters ---
        st.markdown("#### Filter & Explore")
        with st.expander("Adjust Filters", expanded=True):
            col_f1_veh, col_f2_veh = st.columns(2)
            
            type_options_veh = df_veh['VEHICLE TYPE'].unique() if 'VEHICLE TYPE' in df_veh.columns else []
            selected_types_veh = col_f1_veh.multiselect("Filter by Vehicle Type", options=type_options_veh, default=type_options_veh)

            owner_options_veh = df_veh['OWNER'].unique() if 'OWNER' in df_veh.columns else []
            selected_owners_veh = col_f2_veh.multiselect("Filter by Owner", options=owner_options_veh, default=owner_options_veh)

        # --- Apply Filters ---
        mask_veh = pd.Series(True, index=df_veh.index)
        if selected_types_veh and 'VEHICLE TYPE' in df_veh.columns:
            mask_veh &= df_veh['VEHICLE TYPE'].isin(selected_types_veh)
        if selected_owners_veh and 'OWNER' in df_veh.columns:
            mask_veh &= df_veh['OWNER'].isin(selected_owners_veh)
        
        df_filtered_veh = df_veh[mask_veh]

        if df_filtered_veh.empty:
            st.warning("No data matches the selected filters.")
            return

        # --- Expiry Table ---
        st.subheader("🚨 Vehicle Document Expiry Alerts")
        id_cols_veh = ["VEHICLE TYPE", "PLATE NO", "OWNER", "DRIVER NAME"]
        
        existing_id_cols_veh = [c for c in id_cols_veh if c in df_filtered_veh.columns]
        existing_date_cols_veh = [c for c in date_cols_veh if c in df_filtered_veh.columns]

        if not existing_date_cols_veh or not existing_id_cols_veh:
            st.warning("Could not generate alerts. Key identifier or date columns are missing from the sheet.")
        else:
            df_long_veh = df_filtered_veh.melt(
                id_vars=existing_id_cols_veh,
                value_vars=existing_date_cols_veh,
                var_name="Document Type",
                value_name="Expiry Date"
            )
            df_long_veh.dropna(subset=['Expiry Date'], inplace=True)
            df_alerts_veh = df_long_veh[df_long_veh['Expiry Date'] <= thirty_days].copy()

            if df_alerts_veh.empty:
                st.success("✅ No vehicle documents are expired or expiring within 30 days.")
            else:
                df_alerts_veh['Status'] = df_alerts_veh['Expiry Date'].apply(lambda d: "🚨 Expired" if d < today else "⚠️ Expiring Soon")
                df_alerts_veh['Expiry Date'] = df_alerts_veh['Expiry Date'].apply(lambda d: d.strftime('%d-%b-%Y'))
                df_alerts_veh = df_alerts_veh.sort_values(by=["Status", "Expiry Date"])
                
                display_cols_veh = ["VEHICLE TYPE", "PLATE NO", "Document Type", "Expiry Date", "Status", "DRIVER NAME", "OWNER"]
                final_cols_veh = [col for col in display_cols_veh if col in df_alerts_veh.columns]
                st.dataframe(df_alerts_veh[final_cols_veh], use_container_width=True, hide_index=True)
        # --- END OF TABLE ---

        st.markdown("---")

        # --- KPIs ---
        total_vehicles = len(df_filtered_veh)
        expired_count_veh = 0
        expiring_soon_count_veh = 0

        for col in existing_date_cols_veh:
            expired_count_veh += df_filtered_veh.loc[df_filtered_veh[col] < today].shape[0]
            expiring_soon_count_veh += df_filtered_veh.loc[(df_filtered_veh[col] >= today) & (df_filtered_veh[col] <= thirty_days)].shape[0]

        kpi1_veh, kpi2_veh, kpi3_veh = st.columns(3)
        kpi1_veh.metric(label="Total Vehicles (Filtered)", value=total_vehicles)
        kpi2_veh.metric(label="Total Expired Items", value=expired_count_veh, delta="Action Required", delta_color="inverse")
        kpi3_veh.metric(label="Expiring in 30 Days", value=expiring_soon_count_veh, delta="Monitor Closely", delta_color="off")
        
        st.markdown("---")
        
        # --- Charts ---
        st.subheader("Visual Insights")
        c1_veh, c2_veh = st.columns(2)

        with c1_veh:
            if 'VEHICLE TYPE' in df_filtered_veh.columns:
                fig_type_veh = px.bar(
                    df_filtered_veh['VEHICLE TYPE'].value_counts().reset_index(),
                    x='VEHICLE TYPE', y='count', title='Vehicle Distribution by Type',
                    labels={'count': 'Number of Units', 'VEHICLE TYPE': 'Type'},
                    text_auto=True
                )
                fig_type_veh.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_type_veh, use_container_width=True)

        with c2_veh:
            if 'PWAS STATUS' in df_filtered_veh.columns:
                fig_pwas_veh = px.pie(
                    df_filtered_veh, names='PWAS STATUS', title='PWAS Status Overview',
                    hole=0.3
                )
                st.plotly_chart(fig_pwas_veh, use_container_width=True)
                
        if 'TYRE CONDITION' in df_filtered_veh.columns:
            fig_tyre = px.bar(
                df_filtered_veh['TYRE CONDITION'].value_counts().reset_index(),
                x='TYRE CONDITION', y='count', title='Tyre Condition Overview',
                labels={'count': 'Count', 'TYRE CONDITION': 'Condition'},
                text_auto=True
            )
            st.plotly_chart(fig_tyre, use_container_width=True)
        
        # --- Full Table ---
        st.markdown("---")
        st.subheader("Full Heavy Vehicle Data (Filtered)")
        df_display_veh = df_filtered_veh.copy()
        for col in existing_date_cols_veh:
            if col in df_display_veh.columns:
                df_display_veh[col] = df_display_veh[col].apply(badge_expiry, expiry_days=30)
        
        st.dataframe(df_display_veh, use_container_width=True, hide_index=True)

    # -------------------- END: NEW HEAVY VEHICLE TAB --------------------

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





