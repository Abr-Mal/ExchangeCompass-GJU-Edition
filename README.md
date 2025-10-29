# 🇩🇪 ExchangeCompass: GJU Edition (Multilingual Student Advisor) 🧭

## 🚀 1. Overview and Problem Statement

**The Challenge:** Students from GJU preparing for their final-year exchange to Germany face a significant information gap. They rely on scattered, non-standardized feedback to decide on a host university, particularly regarding non-academic factors like **Cost of Living** and **Accommodation**.

**The Solution:** ExchangeCompass is a full-stack, data-driven web application designed to centralize and quantify this scattered student opinion. It provides a transparent, objective platform by analyzing multilingual student feedback (English and Arabic) and converting it into comparable, objective scores.

**Key Deliverable:** The project's success is defined by its ability to merge high-integrity survey data with publicly sourced reviews, proving the viability of using advanced AI for niche, real-world advisory services.

---

**⚠️ Disclaimer:** This project uses **simulated and mock data** for demonstration and showcase purposes only. The university reviews, scores, and all related information are not real and should not be used for actual decision-making regarding exchange programs. The data is generated or curated to demonstrate the application's features and capabilities.

### ✨ 2. Core Features

The application provides the following actionable features:

1.  **Aspect-Based Sentiment Analysis (ABSA):**
    * Utilizes the **Google Gemini API** to analyze unstructured text and break down student feedback into quantifiable scores (1-5) across four critical aspects: **Academic Rigor, Cost of Living, Social Scene, and Accommodation.**
2.  **Multilingual Pipeline:**
    * Successfully processes and standardizes feedback collected in **English and Arabic** within a single AI-driven ingestion pipeline, demonstrating robust cross-lingual data handling.
3.  **Data Blending & Trust Score:**
    * Unifies two data streams: **Consent-based Survey Responses** (high trust) and **Anonymized Web-Scraped Reviews** (high volume). Users can filter results based on the data source.
4.  **Interactive Comparison Dashboard:**
    * Allows users to select two universities for a side-by-side comparison of all ABSA scores, core cost metrics, and underlying qualitative review summaries.

---

### ⚙️ 3. Technical Stack

| Component | Technology | Role in Project |
| :--- | :--- | :--- |
| **Backend/AI Logic** | **Python (Flask)** | Handles the core business logic, database interaction, and powers the data processing scripts. |
| **Artificial Intelligence** | **Google Gemini API** | Executes the multilingual Aspect-Based Sentiment Analysis and generates structured JSON output. |
| **Data Acquisition** | **BeautifulSoup** / **Requests** | Used for ethical web scraping of publicly available university review sites and forums. |
| **Database** | **PostgreSQL** | Relational database used for storing structured cost data and the processed, enriched sentiment scores. |
| **Frontend/UI** | **React** | Used for building a component-based, responsive, and interactive user interface. |
| **Visualization** | **Chart.js** | Used to generate dynamic Comparative Bar Charts and Radar Diagrams for visual insights. |
| **Deployment** | **Vercel/Netlify** (Frontend) & **Cloud Run/Heroku** (Backend) | Planned for a professional, scalable live deployment. |

---

### 🛠️ 4. Setup Instructions

Follow these steps to get the ExchangeCompass application up and running on your local machine.

#### Prerequisites

*   **Python 3.8+**
*   **Node.js 18+**
*   **PostgreSQL**: Ensure you have a PostgreSQL server running and accessible.
*   **Google Gemini API Key**: Obtain an API key from the Google Cloud Console or AI Studio.

#### 4.1. Backend Setup

1.  **Navigate to the `backend` directory:**
    ```bash
    cd backend
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    In the `backend` directory, create a file named `.env` and add your database credentials and Gemini API key. Replace the placeholder values with your actual information.
    ```
    DB_HOST=your_db_host
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    GEMINI_API_KEY=your_gemini_api_key
    ```

5.  **Database Schema (example for `exchange_reviews` table):**
    Connect to your PostgreSQL database and create the `exchange_reviews` table if it doesn't exist. Here's a sample schema:
    ```sql
    CREATE TABLE exchange_reviews (
        id SERIAL PRIMARY KEY,
        uni_name VARCHAR(255) NOT NULL,
        city VARCHAR(255),
        source_type VARCHAR(50),
        raw_review_text TEXT,
        raw_language VARCHAR(10),
        overall_sentiment VARCHAR(50),
        academics_score INTEGER,
        cost_score INTEGER,
        social_score INTEGER,
        accommodation_score INTEGER,
        theme_summary TEXT
    );
    ```

6.  **Run the AI Processor to populate the database (optional, for initial data):**
    This script will read from `data/raw_survey_data.csv` and `frontend/src/mock_reviews.html`, process reviews with Gemini, and insert them into your database.
    ```bash
    python ai_processor.py
    ```

7.  **Run the Flask backend server:**
    ```bash
    flask run
    # Or for production with Gunicorn (as defined in Procfile):
    # gunicorn app:app
    ```
    The backend will typically run on `http://127.0.0.1:5000`.

#### 4.2. Frontend Setup

1.  **Navigate to the `frontend` directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Backend URL (if different from default):**
    If your backend is running on a different URL or port than `http://127.0.0.1:5000`, create a `.env` file in the `frontend` directory and specify it:
    ```
    VITE_BACKEND_URL=http://your_backend_ip:your_backend_port
    ```

4.  **Run the React development server:**
    ```bash
    npm run dev
    ```
    The frontend will typically run on `http://localhost:5173` (or another available port).

---

### 5. Known Limitations

*   **Basic Language Detection:** The current language detection in `ai_processor.py` (for `raw_language`) is a simple heuristic that differentiates between English and Arabic based on character ranges. It may not be accurate for all cases or other languages.

---

### 6. Ethical & Security Commitments

* **Data Integrity & Privacy:** All data collected via the survey includes a **mandatory consent statement**. All data, regardless of source, is immediately **anonymized** before storage.
* **No PII Stored:** No personal information (user names, IDs, email addresses, or direct source links) is ever stored or displayed.
* **Scraping:** Web scraping is strictly limited to **publicly accessible, non-gated text** only and adheres to all ethical scraping practices (rate limiting, robots.txt consideration).

---

### 🔮 7. Project Status

**Current Phase:** Week 1 - Foundation and Setup

**Live Demo URL:** (To be added upon final deployment in Phase 5)

**Creator:** [Abrahim Abu Malouh / https://github.com/Abr-Mal]
