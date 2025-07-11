from datetime import datetime

def get_user_schema(data):
    return {
        "username": data.get("username"),
        "email": data.get("email"),
        "password": data.get("password"),
        "created_at": datetime.utcnow(),
    }

def get_conversation_schema(data, user_id):
    return {
        "user_id": user_id,
        "input_text": data.get("input_text"),
        "output_text": data.get("output_text"),
        "type": data.get("type"),  # e.g., 'summary', 'explanation', 'translation'
        "language": data.get("language", "en"),
        "is_saved": data.get("is_saved", False),
        "timestamp": datetime.utcnow(),
    }
