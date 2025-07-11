from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET", "supersecretkey")
jwt = JWTManager(app)

from routes.auth import auth_bp
from routes.conversation import convo_bp
from routes.ai import ai_bp
from routes.ocr import ocr_bp  

app.register_blueprint(auth_bp)
app.register_blueprint(convo_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(ocr_bp) 

if __name__ == '__main__':
    app.run(debug=True)
