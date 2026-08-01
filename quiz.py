import os
import logging
from google import genai
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# ओरिजिनल जेमिनी क्लाइंट सेटअप
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables.")
    return genai.Client(api_key=api_key)

# ओरिजिनल कंटेंट जनरेशन फंक्शन
def generate_content_with_gemini(prompt_text, model_name="gemini-2.0-flash"):
    client = get_gemini_client()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt_text
    )
    return response.text

# ओरिजिनल क्विज़ भेजने का लॉजिक
async def generate_and_send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str = "Biology", count: int = 5):
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id and context.job:
        chat_id = context.job.chat_id

    try:
        prompt = (
            f"Generate {count} multiple-choice questions for NEET exam on the topic '{topic}'. "
            "Format each question clearly with options A, B, C, D and provide the correct answer at the end."
        )
        
        quiz_text = generate_content_with_gemini(prompt)
        
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=quiz_text)
            
    except Exception as e:
        error_msg = f"Failed to generate questions. Error: {e}"
        logger.error(error_msg)
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ माफ कीजिए, अभी API की लिमिट या किसी तकनीकी समस्या के कारण क्विज़ जनरेट नहीं हो पा रहा है। कुछ देर बाद कोशिश करें।")
