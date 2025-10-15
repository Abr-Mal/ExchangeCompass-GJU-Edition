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

def get_raw_reviews_text(uni_name):
    """Fetches a list of all raw review texts for a given university."""
    # This logic should be similar to get_individual_reviews, but only select raw_review_text
    conn = get_db_connection()
    if conn is None: return []

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT raw_review_text FROM exchange_reviews WHERE uni_name = %s;",
            (uni_name,)
        )
        # Flatten the list of tuples into a single list of strings
        reviews = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return reviews
    except Exception as e:
        print(f"Error fetching raw reviews: {e}")
        return []

@app.route('/api/summary/<uni_name>', methods=['GET'])
def get_ai_summary(uni_name):
    """Generates a comprehensive summary review using Gemini based on all raw reviews."""
    
    # 1. Retrieve all raw reviews
    raw_reviews_list = get_raw_reviews_text(uni_name)
    if not raw_reviews_list:
        return jsonify({"summary": f"No reviews found for {uni_name}."}), 200

    # Combine reviews into a single string for the LLM context
    all_reviews_text = "\n---\n".join(raw_reviews_list)
    
    # 2. Call the Gemini API for Synthesis
    # NOTE: You MUST import the Gemini client setup from ai_processor.py or reconfigure it here.
    from ai_processor import client # Assuming you set up the client correctly in ai_processor.py
    
    synthesis_prompt = f"""
    You are the "ExchangeCompass Advisor". Your task is to synthesize a single, balanced narrative review (about 200 words) for the university "{uni_name}". 
    
    The review must cover the four main aspects: Academics, Cost of Living, Social Scene, and Accommodation.
    
    Synthesize the report from the following raw student feedback (which may contain both English and Arabic):
    
    --- START FEEDBACK ---
    {all_reviews_text}
    --- END FEEDBACK ---
    
    Focus on extracting the general consensus and noting any major conflicts in opinion. Structure the output as a single narrative paragraph.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro', # Use the Pro model for better summarization over long context
            contents=synthesis_prompt
        )
        return jsonify({"summary": response.text}), 200
    except Exception as e:
        return jsonify({"error": f"Synthesis failed: {e}"}), 500


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
@app.route('/api/unis', methods=['GET'])
def get_unis_live():
    """Fetches all processed university reviews from the PostgreSQL database."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    
    try:
        # Query all records from the table
        cursor.execute("SELECT * FROM exchange_reviews;")
        records = cursor.fetchall()

        # Get column names for building the dictionary list (important for JSON conversion)
        column_names = [desc[0] for desc in cursor.description]

        # Convert list of tuples (records) into a list of dictionaries (JSON format)
        unis_data = []
        for record in records:
            unis_data.append(dict(zip(column_names, record)))

        cursor.close()
        conn.close()
        
        # Flask's jsonify handles turning the Python list of dicts into a JSON response
        return jsonify(unis_data)
        
    except Exception as e:
        cursor.close()
        conn.close()
        print(f"Error querying database: {e}")
        return jsonify({"error": f"Error fetching data: {e}"}), 500

@app.route('/api/reviews/<uni_name>', methods=['GET'])
def get_individual_reviews(uni_name):
    """Fetches all individual reviews for a specific university."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    
    try:
        # Use a parameterized query to prevent SQL injection and filter by uni_name
        cursor.execute(
            "SELECT * FROM exchange_reviews WHERE uni_name = %s;",
            (uni_name,)
        )
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        reviews_data = []
        for record in records:
            reviews_data.append(dict(zip(column_names, record)))

        cursor.close()
        conn.close()
        return jsonify(reviews_data)
        
    except Exception as e:
        cursor.close()
        conn.close()
        print(f"Error querying reviews: {e}")
        return jsonify({"error": f"Error fetching reviews: {e}"}), 500

# --- 6. Run Application ---
if __name__ == '__main__':
    app.run(debug=True)
