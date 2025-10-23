import os
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
    
    # 1. Define the Structured Output Schema (Pydantic style for clarity)
    # This is critical for getting clean, reliable data into your DB.
    response_schema = {
        "type": "object",
        "properties": {
            "overall_sentiment": {"type": "string", "description": "Positive, Neutral, or Negative."},
            "academics_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "cost_score": {"type": "integer", "description": "Score from 1 (expensive) to 5 (cheap)."},
            "social_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "accommodation_score": {"type": "integer", "description": "Score from 1 (difficult) to 5 (easy/good)."},
            "theme_summary": {"type": "string", "description": "A comprehensive narrative summary (around 250 words) covering academics, cost, social scene, and accommodation, including 1-2 direct quotes from the original review text to support the points."}
        },
        "required": ["overall_sentiment", "academics_score", "cost_score", "social_score", "accommodation_score", "theme_summary"]
    }
    
    # 2. Craft the Multilingual Prompt (The Magic)
    prompt = f"""
    You are an expert student advisor analyzing feedback for {uni_name}. 
    Your goal is to synthesize a detailed, balanced narrative review (approximately 250 words) for the university "{uni_name}". 
    
    The review must cover the four main aspects: Academics, Cost of Living, Social Scene, and Accommodation.
    
    Incorporate 1-2 direct, short quotes from the provided student feedback to illustrate or support your points. Ensure the summary is structured as a single narrative paragraph.
    
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
        # The response text will be a clean JSON string, which we parse
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return None

def process_data_pipeline():
    """Reads raw CSV data, cleans it, and processes reviews with Gemini."""

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw_survey_data.csv')
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'mock_reviews.html')

    all_raw_data = []

    # 1. READ DATA FROM CSV
    try:
        df_csv = pd.read_csv(csv_path)
        df_csv.rename(columns={
            'Timestamp': 'date_collected',
            'Which university are you rating?': 'uni_name',
            'City': 'city',
            'Cost of living': 'cost_score',
            'Social scene quality': 'social_score',
            'Accommodation ease (How easy it is to find a living space)': 'accommodation_score',
            'Please provide your overall experience or any additional comments about your univerisity': 'raw_review_text',
        }, inplace=True)
        # Convert DataFrame to a list of dictionaries
        all_raw_data.extend(df_csv.to_dict(orient='records'))

    except FileNotFoundError:
        print(f"❌ ERROR: Raw survey data not found at {csv_path}")

    # 2. READ DATA FROM MOCK HTML
    html_reviews = parse_html_reviews(html_path)
    all_raw_data.extend(html_reviews)

    if not all_raw_data:
        print("No data found from CSV or HTML. Returning empty list.")
        return []

    # Convert combined data to a DataFrame for easier processing
    df = pd.DataFrame(all_raw_data)

    processed_records = []

    # 3. ITERATE, PROCESS, and ENRICH
    for index, row in df.iterrows():
        # Skip reviews where the core text is missing
        if pd.isna(row['raw_review_text']):
            continue

        # Ensure you pass the correct data to Gemini's prompt:
        gemini_result = analyze_review_with_gemini(row['raw_review_text'], row['uni_name'])

        if gemini_result:
            record = {
                'uni_name': row['uni_name'],
                'city': row['city'], # Ensure 'city' column exists in your CSV or add it manually!
                'source_type': 'survey', 
                'raw_review_text': row['raw_review_text'],
                **gemini_result 
            }
            processed_records.append(record)
            print(f"Successfully processed: {row['uni_name']}")

    return processed_records

    # --- SIMULATE GETTING DATA FROM GOOGLE SHEET ---
    # NOTE: For now, manually create a small CSV/Excel file in your 'data/' folder 
    # that mimics your Google Sheet output for testing.

    # Data is simulated here (replace with actual Google Sheet/CSV read later)
    # The 'raw_review_text' contains the multilingual input for Gemini
    mock_raw_data = {
        'uni_name': ['LMU Munich', 'LMU Munich', 'TUHH Hamburg'],
        'raw_review_text': [
            "The academics were fantastic, very challenging but worth it. However, the rent here is criminal for a student.", 
            "الجامعة جيدة لكن صعوبة إيجاد سكن طلابي كانت مرهقة جداً.", # Arabic review
            "Social life was okay, good parks, but the professors were a bit dull."
        ],
        'city': ['Munich', 'Munich', 'Hamburg']
    }
    df = pd.DataFrame(mock_raw_data)
    
    processed_records = []
    for index, row in df.iterrows():
        gemini_result = analyze_review_with_gemini(row['raw_review_text'], row['uni_name'])
        
        if gemini_result:
            # Merge the result with the original data for the database insert
            record = {
                'uni_name': row['uni_name'],
                'city': row['city'],
                'source_type': 'survey',
                'raw_review_text': row['raw_review_text'],
                # Add the scores from Gemini
                **gemini_result 
            }
            processed_records.append(record)
            print(f"Successfully processed: {row['uni_name']}")
    
    return processed_records

if __name__ == '__main__':
    processed_data = process_data_pipeline()
    # Next step (Day 9): Insert this processed_data into PostgreSQL
    print("\n--- FINAL PROCESSED DATA SAMPLE ---")
    print(processed_data[:2])

    # Insert this function into your existing ai_processor.py file
def insert_records(records):
    """Inserts a list of processed review dictionaries into the PostgreSQL database."""
    from app import get_db_connection # Import the connector function from app.py
    
    conn = get_db_connection()
    if conn is None:
        print("FATAL ERROR: Cannot insert data. Database connection failed.")
        return

    cursor = conn.cursor()
    # Define the columns that we are inserting data into
    columns = (
        "uni_name, city, source_type, raw_language, academics_score, "
        "cost_score, social_score, accommodation_score, theme_summary, raw_review_text"
    )
    
    # Placeholder values for the SQL query (10 columns)
    placeholders = ', '.join(['%s'] * 10) 
    
    sql_insert = f"""
        INSERT INTO exchange_reviews ({columns}) 
        VALUES ({placeholders});
    """
    
    insert_count = 0
    try:
        for record in records:
            # Prepare the tuple of values, ensuring the order matches the columns defined above
            values = (
                record['uni_name'],
                record['city'],
                record.get('source_type', 'ai_simulated'), # Use 'ai_simulated' as default for testing
                'en' if any(c.isalpha() for c in record['raw_review_text']) and not any('\u0600' <= c <= '\u06FF' for c in record['raw_review_text']) else 'ar', # Simple language guess
                record['academics_score'],
                record['cost_score'],
                record['social_score'],
                record['accommodation_score'],
                record['theme_summary'],
                record['raw_review_text']
            )
            cursor.execute(sql_insert, values)
            insert_count += 1
        
        conn.commit()
        print(f"✅ SUCCESS: Successfully inserted {insert_count} records into the database.")
        
    except Exception as e:
        conn.rollback() # Undo any partial inserts on error
        print(f"❌ ERROR during insertion: {e}")
        
    finally:
        cursor.close()
        conn.close()


# --- Update the main execution block at the bottom of ai_processor.py ---
if __name__ == '__main__':
    print("--- Starting AI Processing Pipeline ---")
    processed_data = process_data_pipeline()
    
    if processed_data:
        print(f"Pipeline complete. Inserting {len(processed_data)} records...")
        insert_records(processed_data)
    else:
        print("No data processed. Database insertion skipped.")