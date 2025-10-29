import os
import psycopg2
from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

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

# --- Helper function for database connection ---
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

def get_raw_reviews_text(uni_name):
    """Fetches a list of all raw review texts for a given university."""
    conn = get_db_connection()
    if conn is None: return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT raw_review_text FROM exchange_reviews WHERE uni_name = %s;",
            (uni_name,)
        )
        reviews = [row[0] for row in cursor.fetchall()]
        return reviews
    except Exception as e:
        print(f"Error fetching raw reviews: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/summary/<uni_name>', methods=['GET'])
def get_ai_summary(uni_name):
    """Generates a comprehensive summary review using Gemini based on all raw reviews."""
    
    # 1. Retrieve all raw reviews for the given university.
    raw_reviews_list = get_raw_reviews_text(uni_name)
    if not raw_reviews_list:
        return jsonify({"summary": f"No reviews found for {uni_name}."}), 200

    # Combine reviews into a single string to provide sufficient context for the LLM.
    all_reviews_text = "\n---\n".join(raw_reviews_list)
    
    # 2. Dynamically import the AI analysis function to avoid circular dependencies
    # if ai_processor.py also imports app.py components.
    from ai_processor import analyze_review_with_gemini
    
    try:
        # Call the dedicated AI analysis function from ai_processor.py.
        gemini_result = analyze_review_with_gemini(all_reviews_text, uni_name)

        if gemini_result and gemini_result.get("theme_summary"):
            return jsonify({"summary": gemini_result["theme_summary"]}), 200
        else:
            return jsonify({"error": "AI summary could not be generated or was empty."}), 500
    except Exception as e:
        # Log the detailed error on the server side, but return a generic error to the client.
        print(f"Synthesis failed for {uni_name}: {e}")
        return jsonify({"error": "Failed to generate AI summary due to an internal error."}), 500

# --- 5. Flask Routes ---

@app.route('/')
def index():
    """Test route to verify database connection status and table existence."""
    conn = get_db_connection()
    if conn is None:
        return "Server is running, but **Database Connection FAILED**! Check .env and PostgreSQL setup.", 500

    cursor = conn.cursor()
    try:
        # Attempt a simple query to ensure the table 'exchange_reviews' exists.
        cursor.execute("SELECT COUNT(*) FROM exchange_reviews;")
        count = cursor.fetchone()[0]
        return f"Database Connection SUCCESS! The 'exchange_reviews' table has {count} entries. Backend is ready.", 200
    except Exception as e:
        # Return a more informative error if the table query fails.
        print(f"Error querying exchange_reviews table: {e}")
        return f"Database Connected, but Table Query FAILED. Check your table name and schema: {e}", 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/unis', methods=['GET'])
def get_unis_live():
    """Fetches all processed university reviews from the PostgreSQL database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Query all records from the table to display all universities.
        cursor.execute("SELECT * FROM exchange_reviews;")
        records = cursor.fetchall()

        # Get column names dynamically for flexible JSON conversion.
        column_names = [desc[0] for desc in cursor.description]
        unis_data = []
        for record in records:
            unis_data.append(dict(zip(column_names, record)))
        
        return jsonify(unis_data)
    except Exception as e:
        print(f"Error querying database for universities: {e}")
        return jsonify({"error": "Failed to fetch university data from the database."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/reviews/<uni_name>', methods=['GET'])
def get_individual_reviews(uni_name):
    """Fetches all individual reviews for a specific university."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Use a parameterized query to prevent SQL injection and filter reviews by university name.
        cursor.execute(
            "SELECT * FROM exchange_reviews WHERE uni_name = %s;",
            (uni_name,)
        )
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        reviews_data = []
        for record in records:
            reviews_data.append(dict(zip(column_names, record)))
        
        return jsonify(reviews_data)
    except Exception as e:
        print(f"Error querying reviews for {uni_name}: {e}")
        return jsonify({"error": "Failed to fetch reviews for the specified university."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- 6. Run Application ---
if __name__ == '__main__':
    app.run(debug=True)