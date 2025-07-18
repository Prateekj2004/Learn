from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from db.connection import users_collection
from utils.schema import get_user_schema
import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Signup Route
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 409

    user_doc = get_user_schema(data)
    users_collection.insert_one(user_doc)
    return jsonify({"message": "Signup successful"}), 201

# Login Route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(
        identity=str(user["_id"]),
        expires_delta=datetime.timedelta(days=1)
    )
    return jsonify({"token": token, "email": user["email"]})

# Update Profile Route
@auth_bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()

    name = data.get('name')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({'error': 'User not found'}), 404

    updates = {}
    if name:
        updates['name'] = name

    if old_password and new_password:
        if not check_password_hash(user['password'], old_password):
            return jsonify({'error': 'Old password incorrect'}), 401
        updates['password'] = generate_password_hash(new_password)

    if updates:
        users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        return jsonify({'message': 'Profile updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes made'}), 400
