from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from .config import config_by_name
import os


def create_app():
    load_dotenv()

    env_name = os.getenv("FLASK_ENV", "development")
    config_class = config_by_name.get(env_name, config_by_name["development"])()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # FIXED CORS - Very permissive for development
    CORS(app, 
         resources={r"/*": {
             "origins": "*",  # Allow all origins for now
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False,
             "max_age": 3600
         }})

    # Add CORS headers manually for all responses
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    # MongoDB Connection
    try:
        mongo_uri = app.config.get("MONGO_URI")
        print(f"🔗 Connecting to MongoDB: {mongo_uri}")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        app.db = client[os.getenv("MONGO_DB", "mood_journal_db")]
        
        # Test connection
        client.server_info()
        print("✅ MongoDB connected successfully")
        
        # Ensure indexes
        from app.models import ensure_indexes
        ensure_indexes(app.db["moods"])
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        # Don't raise - let app run without DB for testing
        app.db = None

    # Health route and main blueprint
    from app.routes import main
    app.register_blueprint(main)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad Request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not Found", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Server Error", "message": str(error)}), 500

    print("✅ Flask app created successfully")
    print(f"📍 Access at: http://127.0.0.1:5000")
    
    return app