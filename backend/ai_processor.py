import os
import time
import json
import pandas as pd
import google.generativeai as genai
from google.generativeai import types
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables (including GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def parse_html_reviews(html_file_path):
    """Parses the mock HTML file to extract university reviews."""
    reviews_data = []
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        review_cards = soup.find_all('div', class_='uni-review-card')
        
        for card in review_cards:
            uni_name = card.find('h4', class_='uni-name').get_text(strip=True) if card.find('h4', class_='uni-name') else None
            city = card.find('p', class_='uni-city').get_text(strip=True) if card.find('p', class_='uni-city') else None
            review_body = card.find('p', class_='review-body').get_text(strip=True) if card.find('p', class_='review-body') else None
            
            if uni_name and review_body: # City is optional, but name and review are essential
                reviews_data.append({
                    'uni_name': uni_name,
                    'city': city,
                    'raw_review_text': review_body,
                    'source_type': 'html_scrape' # Indicate the source of this data
                })
    except FileNotFoundError:
        print(f"❌ ERROR: HTML mock reviews file not found at {html_file_path}")
        return []
    except Exception as e:
        print(f"❌ ERROR parsing HTML reviews: {e}")
        return []
    
    return reviews_data

def analyze_review_with_gemini(review_text, uni_name):
    """Sends the review to Gemini for ABSA and structured JSON return."""
    
    # 1. Define the Structured Output Schema (Pydantic style for clarity).
    # This is critical for getting clean, reliable data into your DB.
    response_schema = {
        "type": "object",
        "properties": {
            "overall_sentiment": {"type": "string", "description": "Positive, Neutral, or Negative."},
            "academics_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "cost_score": {"type": "integer", "description": "Score from 1 (expensive) to 5 (cheap)."},
            "social_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "accommodation_score": {"type": "integer", "description": "Score from 1 (difficult) to 5 (easy/good)."},
            "theme_summary": {"type": "string", "description": "A concise narrative summary (around 30-40 words) using simple language, covering academics, cost, social scene, and accommodation, including a short quote from the original review text."}
        },
        "required": ["overall_sentiment", "academics_score", "cost_score", "social_score", "accommodation_score", "theme_summary"]
    }
    
    # 2. Craft the Multilingual Prompt (The Magic)
    prompt = f"""
    You are an expert student advisor analyzing feedback for {uni_name}. 
    Your goal is to synthesize a very concise, easy-to-understand narrative review (approximately 30-40 words) for the university "{uni_name}". 
    
    The review must briefly cover Academics, Cost of Living, Social Scene, and Accommodation, using simple, direct language.
    
    Include one very short, direct quote from the provided student feedback to support a key point. Ensure the summary is structured as a single narrative paragraph.
    
    Synthesize the report from the following raw student feedback (which may contain both English and Arabic):
    
    Review Text: "{review_text}"
    """
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            generation_config=types.GenerationConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        response = model.generate_content(prompt)
        # The response text will be a clean JSON string, which we parse.
        return json.loads(response.text)
        
    except Exception as e:
        print(f"❌ Gemini API call failed for {uni_name}: {e}")
        return None

def assign_mock_majors(uni_name):
    """Assigns mock major data based on the university name."""
    # This is a placeholder function. In a real application, you would have a
    # more sophisticated logic to determine the major based on uni_name.
    # For now, we'll return a dummy major.
    if "University of Technology" in uni_name:
        return ["Computer Science", "Electrical Engineering"]
    elif "University of Arts" in uni_name:
        return ["Graphic Design", "Animation"]
    elif "University of Medicine" in uni_name:
        return ["Medicine", "Pharmacy"]
    elif "University of Engineering" in uni_name:
        return ["Mechanical Engineering", "Civil Engineering"]
    else:
        return ["General Studies"]

def process_data_pipeline():
    """Reads raw CSV data, cleans it, and processes reviews with Gemini."""

    # Construct absolute paths to data files.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, '..', 'data', 'raw_survey_data.csv')
    html_path = os.path.join(script_dir, '..', 'frontend', 'src', 'mock_reviews.html')

    all_raw_data = []

    # 1. READ DATA FROM CSV
    try:
        df_csv = pd.read_csv(csv_path)
        # Rename columns for consistency and clarity in the processing pipeline.
        df_csv.rename(columns={
            'Timestamp': 'date_collected',
            'Which university are you rating?': 'uni_name',
            'City': 'city',
            'Cost of living': 'cost_score',
            'Social scene quality': 'social_score',
            'Accommodation ease (How easy it is to find a living space)': 'accommodation_score',
            'Please provide your overall experience or any additional comments about your univerisity': 'raw_review_text',
        }, inplace=True)
        # Convert DataFrame rows to a list of dictionaries.
        all_raw_data.extend(df_csv.to_dict(orient='records'))

    except FileNotFoundError:
        print(f"❌ ERROR: Raw survey data not found at {csv_path}")
    except Exception as e:
        print(f"❌ ERROR reading or processing CSV data: {e}")

    # 2. READ DATA FROM MOCK HTML
    html_reviews = parse_html_reviews(html_path)
    all_raw_data.extend(html_reviews)

    if not all_raw_data:
        print("⚠️ WARNING: No data found from CSV or HTML. Returning empty list for processing.")
        return []

    # Convert combined data to a DataFrame for easier processing.
    df = pd.DataFrame(all_raw_data)

    processed_records = []

    # 3. ITERATE, PROCESS, and ENRICH each review using the Gemini AI.
    for index, row in df.iterrows():
        # Skip reviews where the core text is missing to avoid unnecessary AI calls.
        if pd.isna(row['raw_review_text']):
            print(f"⚠️ Skipping review for {row.get('uni_name', 'Unknown Uni')} due to missing raw_review_text.")
            continue

        # Call the Gemini API to analyze the review.
        gemini_result = analyze_review_with_gemini(row['raw_review_text'], row['uni_name'])

        if gemini_result:
            # Merge the AI-generated results with the original data.
            record = {
                'uni_name': row['uni_name'],
                'city': row['city'],
                'source_type': row.get('source_type', 'csv_survey'), # Default to csv_survey if not specified.
                'raw_review_text': row['raw_review_text'],
                **gemini_result, # Unpack the dictionary containing AI scores and summary.
                'major': assign_mock_majors(row['uni_name']) # Assign mock majors
            }
            processed_records.append(record)
            print(f"✅ Successfully processed and enriched review for: {row['uni_name']}")
            # Rate limit protection: pause 13 seconds to avoid 429 errors from Gemini API
            print("⏳ Pausing for 13 seconds to avoid Gemini API rate limit (429 error)...")
            time.sleep(13)
        else:
            print(f"❌ Failed to get Gemini result for review from {row.get('uni_name', 'Unknown Uni')}. Skipping.")

    return processed_records

# --- DATABASE INSERTION FUNCTION ---
def insert_records(records):
    """Inserts a list of processed review dictionaries into the PostgreSQL database."""
    from app import get_db_connection # Import the connector function from app.py to establish DB connection.
    
    conn = get_db_connection()
    if conn is None:
        print("❌ FATAL ERROR: Cannot insert data. Database connection failed.")
        return

    cursor = conn.cursor()
    # Define the columns that we are inserting data into in the `exchange_reviews` table.
    columns = (
        "uni_name, city, source_type, raw_language, academics_score, "
        "cost_score, social_score, accommodation_score, theme_summary, raw_review_text, reviewer_type, status, major"
    )
    
    insert_count = 0
    update_count = 0
    try:
        for record in records:
            # Prepare the tuple of values, ensuring the order matches the columns defined above.
            raw_language_guess = 'ar' if any('\u0600' <= c <= '\u06FF' for c in record['raw_review_text']) else 'en'
            
            # For AI-processed records, ensure reviewer_type is 'ai_processed' and status is 'approved'
            record_reviewer_type = 'ai_processed'
            record_status = 'approved'

            values = (
                record['uni_name'],
                record['city'],
                record.get('source_type', 'unknown'),
                raw_language_guess,
                record['academics_score'],
                record['cost_score'],
                record['social_score'],
                record['accommodation_score'],
                record['theme_summary'],
                record['raw_review_text'],
                record_reviewer_type,
                record_status,
                record['major'] # Include the major array
            )

            # Check if the record already exists based on uni_name, raw_review_text, and reviewer_type
            cursor.execute(
                "SELECT id FROM exchange_reviews WHERE uni_name = %s AND raw_review_text = %s AND reviewer_type = %s;",
                (record['uni_name'], record['raw_review_text'], record_reviewer_type)
            )
            existing_record = cursor.fetchone()

            if existing_record:
                # If record exists, update its AI-generated fields and status
                sql_update = """
                    UPDATE exchange_reviews
                    SET 
                        city = %s,
                        source_type = %s,
                        raw_language = %s,
                        academics_score = %s,
                        cost_score = %s,
                        social_score = %s,
                        accommodation_score = %s,
                        theme_summary = %s,
                        status = %s,
                        major = %s
                    WHERE id = %s;
                """
                cursor.execute(sql_update, (
                    record['city'],
                    record.get('source_type', 'unknown'),
                    raw_language_guess,
                    record['academics_score'],
                    record['cost_score'],
                    record['social_score'],
                    record['accommodation_score'],
                    record['theme_summary'],
                    record_status, # Update status to approved for AI-processed reviews
                    record['major'],
                    existing_record[0]
                ))
                update_count += 1
            else:
                # If record does not exist, insert a new one
                placeholders = ', '.join(['%s'] * len(columns.split(', ')))
                sql_insert = f"""
                    INSERT INTO exchange_reviews ({columns}) 
                    VALUES ({placeholders});
                """
                cursor.execute(sql_insert, values)
                insert_count += 1
        
        conn.commit()
        print(f"✅ SUCCESS: Successfully inserted {insert_count} new records and updated {update_count} existing records into the database.")
        
    except Exception as e:
        conn.rollback() # Rollback any partial inserts on error to maintain database consistency.
        print(f"❌ ERROR during insertion/update into database: {e}")
        
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

# --- Main execution block when the script is run directly ---
if __name__ == '__main__':
    print("--- Starting AI Processing Pipeline ---")
    processed_data = process_data_pipeline()
    
    if processed_data:
        print(f"Pipeline complete. Attempting to insert {len(processed_data)} records into the database...")
        insert_records(processed_data)
    else:
        print("No data processed. Database insertion skipped.")