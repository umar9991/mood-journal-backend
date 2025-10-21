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

    # CORS - Allow frontend domain
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS(app, 
         resources={r"/*": {
             "origins": cors_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": False,
             "max_age": 3600
         }})

    @app.after_request
    def after_request(response):
        origin = os.getenv("CORS_ORIGINS", "*")
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

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

    # Register blueprints
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
    
    return app