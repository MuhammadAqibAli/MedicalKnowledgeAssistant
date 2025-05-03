import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom JSON encoder to handle datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Create Flask app
app = Flask(__name__)
app.json_encoder = CustomJSONEncoder
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Max upload file size: 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Initialize SQLAlchemy with the app
db = SQLAlchemy(app)

# Import models
from db_models import Base, User, Document, DocumentChunk, GeneratedContent, ValidationResult

# CORS settings for API
@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
    return response

# Root endpoint to indicate API is working
@app.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'NZ Medical Document Assistant API is running',
        'version': '1.0',
        'documentation': '/api/v1/docs'
    })

if __name__ == '__main__':
    with app.app_context():
        # Create all tables
        try:
            Base.metadata.create_all(db.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
    
    # Import and register routes after models are set up
    from routes import register_routes
    register_routes(app)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
