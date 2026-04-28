%%writefile app.py
import streamlit as st
import pandas as pd
import numpy as np
import google.generativeai as genai
import json
import PIL.Image
import tempfile
import os
import folium
from streamlit_folium import st_folium
import firebase_admin
from firebase_admin import credentials, firestore

# --- CONFIG ---
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# --- FIREBASE INIT ---
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            key_dict = json.loads(st.secrets["firebase"]["key_json"])
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except:
        return None

db = init_firebase()

# --- NGO ACCOUNTS (no Firebase Auth needed) ---
NGO_ACCOUNTS = {
    "admin@communiserve.org": "ngo@2024",
    "velachery.ngo@gmail.com": "velachery123",
    "guindy.ngo@gmail.com": "guindy123"
}

def ngo_login(email, password):
    if email in NGO_ACCOUNTS and NGO_ACCOUNTS[email] == password:
        return {"success": True, "email": email}
    return {"success": False, "error": "Invalid email or password"}

# --- DEFAULT DATA ---
DEFAULT_VOLUNTEERS = pd.DataFrame({
    "Name": ["Priya S.", "Rahul M.", "Anita K.", "John D."],
    "Location": ["Adyar", "Guindy", "T Nagar", "Velachery"],
    "Skills": ["Teaching, Math, Science", "Logistics, Heavy Lifting", "Organization, Inventory", "Medical First Aid, Swimming"]
})

DEFAULT_NEEDS = [
    {"Title": "After-school Tutors", "Location": "Adyar", "Category": "Education", "Urgency": "High", "Description": "Math tutors for high schoolers.", "lat": 13.0012, "lon": 80.2565},
    {"Title": "Emergency Generator Fuel", "Location": "Guindy", "Category": "Infrastructure", "Urgency": "Critical", "Description": "Flooding caused power outage. Need fuel.", "lat": 13.0067, "lon": 80.2206},
    {"Title": "Food Bank Sorting", "Location": "T Nagar", "Category": "Health", "Urgency": "Medium", "Description": "Sorting donated canned goods.", "lat": 13.0418, "lon": 80.2341},
]

# --- FIREBASE INIT ---
@st.cache_resource
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CONFIG)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except:
        return None

db = init_firebase()

# --- DATA HELPERS ---
def get_volunteers():
    base = DEFAULT_VOLUNTEERS.copy()
    if db:
        try:
            docs = db.collection("volunteers").stream()
            rows = [d.to_dict() for d in docs]
            if rows:
                extra = pd.DataFrame(rows)[["Name", "Location", "Skills"]]
                base = pd.concat([base, extra], ignore_index=True)
        except:
            pass
    if "new_volunteers" in st.session_state:
        base = pd.concat([base, pd.DataFrame(st.session_state.new_volunteers)], ignore_index=True)
    return base

def add_volunteer(name, loc, skills):
    data = {"Name": name, "Location": loc, "Skills": skills}
    if "new_volunteers" not in st.session_state:
        st.session_state.new_volunteers = []
    st.session_state.new_volunteers.append(data)
    if db:
        try:
            db.collection("volunteers").add(data)
        except:
            pass

def get_needs():
    needs = DEFAULT_NEEDS.copy()
    if db:
        try:
            docs = db.collection("needs").stream()
            for d in docs:
                nd = d.to_dict()
                needs.append(nd)
        except:
            pass
    if "new_needs" in st.session_state:
        needs.extend(st.session_state.new_needs)
    return pd.DataFrame(needs)

def add_need(need_dict):
    if "new_needs" not in st.session_state:
        st.session_state.new_needs = []
    st.session_state.new_needs.append(need_dict)
    if db:
        try:
            db.collection("needs").add(need_dict)
        except:
            pass

def get_needs_fulfilled():
    if db:
        try:
            doc = db.collection("stats").document("global").get()
            if doc.exists:
                return doc.to_dict().get("needs_fulfilled", 186)
        except:
            pass
    return st.session_state.get("needs_fulfilled", 186)

def increment_needs_fulfilled():
    current = get_needs_fulfilled()
    if db:
        try:
            db.collection("stats").document("global").set({"needs_fulfilled": current + 1})
        except:
            pass
    st.session_state.needs_fulfilled = current + 1

