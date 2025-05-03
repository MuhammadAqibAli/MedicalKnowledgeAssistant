import os
import logging
from flask import render_template, request, jsonify, send_from_directory, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app import db
from models import Document, GeneratedContent, User
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
    
    @app.route('/')
    def index():
        """Home page"""
        return render_template('index.html')
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        """Document upload page and handler"""
        if request.method == 'POST':
            # Check if file was uploaded
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            
            file = request.files['file']
            
            # Check if file was selected
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            
            # Get form data
            title = request.form.get('title', 'Untitled Document')
            doc_type = request.form.get('doc_type')
            
            # Validate file extension
            if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
                # For demo purposes, use a fixed user ID. In production, get from authenticated user.
                user_id = 1
                
                # Process the document
                document_id = document_processor.process_document(file, title, doc_type, user_id)
                
                if document_id:
                    flash('Document uploaded and processed successfully!')
                    return redirect(url_for('documents'))
                else:
                    flash('Error processing document')
                    return redirect(request.url)
            else:
                flash('Invalid file type')
                return redirect(request.url)
        
        return render_template('upload.html', document_types=DOCUMENT_TYPES)
    
    @app.route('/generate', methods=['GET', 'POST'])
    def generate():
        """Content generation page and handler"""
        if request.method == 'POST':
            # Get form data
            topic = request.form.get('topic')
            content_type = request.form.get('content_type')
            model_choice = request.form.get('model_choice')
            use_rag = request.form.get('use_rag') == 'on'
            
            if not topic or not content_type:
                flash('Topic and content type are required')
                return redirect(request.url)
            
            # For demo purposes, use a fixed user ID
            user_id = 1
            
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
                
                if validation_id:
                    flash('Content generated and validated successfully!')
                else:
                    flash('Content generated, but validation failed')
                
                # Redirect to view the content
                return redirect(url_for('view_content', content_id=content_id))
            else:
                flash('Error generating content')
                return redirect(request.url)
        
        return render_template('generate.html', 
                              document_types=DOCUMENT_TYPES,
                              models=LLM_MODELS)
    
    @app.route('/documents')
    def documents():
        """Document management page"""
        # For demo purposes, use a fixed user ID
        user_id = 1
        
        # Get all documents
        documents = Document.query.filter_by(user_id=user_id).all()
        
        return render_template('documents.html', documents=documents)
    
    @app.route('/content/<int:content_id>')
    def view_content(content_id):
        """View generated content"""
        content = GeneratedContent.query.get_or_404(content_id)
        
        # Get associated documents if any
        source_documents = []
        if content.rag_used:
            # Query for source documents through the association table
            source_documents = db.session.query(Document).join(
                DocumentContentAssociation,
                Document.id == DocumentContentAssociation.document_id
            ).filter(
                DocumentContentAssociation.content_id == content_id
            ).all()
        
        return render_template('view_content.html', 
                              content=content,
                              source_documents=source_documents)
    
    @app.route('/api/search_documents', methods=['POST'])
    def search_documents():
        """API endpoint to search documents"""
        query = request.json.get('query', '')
        doc_type = request.json.get('doc_type', None)
        
        rag_context = rag_engine.get_rag_context(query, doc_type)
        
        return jsonify({
            'success': True,
            'has_context': rag_context['has_relevant_context'],
            'document_count': len(set(rag_context['document_ids'])),
            'context_preview': rag_context['context'][:200] + '...' if rag_context['context'] else ''
        })
    
    @app.route('/api/list_contents')
    def list_contents():
        """API endpoint to list generated contents"""
        # For demo purposes, use a fixed user ID
        user_id = 1
        
        # Get query parameters for filtering
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
        
        return jsonify(result)
    
    # Add error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
