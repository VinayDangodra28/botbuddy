import google.generativeai as genai
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- API KEY CONFIG ---
def initialize_gemini(api_key: str):
    try:
        # Only use the provided api_key, do not use any hardcoded value
        genai.configure(api_key=api_key)
        logger.info("Gemini API initialized successfully.")
    except Exception as e:
        logger.error("Failed to configure Gemini API", exc_info=True)
        raise

# --- SEND TO GEMINI ---
def send_to_gemini(prompt: str, api_key: str) -> str:
    try:
        # Configure Gemini API with the provided key
        initialize_gemini(api_key)

        # Build prompt
        full_prompt_parts = []
        user_prompt = "User has asked: " + prompt
        full_prompt_parts.append(user_prompt)
        full_prompt = "\n\n".join(full_prompt_parts)

        # Load and run model
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        response = gemini_model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        logger.error("Error in send_to_gemini", exc_info=True)
        return "Sorry, something went wrong while getting a response from Gemini."
