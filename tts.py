from flask import Flask, request, render_template, jsonify, send_from_directory
from gtts import gTTS
from deep_translator import GoogleTranslator
import os
import json

app = Flask(__name__)
STATIC_FOLDER = "static"
AUDIO_FOLDER = os.path.join(STATIC_FOLDER, "NewsAudio")
NEWS_FILE = os.path.join(STATIC_FOLDER, "news.json")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

def translate_text(text, target_lang):
    """Uses deep_translator for translation without requiring an API key."""
    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return translated
    except Exception as e:
        print("Translation Error:", str(e))
        return None

def text_to_speech(text, lang, news_index):
    """Converts text to speech and caches the result."""
    try:
        news_folder = os.path.join(AUDIO_FOLDER, f"news_{news_index}")
        os.makedirs(news_folder, exist_ok=True)

        filename = f"{lang}.mp3"
        output_path = os.path.join(news_folder, filename)

        if os.path.exists(output_path):
            return f"/static/NewsAudio/news_{news_index}/{filename}"

        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)

        return f"/static/NewsAudio/news_{news_index}/{filename}"
    except Exception as e:
        print("TTS Error:", str(e))
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/news')
def get_news():
    """Fetches news from the JSON file."""
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as file:
            news_data = json.load(file)
        return jsonify(news_data)
    except Exception as e:
        return jsonify({"error": "Could not load news", "details": str(e)}), 500

@app.route('/translate_tts', methods=['POST'])
def translate_tts():
    """Translates text and converts it to speech."""
    data = request.json
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    news_index = data.get("index", -1)

    if not text or news_index == -1:
        return jsonify({"error": "Invalid text or index"}), 400

    translated_text = translate_text(text, lang) if lang != "en" else text
    if not translated_text:
        return jsonify({"error": "Translation failed"}), 500

    audio_url = text_to_speech(translated_text, lang, news_index)
    if audio_url is None:
        return jsonify({"error": "Failed to generate audio"}), 500

    return jsonify({"audio_url": audio_url})

@app.route('/static/NewsAudio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
