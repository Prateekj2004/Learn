import os
import pytesseract
import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from io import BytesIO
from flask_cors import CORS
from huggingface_hub import InferenceClient
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64
from langdetect import detect
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Hugging Face client (DeepSeek-R1-0528)
client = InferenceClient(
    model="deepseek-ai/DeepSeek-R1-0528",
    api_key=os.environ["HF_TOKEN"]
)

# Helper to send prompt to DeepSeek
def ask_deepseek(prompt):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
    )
    full = response.choices[0].message.content.strip()
    
    clean = re.sub(r"<think>.*?</think>", "", full, flags=re.DOTALL).strip()
    return clean

# OCR from image
@app.route('/api/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        img_bytes = image_file.read()
        np_img = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        denoised = cv2.medianBlur(thresh, 3)
        text = pytesseract.image_to_string(denoised)
        language = detect(text)
        return jsonify({'text': text, 'language': language})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI explanation
@app.route('/api/explain', methods=['POST'])
def explain_text():
    data = request.get_json()
    if 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    try:
        lines = [line.strip() for line in data['text'].split('\n') if line.strip()]
        explanations = []
        for line in lines:
            prompt = f"Explain this in simple terms: {line}"
            explanation = ask_deepseek(prompt)
            explanations.append({'original': line, 'explanation': explanation})

        return jsonify({'explanations': explanations})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# AI summarization
@app.route('/api/summarize', methods=['POST'])
def summarize_text():
    data = request.get_json()
    if 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    try:
        prompt = f"Summarize this:\n\n{data['text']}"
        summary = ask_deepseek(prompt)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Translation
@app.route('/api/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    if 'text' not in data or 'target_lang' not in data:
        return jsonify({'error': 'Please provide both \"text\" and \"target_lang\"'}), 400

    try:
        translated = GoogleTranslator(source='auto', target=data['target_lang']).translate(data['text'])
        return jsonify({'translated_text': translated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Text-to-Speech
@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    if 'text' not in data or not data['text'].strip():
        return jsonify({'error': 'No text provided'}), 400

    lang = data.get('lang', 'en')
    try:
        tts = gTTS(text=data['text'], lang=lang)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        base64_audio = base64.b64encode(audio_bytes.read()).decode('utf-8')
        return jsonify({'audio': base64_audio})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
