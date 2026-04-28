# 🌍 Communiserve — Data-Driven Volunteer Coordination for Social Impact

> **Google Solutions Challenge 2025 Submission**
> Aligning with UN SDGs: 🏙️ SDG 11 (Sustainable Cities) | 🤝 SDG 17 (Partnerships) | ❤️ SDG 3 (Good Health)

---

## 📌 The Problem

Local NGOs and social groups collect critical community needs through **paper surveys and field reports** — but this data is scattered, hard to act on, and volunteers are matched manually. This leads to:

- Urgent needs going unaddressed for days
- Wrong volunteers being sent to wrong locations
- No visibility into what's happening on the ground
- Zero data for planning future resource allocation

---

## 💡 Our Solution

**Communiserve** is an AI-powered platform that:

1. **Digitizes** scattered community needs from paper surveys, voice recordings, and field reports
2. **Intelligently matches** volunteers to needs based on skills, location, and urgency using Gemini AI
3. **Verifies** task completion through AI-powered photo proof
4. **Forecasts** future volunteer demand using predictive models

---

## 🎥 Demo Video

▶️ [Watch 2-minute Demo](https://your-demo-link-here)

🌐 **Live App:** [communiserve.ycloudflare.com](https://communiserve.ycloudflare.com)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Real-Time Dashboard** | Live volunteer count, needs fulfilled, match accuracy |
| 🙋 **Volunteer Onboarding** | Register with skills + AI instantly matches best task |
| 🆘 **SOS Auto-Triage** | Raw incident text → Gemini AI → dispatches 2 best volunteers |
| 🤖 **Command Dispatch** | Select any need → AI finds optimal volunteer pair |
| 📸 **Task Verification** | Upload photo proof → AI verifies completion |
| 🗺️ **Geospatial Map** | Interactive Folium map showing all active needs with urgency colors |
| 🎙️ **Voice Intake** | Upload audio → Gemini extracts need, category, urgency |
| 📄 **Survey OCR** | Upload paper survey photo → AI digitizes into structured data |
| 📈 **Demand Forecasting** | ARIMA, LSTM, Prophet models predict volunteer demand |
| 🏢 **NGO Admin Panel** | Secure login → submit new community needs → appear on map instantly |
| 🌐 **Tamil Bilingual** | Full Tamil + English support across all pages |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **AI / ML** | Google Gemini AI (gemini-1.5-flash) |
| **Backend** | Python, Streamlit |
| **Database** | Firebase Firestore |
| **Maps** | Folium + OpenStreetMap |
| **Forecasting** | ARIMA, Prophet, LSTM models |
| **Hosting** | Cloudflare (via localhost.run tunnel) |
| **Language** | Tamil + English bilingual |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Google Gemini API Key
- Firebase project (Firestore enabled)
- Google Colab (recommended for mobile users)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/techcode20/communiserve.git
cd communiserve

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your keys in app.py
GEMINI_API_KEY = "your-gemini-api-key"
# Add Firebase config from your service account JSON

# 4. Run the app
streamlit run app.py
```

### requirements.txt
```
streamlit
google-generativeai
Pillow
pandas
numpy
folium
streamlit-folium
firebase-admin
requests
```

---

## 🔑 NGO Admin Demo Credentials

```
Email:    admin@communiserve.org
Password: ngo@2024
```

---

## 🗺️ How It Works

```
Paper Survey / Voice Report / Field Data
            ↓
    Gemini AI Digitization
            ↓
   Community Need on Map
            ↓
  AI Volunteer Matching Engine
            ↓
    Volunteer Dispatched
            ↓
  Photo Proof → AI Verification
            ↓
   Dashboard Updated Live
```

---

## 📁 Project Structure

```
communiserve/
│
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## 🌐 UN SDG Alignment

- **SDG 11 — Sustainable Cities:** Helps urban communities identify and respond to local needs efficiently
- **SDG 17 — Partnerships:** Connects NGOs, volunteers, and communities on one platform
- **SDG 3 — Good Health:** Ensures health-related needs (medical aid, food) are matched with skilled volunteers fast

---

## 👩‍💻 Team

| Name | Role | College |
|---|---|---|
| Khanishka | Developer & ML Engineer | Jeppiaar Engineering College, Chennai |

---

## 📸 Screenshots

### Home Page
![Home](screenshots/home.png)

### Active Needs Map
![Map](screenshots/map.png)

### SOS Auto-Triage
![SOS](screenshots/sos.png)

### NGO Admin Panel
![NGO](screenshots/ngo.png)

---

## 🏆 Google Solutions Challenge 2025

This project was built for the **Google Solutions Challenge 2025**, using:
- ✨ **Gemini AI** — for intelligent volunteer matching, SOS triage, task verification, OCR, and audio analysis
- 🔥 **Firebase Firestore** — for real-time data persistence across volunteers and community needs

---

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

*Built with ❤️ from Chennai, India 🇮🇳*
