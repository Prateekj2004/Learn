import pytesseract
import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify
from io import BytesIO
from flask_cors import CORS
from transformers import pipeline
from deep_translator import GoogleTranslator
from gtts import gTTS
import base64


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
CORS(app)

@app.route('/api/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Convert uploaded image to OpenCV format
        img_bytes = image_file.read()
        np_img = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # STEP 1: Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # STEP 2: Apply threshold
        thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # STEP 3: Denoise (optional)
        denoised = cv2.medianBlur(thresh, 3)

        # STEP 4: OCR
        text = pytesseract.image_to_string(denoised)

        return jsonify({'text': text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

summarizer = pipeline("summarization")

@app.route('/api/summarize', methods=['POST'])

def summarize_text():
    data = request.get_json()
    if 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    try:
        summary = summarizer(data['text'], max_length=100, min_length=25, do_sample=False)
        return jsonify({'summary': summary[0]['summary_text']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    
    if 'text' not in data or 'target_lang' not in data:
        return jsonify({'error': 'Please provide both "text" and "target_lang"'}), 400

    try:
        translated = GoogleTranslator(source='auto', target=data['target_lang']).translate(data['text'])
        return jsonify({'translated_text': translated})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    
    if 'text' not in data or not data['text'].strip():
        return jsonify({'error': 'No text provided'}), 400

    lang = data.get('lang', 'en')  # Default to English if not provided

    try:
        tts = gTTS(text=data['text'], lang=lang)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        base64_audio = base64.b64encode(audio_bytes.read()).decode('utf-8')
        return jsonify({'audio': base64_audio})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
