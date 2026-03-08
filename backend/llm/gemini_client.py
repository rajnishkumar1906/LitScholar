"""
Gemini LLM client. API key from env GEMINI_API_KEY or backend config.
"""
# from google import genai
import google.genai as genai
from core.config import settings
import re

_client = None
_last_api_key = None

def _get_client():
    global _client, _last_api_key
    current_key = (settings.GEMINI_API_KEY or "").strip() or None
    
    if _client is None or current_key != _last_api_key:
        key_preview = f"{current_key[:6]}...{current_key[-4:]}" if current_key else "None"
        print(f"🔄 Initializing new Gemini client with key: {key_preview}")
        _client = genai.Client(api_key=current_key) if current_key else genai.Client()
        _last_api_key = current_key
    return _client

# GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_MODELS = [
    "gemini-1.5-flash", 
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash", 
    "gemini-1.5-flash-8b"
]

def clean_llm_output(text):
    """
    Remove unwanted characters from LLM response for clean web display
    """
    if not text:
        return text
        
    # Remove markdown symbols (*, _, #, `)
    text = re.sub(r'[*_#`]', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation (. , ! ? - ')
    text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
    
    # Fix common punctuation issues
    text = text.replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?')
    
    # Remove spaces before punctuation
    text = re.sub(r'\s+([\.\,\!\?\-\'])', r'\1', text)
    
    return text.strip()

def ask_gemini(prompt: str) -> str:
    """Send prompt to Gemini and return response text with model fallback."""
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        print("❌ GEMINI_API_KEY is missing in settings!")
        raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")
    
    last_error = ""
    for model in GEMINI_MODELS:
        try:
            print(f"📡 Calling Gemini with model: {model}...")
            client = _get_client()
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            # Get raw response
            raw_response = (response.text or "").strip()
            # Clean the response for web display
            cleaned_response = clean_llm_output(raw_response)
            
            if not cleaned_response:
                print(f"⚠️ Gemini returned an empty response for {model}")
                continue

            print(f"✅ Gemini response successful using {model}")
            return cleaned_response
            
        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            print(f"❌ [Gemini Error] Model {model} failed: {error_msg}")
            
            # Quota exceeded or model not found on one model might not mean all are exhausted
            if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                print(f"⚠️ Quota exceeded for {model}. Trying next model in fallback list...")
            elif "404" in error_msg or "not found" in error_msg.lower():
                print(f"⚠️ Model {model} not found or unsupported. Trying next...")
            
            # Continue to next model regardless of the error type
            continue
            
    # If we get here, everything failed
    print(f"‼️ All Gemini models failed in fallback chain. Last error: {last_error}")
    
    if "429" in last_error or "quota" in last_error.lower() or "limit" in last_error.lower():
        return "ERROR: All Gemini models reached their rate limits. Please try again in 1 minute."
        
    return f"ERROR: Gemini service currently unavailable. ({last_error})"