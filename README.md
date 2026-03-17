# FundWise AI - RAG Chatbot for Groww Mutual Funds

A Retrieval-Augmented Generation (RAG) chatbot for querying information about Axis Mutual Funds available on Groww platform.

## 🚀 Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_STREAMLIT_URL_HERE)

## 📊 Supported Funds

- **Axis Large Cap Fund**
- **Axis Small Cap Fund**
- **Axis Nifty 500 Index Fund**
- **Axis ELSS Tax Saver**

## ✨ Features

- **NAV Queries**: Get latest NAV values with dates
- **Fund Documents**: Access KIM, SID, and Leaflet documents
- **Fund Details**: Expense ratio, exit load, minimum SIP amounts
- **Multi-Fund Support**: Query multiple funds at once
- **Source Attribution**: Every answer includes source links
- **Real-time Data**: Scheduler keeps data updated automatically

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Data Scraping**: Selenium + BeautifulSoup
- **Scheduler**: APScheduler

## 📁 Project Structure

```
.
├── app.py                          # Streamlit entry point
├── requirements.txt                # Python dependencies
├── phase1/                         # Data Ingestion
│   └── scrapers/
├── phase2/                         # Document Processing
│   └── processors/
├── phase3/                         # Vector Store & Embeddings
│   └── embeddings/
├── phase4/                         # Backend & Frontend
│   ├── backend/
│   └── frontend/
├── phase5/                         # API Layer
├── phase6/                         # Conversation Memory
├── phase7/                         # Scheduler
│   └── scheduler/
├── shared/                         # Shared components
│   ├── config/
│   └── data/
└── data/                           # CSV data files
```

## 🚀 Deployment on Streamlit Cloud

### Step 1: Fork/Clone this Repository

```bash
git clone https://github.com/YOUR_USERNAME/fundwise-ai.git
cd fundwise-ai
```

### Step 2: Set Up Secrets

Create a `.streamlit/secrets.toml` file (for local testing):

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

For Streamlit Cloud deployment, add secrets in the app settings.

### Step 3: Deploy

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Connect your GitHub repository
3. Select the main branch
4. Set the main file path to `app.py`
5. Add your `GROQ_API_KEY` in the secrets section
6. Deploy!

## 🔧 Local Development

### Prerequisites

- Python 3.9+
- Chrome browser (for scraping)

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/fundwise-ai.git
cd fundwise-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run Locally

```bash
# Run the Streamlit app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## 📋 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |

## 🔄 Data Refresh Schedule

The scheduler (Phase 7) automatically refreshes data:

| Data Type | Frequency | Schedule |
|-----------|-----------|----------|
| NAV | Daily | 9:00 PM IST |
| Expense Ratio | Weekly | Monday 9:00 AM IST |
| Full Documents | Monthly | 1st at 6:00 AM IST |

## ⚠️ Disclaimer

This chatbot provides information only and is **not SEBI registered**. It does not provide investment advice. Always consult a financial advisor before making investment decisions.

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.
