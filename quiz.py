import os
import logging
from google import genai
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ==========================================
# 1. Multi-Key Fallback Client Setup
# ==========================================
def get_gemini_client():
    """
    यह फंक्शन पहले Primary Key (GEMINI_API_KEY) से कनेक्ट करने की कोशिश करता है।
    अगर वह काम नहीं करती या उस पर लिमिट खत्म हो जाती है, तो यह 
    अटोमैटिकली Fallback Key (GEMINI_API_KEY_2) पर स्विच हो जाता है।
    """
    primary_key = os.getenv("GEMINI_API_KEY")
    fallback_key = os.getenv("GEMINI_API_KEY_2")
    
    # पहले Primary Key से कोशिश करें
    if primary_key:
        try:
            client = genai.Client(api_key=primary_key)
            return client
        except Exception as e:
            logger.warning(f"⚠️ Primary GEMINI_API_KEY failed: {e}. Trying fallback...")
            
    # अगर Primary फेल हो या न हो, तो Fallback Key इस्तेमाल करें
    if fallback_key:
        try:
            logger.info("🔄 Switching to GEMINI_API_KEY_2...")
            client = genai.Client(api_key=fallback_key)
            return client
        except Exception as e:
            logger.error(f"❌ Fallback GEMINI_API_KEY_2 also failed: {e}")
            raise e
            
    # अगर दोनों में से कोई की न मिले
    raise ValueError("❌ Neither GEMINI_API_KEY nor GEMINI_API_KEY_2 is set or working in environment variables.")


# ==========================================
# 2. Content Generation with Multi-Key Support
# ==========================================
def generate_content_with_gemini(prompt_text, model_name="gemini-2.0-flash"):
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text
        )
        return response.text
    except Exception as e:
        logger.error(f"Failed to generate content. Error: {e}")
        raise e


# ==========================================
# 3. Quiz Generation Logic
# ==========================================
async def generate_and_send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str = "Biology", count: int = 5):
    """
    NEET क्विज़ जेनरेट करने और टेलीग्राम पर भेजने का मुख्य फंक्शन।
    """
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id and context.job:
        chat_id = context.job.chat_id

    try:
        prompt = (
            f"Generate {count} multiple-choice questions for NEET exam on the topic '{topic}'. "
            "Format each question clearly with options A, B, C, D and provide the correct answer at the end."
        )
        
        # जेमिनी सेफली कॉल होगा (दोनों कीज़ के फॉलबैक के साथ)
        quiz_text = generate_content_with_gemini(prompt)
        
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=quiz_text)
            
    except Exception as e:
        error_msg = f"Failed to generate questions. Error: {e}"
        logger.error(error_msg)
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ माफ कीजिए, अभी API की लिमिट या किसी तकनीकी समस्या के कारण क्विज़ जनरेट नहीं हो पा रहा है। कुछ देर बाद कोशिश करें।")
