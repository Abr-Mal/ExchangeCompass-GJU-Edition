import os
import json
import pandas as pd
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (including GEMINI_API_KEY)
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    exit()

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
            "theme_summary": {"type": "string", "description": "A 1-2 sentence English summary of the review's main point."}
        },
        "required": ["overall_sentiment", "academics_score", "cost_score", "social_score", "accommodation_score", "theme_summary"]
    }
    
    # 2. Craft the Multilingual Prompt (The Magic)
    prompt = f"""
    You are an expert student advisor analyzing feedback for {uni_name}. 
    Analyze the following review, which may be in English or Arabic. 
    Score each of the four categories from 1 (worst) to 5 (best) based only on the provided text.
    Translate the main point into a concise English summary.

    Review Text: "{review_text}"
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', # A fast, capable model
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            ),
        )
        # The response text will be a clean JSON string, which we parse
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Gemini API call failed: {e}")
        return None

def process_data_pipeline():
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