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
5.  **User Review Submission:**
    * Enables students to directly submit their reviews and aspect-based scores for universities.
6.  **Admin Moderation System:**
    * Implements a review moderation workflow where user-submitted reviews require admin approval before being publicly displayed.
7.  **Performance Optimization (Caching):**
    * Introduces caching for AI-generated summaries and aggregated university details to significantly reduce latency and improve response times.

---

### ⚙️ 3. Technical Stack

| Component | Technology | Role in Project |
| :--- | :--- | :--- |
| **Backend/AI Logic** | **Python (Flask)** | Handles the core business logic, database interaction, and powers the data processing scripts. |
| **Artificial Intelligence** | **Google Gemini API** | Executes the multilingual Aspect-Based Sentiment Analysis and generates structured JSON output. Now with **summary caching** for improved performance. |
| **Data Acquisition** | **BeautifulSoup** / **Requests** | Used for ethical web scraping of publicly available university review sites and forums. |
| **Database** | **PostgreSQL** | Relational database used for storing structured cost data and the processed, enriched sentiment scores, including **review moderation status** and `reviewer_type`. |
| **Backend/Admin Security** | **API Key** | Simple API key implementation to secure administrative endpoints for review moderation. |
| **Frontend/UI** | **React** | Used for building a component-based, responsive, and interactive user interface. |
| **Visualization** | **Chart.js** | Used to generate dynamic Comparative Bar Charts and Radar Diagrams for visual insights. |
| **Deployment** | **Vercel/Netlify** (Frontend) & **Render** (Backend) | Planned for a professional, scalable live deployment. |

---

### 🛠️ 4. Setup Instructions

Follow these steps to get the ExchangeCompass application up and running on your local machine.

#### Prerequisites

*   **Python 3.8+**
*   **Node.js 18+**
*   **PostgreSQL**: Ensure you have a PostgreSQL server running and accessible. Updated database schema now requires `reviewer_type`, `overall_sentiment`, and `status` columns in `exchange_reviews` table.
*   **Google Gemini API Key**: Obtain an API key from the Google Cloud Console or AI Studio.
*   **Admin API Key**: A secret key required for authenticating with backend admin endpoints (for moderation).

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
    In the `backend` directory, create a file named `.env` and add your database credentials, Gemini API key, and Admin API key. Replace the placeholder values with your actual information.
    ```
    DB_HOST=your_db_host
    DB_NAME=your_db_name
    DB_USER=your_db_user
    DB_PASSWORD=your_db_password
    GEMINI_API_KEY=your_gemini_api_key
    ADMIN_API_KEY=your_admin_api_key # New: Required for admin moderation endpoints
    ```

5.  **Database Schema (for `exchange_reviews` table):**
    Connect to your PostgreSQL database and ensure the `exchange_reviews` table exists with the updated schema. Here's the complete schema:
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
        theme_summary TEXT,
        reviewer_type VARCHAR(50) DEFAULT 'ai_processed', -- New: 'ai_processed' or 'user_submitted'
        status VARCHAR(20) DEFAULT 'approved'            -- New: 'pending', 'approved', or 'rejected'
    );
    ```
    *If your table already exists, run these `ALTER TABLE` commands to add the new columns:*
    ```sql
    ALTER TABLE exchange_reviews ADD COLUMN reviewer_type VARCHAR(50) DEFAULT 'ai_processed';
    ALTER TABLE exchange_reviews ADD COLUMN overall_sentiment VARCHAR(50);
    ALTER TABLE exchange_reviews ADD COLUMN status VARCHAR(20) DEFAULT 'approved';
    ```

6.  **Run the AI Processor to populate/update the database:**
    This script reads from `data/raw_survey_data.csv` and `frontend/src/mock_reviews.html`, processes reviews with Gemini (caching AI summaries), and inserts/updates them into your database. It also ensures initial data is marked `approved`.
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

#### 4.3. Admin Moderation (Local)

To manage user-submitted reviews (approve/reject) using a local script:

1.  **Ensure `requests` and `python-dotenv` are installed** in your backend virtual environment:
    ```bash
    pip install requests python-dotenv
    ```
2.  **Ensure your Flask backend server is running** (as described in step 4.1.7 above).
3.  **Run the `admin_moderator.py` script** in a *separate terminal* (after activating your virtual environment):
    ```bash
    cd backend
    .\venv\Scripts\activate   # Windows
    source venv/bin/activate # macOS/Linux
    python admin_moderator.py
    ```
4.  The script will prompt you for actions (`list_pending`, `approve`, `reject`, `exit`). Use `list_pending` to see IDs of reviews awaiting approval, then `approve` or `reject` with the review ID.

#### 4.4. Frontend Setup

1.  **Navigate to the `frontend` directory:**
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Configure Backend URL (for Local Development & Deployment):**
    *   **For local development:** If your backend is running on a different URL or port than `http://127.0.0.1:5000`, create a `.env` file in the `frontend` directory and specify it:
        ```
        VITE_BACKEND_URL=http://your_backend_ip:your_backend_port
        ```
    *   **For deployment (Vercel/Netlify):** You **must** set `VITE_BACKEND_URL` in your deployment platform's environment variables to the public URL of your deployed Render backend service.

4.  **Run the React development server:**
    ```bash
    npm run dev
    ```
    The frontend will typically run on `http://localhost:5173` (or another available port).

---

### 5. Known Limitations

*   **Basic Language Detection:** The current language detection in `ai_processor.py` (for `raw_language`) is a simple heuristic that differentiates between English and Arabic based on character ranges. It may not be accurate for all cases or other languages.
*   **Lack of Advanced Admin UI:** Currently, admin moderation is handled via a local Python script and direct API calls. A full-featured admin user interface is not yet implemented.
*   **Single-User API Key Security:** The current API key implementation is suitable for a single administrator. For multi-user administrative access, a more robust authentication system (e.g., JWT) would be required.

---

### 6. Ethical & Security Commitments

*   **Data Integrity & Privacy:** All data collected via the survey includes a **mandatory consent statement**. All data, regardless of source, is immediately **anonymized** before storage.
*   **No PII Stored:** No personal information (user names, IDs, email addresses, or direct source links) is ever stored or displayed.
*   **Scraping:** Web scraping is strictly limited to **publicly accessible, non-gated text** only and adheres to all ethical scraping practices (rate limiting, robots.txt consideration).
*   **Admin API Key Security Note:** It is **CRITICAL** to keep your `ADMIN_API_KEY` confidential. For deployed applications, always set this as a secure environment variable on your hosting platform (e.g., Render) and **never commit it directly to your codebase.**

---

### 🔮 7. Project Status

**Current Phase:** Feature Enhancement & Deployment Preparation (Review System, Moderation, Caching)

**Live Demo URL:** (To be added upon final deployment in Phase 5)

**Creator:** [Abrahim Abu Malouh / https://github.com/Abr-Mal]