from flask import Flask, request, render_template, jsonify, send_from_directory
from google.cloud import translate_v2 as translate
from gtts import gTTS
import os
import json

app = Flask(__name__)
STATIC_FOLDER = "static"
AUDIO_FOLDER = os.path.join(STATIC_FOLDER, "NewsAudio")
NEWS_FILE = os.path.join(STATIC_FOLDER, "news.json")

os.makedirs(AUDIO_FOLDER, exist_ok=True)

SUPPORTED_LANGUAGES = ["en", "hi", "bn", "ta", "te", "mr", "gu", "kn", "ml"]

# Initialize Google Cloud Translation Client
translate_client = translate.Client()

def translate_text(text, target_lang):
    try:
        result = translate_client.translate(text, target_language=target_lang)
        return result["translatedText"]
    except Exception as e:
        print("Translation Error:", str(e))
        return None

def text_to_speech(text, lang, news_index):
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
    try:
        with open(NEWS_FILE, 'r', encoding='utf-8') as file:
            news_data = json.load(file)
        return jsonify(news_data)
    except Exception as e:
        return jsonify({"error": "Could not load news", "details": str(e)}), 500

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")

    if not text or lang not in SUPPORTED_LANGUAGES:
        return jsonify({"error": "Invalid text or unsupported language"}), 400

    translated_text = translate_text(text, lang)
    if not translated_text:
        return jsonify({"error": "Translation failed"}), 500

    return jsonify({"translated_text": translated_text})

@app.route('/translate_tts', methods=['POST'])
def translate_tts():
    data = request.json
    text = data.get("text", "").strip()
    lang = data.get("lang", "en")
    news_index = data.get("index", -1)

    if not text or lang not in SUPPORTED_LANGUAGES or news_index == -1:
        return jsonify({"error": "Invalid text, language, or index"}), 400

    audio_url = text_to_speech(text, lang, news_index)
    if audio_url is None:
        return jsonify({"error": "Failed to generate audio"}), 500

    return jsonify({"audio_url": audio_url})

@app.route('/static/NewsAudio/<path:filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
