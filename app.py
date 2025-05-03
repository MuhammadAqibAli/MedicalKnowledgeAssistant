import os
import logging
from flask import Flask, jsonify
import json
from datetime import datetime
from dotenv import load_dotenv
from database import db

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

# Initialize extensions
db.init_app(app)

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

# Initialize the database
with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Import and register routes
from routes import register_routes
register_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
