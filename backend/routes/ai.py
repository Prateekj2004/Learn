import os
import pytesseract
import cv2
import numpy as np
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from huggingface_hub import InferenceClient
from gtts import gTTS
from deep_translator import GoogleTranslator
from langdetect import detect
from io import BytesIO
import base64
import re
from datetime import datetime
from db.connection import conversations_collection

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

client = InferenceClient(
    model="deepseek-ai/DeepSeek-R1-0528",
    api_key=os.environ["HF_TOKEN"]
)

pytesseract.pytesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def ask_deepseek(prompt):
    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}])
    full = res.choices[0].message.content.strip()
    return re.sub(r"<think>.*?</think>", "", full, flags=re.DOTALL).strip()

def auto_save(user_id, content, save_flag):
    if save_flag:
        conversations_collection.insert_one({
            "user_id": user_id,
            "content": content,
            "timestamp": datetime.utcnow(),
            "saved": True
        })

@ai_bp.route("/ocr", methods=["POST"])
@jwt_required()
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
        lang = detect(text)
        return jsonify({'text': text, 'language': lang})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route("/explain", methods=["POST"])
@jwt_required()
def explain():
    data = request.get_json()
    user_id = get_jwt_identity()

    text = data.get("text", "")
    save_flag = data.get("save", False)

    lines = [line.strip() for line in text.split('\n') if line.strip()]
    results = []

    for line in lines:
        prompt = f"Explain this in simple terms: {line}"
        explanation = ask_deepseek(prompt)
        results.append({"original": line, "explanation": explanation})

    if save_flag:
        auto_save(user_id, {"task": "explanation", "input": text, "output": results}, True)

    return jsonify({"explanations": results})

@ai_bp.route("/summarize", methods=["POST"])
@jwt_required()
def summarize():
    data = request.get_json()
    user_id = get_jwt_identity()

    text = data.get("text", "")
    save_flag = data.get("save", False)

    summary = ask_deepseek(f"Summarize this:\n\n{text}")

    if save_flag:
        auto_save(user_id, {"task": "summarization", "input": text, "output": summary}, True)

    return jsonify({"summary": summary})

@ai_bp.route("/translate", methods=["POST"])
@jwt_required()
def translate():
    data = request.get_json()
    user_id = get_jwt_identity()

    text = data.get("text", "")
    target_lang = data.get("target_lang", "")
    save_flag = data.get("save", False)

    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)

        if save_flag:
            auto_save(user_id, {"task": "translation", "input": text, "output": translated}, True)

        return jsonify({"translated_text": translated})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_bp.route("/tts", methods=["POST"])
@jwt_required()
def tts():
    data = request.get_json()
    user_id = get_jwt_identity()

    text = data.get("text", "")
    lang = data.get("lang", "en")
    save_flag = data.get("save", False)

    try:
        tts = gTTS(text=text, lang=lang)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        base64_audio = base64.b64encode(audio_bytes.read()).decode('utf-8')

        if save_flag:
            auto_save(user_id, {"task": "text-to-speech", "input": text, "output": "audio.mp3"}, True)

        return jsonify({"audio": base64_audio})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
