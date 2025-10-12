import os
import psycopg2
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS # We added this for Day 6, so include it now

# --- 1. Load Environment Variables from .env file ---
# This makes your DB credentials available to the application.
load_dotenv()

# --- 2. Configure Database Connection Details from .env ---
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# --- 3. Flask App Initialization ---
app = Flask(__name__)
# Enable CORS to allow the frontend (on a different port) to access this backend
CORS(app) 

# --- MOCK DATA FOR FRONTEND DEVELOPMENT (for /api/unis route) ---
MOCK_UNI_DATA = [
    {
        "id": 1,
        "uni_name": "LMU Munich",
        "city": "Munich",
        "overall_score": 4.5,
        "academic_score": 4.8,
        "cost_score": 1.5,
        "social_score": 4.2,
        "accommodation_score": 2.5,
        "summary": "Excellent academics, very high cost of living."
    },
    {
        "id": 2,
        "uni_name": "Technical University Hamburg (TUHH)",
        "city": "Hamburg",
        "overall_score": 3.9,
        "academic_score": 4.1,
        "cost_score": 3.2,
        "social_score": 3.8,
        "accommodation_score": 3.5,
        "summary": "Solid all-around choice with manageable living costs."
    },
    {
        "id": 3,
        "uni_name": "University of Cologne",
        "city": "Cologne",
        "overall_score": 4.2,
        "academic_score": 4.0,
        "cost_score": 3.5,
        "social_score": 4.9,
        "accommodation_score": 3.0,
        "summary": "الجامعة ممتازة أكاديمياً ولكن الحياة الاجتماعية رائعة حقاً." 
    }
]

# --- 4. Database Connection Function ---
def get_db_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Database connection established successfully!")
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# --- 5. Flask Routes ---

@app.route('/')
def index():
    """Test route to verify database connection status."""
    conn = get_db_connection()
    if conn is None:
        return "Server is running, but **Database Connection FAILED**! Check .env and PostgreSQL setup.", 500

    # Simple test query to check if the table exists
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM exchange_reviews;")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return f"Database Connection SUCCESS! The 'exchange_reviews' table has {count} entries. Backend is ready.", 200
    except Exception as e:
        cursor.close()
        conn.close()
        return f"Database Connected, but Table Query FAILED. Check your table name and schema: {e}", 500

@app.route('/api/unis', methods=['GET'])
def get_unis_mock():
    """Returns mock university data for the frontend to build the dashboard."""
    return jsonify(MOCK_UNI_DATA)


# --- 6. Run Application ---
if __name__ == '__main__':
    app.run(debug=True)