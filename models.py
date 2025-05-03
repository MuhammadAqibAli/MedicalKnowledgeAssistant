from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from flask_login import UserMixin
# Import db from a separate file to avoid circular imports
from database import db

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(64), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password_hash = db.Column(String(256), nullable=False)
    organization = db.Column(String(128))
    role = db.Column(String(64))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    documents = relationship("Document", back_populates="user")
    generated_contents = relationship("GeneratedContent", back_populates="user")
    
    def __repr__(self):
        return f'<User {self.username}>'

# Document model
class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False)
    doc_type = db.Column(String(64), nullable=False)  # Policy, Best Practice, Procedure, Standing Order
    file_path = db.Column(String(512), nullable=False)  # Path in storage
    original_filename = db.Column(String(255), nullable=False)
    file_extension = db.Column(String(10), nullable=False)  # pdf, docx
    uploaded_at = db.Column(DateTime, default=datetime.utcnow)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    doc_metadata = db.Column(JSONB)  # Additional document metadata
    
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")
    generated_contents = relationship("GeneratedContent", secondary="document_content_association")
    
    def __repr__(self):
        return f'<Document {self.title}>'

# Document Chunk model
class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'
    
    id = db.Column(Integer, primary_key=True)
    document_id = db.Column(Integer, ForeignKey('documents.id'), nullable=False)
    chunk_index = db.Column(Integer, nullable=False)
    text_content = db.Column(Text, nullable=False)
    embedding = db.Column(ARRAY(Float))  # Vector embedding
    chunk_metadata = db.Column(JSONB)  # Page number, paragraph, etc.
    
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f'<DocumentChunk {self.document_id}-{self.chunk_index}>'
    
    __table_args__ = (
        db.Index('idx_document_chunks_embedding', embedding),
    )

# Generated Content model
class GeneratedContent(db.Model):
    __tablename__ = 'generated_contents'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False)
    content_type = db.Column(String(64), nullable=False)  # Policy, Best Practice, etc.
    content = db.Column(Text, nullable=False)
    llm_model_used = db.Column(String(128), nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    rag_used = db.Column(Boolean, default=False)
    validation_score = db.Column(Float)
    validation_feedback = db.Column(JSONB)
    
    user = relationship("User", back_populates="generated_contents")
    validation_results = relationship("ValidationResult", back_populates="generated_content")
    
    def __repr__(self):
        return f'<GeneratedContent {self.title}>'

# Document-Content Association model
class DocumentContentAssociation(db.Model):
    __tablename__ = 'document_content_association'
    
    document_id = db.Column(Integer, ForeignKey('documents.id'), primary_key=True)
    content_id = db.Column(Integer, ForeignKey('generated_contents.id'), primary_key=True)
    relevance_score = db.Column(Float)  # How relevant was this document to the generation
    
    def __repr__(self):
        return f'<DocumentContentAssociation {self.document_id}-{self.content_id}>'

# Validation Result model
class ValidationResult(db.Model):
    __tablename__ = 'validation_results'
    
    id = db.Column(Integer, primary_key=True)
    generated_content_id = db.Column(Integer, ForeignKey('generated_contents.id'), nullable=False)
    validator_model = db.Column(String(128), nullable=False)
    consistency_score = db.Column(Float)
    clinical_relevance_score = db.Column(Float)
    language_tone_score = db.Column(Float)
    nz_compliance_score = db.Column(Float)
    validation_details = db.Column(JSONB)  # Detailed feedback
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    generated_content = relationship("GeneratedContent", back_populates="validation_results")
    
    def __repr__(self):
        return f'<ValidationResult {self.id}>'