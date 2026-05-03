import os
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'election-nav-secret-2026')

# --- API Keys ---
def _clean_key(k):
    return k.strip().strip('"').strip("'") if k else ''

GEMINI_API_KEY    = _clean_key(os.getenv('GEMINI_API_KEY', ''))
OPENROUTER_API_KEY = _clean_key(os.getenv('OPENROUTER_API_KEY', ''))
MAPS_API_KEY       = _clean_key(os.getenv('GOOGLE_MAPS_API_KEY', ''))

# Configure Gemini if key exists
gemini_available = False
if GEMINI_API_KEY and GEMINI_API_KEY not in ('your_gemini_api_key_here', 'PASTE_YOUR_API_KEY_HERE'):
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_available = True
        logger.info("✅ Gemini API configured.")
    except Exception as e:
        logger.warning(f"Gemini config failed: {e}")

# Configure OpenRouter if key exists
openrouter_available = False
if OPENROUTER_API_KEY and OPENROUTER_API_KEY not in ('your_openrouter_key_here', ''):
    openrouter_available = True
    logger.info("✅ OpenRouter API configured.")

if not gemini_available and not openrouter_available:
    logger.warning("⚠️  No AI provider configured. Chat will not work.")


# ─── System Prompt ────────────────────────────────────────────────────────────

def get_system_instruction(language="English", user_context="General Voter"):
    """Build a context-aware, persona-based system prompt for the AI."""

    persona_map = {
        "First-Time Voter": (
            "The user is a FIRST-TIME VOTER in India. Use extremely simple language. "
            "Always start by reminding them to check their name on the Electoral Roll at voters.eci.gov.in. "
            "Explain ECI, EPIC (Voter ID card), and polling booths in plain terms."
        ),
        "Overseas/Absentee Voter": (
            "The user is an OVERSEAS or ABSENTEE voter. Focus on overseas voter registration under the "
            "Representation of the People Act 1950, Postal Ballot procedures, NRI voting rights, "
            "and ECI's overseas voter registration portal."
        ),
        "Accessibility Needs": (
            "The user has ACCESSIBILITY NEEDS. Highlight PwD voter facilities, wheelchair-accessible "
            "polling booths, home voting for seniors 85+, the Saksham app, and voter assistance at booths."
        ),
    }
    context_logic = persona_map.get(
        user_context,
        "The user is a general voter in India. Provide standard election information relevant to Indian elections."
    )

    return (
        f'You are the "Smart Election Navigator" — a non-partisan, professional AI assistant for the '
        f'"Election Process Education" vertical, focused on INDIA\'s electoral system run by the '
        f'Election Commission of India (ECI).\n\n'
        f'STRICT RULES:\n'
        f'1. NON-PARTISANSHIP: NEVER endorse any party (BJP, INC, AAP, etc.), candidate, or ideology.\n'
        f'2. PERSONA CONTEXT: {context_logic}\n'
        f'3. ACCURACY: Give only factual information. Cite ECI, election laws, or Voter Helpline 1950 when relevant.\n'
        f'4. SAFETY: Refuse political debate. Redirect to voting logistics only.\n'
        f'5. LANGUAGE: Respond ENTIRELY in {language}. Do NOT mix languages.\n\n'
        f'Tone: Friendly, clear, encouraging, and professional.'
    )


# ─── AI Provider: Gemini Direct ───────────────────────────────────────────────

def _try_gemini(user_message, system_instruction):
    """Try calling Google Gemini API directly."""
    import google.generativeai as genai
    GEMINI_MODELS = ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-2.5-flash"]

    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=512,
                )
            )
            response = model.generate_content(user_message)
            logger.info(f"✅ Gemini response via {model_name}")
            return response.text
        except Exception as e:
            err = str(e)
            if '429' in err or 'quota' in err.lower() or 'ResourceExhausted' in type(e).__name__:
                logger.warning(f"⏳ Gemini quota hit on {model_name}, trying next...")
                continue
            elif 'SAFETY' in err.upper() or 'BlockedPrompt' in type(e).__name__:
                return None  # Safety block — don't retry
            else:
                logger.error(f"Gemini error on {model_name}: {type(e).__name__}: {e}")
                return None
    return None  # All Gemini models exhausted


# ─── AI Provider: OpenRouter (Google Gemini via OpenRouter) ───────────────────

def _try_openrouter(user_message, system_instruction):
    """Call Google Gemini via OpenRouter using raw HTTP requests."""
    import requests

    OPENROUTER_MODELS = [
        "google/gemini-2.0-flash-lite-001",
        "google/gemini-2.0-flash-001",
        "google/gemini-flash-1.5",
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "Smart Election Navigator",
    }

    for model_name in OPENROUTER_MODELS:
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user",   "content": user_message},
                ],
                "max_tokens": 512,
                "temperature": 0.4,
            }
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if r.status_code == 200:
                text = r.json()["choices"][0]["message"]["content"]
                logger.info(f"✅ OpenRouter response via {model_name}")
                return text
            elif r.status_code in (429, 503):
                logger.warning(f"⏳ OpenRouter rate limit on {model_name}, trying next...")
                continue
            else:
                logger.error(f"OpenRouter HTTP {r.status_code} on {model_name}: {r.text[:200]}")
                continue
        except Exception as e:
            logger.error(f"OpenRouter exception on {model_name}: {type(e).__name__}: {e}")
            continue
    return None


# ─── Master Chat Function ─────────────────────────────────────────────────────

def get_chat_response(user_message, language="English", user_context="General Voter"):
    """Try Gemini first, fall back to OpenRouter (also using a Google model)."""

    if not gemini_available and not openrouter_available:
        return (
            "⚠️ No AI provider is configured. Please add your GEMINI_API_KEY or "
            "OPENROUTER_API_KEY to the .env file and restart the server."
        )

    system_instruction = get_system_instruction(language, user_context)
    response_text = None

    # 1. Try Gemini Direct
    if gemini_available:
        response_text = _try_gemini(user_message, system_instruction)
        if response_text:
            return response_text
        logger.warning("Gemini unavailable, falling back to OpenRouter...")

    # 2. Fallback: OpenRouter (Google Gemini model)
    if openrouter_available:
        response_text = _try_openrouter(user_message, system_instruction)
        if response_text:
            return response_text

    # 3. Both failed
    return (
        "⚠️ The AI assistant is temporarily unavailable due to API quota limits. "
        "Please try again in a few minutes, or check your API keys at "
        "https://aistudio.google.com and https://openrouter.ai/keys."
    )


# ─── Flask Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Serve the main dashboard."""
    return render_template('index.html', maps_api_key=MAPS_API_KEY)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Secure proxy endpoint — handles AI provider routing."""
    data = request.get_json(silent=True)

    if not data or not data.get('message', '').strip():
        return jsonify({'error': 'A non-empty message is required.'}), 400

    user_message = data['message'].strip()
    language    = data.get('language', 'English')
    user_context = data.get('context', 'General Voter')

    if len(user_message) > 1000:
        return jsonify({'error': 'Message too long. Keep it under 1000 characters.'}), 400

    logger.info(f"Chat | context={user_context} | lang={language} | msg={user_message[:40]!r}")
    ai_response = get_chat_response(user_message, language, user_context)

    return jsonify({'response': ai_response})


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found.'}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error.'}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🚀 Smart Election Navigator on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
