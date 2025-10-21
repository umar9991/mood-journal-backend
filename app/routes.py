from flask import Blueprint, request, jsonify, current_app
from bson.objectid import ObjectId
from datetime import datetime

main = Blueprint('main', __name__)

def serialize_mood(doc):
    return {
        "id": str(doc.get("_id")),
        "mood": doc.get("mood"),
        "note": doc.get("note"),
        "date": doc.get("date"),
    }

@main.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Mood Journal Backend Running ✅"})

# ✅ ADD THESE TEST ROUTES
@main.route('/api/test-simple', methods=['GET'])
def test_simple():
    return jsonify({
        "message": "✅ Basic API route working!", 
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@main.route('/api/test-db', methods=['GET'])
def test_db():
    try:
        if current_app.db is None:
            return jsonify({"error": "Database not connected"}), 500
        
        # Simple database operation
        count = current_app.db.moods.count_documents({})
        return jsonify({
            "message": "✅ Database connected!",
            "moods_count": count,
            "database": current_app.db.name
        }), 200
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@main.route('/health', methods=['GET'])
def health():
    try:
        if current_app.db is None:
            return jsonify({
                "status": "unhealthy",
                "message": "Database not initialized",
                "database": "disconnected"
            }), 500
            
        # Simple find operation to test connection
        current_app.db.moods.find_one()
        return jsonify({
            "status": "healthy",
            "message": "Backend is running",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "message": str(e),
            "database": "disconnected"
        }), 500

# ✅ IMPROVED MOODS ROUTE WITH ERROR HANDLING
@main.route('/api/moods', methods=['POST'])
def create_mood():
    try:
        # Check database connection
        if current_app.db is None:
            return jsonify({"error": "Database not connected"}), 500
            
        body = request.get_json(silent=True) or {}
        mood = (body.get("mood") or "").strip()
        note = (body.get("note") or "").strip()
        date = body.get("date") or datetime.utcnow().isoformat()

        if not mood:
            return jsonify({"error": "ValidationError", "message": "'mood' is required"}), 400

        doc = {"mood": mood, "note": note, "date": date}
        result = current_app.db["moods"].insert_one(doc)
        doc["_id"] = result.inserted_id
        
        return jsonify(serialize_mood(doc)), 201
        
    except Exception as e:
        print(f"❌ Error in create_mood: {str(e)}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500

@main.route('/api/moods', methods=['GET'])
def list_moods():
    try:
        if current_app.db is None:
            return jsonify({"error": "Database not connected"}), 500
            
        moods = current_app.db["moods"].find({}, sort=[("date", -1)])
        return jsonify([serialize_mood(m) for m in moods])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/api/moods/<id>', methods=['GET'])
def get_mood(id):
    try:
        doc = current_app.db["moods"].find_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error": "InvalidId"}), 400
    if not doc:
        return jsonify({"error": "NotFound"}), 404
    return jsonify(serialize_mood(doc))

@main.route('/api/moods/<id>', methods=['PUT'])
def update_mood(id):
    body = request.get_json(silent=True) or {}
    update = {}
    if "mood" in body:
        update["mood"] = (body.get("mood") or "").strip()
    if "note" in body:
        update["note"] = (body.get("note") or "").strip()
    if "date" in body:
        update["date"] = body.get("date")
    if not update:
        return jsonify({"error": "ValidationError", "message": "No fields to update"}), 400
    try:
        res = current_app.db["moods"].find_one_and_update(
            {"_id": ObjectId(id)}, {"$set": update}, return_document=True
        )
    except Exception:
        return jsonify({"error": "InvalidId"}), 400
    if not res:
        return jsonify({"error": "NotFound"}), 404
    return jsonify(serialize_mood(res))

@main.route('/api/moods/<id>', methods=['DELETE'])
def delete_mood(id):
    try:
        res = current_app.db["moods"].delete_one({"_id": ObjectId(id)})
    except Exception:
        return jsonify({"error": "InvalidId"}), 400
    if res.deleted_count == 0:
        return jsonify({"error": "NotFound"}), 404
    return jsonify({"deleted": True})