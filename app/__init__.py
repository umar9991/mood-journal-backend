from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from .config import config_by_name
import os

def create_app():
    load_dotenv()

    env_name = os.getenv("FLASK_ENV", "production")
    config_class = config_by_name.get(env_name, config_by_name["production"])()

    app = Flask(__name__)
    app.config.from_object(config_class)

    # ✅ Fixed CORS setup
    cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
    cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]
    
    if not cors_origins:
        cors_origins = [
            "https://mood-journal-frontend.vercel.app",
            "http://localhost:5173", 
            "http://localhost:3000"
        ]
    
    print(f"🔄 CORS Origins: {cors_origins}")
    
    CORS(app, 
         origins=cors_origins,
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"],
         supports_credentials=False,
         max_age=3600)

    # MongoDB Atlas Connection
    try:
        mongo_uri = app.config.get("MONGO_URI")
        if not mongo_uri:
            raise ValueError("MONGO_URI not found in environment variables")
        
        print(f"🔗 Connecting to MongoDB Atlas...")
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        db_name = os.getenv("MONGO_DB", "mood_journal_db")
        app.db = client[db_name]
        
        # Test connection
        client.server_info()
        print(f"✅ MongoDB Atlas connected: {db_name}")
        
        # Ensure indexes
        from app.models import ensure_indexes
        ensure_indexes(app.db["moods"])
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        app.db = None

    # ✅ FIXED: Blueprint registration WITHOUT url_prefix
    from app.routes import main
    app.register_blueprint(main)  # ❌ url_prefix mat use karein

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
    
    return app