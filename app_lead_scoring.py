import streamlit as st
import pandas as pd
import numpy as np
import time
import os
import json
from io import BytesIO

# Try importing Google AI & Google sheets dependencies
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

try:
    import gspread
    from google.oauth2.service_account import Credentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# Set page config for a widescreen premium look
st.set_page_config(
    page_title="Hệ thống AI Lead Scoring - Bất Động Sản",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Glassmorphism and Dark Mode styling
st.markdown("""
<style>
    /* Dark canvas background */
    [data-testid="stAppViewContainer"] {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    
    /* Modern text headers */
    h1, h2, h3 {
        color: #F1F5F9 !important;
        font-family: 'Inter', -apple-system, sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Transparent sidebar with fine border */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Custom CSS Glassmorphism KPI Container and Cards */
    .kpi-container {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 24px;
        width: 100%;
    }
    
    .kpi-card {
        flex: 1;
        min-width: 200px;
        padding: 20px;
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    .kpi-title {
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: rgba(255, 255, 255, 0.5);
        margin-bottom: 6px;
        text-align: center;
    }
    
    .kpi-value {
        font-family: 'Fira Code', 'Courier New', monospace;
        font-size: 32px;
        font-weight: 700;
        color: #FFFFFF;
        text-align: center;
    }
    
    /* Color tints for the KPIs */
    .kpi-vip {
        border-left: 4px solid #10B981;
    }
    .kpi-normal {
        border-left: 4px solid #3B82F6;
    }
    .kpi-junk {
        border-left: 4px solid #EF4444;
    }
    .kpi-total {
        border-left: 4px solid #8B5CF6;
    }
    
    .kpi-vip .kpi-value {
        color: #34D399;
    }
    .kpi-normal .kpi-value {
        color: #60A5FA;
    }
    .kpi-junk .kpi-value {
        color: #F87171;
    }
    .kpi-total .kpi-value {
        color: #C084FC;
    }
    
    /* Glow highlights for updates */
    .status-badge {
        padding: 4px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE MEMORY SETUP -----------------
if 'raw_data' not in st.session_state:
    st.session_state['raw_data'] = None
if 'scored_data' not in st.session_state:
    st.session_state['scored_data'] = None
if 'api_logs' not in st.session_state:
    st.session_state['api_logs'] = []
if 'credentials_dict' not in st.session_state:
    st.session_state['credentials_dict'] = None

# Default Sheet details
DEFAULT_SPREADSHEET_ID = "16tCAf_qqtgYZxoumYQKMEOdBhKE0wg5A"
DEFAULT_PUBLIC_URL = f"https://docs.google.com/spreadsheets/d/{DEFAULT_SPREADSHEET_ID}/export?format=xlsx"

# ----------------- SIDEBAR CONFIGURATION -----------------
st.sidebar.image("https://img.icons8.com/nolan/96/real-estate.png", width=80)
st.sidebar.title("AI Lead Scoring System")
st.sidebar.write("*Phiên bản Premium UI/UX*")

st.sidebar.markdown("---")

# 1. API Configuration
st.sidebar.subheader("🔌 Cấu hình AI Brain")
gemini_key = st.sidebar.text_input("Gemini API Key", type="password", help="Nhập Gemini API Key của bạn để chạy phân tích AI thực tế. Nếu trống, hệ thống sẽ sử dụng bộ quy tắc cứng (Rule-based engine) để mô phỏng.")
selected_model = st.sidebar.selectbox("Mô hình AI", ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-2.5-pro"])

# 2. Data Source Configuration
st.sidebar.subheader("📊 Nguồn dữ liệu Google Sheets")
connection_mode = st.sidebar.radio("Chế độ kết nối", ["Public Link (Mặc định)", "Private Google Sheet (Bảo mật)"])

sheet_url = DEFAULT_PUBLIC_URL
if connection_mode == "Public Link (Mặc định)":
    input_sheet_id = st.sidebar.text_input("Google Sheet ID hoặc Link Export", DEFAULT_SPREADSHEET_ID, help="Nhập ID của Google Sheet")
    if input_sheet_id:
        if "docs.google.com" in input_sheet_id:
            sheet_url = input_sheet_id
        else:
            sheet_url = f"https://docs.google.com/spreadsheets/d/{input_sheet_id}/export?format=xlsx"
else:
    st.sidebar.markdown("**Cấu hình Service Account (Private)**")
    uploaded_creds = st.sidebar.file_uploader("Tải lên file JSON Credentials", type="json")
    if uploaded_creds:
        try:
            st.session_state['credentials_dict'] = json.load(uploaded_creds)
            st.sidebar.success("🔑 Đã nhận file Credentials!")
        except Exception as e:
            st.sidebar.error(f"Lỗi đọc file JSON: {e}")
            
    private_sheet_id = st.sidebar.text_input("Private Google Sheet ID", DEFAULT_SPREADSHEET_ID)
    private_sheet_name = st.sidebar.text_input("Tên Sheet Tab", "Sheet1")

# 3. System Audit - 7 Elements Dashboard
st.sidebar.markdown("---")
st.sidebar.subheader("📋 Audit 7 Thành tố Hệ thống")
st.sidebar.markdown(f"""
- 📥 **1. Input**: `Google Sheets` ({'Private' if connection_mode == 'Private Google Sheet (Bảo mật)' else 'Public'})
- 🧠 **2. Agent**: `Gemini API` ({'Thực tế' if gemini_key else 'Mô phỏng/Rule-based'})
- 🛠️ **3. Tools**: `Streamlit`, `Pandas`, `openpyxl`
- 📚 **4. Knowledge**: `tieu_chi_cham_diem.txt`
- 💾 **5. Memory**: `st.session_state` (Tạm thời)
- 🔄 **6. Workflow**: `Sheets → AI → Duyệt (HITL) → Excel`
- 📤 **7. Output**: `File Excel Bàn Giao`
""")

# ----------------- FUNCTIONS -----------------

@st.cache_data(ttl=600)
def download_public_sheet(url):
    try:
        df = pd.read_excel(url)
        # Standardize columns
        df.columns = [col.strip().lower() for col in df.columns]
        # Re-check columns matching requirements
        required_cols = ['id', 'ten_khach', 'sdt', 'nhu_cau_mo_ta']
        for col in required_cols:
            if col not in df.columns:
                # Add default values if missing
                df[col] = ""
        # Keep only required columns and return
        df = df[required_cols]
        # Fill missing values
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ Public Sheet: {e}")
        return None

def download_private_sheet(sheet_id, tab_name, credentials_dict):
    if not HAS_GSPREAD:
        st.error("Chưa cài đặt thư viện `gspread`. Vui lòng cài đặt để chạy chế độ bảo mật.")
        return None
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.worksheet(tab_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        df.columns = [col.strip().lower() for col in df.columns]
        required_cols = ['id', 'ten_khach', 'sdt', 'nhu_cau_mo_ta']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""
        df = df[required_cols]
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"Lỗi kết nối Private Sheet: {e}")
        return None

def read_knowledge_base():
    """Read lead_scoring_skill.md from folder"""
    kb_path = "lead_scoring_skill.md"
    if os.path.exists(kb_path):
        with open(kb_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Fallback inline definition
        return "Bộ quy tắc chấm điểm: VIP cộng 50 điểm, Rác trừ 50 điểm."

def mock_score_lead(lead_desc):
    lead_desc_lower = lead_desc.lower()
    
    # 1. VIP Criteria
    vip_keywords = [
        "20 tỷ", "30 tỷ", "40 tỷ", "50 tỷ", "tài chính mạnh", "không thành vấn đề", 
        "biệt thự đơn lập", "penthouse", "shophouse mặt đường lớn", "quỹ đất công nghiệp", 
        "sàn văn phòng diện tích lớn", "quận 1", "ven sông", "vinhomes ocean park", 
        "phú mỹ hưng", "chủ doanh nghiệp", "nhà đầu tư chuyên nghiệp", "mua sỉ", 
        "mua số lượng lớn", "pháp lý chuẩn", "sổ hồng riêng", "gặp trực tiếp chủ đầu tư"
    ]
    
    # 2. Junk Criteria
    junk_keywords = [
        "nhà quận 1 giá 1-2 tỷ", "nhà trung tâm có sân vườn hồ bơi giá vài trăm triệu", 
        "nhầm số", "không có nhu cầu", "dữ liệu cũ", "nhầm ngành", "hỏi giá cho vui", 
        "chưa có ý định mua", "thái độ không hợp tác", "bảo hiểm", "vay vốn", 
        "mời chào", "thuê bao", "gọi nhiều lần không bắt máy", "không phản hồi zalo"
    ]
    
    # Check for keyword matches
    vip_matches = [kw for kw in vip_keywords if kw in lead_desc_lower]
    junk_matches = [kw for kw in junk_keywords if kw in lead_desc_lower]
    
    if vip_matches and not junk_matches:
        return {
            "diem_tiem_nang": 50,
            "phan_loai": "VIP",
            "ly_do_cham_diem": f"Mô phỏng AI (Khớp VIP): Chứa từ khóa '{vip_matches[0]}'"
        }
    elif junk_matches:
        return {
            "diem_tiem_nang": -50,
            "phan_loai": "Rac",
            "ly_do_cham_diem": f"Mô phỏng AI (Khớp Rác): Chứa từ khóa '{junk_matches[0]}'"
        }
    else:
        # Check mid-range
        if "chung cư" in lead_desc_lower or "nhà phố" in lead_desc_lower or "tầm trung" in lead_desc_lower or "3 tỷ" in lead_desc_lower or "10 tỷ" in lead_desc_lower:
            return {
                "diem_tiem_nang": 10,
                "phan_loai": "Binh Thuong",
                "ly_do_cham_diem": "Mô phỏng AI (Khớp Bình Thường): Mua chung cư/nhà phố tầm trung (3-10 tỷ)"
            }
        return {
            "diem_tiem_nang": 0,
            "phan_loai": "Binh Thuong",
            "ly_do_cham_diem": "Mô phỏng AI: Khách hàng có nhu cầu cơ bản, cần tư vấn thêm"
        }

def ai_score_lead(api_key, model_name, lead_desc, system_instruction):
    import requests
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [{
                "parts": [{"text": f"Hãy đánh giá và chấm điểm lead sau đây dựa trên quy tắc nghiệp vụ:\n\nNhu cầu khách hàng: \"{lead_desc}\""}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json"
            },
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            try:
                candidate_text = res_json['candidates'][0]['content']['parts'][0]['text']
                result = json.loads(candidate_text.strip())
                return {
                    "diem_tiem_nang": int(result.get("score", 0)),
                    "phan_loai": result.get("classification", "Binh Thuong"),
                    "ly_do_cham_diem": result.get("reason", "Đã đánh giá thành công bằng Gemini API.")
                }
            except Exception as parse_error:
                return {
                    "diem_tiem_nang": 0,
                    "phan_loai": "Binh Thuong",
                    "ly_do_cham_diem": f"Lỗi parse kết quả AI: {str(parse_error)}. Raw: {response.text[:150]}"
                }
        else:
            return {
                "diem_tiem_nang": 0,
                "phan_loai": "Binh Thuong",
                "ly_do_cham_diem": f"Lỗi API (Status {response.status_code}): {response.text[:150]}"
            }
    except Exception as e:
        return {
            "diem_tiem_nang": 0,
            "phan_loai": "Binh Thuong",
            "ly_do_cham_diem": f"Lỗi kết nối API: {str(e)}"
        }


def export_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Leads Scored')
    processed_data = output.getvalue()
    return processed_data

# ----------------- MAIN UI APP -----------------

# Page Banner / Title
st.markdown("""
<div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); padding: 30px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 24px;">
    <h1 style="margin: 0; font-size: 36px; background: linear-gradient(to right, #38BDF8, #818CF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
        🏠 AI Lead Scoring & Automation System
    </h1>
    <p style="margin: 5px 0 0 0; color: rgba(255, 255, 255, 0.7); font-size: 16px;">
        Đánh giá tiềm năng khách hàng thời gian thực qua AI + Kiểm duyệt tương tác Human-in-the-loop
    </p>
</div>
""", unsafe_allow_html=True)

# LOAD DATA SOURCE SECTION
if st.session_state['raw_data'] is None:
    with st.spinner("⏳ Đang kết nối và tải dữ liệu thô từ Google Sheets..."):
        if connection_mode == "Public Link (Mặc định)":
            df_leads = download_public_sheet(sheet_url)
        else:
            if st.session_state['credentials_dict'] is None:
                st.warning("⚠️ Vui lòng tải lên file JSON Credentials trong Sidebar để kết nối Private Google Sheet.")
                df_leads = None
            else:
                df_leads = download_private_sheet(private_sheet_id, private_sheet_name, st.session_state['credentials_dict'])
        
        if df_leads is not None:
            st.session_state['raw_data'] = df_leads
            # Initialize scored data columns if not present
            df_scored = df_leads.copy()
            df_scored['diem_tiem_nang'] = 0
            df_scored['phan_loai'] = "Binh Thuong"
            df_scored['ly_do_cham_diem'] = "Chưa chấm điểm"
            df_scored['trang_thai_duyet'] = "Chờ Duyệt"
            st.session_state['scored_data'] = df_scored
            st.success(f"📥 Đã tải thành công {len(df_leads)} dòng dữ liệu từ Google Sheets!")

# RE-DOWNLOAD DATA BUTTON
if st.button("🔄 Tải lại dữ liệu từ Google Sheets"):
    st.session_state['raw_data'] = None
    st.session_state['scored_data'] = None
    st.rerun()

# ----------------- ACTIONS & ANALYSIS CONTROL -----------------
if st.session_state['scored_data'] is not None:
    df_current = st.session_state['scored_data']
    
    st.subheader("🤖 Phân tích & Chấm điểm bằng AI Agent")
    
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    
    with col_ctrl1:
        st.write("Chọn phạm vi khách hàng bạn muốn chấm điểm:")
        score_mode = st.radio("Phạm vi chạy AI", ["Chỉ 10 dòng đầu (Khuyên dùng để test nhanh)", "Chỉ 50 dòng đầu", "Tất cả 500 dòng (Có thể mất nhiều thời gian và quota)"], horizontal=True)
        
        run_ai = st.button("⚡ Bắt đầu Chạy AI Lead Scoring", use_container_width=True)
        
    with col_ctrl2:
        if gemini_key:
            st.success("🤖 Trạng thái AI: Đang sử dụng **Gemini API** thực tế.")
        else:
            st.info("ℹ️ Trạng thái AI: API Key trống. Đang dùng **Bộ quy tắc cứng (Rule-based)** để mô phỏng.")
            
    # Execution Logic
    if run_ai:
        system_instruction = read_knowledge_base()
        
        # Determine rows to process
        if score_mode == "Chỉ 10 dòng đầu (Khuyên dùng để test nhanh)":
            limit = 10
        elif score_mode == "Chỉ 50 dòng đầu":
            limit = 50
        else:
            limit = len(df_current)
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Make a copy of df to write modifications
        df_new = df_current.copy()
        
        for idx in range(limit):
            row = df_new.iloc[idx]
            lead_desc = row['nhu_cau_mo_ta']
            
            status_text.text(f"⏳ Đang chấm điểm Lead #{idx+1}/{limit}: {row['ten_khach']}...")
            
            if gemini_key:
                # Real LLM Scoring
                res = ai_score_lead(gemini_key, selected_model, lead_desc, system_instruction)
            else:
                # Rule-based Simulation
                res = mock_score_lead(lead_desc)
                time.sleep(0.05) # Small sleep for animation effect
                
            df_new.at[idx, 'diem_tiem_nang'] = res['diem_tiem_nang']
            df_new.at[idx, 'phan_loai'] = res['phan_loai']
            df_new.at[idx, 'ly_do_cham_diem'] = res['ly_do_cham_diem']
            df_new.at[idx, 'trang_thai_duyet'] = "Chờ Duyệt"
            
            progress_bar.progress((idx + 1) / limit)
            
        status_text.success(f"✅ Đã phân tích xong {limit} khách hàng!")
        st.session_state['scored_data'] = df_new
        st.rerun()

    # ----------------- PREMIUM METRICS DASHBOARD -----------------
    st.markdown("---")
    st.subheader("📊 Bảng thống kê Chất lượng Khách hàng (Metrics)")
    
    # Calculate counts based on current state
    df_calc = st.session_state['scored_data']
    total_leads = len(df_calc)
    vip_leads = len(df_calc[df_calc['phan_loai'] == "VIP"])
    normal_leads = len(df_calc[df_calc['phan_loai'] == "Binh Thuong"])
    junk_leads = len(df_calc[df_calc['phan_loai'] == "Rac"])
    
    # Standard Streamlit columns and metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="📊 Tổng Khách Hàng", value=total_leads)
    with col_m2:
        st.metric(label="🔥 Khách VIP (+50đ)", value=vip_leads, delta=f"{vip_leads} leads")
    with col_m3:
        st.metric(label="🗑️ Khách Rác (-50đ)", value=junk_leads, delta=f"{junk_leads} leads", delta_color="inverse")

    # ----------------- HUMAN IN THE LOOP GRID -----------------
    st.markdown("---")
    st.subheader("🛡️ Checkpoint Kiểm Duyệt (Human-in-the-loop)")
    
    # Filters and search row
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        status_filter = st.selectbox("Lọc theo trạng thái duyệt", ["Tất cả", "Chờ Duyệt", "Đã Duyệt", "Đã Loại"], key="status_filter_sb")
    with col_f2:
        class_filter = st.selectbox("Lọc theo phân loại AI", ["Tất cả", "VIP", "Binh Thuong", "Rac"], key="class_filter_sb")
    with col_f3:
        search_query = st.text_input("🔍 Tìm kiếm tên hoặc SĐT", "", key="search_query_ti")
        
    # Apply filters
    df_disp = df_calc.copy()
    if status_filter != "Tất cả":
        df_disp = df_disp[df_disp['trang_thai_duyet'] == status_filter]
    if class_filter != "Tất cả":
        df_disp = df_disp[df_disp['phan_loai'] == class_filter]
    if search_query:
        df_disp = df_disp[
            df_disp['ten_khach'].astype(str).str.contains(search_query, case=False, na=False) | 
            df_disp['sdt'].astype(str).str.contains(search_query, case=False, na=False)
        ]
        
    # Interactive data editor
    st.info("👉 **Mẹo**: Bạn có thể click đúp chuột trực tiếp vào các ô dưới đây để chỉnh sửa nhanh Điểm, Phân loại, Trạng thái hoặc Lý do chấm điểm.")
    
    edited_disp_df = st.data_editor(
        df_disp,
        key="leads_editor",
        num_rows="fixed",
        use_container_width=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "ten_khach": st.column_config.TextColumn("Tên Khách", disabled=True),
            "sdt": st.column_config.TextColumn("SĐT", disabled=True),
            "nhu_cau_mo_ta": st.column_config.TextColumn("Nhu Cầu Mô Tả", disabled=True, width="large"),
            "diem_tiem_nang": st.column_config.NumberColumn("Điểm Tiềm Năng", min_value=-100, max_value=100, step=10),
            "phan_loai": st.column_config.SelectboxColumn("Phân Loại", options=["VIP", "Binh Thuong", "Rac"]),
            "trang_thai_duyet": st.column_config.SelectboxColumn("Trạng Thái Duyệt", options=["Chờ Duyệt", "Đã Duyệt", "Đã Loại"]),
            "ly_do_cham_diem": st.column_config.TextColumn("Lý Do Chấm Điểm", width="large")
        }
    )
    
    # Sync modifications back to st.session_state['scored_data']
    if not edited_disp_df.equals(df_disp):
        for idx, row in edited_disp_df.iterrows():
            id_val = row['id']
            orig_idx = st.session_state['scored_data'][st.session_state['scored_data']['id'] == id_val].index
            if len(orig_idx) > 0:
                st.session_state['scored_data'].loc[orig_idx[0], 'diem_tiem_nang'] = row['diem_tiem_nang']
                st.session_state['scored_data'].loc[orig_idx[0], 'phan_loai'] = row['phan_loai']
                st.session_state['scored_data'].loc[orig_idx[0], 'trang_thai_duyet'] = row['trang_thai_duyet']
                st.session_state['scored_data'].loc[orig_idx[0], 'ly_do_cham_diem'] = row['ly_do_cham_diem']
        st.rerun()
        
    edited_df = st.session_state['scored_data']


    # ----------------- EXPORT SECTION -----------------
    st.markdown("---")
    st.subheader("📤 Bàn Giao Dữ Liệu (Handoff)")
    
    col_exp1, col_exp2 = st.columns([2, 1])
    
    with col_exp1:
        st.write("Sau khi hoàn tất kiểm duyệt và phê duyệt trạng thái, bạn có thể xuất tệp Excel sạch để bàn giao trực tiếp cho đội ngũ Sales/Telesales.")
        
        # Calculate stats for the file
        approved_count = len(edited_df[edited_df['trang_thai_duyet'] == "Đã Duyệt"])
        rejected_count = len(edited_df[edited_df['trang_thai_duyet'] == "Đã Loại"])
        pending_count = len(edited_df[edited_df['trang_thai_duyet'] == "Chờ Duyệt"])
        
        st.markdown(f"""
        - Số lượng Lead đã duyệt chính thức: **{approved_count}**
        - Số lượng Lead đã loại: **{rejected_count}**
        - Số lượng Lead chờ duyệt còn lại: **{pending_count}**
        """)
        
    with col_exp2:
        # Generate Excel download button
        excel_data = export_to_excel(edited_df)
        st.download_button(
            label="📥 Tải Tệp Excel Bàn Giao",
            data=excel_data,
            file_name="leads_scored_final.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.success("Tệp Excel chứa đầy đủ thông tin chấm điểm, lý do và trạng thái phê duyệt cuối cùng.")
else:
    st.info("Nhập các cấu hình và nguồn dữ liệu ở Sidebar để bắt đầu chạy ứng dụng.")
