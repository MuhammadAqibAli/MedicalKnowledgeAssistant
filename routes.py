import os
import logging
from flask import request, jsonify
from werkzeug.utils import secure_filename
from app import db
from models import Document, GeneratedContent, DocumentContentAssociation, ValidationResult, User
from document_processor import DocumentProcessor
from rag_engine import RAGEngine
from llm_service import LLMService
from validation_service import ValidationService
from config import ALLOWED_EXTENSIONS, DOCUMENT_TYPES, LLM_MODELS

logger = logging.getLogger(__name__)

# Initialize services
document_processor = DocumentProcessor()
rag_engine = RAGEngine()
llm_service = LLMService()
validation_service = ValidationService()

def register_routes(app):
    """Register all routes with the Flask app"""
    
    @app.route('/api/v1/documents', methods=['POST'])
    def upload_document():
        """
        Upload and process a document
        ---
        Endpoint for uploading and processing a document
        """
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400
        
        # Get form data
        title = request.form.get('title', 'Untitled Document')
        doc_type = request.form.get('doc_type')
        user_id = request.form.get('user_id', 1)
        
        # Validate doc_type
        if not doc_type or doc_type not in DOCUMENT_TYPES:
            return jsonify({'success': False, 'error': 'Invalid document type'}), 400
        
        # Validate file extension
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            # Process the document
            document_id = document_processor.process_document(file, title, doc_type, user_id)
            
            if document_id:
                # Get the document to return its details
                document = Document.query.get(document_id)
                return jsonify({
                    'success': True, 
                    'document': {
                        'id': document.id,
                        'title': document.title,
                        'doc_type': document.doc_type,
                        'file_extension': document.file_extension,
                        'original_filename': document.original_filename,
                        'uploaded_at': document.uploaded_at.isoformat()
                    }
                }), 201
            else:
                return jsonify({'success': False, 'error': 'Error processing document'}), 500
        else:
            return jsonify({'success': False, 'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    @app.route('/api/v1/documents', methods=['GET'])
    def get_documents():
        """
        Get all documents for a user
        ---
        Endpoint to retrieve all documents for a specific user
        """
        user_id = request.args.get('user_id', 1)
        doc_type = request.args.get('doc_type')
        
        # Build query
        query = Document.query.filter_by(user_id=user_id)
        
        if doc_type:
            query = query.filter_by(doc_type=doc_type)
        
        # Get documents
        documents = query.order_by(Document.uploaded_at.desc()).all()
        
        # Prepare response
        result = []
        for document in documents:
            result.append({
                'id': document.id,
                'title': document.title,
                'doc_type': document.doc_type,
                'file_extension': document.file_extension,
                'original_filename': document.original_filename,
                'uploaded_at': document.uploaded_at.isoformat()
            })
        
        return jsonify({'success': True, 'documents': result})
    
    @app.route('/api/v1/documents/<int:document_id>', methods=['GET'])
    def get_document(document_id):
        """
        Get a specific document's details
        ---
        Endpoint to retrieve details of a specific document
        """
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        # Get document chunks
        chunks = []
        for chunk in document.chunks:
            chunks.append({
                'id': chunk.id,
                'chunk_index': chunk.chunk_index,
                'text_content': chunk.text_content[:200] + '...' if len(chunk.text_content) > 200 else chunk.text_content
            })
        
        return jsonify({
            'success': True,
            'document': {
                'id': document.id,
                'title': document.title,
                'doc_type': document.doc_type,
                'file_extension': document.file_extension,
                'original_filename': document.original_filename,
                'uploaded_at': document.uploaded_at.isoformat(),
                'chunks': chunks
            }
        })
    
    @app.route('/api/v1/generate', methods=['POST'])
    def generate_content():
        """
        Generate content using LLM
        ---
        Endpoint for generating content using LLM with optional RAG
        """
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Extract parameters
        topic = data.get('topic')
        content_type = data.get('content_type')
        model_choice = data.get('model_choice')
        use_rag = data.get('use_rag', True)
        user_id = data.get('user_id', 1)
        
        if not topic or not content_type:
            return jsonify({'success': False, 'error': 'Topic and content type are required'}), 400
        
        # Get RAG context if enabled
        rag_context = None
        if use_rag:
            rag_context = rag_engine.get_rag_context(topic, content_type)
        
        # Generate content
        content_id = llm_service.generate_content(
            topic=topic,
            content_type=content_type,
            user_id=user_id,
            model_choice=model_choice,
            rag_context=rag_context
        )
        
        if content_id:
            # Validate the generated content
            validation_id = validation_service.validate_content(content_id)
            
            # Get the generated content
            content = GeneratedContent.query.get(content_id)
            
            # Get associated documents if RAG was used
            source_documents = []
            if content.rag_used:
                # Query for source documents through the association table
                doc_associations = db.session.query(Document, DocumentContentAssociation).join(
                    DocumentContentAssociation,
                    Document.id == DocumentContentAssociation.document_id
                ).filter(
                    DocumentContentAssociation.content_id == content_id
                ).all()
                
                for document, association in doc_associations:
                    source_documents.append({
                        'id': document.id,
                        'title': document.title,
                        'relevance_score': association.relevance_score
                    })
            
            return jsonify({
                'success': True,
                'content': {
                    'id': content.id,
                    'title': content.title,
                    'content_type': content.content_type,
                    'content': content.content,
                    'llm_model_used': content.llm_model_used,
                    'created_at': content.created_at.isoformat(),
                    'validation_score': content.validation_score,
                    'validation_feedback': content.validation_feedback,
                    'rag_used': content.rag_used,
                    'source_documents': source_documents
                }
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Error generating content'}), 500
    
    @app.route('/api/v1/search', methods=['POST'])
    def search_documents():
        """
        Search documents using RAG
        ---
        Endpoint to search documents using RAG engine
        """
        data = request.json
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        query = data.get('query', '')
        doc_type = data.get('doc_type')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        rag_context = rag_engine.get_rag_context(query, doc_type)
        
        # Get detailed document information
        document_details = []
        if rag_context['has_relevant_context']:
            doc_ids = set(rag_context['document_ids'])
            documents = Document.query.filter(Document.id.in_(doc_ids)).all()
            
            for doc in documents:
                document_details.append({
                    'id': doc.id,
                    'title': doc.title,
                    'doc_type': doc.doc_type
                })
        
        return jsonify({
            'success': True,
            'has_context': rag_context['has_relevant_context'],
            'document_count': len(set(rag_context['document_ids'])),
            'context': rag_context['context'],
            'documents': document_details
        })
    
    @app.route('/api/v1/contents', methods=['GET'])
    def list_contents():
        """
        List generated contents
        ---
        Endpoint to list generated contents with optional filtering
        """
        user_id = request.args.get('user_id', 1)
        content_type = request.args.get('content_type')
        llm_model = request.args.get('llm_model')
        min_validation = request.args.get('min_validation')
        
        # Build query
        query = GeneratedContent.query.filter_by(user_id=user_id)
        
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        if llm_model:
            query = query.filter_by(llm_model_used=llm_model)
        
        if min_validation:
            try:
                min_val = float(min_validation)
                query = query.filter(GeneratedContent.validation_score >= min_val)
            except ValueError:
                pass
        
        # Get results
        contents = query.order_by(GeneratedContent.created_at.desc()).all()
        
        # Prepare response
        result = []
        for content in contents:
            result.append({
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'created_at': content.created_at.isoformat(),
                'llm_model_used': content.llm_model_used,
                'validation_score': content.validation_score,
                'rag_used': content.rag_used
            })
        
        return jsonify({'success': True, 'contents': result})
    
    @app.route('/api/v1/contents/<int:content_id>', methods=['GET'])
    def get_content(content_id):
        """
        Get specific generated content
        ---
        Endpoint to retrieve details of a specific generated content
        """
        content = GeneratedContent.query.get(content_id)
        
        if not content:
            return jsonify({'success': False, 'error': 'Content not found'}), 404
        
        # Get associated documents if RAG was used
        source_documents = []
        if content.rag_used:
            # Query for source documents through the association table
            doc_associations = db.session.query(Document, DocumentContentAssociation).join(
                DocumentContentAssociation,
                Document.id == DocumentContentAssociation.document_id
            ).filter(
                DocumentContentAssociation.content_id == content_id
            ).all()
            
            for document, association in doc_associations:
                source_documents.append({
                    'id': document.id,
                    'title': document.title,
                    'relevance_score': association.relevance_score
                })
        
        # Get validation results
        validation_results = []
        for validation in content.validation_results:
            validation_results.append({
                'id': validation.id,
                'validator_model': validation.validator_model,
                'consistency_score': validation.consistency_score,
                'clinical_relevance_score': validation.clinical_relevance_score,
                'language_tone_score': validation.language_tone_score,
                'nz_compliance_score': validation.nz_compliance_score,
                'validation_details': validation.validation_details,
                'created_at': validation.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'content': {
                'id': content.id,
                'title': content.title,
                'content_type': content.content_type,
                'content': content.content,
                'llm_model_used': content.llm_model_used,
                'created_at': content.created_at.isoformat(),
                'validation_score': content.validation_score,
                'validation_feedback': content.validation_feedback,
                'rag_used': content.rag_used,
                'source_documents': source_documents,
                'validation_results': validation_results
            }
        })
    
    @app.route('/api/v1/models', methods=['GET'])
    def get_models():
        """
        Get available LLM models
        ---
        Endpoint to retrieve available LLM models
        """
        return jsonify({
            'success': True,
            'models': LLM_MODELS
        })
    
    @app.route('/api/v1/document-types', methods=['GET'])
    def get_document_types():
        """
        Get available document types
        ---
        Endpoint to retrieve available document types
        """
        return jsonify({
            'success': True,
            'document_types': DOCUMENT_TYPES
        })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
