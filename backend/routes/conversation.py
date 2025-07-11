from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db.connection import conversations_collection
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from utils.schema import get_conversation_schema

convo_bp = Blueprint('conversation', __name__, url_prefix='/api/convo')

# Save conversation (used by AI features to insert conversation)
@convo_bp.route('/save', methods=['POST'])
@jwt_required()
def save_conversation():
    data = request.get_json()
    user_id = get_jwt_identity()

    convo_doc = get_conversation_schema(data, user_id)
    conversations_collection.insert_one(convo_doc)
    return jsonify({"message": "Conversation saved"}), 201

# Get conversations from last 24h (not saved manually)
@convo_bp.route('/unsaved', methods=['GET'])
@jwt_required()
def get_unsaved():
    user_id = get_jwt_identity()
    time_limit = datetime.utcnow() - timedelta(hours=24)

    results = list(conversations_collection.find({
        "user_id": user_id,
        "is_saved": False,
        "timestamp": {"$gte": time_limit}
    }, {"_id": 0}))

    return jsonify({"unsaved": results})

# Get saved conversations
@convo_bp.route('/saved', methods=['GET'])
@jwt_required()
def get_saved():
    user_id = get_jwt_identity()

    results = list(conversations_collection.find({
        "user_id": user_id,
        "is_saved": True
    }, {"_id": 0}))

    return jsonify({"saved": results})

# Mark any convo saved manually
@convo_bp.route('/mark-saved', methods=['POST'])
@jwt_required()
def mark_as_saved():
    data = request.get_json()
    user_id = get_jwt_identity()
    convo_id = data.get("convo_id")

    if not convo_id:
        return jsonify({"error": "Missing convo_id"}), 400

    result = conversations_collection.update_one(
        {"_id": ObjectId(convo_id), "user_id": user_id},
        {"$set": {"is_saved": True}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Conversation not found or unauthorized"}), 404

    return jsonify({"message": "Conversation marked as saved"}), 200
