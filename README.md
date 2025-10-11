# 🇩🇪 ExchangeCompass: GJU Edition (Multilingual Student Advisor) 🧭

## 🚀 1. Overview and Problem Statement

**The Challenge:** Students from GJU preparing for their final-year exchange to Germany face a significant information gap. They rely on scattered, non-standardized feedback to decide on a host university, particularly regarding non-academic factors like **Cost of Living** and **Accommodation**.

**The Solution:** ExchangeCompass is a full-stack, data-driven web application designed to centralize and quantify this scattered student opinion. It provides a transparent, objective platform by analyzing multilingual student feedback (English and Arabic) and converting it into comparable, objective scores.

**Key Deliverable:** The project's success is defined by its ability to merge high-integrity survey data with publicly sourced reviews, proving the viability of using advanced AI for niche, real-world advisory services.

---

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
| **Backend/AI Logic** | **Python (Flask/Django)** | Handles the core business logic, database interaction, and powers the data processing scripts. |
| **Artificial Intelligence** | **Google Gemini API** | Executes the multilingual Aspect-Based Sentiment Analysis and generates structured JSON output. |
| **Data Acquisition** | **BeautifulSoup** / **Requests** | Used for ethical web scraping of publicly available university review sites and forums. |
| **Database** | **PostgreSQL** | Relational database used for storing structured cost data and the processed, enriched sentiment scores. |
| **Frontend/UI** | **React / Vue.js** | Used for building a component-based, responsive, and interactive user interface. |
| **Visualization** | **Chart.js / D3.js** | Used to generate dynamic Comparative Bar Charts and Radar Diagrams for visual insights. |
| **Deployment** | **Vercel/Netlify** (Frontend) & **Cloud Run/Heroku** (Backend) | Planned for a professional, scalable live deployment. |

---

### 🔒 4. Ethical & Security Commitments

* **Data Integrity & Privacy:** All data collected via the survey includes a **mandatory
