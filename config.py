import os

# Environment settings
ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = ENV == 'development'

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# File upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# LLM Model settings
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODELS = {
    "llama": "meta-llama/Llama-2-7b-chat-hf",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.2",
    "falcon": "tiiuae/falcon-7b-instruct"
}
DEFAULT_LLM_MODEL = "mistral"

# Chunking settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# RAG settings
VECTOR_SIMILARITY_THRESHOLD = 0.75
TOP_K_RESULTS = 5

# Validation settings
VALIDATION_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"  # Smaller/faster model for validation
VALIDATION_THRESHOLD = 0.7

# NZ Healthcare specific settings
HEALTHCARE_DOMAINS = [
    "Clinical Guidelines",
    "Medical Ethics",
    "Patient Privacy",
    "Treatment Protocols",
    "Public Health Policy",
    "Medical Research",
    "Healthcare Administration",
    "Patient Care",
    "Health and Safety",
    "Emergency Procedures"
]

# Document types
DOCUMENT_TYPES = [
    "Policy",
    "Best Practice",
    "Procedure",
    "Standing Order"
]