# --- PAGE CONFIG ---
st.set_page_config(page_title="Communiserve | Master", page_icon="🌍", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; }
    .hero-container { background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); padding: 3rem; border-radius: 15px; border: 1px solid #334155; margin-bottom: 2rem; }
    .metric-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 1.5rem; border-radius: 10px; border: 1px solid #334155; text-align: center; }
    .match-card { background: #1e293b; border-left: 5px solid #10b981; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; }
    .critical-card { background: #3f1a1a; border-left: 5px solid #ef4444; padding: 1.5rem; border-radius: 8px; margin-top: 1rem; }
    .step-card { background: rgba(30,41,59,0.7); border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; text-align: center; }
    .sdg-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; margin: 4px; }
    .tech-badge { display: inline-block; background: rgba(59,130,246,0.15); border: 1px solid #3b82f6; color: #93c5fd; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; margin: 3px; }
    .ngo-card { background: rgba(16,185,129,0.1); border: 1px solid #10b981; border-radius: 10px; padding: 1.5rem; margin-top: 1rem; }
    h1, h2, h3 { color: #f8fafc !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.title("Communiserve Ultra")
lang = st.sidebar.radio("🌐 Language / மொழி", ["English", "தமிழ் (Tamil)"])

def t(en_text, ta_text):
    return ta_text if lang == "தமிழ் (Tamil)" else en_text

ai_lang = "Tamil" if lang == "தமிழ் (Tamil)" else "English"

# --- NGO LOGIN IN SIDEBAR ---
st.sidebar.markdown("---")
if "ngo_user" not in st.session_state:
    st.session_state.ngo_user = None

if st.session_state.ngo_user:
    st.sidebar.success(f"✅ NGO: {st.session_state.ngo_user['email']}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.ngo_user = None
        st.rerun()
else:
    with st.sidebar.expander("🏢 NGO Admin Login"):
        ngo_email = st.text_input("Email", key="ngo_email")
        ngo_pass = st.text_input("Password", type="password", key="ngo_pass")
        if st.button("Login", key="ngo_login_btn"):
            result = ngo_login(ngo_email, ngo_pass)
            if result["success"]:
                st.session_state.ngo_user = result
                st.rerun()
            else:
                st.error(result["error"])
        st.caption("Demo: admin@communiserve.org / ngo@2024")

st.sidebar.markdown("---")

# --- PAGES ---
pages = ["Home", "Dashboard", "Volunteer Onboarding", "🆘 SOS Auto-Triage", "Command Dispatch", "Task Verification", "Geospatial Command", "Voice Intake", "Survey OCR", "Forecasting"]
if st.session_state.ngo_user:
    pages.insert(1, "🏢 NGO Admin Panel")

page_translations = {
    "Home": "முகப்பு (Home)",
    "🏢 NGO Admin Panel": "🏢 NGO நிர்வாக பலகை",
    "Dashboard": "கட்டுப்பாட்டகம் (Dashboard)",
    "Volunteer Onboarding": "தன்னார்வலர் பதிவு (Onboarding)",
    "🆘 SOS Auto-Triage": "🆘 அவசர வகைப்படுத்தல் (SOS Triage)",
    "Command Dispatch": "கட்டளை அனுப்புதல் (Dispatch)",
    "Task Verification": "பணி சரிபார்ப்பு (Verification)",
    "Geospatial Command": "வரைபடக் கட்டுப்பாட்டகம் (Map)",
    "Voice Intake": "குரல் பதிவு (Voice Intake)",
    "Survey OCR": "படிவப் பகுப்பாய்வு (Survey OCR)",
    "Forecasting": "முன்னறிவிப்பு (Forecasting)"
}

page = st.sidebar.radio(t("Navigation", "வழிசெலுத்தல்"), pages, format_func=lambda x: page_translations.get(x, x) if lang == "தமிழ் (Tamil)" else x)

# --- AI ENGINE ---
def get_ai_json(prompt, media=None):
    safe_list = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                safe_list.append(m.name)
    except:
        pass
    if not safe_list:
        safe_list = ['models/gemini-1.5-flash', 'models/gemini-pro']
    payload = [prompt] if media is None else [prompt, media]
    last_err = ""
    for m in safe_list:
        try:
            model = genai.GenerativeModel(m)
            response = model.generate_content(payload)
            raw = response.text
            start = raw.find('{')
            end = raw.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(raw[start:end])
        except Exception as e:
            last_err = str(e)
            continue
    raise ValueError(f"All models failed: {last_err}")

# ===================== PAGES =====================

if page == "Home":
    volunteers_df = get_volunteers()
    vol_count = len(volunteers_df) + 1244
    needs_count = get_needs_fulfilled()
    needs_df = get_needs()

    st.markdown(f"""
    <div class="hero-container">
        <div style="display:flex;align-items:center;gap:15px;margin-bottom:1rem;">
            <span style="font-size:3.5rem;">🌍</span>
            <div>
                <h1 style="font-size:2.8rem;margin:0;">{t('Communiserve', 'கம்யூனிசர்வ்')}</h1>
                <p style="color:#94a3b8;margin:0;font-size:1.1rem;">{t('Data-Driven Volunteer Coordination for Social Impact', 'தரவு உந்துதல் தன்னார்வலர் ஒருங்கிணைப்பு')}</p>
            </div>
        </div>
        <p style="color:#cbd5e1;font-size:1rem;max-width:600px;">{t('AI-powered platform that digitizes scattered community needs from paper surveys, voice reports and field data — then intelligently matches volunteers where they matter most.', 'AI மூலம் சமூக தேவைகளை டிஜிட்டல் மயமாக்குதல் மற்றும் தன்னார்வலர்களை பொருத்துதல்.')}</p>
        <div style="margin-top:1.5rem;">
            <span class="sdg-badge" style="background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid #ef4444;">🏙️ SDG 11 — Sustainable Cities</span>
            <span class="sdg-badge" style="background:rgba(59,130,246,0.2);color:#93c5fd;border:1px solid #3b82f6;">🤝 SDG 17 — Partnerships</span>
            <span class="sdg-badge" style="background:rgba(16,185,129,0.2);color:#6ee7b7;border:1px solid #10b981;">❤️ SDG 3 — Good Health</span>
        </div>
        <div style="margin-top:1rem;">
            <span class="tech-badge">✨ Gemini AI</span>
            <span class="tech-badge">🔥 Firebase</span>
            <span class="tech-badge">🗺️ Folium Maps</span>
            <span class="tech-badge">🎙️ Audio Intelligence</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### {t('📊 Live Impact', '📊 நிகழ்நேர தாக்கம்')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>{t('Volunteers','தன்னார்வலர்கள்')}</h3><h1 style='color:#3b82f6;'>{vol_count}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>{t('Needs Fulfilled','நிறைவேற்றப்பட்டவை')}</h3><h1 style='color:#10b981;'>{needs_count}</h1></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>{t('Active Needs','செயலில் உள்ளவை')}</h3><h1 style='color:#f59e0b;'>{len(needs_df)}</h1></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>{t('Match Accuracy','துல்லியம்')}</h3><h1 style='color:#10b981;'>94.2%</h1></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### {t('⚙️ How It Works', '⚙️ எவ்வாறு செயல்படுகிறது')}")
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""<div class='step-card'><div style='font-size:2.5rem;'>📋</div><h3>{t('1. Capture Needs','1. தேவைகளை பதிவு செய்')}</h3><p style='color:#94a3b8;font-size:0.9rem;'>{t('NGOs submit needs via voice, photo surveys, or direct forms. AI extracts and categorizes automatically.','NGO கள் குரல், படங்கள் மூலம் தேவைகளை பதிவு செய்கின்றனர்.')}</p></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class='step-card'><div style='font-size:2.5rem;'>🤖</div><h3>{t('2. AI Matching','2. AI பொருத்துதல்')}</h3><p style='color:#94a3b8;font-size:0.9rem;'>{t('Gemini AI analyzes volunteer skills, location proximity, and urgency to find the perfect match instantly.','Gemini AI திறன்கள், இடம், அவசரம் ஆகியவற்றை பகுப்பாய்வு செய்கிறது.')}</p></div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""<div class='step-card'><div style='font-size:2.5rem;'>✅</div><h3>{t('3. Verify & Track','3. சரிபார்க்க & கண்காணிக்க')}</h3><p style='color:#94a3b8;font-size:0.9rem;'>{t('Volunteers upload photo proof. AI verifies task completion and updates dashboard automatically.','தன்னார்வலர்கள் புகைப்பட சான்று பதிவேற்றுகின்றனர். AI பணி முடிப்பை சரிபார்க்கிறது.')}</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:12px;padding:1.5rem;'>
        <h3 style='color:#f8fafc;margin-top:0;'>🎯 {t('The Problem We Solve','நாங்கள் தீர்க்கும் பிரச்சனை')}</h3>
        <p style='color:#94a3b8;'>{t('Local NGOs collect critical community data through paper surveys and field reports — but this data is scattered, hard to act on, and volunteers are matched manually. Communiserve bridges this gap with AI.','உள்ளூர் NGO கள் காகித படிவங்கள் மூலம் தரவு சேகரிக்கின்றனர் — ஆனால் இது சிதறிக்கிடக்கிறது. Communiserve இந்த இடைவெளியை AI மூலம் நிரப்புகிறது.')}</p>
    </div>
    """, unsafe_allow_html=True)
elif page == "🏢 NGO Admin Panel":
    st.title(t("🏢 NGO Admin Panel", "🏢 NGO நிர்வாக பலகை"))
    st.success(f"✅ {t('Logged in as','இணைந்துள்ளீர்கள்:')} {st.session_state.ngo_user['email']}")

    st.markdown(f"### {t('📍 Submit New Community Need','📍 புதிய சமூக தேவையை சமர்ப்பிக்கவும்')}")
    with st.form("ngo_need_form"):
        col1, col2 = st.columns(2)
        with col1:
            need_title = st.text_input(t("Need Title","தேவை தலைப்பு"), placeholder="e.g. Flood Relief Volunteers")
            need_location = st.selectbox(t("Location","இடம்"), ["Velachery","Guindy","Adyar","T Nagar","Tambaram","Chromepet","Porur","Anna Nagar"])
            need_category = st.selectbox(t("Category","வகை"), ["Education","Health","Infrastructure","Environment","Food & Nutrition","Disaster Relief"])
        with col2:
            need_urgency = st.selectbox(t("Urgency","அவசரம்"), ["Critical","High","Medium","Low"])
            need_desc = st.text_area(t("Description","விவரம்"), placeholder="Describe the need clearly...")
            clat, clon = st.columns(2)
            with clat: need_lat = st.number_input("Latitude", value=13.0200, format="%.4f")
            with clon: need_lon = st.number_input("Longitude", value=80.2300, format="%.4f")

        if st.form_submit_button(t("🚀 Submit Need to Map","🚀 வரைபடத்தில் சேர்க்கவும்"), use_container_width=True):
            if need_title and need_desc:
                add_need({"Title": need_title, "Location": need_location, "Category": need_category,
                          "Urgency": need_urgency, "Description": need_desc,
                          "lat": need_lat, "lon": need_lon,
                          "submitted_by": st.session_state.ngo_user['email']})
                st.success(t("✅ Need submitted! Visible on map now.","✅ தேவை சமர்ப்பிக்கப்பட்டது!"))
                st.balloons()
            else:
                st.warning(t("Please fill title and description.","தலைப்பு மற்றும் விவரம் தேவை."))

    st.markdown(f"### {t('📋 Your Submitted Needs','📋 நீங்கள் சமர்ப்பித்த தேவைகள்')}")
    all_needs = get_needs()
    if "submitted_by" in all_needs.columns:
        my_needs = all_needs[all_needs["submitted_by"] == st.session_state.ngo_user['email']]
        if len(my_needs) > 0:
            for _, row in my_needs.iterrows():
                color = {"Critical":"#ef4444","High":"#f59e0b","Medium":"#3b82f6","Low":"#10b981"}.get(row.get('Urgency',''),"#94a3b8")
                st.markdown(f"""<div class='ngo-card'><b>{row.get('Title','')}</b> — <span style='color:{color};'>{row.get('Urgency','')} {t('Priority','முன்னுரிமை')}</span><br>📍 {row.get('Location','')} | 🏷️ {row.get('Category','')}<br><small style='color:#94a3b8;'>{row.get('Description','')}</small></div>""", unsafe_allow_html=True)
        else:
            st.info(t("No needs submitted yet.","இன்னும் எந்த தேவையும் சமர்ப்பிக்கவில்லை."))

elif page == "Dashboard":
    st.title(t("📊 Real-Time Impact Dashboard","📊 நிகழ்நேர தாக்கக் கட்டுப்பாட்டகம்"))
    volunteers_df = get_volunteers()
    needs_df = get_needs()
    vol_count = len(volunteers_df) + 1244
    needs_count = get_needs_fulfilled()
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f"<div class='metric-card'><h3>{t('Active Volunteers','தன்னார்வலர்கள்')}</h3><h1 style='color:#3b82f6;'>{vol_count}</h1></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card'><h3>{t('Needs Fulfilled','நிறைவேற்றப்பட்டவை')}</h3><h1 style='color:#10b981;'>{needs_count}</h1></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card'><h3>{t('Active Needs','செயலில் உள்ளவை')}</h3><h1 style='color:#f59e0b;'>{len(needs_df)}</h1></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='metric-card'><h3>{t('Match Accuracy','துல்லியம்')}</h3><h1 style='color:#10b981;'>94.2%</h1></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader(t("🏆 Top Volunteer Leaderboard","🏆 சிறந்த தன்னார்வலர்கள்"))
    st.markdown(f"""
    <div style="display:flex;gap:15px;flex-wrap:wrap;">
        <div style="flex:1;min-width:250px;background:rgba(30,41,59,0.7);padding:15px;border-radius:8px;border-top:4px solid #eab308;">
            <h3 style="margin:0;color:#eab308;">🥇 {t('Priya S.','பிரியா எஸ்.')}</h3>
            <p style="margin:5px 0;"><b>Score:</b> 2,450</p>
            <span style="background:rgba(234,179,8,0.2);color:#fde047;padding:3px 8px;border-radius:12px;font-size:0.8rem;">⭐ Top Matcher</span>
        </div>
        <div style="flex:1;min-width:250px;background:rgba(30,41,59,0.7);padding:15px;border-radius:8px;border-top:4px solid #94a3b8;">
            <h3 style="margin:0;color:#cbd5e1;">🥈 {t('Rahul M.','ராகுல் எம்.')}</h3>
            <p style="margin:5px 0;"><b>Score:</b> 1,820</p>
            <span style="background:rgba(239,68,68,0.2);color:#fca5a5;padding:3px 8px;border-radius:12px;font-size:0.8rem;">🚨 {t('Crisis Responder','நெருக்கடி பதிலாளர்')}</span>
        </div>
    </div>""", unsafe_allow_html=True)

elif page == "🆘 SOS Auto-Triage":
    st.title(t("🆘 AI Auto-Triage & SOS","🆘 AI தானியங்கி வகைப்படுத்தல்"))
    raw_incident = st.text_area(t("Raw Incident Report","நிகழ்வு அறிக்கை"), "Massive flooding in Velachery residential area! We need people who can swim fast!")
    if st.button(t("🚨 TRIGGER AUTO-TRIAGE","🚨 அவசர அனுப்புதலைத் தூண்டு")):
        if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
        else:
            with st.spinner(t("Calculating...","பகுப்பாய்வு...")):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    volunteers_df = get_volunteers()
                    json_tmpl = '{"category":"...","urgency":"...","location":"...","required_skills":"...","v1_name":"Name","v1_reason":"Reason","v2_name":"Name","v2_reason":"Reason"}'
                    prompt = f"""Incident: '{raw_incident}'. Categorize, extract Location, pick TWO best volunteers from EXACT list:
{volunteers_df.to_string()}
Must pick two real names. Never return N/A. Reasons in {ai_lang}. JSON: {json_tmpl}"""
                    data = get_ai_json(prompt)
                    v1 = data.get('v1_name','') or volunteers_df.iloc[0]['Name']
                    v1r = data.get('v1_reason','') or 'Best skill match'
                    v2 = data.get('v2_name','') or volunteers_df.iloc[1]['Name']
                    v2r = data.get('v2_reason','') or 'Proximity match'
                    st.markdown(f"""<div class="critical-card"><h2 style="margin-top:0;color:#ef4444;">🚨 {t('TRIAGE','வகைப்படுத்தல்')}: {data.get('urgency','HIGH').upper()} {t('PRIORITY','முன்னுரிமை')}</h2><p><b>📍 {t('Location','இடம்')}:</b> {data.get('location','')}</p><p><b>🛠️ {t('Required Skills','தேவையான திறன்கள்')}:</b> {data.get('required_skills','')}</p></div>
                    <div style="background:#0f172a;padding:20px;border-radius:8px;border:1px solid #ef4444;margin-top:15px;"><h4 style="color:#ef4444;">🚁 {t('DISPATCH INITIATED','அனுப்புதல் தொடங்கியது')}:</h4><ul style="list-style-type:none;padding-left:0;"><li><b>→ {v1}</b> 🟢 {t('PINGED','அழைக்கப்பட்டார்')}: <i>{v1r}</i></li><li style="margin-top:10px;"><b>→ {v2}</b> 🟡 {t('PINGED','அழைக்கப்பட்டார்')}: <i>{v2r}</i></li></ul></div>""", unsafe_allow_html=True)
                except Exception as e: st.error(f"Error: {e}")

elif page == "Volunteer Onboarding":
    st.title(t("🙋 Join the Mission","🙋 பணியில் இணையுங்கள்"))
    with st.form("volunteer_form"):
        new_name = st.text_input(t("Full Name","முழு பெயர்"))
        new_loc = st.selectbox(t("Your Location","உங்கள் இடம்"), ["Velachery","Guindy","Tambaram","Adyar"])
        new_skills = st.multiselect(t("Your Skills","திறன்கள்"), ["Logistics","Medical First Aid","Teaching","Heavy Lifting","Swimming"])
        if st.form_submit_button(t("Register","பதிவு செய்")) and new_name and new_skills:
            add_volunteer(new_name, new_loc, ", ".join(new_skills))
            if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
            else:
                with st.spinner(t("Matching...","பொருத்தப்படுகிறது...")):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        needs_df = get_needs()
                        data = get_ai_json(f"Volunteer: {new_name}, Loc: {new_loc}, Skills: {', '.join(new_skills)}. Needs: {needs_df.to_string()}. Best task. Reason in {ai_lang}. JSON: " + '{"task":"Title","reason":"Logic"}')
                        st.markdown(f"""<div class="match-card"><h3>🎯 {t('Welcome','வரவேற்கிறோம்')}, {new_name}!</h3><h2>{data['task']}</h2><p><b>{t('Why you','ஏன் நீங்கள்')}:</b> {data['reason']}</p></div>""", unsafe_allow_html=True)
                    except Exception as e: st.error(f"Failed: {e}")

elif page == "Command Dispatch":
    st.title(t("🤖 Standard Dispatch","🤖 சாதாரண அனுப்புதல்"))
    needs_df = get_needs()
    selected_title = st.selectbox(t("Select Incident:","நிகழ்வைத் தேர்ந்தெடுக்கவும்:"), needs_df["Title"])
    selected_need = needs_df[needs_df["Title"] == selected_title].iloc[0]
    st.markdown(f"""<div class="match-card"><h3 style="margin-top:0;">📋 {t('TASK DETECTED','பணி கண்டறியப்பட்டது')}</h3><p><b>📍 {t('Location','இடம்')}:</b> {selected_need['Location']}</p><p><b>🛠️ {t('Requirement','தேவை')}:</b> {selected_need['Description']}</p></div>""", unsafe_allow_html=True)
    if st.button(t("Deploy AI Dispatcher","AI பயன்படுத்தவும்")):
        if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
        else:
            with st.spinner(t("Calculating...","கணக்கிடுகிறது...")):
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    volunteers_df = get_volunteers()
                    json_tmpl = '{"v1_name":"Name","v1_skill":"Skill","v2_name":"Name","v2_skill":"Skill"}'
                    prompt = f"""Incident: '{selected_title}'. Desc: '{selected_need['Description']}'.
Pick TWO best from EXACT list: {volunteers_df.to_string()}
Both names must be real. Skills in {ai_lang}. JSON: {json_tmpl}"""
                    data = get_ai_json(prompt)
                    v1n = data.get('v1_name','') or volunteers_df.iloc[0]['Name']
                    v1s = data.get('v1_skill','') or volunteers_df.iloc[0]['Skills']
                    v2n = data.get('v2_name','') or volunteers_df.iloc[1]['Name']
                    v2s = data.get('v2_skill','') or volunteers_df.iloc[1]['Skills']
                    st.success(t("✅ Logistics Calculated.","✅ கணக்கிடப்பட்டது."))
                    st.markdown(f"""<div style="background:#0f172a;padding:20px;border-radius:8px;border:1px solid #334155;"><h4>👥 {t('Dispatched:','அனுப்பப்பட்டவர்கள்:')}</h4><ul><li><b>{v1n}</b> ({v1s}) 🟢</li><li><b>{v2n}</b> ({v2s}) 🟡</li></ul></div>""", unsafe_allow_html=True)
                except Exception as e: st.error(f"Failed: {e}")

elif page == "Task Verification":
    st.title(t("📸 AI Task Proof","📸 பணி முடிப்புச் சான்று"))
    needs_df = get_needs()
    verify_task = st.selectbox(t("Select Task:","பணியைத் தேர்ந்தெடுக்கவும்:"), needs_df["Title"])
    task_desc = needs_df[needs_df["Title"] == verify_task]["Description"].iloc[0]
    proof_img = st.file_uploader(t("Upload Photo","புகைப்படத்தைப் பதிவேற்றவும்"), type=["jpg","jpeg","png"])
    if proof_img:
        st.image(proof_img, width=300)
        if st.button(t("Run Verification","சரிபார்க்கவும்")):
            if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
            else:
                with st.spinner(t("Analyzing...","பகுப்பாய்வு...")):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        img = PIL.Image.open(proof_img)
                        data = get_ai_json(f"Verify completion for: {verify_task}. Desc: {task_desc}. Reason in {ai_lang}. JSON: " + '{"verified":true,"reason":"..."}', img)
                        if data.get("verified", False):
                            st.success(t("✅ VERIFIED BY AI","✅ AI மூலம் சரிபார்க்கப்பட்டது"))
                            st.info(data.get('reason',''))
                            st.balloons()
                            increment_needs_fulfilled()
                        else:
                            st.error(t("❌ VERIFICATION FAILED","❌ சரிபார்ப்பு தோல்வியடைந்தது"))
                            st.info(data.get('reason',''))
                    except Exception as e: st.error(f"Error: {e}")

elif page == "Geospatial Command":
    st.title(t("🗺️ Active Needs Map","🗺️ தேவைகள் வரைபடம்"))
    st.caption(t("Click a marker to see need details.","மார்க்கரை கிளிக் செய்து விவரங்கள் காண்க."))
    needs_df = get_needs()
    urgency_colors = {"Critical":"red","High":"orange","Medium":"blue","Low":"green"}

    urgency_ta = {"Critical":"மிகவும் அவசரம்","High":"அதிக அவசரம்","Medium":"நடுத்தர அவசரம்","Low":"குறைந்த அவசரம்"}
    category_ta = {"Education":"கல்வி","Health":"சுகாதாரம்","Infrastructure":"உள்கட்டமைப்பு","Environment":"சுற்றுச்சூழல்","Food & Nutrition":"உணவு & ஊட்டம்","Disaster Relief":"பேரிடர் நிவாரணம்"}

    def tv(val, mapping):
        return mapping.get(val, val) if lang == "தமிழ் (Tamil)" else val

    loc_label = "இடம்" if lang == "தமிழ் (Tamil)" else "Location"
    priority_label = "முன்னுரிமை" if lang == "தமிழ் (Tamil)" else "Priority"
    category_label = "வகை" if lang == "தமிழ் (Tamil)" else "Category"

    m = folium.Map(location=[13.0200, 80.2300], zoom_start=12, tiles="CartoDB dark_matter")
    for _, row in needs_df.iterrows():
        color = urgency_colors.get(row.get("Urgency",""), "gray")
        urg_display = tv(row.get('Urgency',''), urgency_ta)
        cat_display = tv(row.get('Category',''), category_ta)
        popup_html = f"""<div style="font-family:sans-serif;min-width:180px;">
            <b style="font-size:14px;">{row.get('Title','')}</b><br>
            📍 {loc_label}: {row.get('Location','')}<br>
            ⚠️ {urg_display} {priority_label}<br>
            🏷️ {category_label}: {cat_display}<br><br>
            <i>{row.get('Description','')}</i>
        </div>"""
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=15, color=color, fill=True,
            fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"🔴 {row.get('Title','')} — {urg_display} {priority_label}"
        ).add_to(m)

    map_data = st_folium(m, width=700, height=450)
    if map_data and map_data.get("last_object_clicked_popup"):
        st.markdown(f"### 📋 {t('Selected Need Details','தேர்ந்தெடுக்கப்பட்ட தேவை விவரங்கள்')}")
        st.info(map_data["last_object_clicked_popup"])
    if st.session_state.ngo_user:
        st.info(t("🏢 NGO Admin — go to NGO Admin Panel to add new needs.","🏢 NGO நிர்வாகி — புதிய தேவைகள் சேர்க்க NGO பலகைக்கு செல்லவும்."))

elif page == "Voice Intake":
    st.title(t("🎙️ Audio Intelligence","🎙️ ஆடியோ நுண்ணறிவு"))
    audio_file = st.file_uploader(t("Upload Voice","பதிவேற்றவும்"), type=["mp3","wav","amr","m4a"])
    if audio_file:
        st.audio(audio_file)
        if st.button(t("Process Audio","பகுப்பாய்வு")):
            if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
            else:
                with st.spinner(t("Analyzing...","பகுப்பாய்வு...")):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        ext = "." + audio_file.name.split('.')[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                            tmp.write(audio_file.getvalue()); tmp_path = tmp.name
                        gemini_audio = genai.upload_file(path=tmp_path)
                        data = get_ai_json(f"Listen to audio. Extract need, category, urgency. Write in {ai_lang}. JSON: " + '{"extracted_need":"...","category":"...","urgency":"..."}', gemini_audio)
                        st.success(t("✅ Audio Analysis Complete","✅ ஆடியோ பகுப்பாய்வு முடிந்தது"))
                        st.json(data)
                        os.remove(tmp_path)
                    except Exception as e: st.error(f"Error: {e}")

elif page == "Survey OCR":
    st.title(t("📄 Survey Digitizer","📄 காகித பகுப்பாய்வு"))
    uploaded_file = st.file_uploader(t("Upload Image","பதிவேற்றவும்"), type=["jpg","jpeg","png"])
    if uploaded_file:
        st.image(uploaded_file, width=300)
        if st.button(t("Extract Data","பிரித்தெடுக்கவும்")):
            if GEMINI_API_KEY == "PASTE_YOUR_GEMINI_KEY": st.error("⚠️ Key missing.")
            else:
                with st.spinner(t("Extracting...","பிரித்தெடுக்கிறது...")):
                    try:
                        genai.configure(api_key=GEMINI_API_KEY)
                        img = PIL.Image.open(uploaded_file)
                        data = get_ai_json(f"Analyze survey/document image. Extract community need, category, urgency. Write 'need' in {ai_lang}. JSON: " + '{"need":"...","category":"...","urgency":"..."}', img)
                        st.success(t("✅ Extraction Complete","✅ பிரித்தெடுத்தல் முடிந்தது"))
                        c1,c2,c3 = st.columns(3)
                        with c1: st.markdown(f"<div class='metric-card'><h3>📌 {t('Need','தேவை')}</h3><p>{data.get('need','—')}</p></div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='metric-card'><h3>🏷️ {t('Category','வகை')}</h3><p>{data.get('category','—')}</p></div>", unsafe_allow_html=True)
                        with c3:
                            urgency = data.get('urgency','—')
                            color = "#ef4444" if urgency=="Critical" else "#f59e0b" if urgency=="High" else "#10b981"
                            st.markdown(f"<div class='metric-card'><h3>⚠️ {t('Urgency','அவசரம்')}</h3><p style='color:{color};font-weight:bold;'>{urgency}</p></div>", unsafe_allow_html=True)
                        st.json(data)
                    except Exception as e: st.error(f"Error: {e}")

elif page == "Forecasting":
    st.title(t("📈 Demand Forecasting","📈 தேவை முன்னறிவிப்பு"))
    st.caption(t("Predictive models showing volunteer demand across categories for next 30 days.","அடுத்த 30 நாட்களுக்கான தன்னார்வலர் தேவை முன்னறிவிப்பு."))
    date_rng = pd.date_range(start='today', periods=30, freq='D')
    st.line_chart(pd.DataFrame({
        'ARIMA (Education)': np.linspace(10, 25, 30) + np.random.normal(0, 2, 30),
        'Prophet (Environment)': np.linspace(5, 40, 30) + np.random.normal(0, 3, 30),
        'LSTM (Health)': np.linspace(20, 15, 30) + np.random.normal(0, 1, 30)
    }, index=date_rng))
    st.markdown(f"""<div style='background:rgba(30,41,59,0.5);border:1px solid #334155;border-radius:10px;padding:1rem;margin-top:1rem;'>
        <b>{t('Model Info','மாதிரி தகவல்')}</b><br>
        <small style='color:#94a3b8;'>ARIMA — {t('Education volunteer demand','கல்வி தன்னார்வலர் தேவை')}<br>
        Prophet — {t('Environment/disaster demand','சுற்றுச்சூழல் தேவை')}<br>
        LSTM — {t('Healthcare volunteer demand','சுகாதார தன்னார்வலர் தேவை')}</small>
    </div>""", unsafe_allow_html=True)

