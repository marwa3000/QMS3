import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import googleapiclient.http
from datetime import datetime

# ✅ Load Google Cloud Credentials
google_creds = st.secrets["GOOGLE_CREDENTIALS"]
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file"]
creds = Credentials.from_service_account_info(google_creds, scopes=scopes)
client = gspread.authorize(creds)

# ✅ Google Sheets Configuration (Use Cached Sheets)
def get_sheets():
    return {name: client.open_by_key(st.secrets[f"GOOGLE_SHEETS_ID_{name.upper().replace(' ', '_')}"]).sheet1 
            for name in ["Complaints", "Deviation", "Change Control"]}

sheets = get_sheets()

# ✅ Authenticate Google Drive API
def authenticate_drive():
    service = build("drive", "v3", credentials=creds)
    return service

drive_service = authenticate_drive()

# ✅ Upload File to Google Drive
def upload_to_drive(uploaded_file, filename):
    folder_id = st.secrets["GOOGLE_DRIVE_FOLDER_ID"]
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = googleapiclient.http.MediaIoBaseUpload(uploaded_file, mimetype=uploaded_file.type)
    file_drive = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return f"https://drive.google.com/file/d/{file_drive['id']}/view"

# ✅ Cached Google Sheet Values to reduce API usage
@st.cache_data(ttl=60)
def get_sheet_values_cached(sheet_key):
    sheet = client.open_by_key(sheet_key).sheet1
    return sheet.get_all_values()

# ✅ Generate Record ID
def generate_record_id(sheet, prefix):
    today = datetime.now()
    month = today.strftime("%m")
    year = today.strftime("%y")
    sheet_key = sheet.spreadsheet.id
    cached_values = get_sheet_values_cached(sheet_key)
    if len(cached_values) < 2:
        return f"{prefix}-{month}{year}-001"
    last_row = cached_values[-1]
    last_id = last_row[1] if len(last_row) > 1 else ""
    if last_id.startswith(f"{prefix}-{month}{year}"):
        last_serial = int(last_id.split("-")[-1])
        next_serial = last_serial + 1
    else:
        next_serial = 1
    return f"{prefix}-{month}{year}-{next_serial:03d}"

# ✅ App UI
st.title("🔬 Pharmaceutical QMS (Quality Management System)")
user_name = st.text_input("👤 Please enter your name to track your submissions:")
if not user_name:
    st.warning("⚠️ Please enter your name to proceed.")
    st.stop()

tab1, tab2, tab3, my_tab, admin_tab = st.tabs(["📋 Complaints", "❌ Deviation", "🔄 Change Control", "👤 My Submissions", "🛡️ QA Admin Panel"])

# ✅ Complaints Section
with tab1:
    st.subheader("📋 Register a New Complaint")
    complaint_id = generate_record_id(sheets["Complaints"], "C")
    product = st.text_input("Product Name")
    severity = st.selectbox("Severity Level", ["High", "Medium", "Low"])
    contact_number = st.text_input("📞 Contact Number")
    details = st.text_area("Complaint Details")
    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="complaint_file")
    if st.button("Submit Complaint"):
        if product and details and contact_number:
            file_url = upload_to_drive(uploaded_file, f"{complaint_id}_{uploaded_file.name}") if uploaded_file else ""
            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), complaint_id, product, severity, contact_number, details, user_name, file_url]
            sheets["Complaints"].append_row(new_data)
            st.success(f"✅ Complaint registered successfully with ID {complaint_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ Deviation Section
with tab2:
    st.subheader("❌ Register a New Deviation")
    deviation_id = generate_record_id(sheets["Deviation"], "D")
    department = st.text_input("Responsible Department")
    deviation_type = st.selectbox("Deviation Type", ["Minor", "Major", "Critical"])
    deviation_description = st.text_area("Deviation Details")
    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="deviation_file")
    if st.button("Submit Deviation"):
        if department and deviation_description:
            file_url = upload_to_drive(uploaded_file, f"{deviation_id}_{uploaded_file.name}") if uploaded_file else ""
            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), deviation_id, department, deviation_type, deviation_description, user_name, file_url]
            sheets["Deviation"].append_row(new_data)
            st.success(f"✅ Deviation registered successfully with ID {deviation_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ Change Control Section
with tab3:
    st.subheader("🔄 Register a Change Request")
    change_id = generate_record_id(sheets["Change Control"], "CC")
    change_type = st.selectbox("Change Type", ["Equipment", "Process", "Document", "Other"])
    justification = st.text_area("Justification for Change")
    impact_analysis = st.text_area("Impact Analysis")
    uploaded_file = st.file_uploader("Attach supporting file (optional)", type=["pdf", "png", "jpg", "jpeg", "docx"], key="change_control_file")
    if st.button("Submit Change Request"):
        if change_type and justification and impact_analysis:
            file_url = upload_to_drive(uploaded_file, f"{change_id}_{uploaded_file.name}") if uploaded_file else ""
            new_data = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), change_id, change_type, justification, impact_analysis, user_name, file_url]
            sheets["Change Control"].append_row(new_data)
            st.success(f"✅ Change request registered successfully with ID {change_id}!")
            if file_url:
                st.markdown(f"📎 [Download Attachment]({file_url})")
        else:
            st.error("❌ Please fill in all required fields!")

# ✅ My Submissions Tab
with my_tab:
    st.subheader("👤 My Submissions")
    sheet_data = {
        name: get_sheet_values_cached(st.secrets[f"GOOGLE_SHEETS_ID_{name.upper().replace(' ', '_')}"]) 
        for name in sheets
    }
    for name, data in sheet_data.items():
        st.subheader(f"📜 {name} Records")
        headers = data[0]
        user_records = [row for row in data[1:] if user_name.lower() in [cell.lower() for cell in row]]
        if user_records:
            st.table([headers] + user_records)
        else:
            st.info(f"No records found for you in {name}.")

# ✅ QA Admin Panel (Full Access)
with admin_tab:
    st.subheader("🛡️ QA Admin Panel - View All Records")
    admin_password = st.text_input("Enter QA Admin Password", type="password")
    if st.button("Access QA Admin Panel"):
        if admin_password == "qaadmin123":
            st.success("✅ Access Granted! Viewing all records.")
            sheet_data = {
                name: get_sheet_values_cached(st.secrets[f"GOOGLE_SHEETS_ID_{name.upper().replace(' ', '_')}"]) 
                for name in sheets
            }
            complaint_tab, deviation_tab, change_tab = st.tabs(["📋 Complaints", "❌ Deviations", "🔄 Change Control"])
            with complaint_tab:
                data = sheet_data["Complaints"]
                st.subheader("📋 All Complaints")
                if len(data) > 1:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("No complaints found.")
            with deviation_tab:
                data = sheet_data["Deviation"]
                st.subheader("❌ All Deviations")
                if len(data) > 1:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("No deviations found.")
            with change_tab:
                data = sheet_data["Change Control"]
                st.subheader("🔄 All Change Requests")
                if len(data) > 1:
                    st.dataframe(data, use_container_width=True)
                else:
                    st.info("No change requests found.")
        else:
            st.error("❌ Incorrect password! Access Denied.")
