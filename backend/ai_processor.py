import os
import json
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.genai import types 
from google.genai.client import Client
from dotenv import load_dotenv

# --- Configuration & Initialization ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Import Database Connection (FIXED) ---
# Importing necessary function from app.py where it is now centralized
from app import get_db_connection 

# --- Initialize Gemini Client (Exported as 'client') ---
try:
    client = Client(api_key=GEMINI_API_KEY) 
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    exit()

# --- 1. Database Helper Functions ---

def review_exists(conn, review_text):
    """Checks if a review with the exact text already exists in the database."""
    cursor = conn.cursor()
    try:
        if pd.isna(review_text) or not review_text.strip():
            return True 
        
        cursor.execute(
            "SELECT 1 FROM exchange_reviews WHERE raw_review_text = %s;", 
            (review_text,)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
    except Exception as e:
        print(f"Error checking review existence: {e}. Defaulting to skip.")
        cursor.close()
        return True 

def insert_records(records):
    """Inserts a list of processed review dictionaries into the PostgreSQL database."""
    
    conn = get_db_connection()
    if conn is None:
        print("FATAL ERROR: Cannot insert data. Database connection failed.")
        return

    cursor = conn.cursor()
    
    # 1. DEFINE COLUMNS (10 core columns + processed_date)
    columns = (
        "uni_name, city, source_type, raw_language, academics_score, "
        "cost_score, social_score, accommodation_score, theme_summary, raw_review_text, processed_date"
    )
    
    # 2. DEFINE PLACEHOLDERS (10 placeholders for Python values + NOW() for date)
    placeholders = ', '.join(['%s'] * 10) 
    
    sql_insert = f"""
        INSERT INTO exchange_reviews ({columns}) 
        VALUES ({placeholders}, NOW()); 
    """
    
    insert_count = 0
    try:
        for record in records:
            values = (
                record['uni_name'],
                record['city'],
                record.get('source_type', 'ai_simulated'),
                record['raw_language'], 
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
        conn.rollback() 
        print(f"❌ ERROR during insertion: {e}")
        
    finally:
        cursor.close()
        conn.close()

# --- 2. Gemini Processor Function ---

def analyze_review_with_gemini(review_text, uni_name):
    """Sends the review to Gemini for ABSA and structured JSON return."""
    
    response_schema = {
        "type": "object",
        "properties": {
            "overall_sentiment": {"type": "string", "description": "Positive, Neutral, or Negative."},
            "academics_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "cost_score": {"type": "integer", "description": "Score from 1 (expensive) to 5 (cheap)."},
            "social_score": {"type": "integer", "description": "Score from 1 (poor) to 5 (excellent)."},
            "accommodation_score": {"type": "integer", "description": "Score from 1 (difficult) to 5 (easy/good)."},
            "theme_summary": {"type": "string", "description": "A 1-2 sentence English summary of the review's main point."}
        },
        "required": ["overall_sentiment", "academics_score", "cost_score", "social_score", "accommodation_score", "theme_summary"]
    }
    
    prompt = f"""
    You are an expert student advisor analyzing feedback for {uni_name}. 
    Analyze the following review, which may be in English or Arabic. 
    Score each of the four categories from 1 (worst) to 5 (best) based only on the provided text.
    Translate the main point into a concise English summary.

    Review Text: "{review_text}"
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            ),
        )
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return None

# --- 3. Scraper Function (Reads Local Mock) ---

def scrape_forum_reviews():
    """Reads mock HTML file content and parses the structure using BeautifulSoup."""
    scraped_records = []
    
    local_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'mock_reviews.html')

    try:
        with open(local_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        review_posts = soup.find_all('div', class_='uni-review-card') 
        
        for post in review_posts:
            uni_name = post.find('h4', class_='uni-name').text.strip()
            city_name = post.find('p', class_='uni-city').text.strip()
            review_text = post.find('p', class_='review-body').text.strip()

            if review_text and uni_name:
                scraped_records.append({
                    'uni_name': uni_name,
                    'city': city_name,
                    'raw_review_text': review_text,
                    'source_type': 'scraped'
                })
        
        print(f"Scraper: Successfully extracted {len(scraped_records)} reviews from mock HTML.")
        return scraped_records

    except FileNotFoundError:
        print(f"Scraper Error: Mock HTML file not found at {local_html_path}. Skipping scraped data load.")
        return []
    except Exception as e:
        print(f"Scraper Parsing Error: {e}")
        return []


# --- 4. Main Pipeline Function (Consolidated) ---

def process_data_pipeline():
    """Reads all data sources, processes new reviews with Gemini, and filters for new records."""
    
    conn = get_db_connection()
    if conn is None:
        print("Database not available. Cannot run pipeline.")
        return []

    # 1. --- LOAD SURVEY DATA (High Trust) ---
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw_survey_data.csv')

    try:
        df_survey = pd.read_csv(csv_path)

        # RENAME COLUMNS (MUST MATCH YOUR CSV HEADERS EXACTLY)
        df_survey.rename(columns={
            'Timestamp': 'date_collected', 
            'Which university are you rating?': 'uni_name', 
            'City': 'city', 
            'Cost of living': 'cost_score',
            'Social scene quality': 'social_score',
            'Accommodation ease (How easy it is to find a living space)': 'accommodation_score',
            'Please provide your overall experience or any additional comments about your univerisity': 'raw_review_text', 
        }, inplace=True)
        df_survey['source_type'] = 'survey'
        survey_records = df_survey.to_dict('records') 

    except FileNotFoundError:
        print(f"❌ ERROR: Raw survey data not found at {csv_path}. Skipping survey load.")
        survey_records = []
    
    # 2. --- LOAD SCRAPED DATA (High Volume/Context) ---
    scraped_records = scrape_forum_reviews()
    
    # 3. --- COMBINE ALL RAW DATA ---
    all_raw_data = survey_records + scraped_records
    
    # 4. --- INCREMENTAL FILTERING & PROCESSING ---
    
    processed_records = []
    
    for record_in in all_raw_data:
        review_text = record_in.get('raw_review_text')
        uni_name = record_in.get('uni_name')
        
        if pd.isna(review_text) or not review_text.strip() or not uni_name:
            continue
        
        # Check if review already exists in DB (Incremental Check)
        if review_exists(conn, review_text):
            print(f"Skipping: Review already processed for {uni_name}.")
            continue
        
        # PROCESS NEW REVIEW WITH GEMINI
        gemini_result = analyze_review_with_gemini(review_text, uni_name)
        
        if gemini_result:
            # FINAL RECORD CONSTRUCTION: All 10 keys for insertion
            record_out = {
                'uni_name': uni_name,
                'city': record_in.get('city', 'Unknown City'),
                'source_type': record_in.get('source_type', 'unknown'),
                'raw_review_text': review_text,
                
                'raw_language': 'en' if any(c.isalpha() for c in review_text) and not any('\u0600' <= c <= '\u06FF' for c in review_text) else 'ar',

                'academics_score': gemini_result.get('academics_score', 3), 
                'cost_score': gemini_result.get('cost_score', 3),
                'social_score': gemini_result.get('social_score', 3),
                'accommodation_score': gemini_result.get('accommodation_score', 3),
                'theme_summary': gemini_result.get('theme_summary', 'N/A')
            }
            
            processed_records.append(record_out)
            print(f"Successfully processed NEW review for: {uni_name}")

    conn.close()
    return processed_records


# --- 5. Main Execution Block ---

if __name__ == '__main__':
    print("--- Starting AI Processing Pipeline ---")
    processed_data = process_data_pipeline()
    
    if processed_data:
        print(f"Pipeline complete. Inserting {len(processed_data)} records...")
        insert_records(processed_data)
    else:
        print("No new data to insert. Database insertion skipped.")