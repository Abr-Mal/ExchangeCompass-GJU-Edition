import os
import psycopg2
from flask import Flask, jsonify, request
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

# --- In-memory cache for aggregated university details ---
university_details_cache = {}
# You could add a simple timestamp to each cached entry for time-based invalidation

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
    """Generates a comprehensive summary review using Gemini based on all raw reviews, with caching."""
    # 1. Attempt to retrieve a cached theme_summary from the database
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        # Look for an approved, AI-processed theme_summary in the database
        cursor.execute(
            "SELECT theme_summary FROM exchange_reviews WHERE uni_name = %s AND theme_summary IS NOT NULL AND reviewer_type = 'ai_processed' AND status = 'approved' LIMIT 1;",
            (uni_name,)
        )
        cached_summary = cursor.fetchone()

        if cached_summary and cached_summary[0]:
            print(f"✅ Cache hit: Returning cached AI summary for {uni_name}.")
            return jsonify({"summary": cached_summary[0]}), 200

        # 2. If no cached summary, retrieve all raw reviews for the given university to generate a new one.
        print(f"⚠️ Cache miss: Generating new AI summary for {uni_name}...")
        raw_reviews_list = get_raw_reviews_text(uni_name)
        if not raw_reviews_list:
            return jsonify({"summary": f"No reviews found for {uni_name}. Cannot generate AI summary."}), 200

        # Combine reviews into a single string to provide sufficient context for the LLM.
        all_reviews_text = "\n---\n".join(raw_reviews_list)

        # 3. Dynamically import the AI analysis function.
        from ai_processor import analyze_review_with_gemini
        
        # Call the dedicated AI analysis function from ai_processor.py.
        gemini_result = analyze_review_with_gemini(all_reviews_text, uni_name)

        if gemini_result and gemini_result.get("theme_summary"):
            generated_summary = gemini_result["theme_summary"]
            print(f"✅ AI summary generated for {uni_name}. Attempting to cache...")

            # Update an existing AI-processed record with the new summary
            # We'll find an existing 'ai_processed' and 'approved' review to update its summary
            # If no such record exists (which shouldn't happen if ai_processor.py ran), we can insert a placeholder
            cursor.execute(
                "UPDATE exchange_reviews SET theme_summary = %s WHERE uni_name = %s AND reviewer_type = 'ai_processed' AND status = 'approved' AND theme_summary IS NOT NULL LIMIT 1 RETURNING id;",
                (generated_summary, uni_name)
            )
            updated_id = cursor.fetchone()
            conn.commit()

            if updated_id:
                print(f"✅ Cached new AI summary in review ID {updated_id[0]} for {uni_name}.")
            else:
                # This case should ideally not happen if ai_processor has run, but as a fallback
                print(f"⚠️ Could not find existing AI-processed review to update for {uni_name}. Consider running ai_processor.py.")
                # Optionally, you could insert a new placeholder AI-processed review here

            return jsonify({"summary": generated_summary}), 200
        else:
            return jsonify({"error": "AI summary could not be generated or was empty."}), 500
    except Exception as e:
        conn.rollback() # Ensure rollback on error
        print(f"Synthesis failed for {uni_name}: {e}")
        return jsonify({"error": "Failed to generate AI summary due to an internal error."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

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

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    """Receives and stores a new user-submitted review."""
    review_data = request.get_json()
    if not review_data:
        return jsonify({"error": "Invalid review data provided."}), 400

    required_fields = ['uni_name', 'raw_review_text', 'academics_score', 'cost_score', 'social_score', 'accommodation_score']
    if not all(field in review_data for field in required_fields):
        return jsonify({"error": "Missing required review fields."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        sql_insert = """
            INSERT INTO exchange_reviews (
                uni_name, city, source_type, raw_review_text, raw_language,
                overall_sentiment, academics_score, cost_score, social_score,
                accommodation_score, theme_summary, reviewer_type, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        # For user-submitted reviews, we'll use placeholder values for AI-generated fields initially.
        # The AI processor will eventually update theme_summary based on all text.
        # Set raw_language to 'en' by default for now, can be expanded later.
        # overall_sentiment and theme_summary will be null/empty until ai_processor runs.
        values = (
            review_data['uni_name'],
            review_data.get('city', 'Unknown'), # City might not be in submission, default to 'Unknown'
            'user_submitted', # Mark as user submitted
            review_data['raw_review_text'],
            review_data.get('raw_language', 'en'), # Assume English for user input, can be enhanced
            'Neutral', # Default sentiment for initial user reviews
            review_data['academics_score'],
            review_data['cost_score'],
            review_data['social_score'],
            review_data['accommodation_score'],
            review_data.get('theme_summary', 'User-provided review.'), # Placeholder summary
            'user_submitted', # Explicitly set reviewer type
            'pending' # New reviews are pending approval
        )
        
        cursor.execute(sql_insert, values)
        conn.commit()
        print(f"✅ Successfully inserted user review for {review_data['uni_name']}. Status: pending")
        return jsonify({"message": "Review submitted successfully! It is pending approval."}), 201
    except Exception as e:
        conn.rollback()
        print(f"Error submitting review: {e}")
        return jsonify({"error": "Failed to submit review due to an internal error."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/university/<uni_name>', methods=['GET'])
def get_university_details(uni_name):
    """Fetches aggregated university details including overall score and theme summary, with caching."""
    # Check cache first
    if uni_name in university_details_cache:
        print(f"✅ Cache hit for university details: {uni_name}")
        return jsonify(university_details_cache[uni_name]), 200

    print(f"⚠️ Cache miss for university details: {uni_name}. Fetching from DB...")
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT
                uni_name,
                city,
                ROUND(AVG(academics_score)::numeric, 2) AS avg_academics,
                ROUND(AVG(cost_score)::numeric, 2) AS avg_cost,
                ROUND(AVG(social_score)::numeric, 2) AS avg_social,
                ROUND(AVG(accommodation_score)::numeric, 2) AS avg_accommodation,
                ROUND(AVG((academics_score + cost_score + social_score + accommodation_score) / 4.0)::numeric, 2) AS overall_score,
                -- Fetching a theme_summary, prioritizing AI-processed ones
                (SELECT theme_summary FROM exchange_reviews WHERE uni_name = %s AND theme_summary IS NOT NULL AND reviewer_type = 'ai_processed' AND status = 'approved' LIMIT 1) AS theme_summary
            FROM
                exchange_reviews
            WHERE
                uni_name = %s AND status = 'approved'
            GROUP BY
                uni_name, city;
        """, (uni_name, uni_name))
        
        record = cursor.fetchone()
        print(f"Raw record from DB for {uni_name}: {record}") # DEBUG LOG

        if record:
            column_names = [desc[0] for desc in cursor.description]
            university_data = dict(zip(column_names, record))
            print(f"Aggregated university data returned: {university_data}") # DEBUG LOG
            
            # Cache the result before returning
            university_details_cache[uni_name] = university_data
            print(f"✅ Cached university details for: {uni_name}")

            return jsonify(university_data)
        else:
            return jsonify({"error": f"University {uni_name} not found or no approved reviews available."}), 404
    except Exception as e:
        print(f"Error fetching aggregated university details for {uni_name}: {e}")
        return jsonify({"error": "Failed to fetch university details due to an internal error."}), 500
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
        cursor.execute("""
            SELECT
                uni_name,
                city,
                COUNT(*) AS review_count,
                ROUND(AVG(academics_score)::numeric, 2) AS avg_academics,
                ROUND(AVG(cost_score)::numeric, 2) AS avg_cost,
                ROUND(AVG(social_score)::numeric, 2) AS avg_social,
                ROUND(AVG(accommodation_score)::numeric, 2) AS avg_accommodation,
                AVG((academics_score + cost_score + social_score + accommodation_score) / 4.0)::numeric AS overall_score
            FROM
                exchange_reviews
            WHERE
                status = 'approved'
            GROUP BY
                uni_name, city;
        """)
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
            "SELECT id, uni_name, raw_review_text, academics_score, cost_score, social_score, accommodation_score, reviewer_type FROM exchange_reviews WHERE uni_name = %s AND status = 'approved' ORDER BY id DESC;",
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

@app.route('/api/admin/reviews/<int:review_id>/status', methods=['PUT'])
def update_review_status(review_id):
    """Admin endpoint to update the status of a review (e.g., approve, reject)."""
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
    incoming_api_key = request.headers.get('X-API-Key')

    if not ADMIN_API_KEY or incoming_api_key != ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

    status_data = request.get_json()
    new_status = status_data.get('status')

    if new_status not in ['approved', 'rejected']:
        return jsonify({"error": "Invalid status provided. Must be 'approved' or 'rejected'."}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE exchange_reviews SET status = %s WHERE id = %s;",
            (new_status, review_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": f"Review with ID {review_id} not found."}), 404
        
        # Invalidate cache for the affected university
        cursor.execute("SELECT uni_name FROM exchange_reviews WHERE id = %s;", (review_id,))
        uni_name_result = cursor.fetchone()
        if uni_name_result:
            affected_uni_name = uni_name_result[0]
            if affected_uni_name in university_details_cache:
                del university_details_cache[affected_uni_name]
                print(f"✅ Cache invalidated for university: {affected_uni_name} due to review status change.")

        print(f"✅ Successfully updated status for review ID {review_id} to {new_status}.")
        return jsonify({"message": f"Review {review_id} status updated to {new_status}."}), 200
    except Exception as e:
        conn.rollback()
        print(f"Error updating review status for ID {review_id}: {e}")
        return jsonify({"error": "Failed to update review status due to an internal error."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@app.route('/api/admin/reviews/pending', methods=['GET'])
def get_pending_reviews_endpoint():
    """Admin endpoint to fetch all reviews with 'pending' status."""
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
    incoming_api_key = request.headers.get('X-API-Key')

    if not ADMIN_API_KEY or incoming_api_key != ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 401
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, uni_name, raw_review_text, reviewer_type FROM exchange_reviews WHERE status = 'pending' ORDER BY id ASC;"
        )
        records = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        pending_reviews_data = []
        for record in records:
            pending_reviews_data.append(dict(zip(column_names, record)))
        
        return jsonify(pending_reviews_data), 200
    except Exception as e:
        print(f"Error fetching pending reviews for admin: {e}")
        return jsonify({"error": "Failed to fetch pending reviews due to an internal error."}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- 6. Run Application ---
if __name__ == '__main__':
    app.run(debug=True)