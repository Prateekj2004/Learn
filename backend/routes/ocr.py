import pytesseract
import cv2
import numpy as np
from flask import Blueprint, request, jsonify
from langdetect import detect

ocr_bp = Blueprint("ocr", __name__)

@ocr_bp.route('/api/ocr', methods=['POST'])
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
