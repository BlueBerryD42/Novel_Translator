import locale
import streamlit as st
import os
import requests
import random
from google.cloud import translate_v2 as translate
from datetime import datetime
from dotenv import load_dotenv
from plyer import notification


# Load environment variables
load_dotenv()

SUPPORTED_LANGS = ["en", "vi"]
LANG_NAMES = {
    "en": "English",
    "vi": "Vietnamese"
}

def init_session_state():
    session_defaults = {
        "translations": {},
        "processing": False,
        "source_text": "",
        "progress": 0,
        "resources": {"cpu": 0, "memory": 0},
        "source_lang": "en",
        "view_mode": "Side by Side",
        "quick_view": False,
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

st.set_page_config(page_title="API Translation App", page_icon="🌐")
init_session_state()

# Configuration
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"
MAX_CHUNK_SIZE = 4500

# Google Cloud Setup
def get_google_translate_client():
    try:
        return translate.Client.from_service_account_json('google-credentials.json')
    except Exception as e:
        raise RuntimeError(f"Google client error: {str(e)}")

def split_text(text, max_length=MAX_CHUNK_SIZE):
    """Splits text into smaller chunks, keeping words intact."""
    lines = text.split("\n")
    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += ("\n" if current_chunk else "") + line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def translate_with_google(text, target_lang):
    """Translates text using Google Translate API with chunking."""
    try:
        client = get_google_translate_client()
        text_chunks = split_text(text)

        translated_chunks = []
        for chunk in text_chunks:
            translated = client.translate(
                values=chunk,
                target_language=target_lang,
                format_='text'
            )
            translated_chunks.append(translated['translatedText'])

        return "\n".join(translated_chunks)
    except Exception as e:
        return f"Google Error: {str(e)}"

def translate_with_deepl(text, target_lang):
    """Translates text using DeepL API with chunking."""
    try:
        text_chunks = split_text(text)
        translated_chunks = []

        for chunk in text_chunks:
            response = requests.post(
                DEEPL_API_URL,
                data={
                    "auth_key": DEEPL_API_KEY,
                    "text": chunk,
                    "target_lang": target_lang.upper()
                }
            )
            response.raise_for_status()
            translated_chunks.append(response.json()["translations"][0]["text"])

        return "\n".join(translated_chunks)
    except Exception as e:
        return f"DeepL Error: {str(e)}"

def notify_completion():
    notification.notify(
        title="Translation Complete",
        message="Your translation process has finished successfully. 🎉",
        app_icon=r"C:\Users\ASUS\Pictures\ICO\12.ico",
        timeout=5
    )

import time
import psutil
import streamlit as st

import time
import streamlit as st

def handle_translation(src_text):
    """Improved translation flow with detailed progress and real-time updates to keep the user engaged."""
    if not src_text.strip():
        st.warning("Please input text to translate.")
        return

    st.session_state.processing = True
    st.session_state.source_text = src_text
    st.session_state.translations = {}

    progress_bar = st.progress(0)  # Initialize progress bar
    status_text = st.empty()  # Placeholder for status updates
    log_area = st.empty()  # Placeholder for verbose logs

    total_chars = len(src_text)
    start_time = time.time()

    try:
        with st.spinner("Processing translations..."):
            # Check credentials first
            if not DEEPL_API_KEY:
                raise ValueError("DeepL API key not found in .env file")

            if not os.path.exists('google-credentials.json'):
                raise FileNotFoundError("Google credentials file not found")

            log_area.text(f"📜 Source text length: {total_chars} characters")

            # Step 1: DeepL Translation
            start = time.time()
            status_text.text("🌐 Translating to English using DeepL...")
            en_translation = translate_with_deepl(src_text, "EN")
            deepl_elapsed = time.time() - start
            progress_bar.progress(33)  # Update to 33% after DeepL translation
            log_area.text(f"✅ DeepL translation completed in {deepl_elapsed:.2f} sec\n📄 Text length: {len(en_translation)} chars")
            if en_translation.startswith("DeepL Error"):
                raise ValueError(en_translation)
            st.session_state.translations["en"] = en_translation

            # Step 2: Google Translation
            start = time.time()
            status_text.text("🌏 Translating English to Vietnamese with Google...")
            vi_translation = translate_with_google(en_translation, "vi")
            google_elapsed = time.time() - start
            progress_bar.progress(66)  # Update to 66% after Google translation
            log_area.text(f"✅ Google translation done in {google_elapsed:.2f} sec\n📄 Text length: {len(vi_translation)} chars")
            if vi_translation.startswith("Google Error"):
                raise ValueError(vi_translation)
            st.session_state.translations["vi"] = vi_translation

            # Step 3: Finalizing
            progress_bar.progress(100)  # Update to 100% once the translations are complete
            status_text.text("✅ Finalizing translations...")

    except Exception as e:
        st.error(f"Translation failed: {str(e)}")
        st.session_state.processing = False
        return

    total_elapsed = time.time() - start_time
    st.session_state.processing = False
    notify_completion()
    progress_bar.empty()  # Remove progress bar
    status_text.text("✅ Translations complete! 🎉")

    # Provide detailed response time breakdown:
    st.write(f"⏱ DeepL translation took: {deepl_elapsed:.2f} seconds")
    st.write(f"⏱ Google translation took: {google_elapsed:.2f} seconds")
    st.write(f"📜 Total time taken: {total_elapsed:.2f} seconds for all translations")




def generate_export_content(format="txt"):
    """Generate export content in text or themed HTML format."""
    if format == "txt":
        content = [
            "=== Original Text ===",
            st.session_state.get("source_text", "No source text available"),
            "\n=== English Translation ===",
            st.session_state.translations.get("en", "No translation available"),
            "\n=== Vietnamese Translation ===",
            st.session_state.translations.get("vi", "No translation available")
        ]
        return "\n".join(content)

    elif format == "html":
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Translation Report</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background: linear-gradient(135deg, #2C3E50, #4A6FA5);
                    color: #E0E0E0;
                    margin: 0;
                    padding: 20px;
                    line-height: 1.6;
                }}
                h1 {{
                    text-align: center;
                    font-size: 28px;
                    background: linear-gradient(45deg, #7D4F95, #5A2D67);
                    color: white;
                    padding: 10px;
                    border-radius: 10px;
                    box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.5);
                    margin-bottom: 20px;
                }}
                .container {{
                    display: flex;
                    justify-content: space-between;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .box {{
                    flex: 1;
                    padding: 15px;
                    background: rgba(37, 37, 37, 0.8);
                    border-radius: 10px;
                    box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.5);
                    border: 2px solid #7D4F95;
                }}
                h2 {{
                    font-size: 20px;
                    color: #C0A3E5;
                    border-bottom: 2px solid #7D4F95;
                    padding-bottom: 5px;
                    margin-top: 0;
                }}
                .original-text {{
                    padding: 15px;
                    background: rgba(34, 34, 34, 0.8);
                    border-radius: 15px;
                    font-size: 18px;
                    text-align: center;
                    font-weight: bold;
                    border: 2px solid #5A2D67;
                    margin-bottom: 20px;
                }}
                .decorative-box {{
                    padding: 15px;
                    text-align: center;
                    font-size: 16px;
                    color: #C0A3E5;
                    background: rgba(30, 30, 30, 0.8);
                    border-radius: 10px;
                    border: 2px dotted #7D4F95;
                    position: relative;
                }}
                .decorative-box::after {{
                    content: '🐾';
                    position: absolute;
                    top: -10px;
                    right: -10px;
                    font-size: 24px;
                    color: #7D4F95;
                }}
                .button-container {{
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                    margin-bottom: 20px;
                }}
                .edit-button, .save-button {{
                    background-color: #7D4F95;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.3s ease;
                }}
                .edit-button:hover, .save-button:hover {{
                    background-color: #5A2D67;
                }}
                [contenteditable="true"] {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 10px;
                    border-radius: 5px;
                    border: 1px solid #7D4F95;
                    outline: none;
                    white-space: pre-line;
                }}
                [contenteditable="false"] {{
                    white-space: pre-line;
                }}
            </style>
        </head>
        <body>
        <div class="button-container">
            <button class="edit-button" onclick="toggleEditMode()">✎ Edit</button>
            <button class="save-button" onclick="saveContent()">💾 Save</button>
        </div>
        <h1>Translation Report</h1>
        <div class="container">
            <div class="box">
                <h2>English Translation</h2>
                <div id="en" contenteditable="false">{en}</div>
            </div>
            <div class="box">
                <h2>Vietnamese Translation</h2>
                <div id="vi" contenteditable="false">{vi}</div>
            </div>
        </div>
        <div class="original-text">
            <h2>Original Text</h2>
            <div id="source" contenteditable="false">{source}</div>
        </div>
        <div class="decorative-box">
            <p>Generated for better readability! 🐾</p>
        </div>
        <script>
            function toggleEditMode() {{
                const elements = document.querySelectorAll('[contenteditable]');
                const btn = document.querySelector('.edit-button');
                const isEditing = btn.textContent === '✎ Edit';

                elements.forEach(element => {{
                    element.contentEditable = isEditing;
                    element.style.border = isEditing ? '1px solid #7D4F95' : 'none';
                }});
                btn.textContent = isEditing ? '✖ Cancel' : '✎ Edit';
            }}

            function saveContent() {{
                const content = {{
                    en: document.getElementById('en').innerText,
                    vi: document.getElementById('vi').innerText,
                    source: document.getElementById('source').innerText
                }};

                // Create downloadable file
                const blob = new Blob([JSON.stringify(content, null, 2)], {{ type: 'text/plain' }});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = 'translation_report.txt';
                a.click();

                alert('Content saved successfully!');
            }}
        </script>
        </body>
        </html>
        """.format(
            en=st.session_state.translations.get("en", "No translation available"),
            vi=st.session_state.translations.get("vi", "No translation available"),
            source=st.session_state.get("source_text", "No source text available")
        )

        return html_content

def get_google_usage():
    return "N/A (Google does not provide direct usage stats)"

locale.setlocale(locale.LC_ALL, '')

def get_deepl_usage():
    try:
        response = requests.get(
            "https://api-free.deepl.com/v2/usage",
            headers={"Authorization": f"DeepL-Auth-Key {os.getenv('DEEPL_API_KEY')}"}
        )
        if response.status_code == 200:
            data = response.json()
            used = data['character_count']
            limit = data['character_limit']
            remaining = limit - used

            used_formatted = locale.format_string("%d", used, grouping=True)
            limit_formatted = locale.format_string("%d", limit, grouping=True)
            remaining_formatted = locale.format_string("%d", remaining, grouping=True)

            return f"{used_formatted} / {limit_formatted}\n\n🟢 Remaining: {remaining_formatted} characters left"
        return "⚠️ Error fetching DeepL usage"
    except Exception:
        return "⚠️ DeepL API key missing or invalid"

# Sidebar Configuration
with st.sidebar:
    st.markdown("## 🌍 API Translation Dashboard")
    st.info("Manage your translation services efficiently!")

    st.markdown("### 🔑 API Credentials Setup")
    st.markdown("""
    Configure your API keys to enable translation:
    - **DeepL API**: Get a key from [DeepL](https://www.deepl.com/pro#developer).
    - **Google Cloud API**: Follow [this guide](https://cloud.google.com/translate/docs/setup) to set up.
    """)

    st.markdown("---")
    st.markdown("### 📊 API Usage Statistics")

    google_usage = get_google_usage()
    deepl_usage = get_deepl_usage()

    st.text(f"🔵 Google Translate Usage: {google_usage}")
    st.text(f"🟣 DeepL Usage: {deepl_usage}")

    st.markdown("---")
    st.markdown("### ⚙️ Translation Setup")
    st.markdown("- **DeepL** → Translates text **to English**.")
    st.markdown("- **Google Translate** → Converts **English to Vietnamese**.")

    st.markdown("---")
    st.markdown("### 🧠 Language Fun Fact of the Day")

    fun_facts = [
        "Did you know? The longest word in English has **189,819 letters**!",
        "The word 'set' has **the most definitions** in the English language!",
        "In Vietnamese, 'hello' is **'Xin chào'** (pronounced: *seen chow*).",
        "The sentence *'The quick brown fox jumps over the lazy dog'* uses **every letter**!"
    ]
    st.markdown(f"📚 **Fun Fact**: {random.choice(fun_facts)}")

    st.markdown("---")
    st.markdown("### ❓ Need Help?")
    st.markdown("Sorry you are on your own! Too lazy to provide help")

    st.markdown("---")
    st.success("🚀 **You're all set! Let's start translating!**")

# Main Interface
if "quick_view" not in st.session_state:
    st.session_state.quick_view = False

def toggle_reading_mode():
    st.session_state.quick_view = not st.session_state.quick_view

reading_mode = st.toggle(
    "Reading Mode",
    value=st.session_state.quick_view,
    key="reading_mode_toggle",
    on_change=toggle_reading_mode
)

if not st.session_state.quick_view:
    st.title("🌐 API-Powered Translator")
    st.caption("Using DeepL and Google Cloud Translation APIs")

if not st.session_state.quick_view:
    with st.container():
        input_text = st.text_area("Enter your text:", key="input_text", height=200)
        translate_btn = st.button(
            "Translate",
            disabled=not (DEEPL_API_KEY and translate.Client.from_service_account_json('google-credentials.json')),
            use_container_width=True
        )

    if translate_btn and input_text:
        handle_translation(input_text)

# Translation display (works in both modes)
if st.session_state.get("translations"):
    # View mode selector
    view_mode = st.selectbox(
        "Display Mode",
        ["Side by Side", "English Only","Vietnamese Only"],
        index=0,
        key="view_mode"
    )

    # Update translation display logic
    if view_mode == "Side by Side":
        cols = st.columns(2)
        with cols[0]:
            st.markdown("### English")
            st.text_area("", value=st.session_state.translations.get("en", ""), height=300)
        with cols[1]:
            st.markdown("### Vietnamese (Refined)")
            st.text_area("", value=st.session_state.translations.get("vi", ""), height=300)
    else:
        lang_map = {
            "English Only": "en",
            "Vietnamese Only": "vi",
        }
        selected_lang = lang_map[view_mode]
        st.text_area(
            "",
            value=st.session_state.translations.get(selected_lang, ""),
            height=400
        )
    # Button to choose format
    export_format = st.selectbox("Choose export format", ["Text", "HTML"])

    # Determine file extension and MIME type
    if export_format == "Text":
        file_content = generate_export_content("txt")
        file_ext = "txt"
        mime_type = "text/plain"
    elif export_format == "HTML":
        file_content = generate_export_content("html")
        file_ext = "html"
        mime_type = "text/html"

    # Export button
    st.download_button(
        label="📥 Export Translations",
        data=file_content,
        file_name=f"translations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}",
        mime=mime_type,
        use_container_width=True
    )

# Empty state for normal mode
elif not st.session_state.quick_view:
    st.info("Enter text and click Translate to see results")

# Error handling (normal mode only)
if not st.session_state.quick_view:
    if not DEEPL_API_KEY:
        st.error("Missing DeepL API key in .env file")
    if not translate.Client.from_service_account_json('google-credentials.json'):
        st.error("Missing Google credentials in .json file")

# Footer (Normal mode only)
if not st.session_state.quick_view:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #777; font-size: 14px;'>
        <p><strong>Crafted with ☕, Debugging, and Existential Crises</strong></p>
        <p>Built in page translation suck 🎆</p>
        <p>Transforming languages, one API call at a time! 🚀</p>
    </div>
    """, unsafe_allow_html=True)
