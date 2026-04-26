# gemini_service.py
import google.genai as genai
import re
from core.config import settings

_client = None
_last_api_key = None


def _get_client():
    """Initialize or reuse Gemini client when API key changes."""
    global _client, _last_api_key
    
    current_key = (settings.GEMINI_API_KEY or "").strip() or None
    
    if _client is None or current_key != _last_api_key:
        key_preview = f"{current_key[:8]}...{current_key[-4:]}" if current_key else "None"
        print(f"🔄 Initializing new Gemini client with key: {key_preview}")
        
        _client = genai.Client(api_key=current_key) if current_key else genai.Client()
        _last_api_key = current_key
    
    return _client


# Current recommended models (April 2026)
# Order: Flash-Lite first (best free tier limits for new keys) → Flash → Pro
GEMINI_MODELS = [
    "gemini-2.5-flash-lite",      # Best for new/free tier keys - highest limits + fast
    "gemini-2.5-flash",           # Good balance of speed and quality
    "gemini-2.5-pro",             # More capable (stricter quotas)
    "gemini-3-flash",             # Newer generation (if available on your key)
    "gemini-3.1-flash-lite",      # Latest lite variant (preview may be available)
]


def clean_llm_output(text: str) -> str:
    """
    Clean LLM response for web display.
    Removes excessive markdown/symbols while keeping readability.
    """
    if not text:
        return ""

    # Remove common markdown symbols
    text = re.sub(r'[*_#`~]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Keep basic punctuation but clean spacing around it
    text = re.sub(r'\s+([.,!?\'-])', r'\1', text)
    text = text.replace(' .', '.').replace(' ,', ',')
    
    return text.strip()


def ask_gemini(prompt: str) -> str:
    """Send prompt to Gemini with smart fallback and improved error handling."""
    
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        print("❌ GEMINI_API_KEY is missing in settings!")
        raise ValueError("GEMINI_API_KEY is not set. Add it to your .env file.")

    print(f"🔑 Using Gemini API key (starts with): {api_key[:8]}...")

    last_error = ""
    
    for model in GEMINI_MODELS:
        try:
            print(f"📡 Calling Gemini with model: {model}...")

            client = _get_client()
            
            response = client.models.generate_content(
                model=model,           # Do NOT add "models/" prefix
                contents=prompt
            )

            raw_response = (response.text or "").strip()
            print(f"DEBUG: Gemini raw response: {raw_response}")
            
            if not raw_response:
                print(f"⚠️ Empty response from {model}, trying next...")
                continue

            # Return raw response without cleaning for assistant answers
            # The assistant service will handle its own cleaning if needed
            print(f"✅ Success using model: {model}")
            return raw_response

        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            
            print(f"❌ Model {model} failed: {error_msg[:250]}...")

            if "429" in error_msg or "quota" in error_msg.lower() or "limit" in error_msg.lower():
                print(f"⚠️ Quota exceeded for {model}. Trying next model...")
            elif "404" in error_msg or "not found" in error_msg.lower():
                print(f"⚠️ Model {model} not available on this key. Trying next...")
            else:
                print(f"⚠️ Unexpected error with {model}. Trying next...")

            continue  # Try next model

    # If we reach here, all models failed
    print(f"‼️ All Gemini models failed in fallback chain. Last error: {last_error}")

    if "429" in last_error or "quota" in last_error.lower() or "limit" in last_error.lower():
        return (
            "ERROR: Gemini free tier quota exceeded. "
            "Please wait 60 seconds and try again. "
            "New keys have limited requests per minute."
        )

    return f"ERROR: Gemini service is currently unavailable. ({last_error[:200]})"