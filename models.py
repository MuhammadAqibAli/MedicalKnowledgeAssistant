from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    organization = db.Column(db.String(128))
    role = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    generated_contents = relationship("GeneratedContent", back_populates="user")

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    doc_type = db.Column(db.String(64), nullable=False)  # Policy, Best Practice, Procedure, Standing Order
    file_path = db.Column(db.String(512), nullable=False)  # Path in storage
    original_filename = db.Column(db.String(255), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)  # pdf, docx
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doc_metadata = db.Column(JSONB)  # Additional document metadata
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")
    generated_contents = relationship("GeneratedContent", secondary="document_content_association")

class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    text_content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.ARRAY(db.Float))  # Vector embedding
    chunk_metadata = db.Column(JSONB)  # Page number, paragraph, etc.
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Regular index instead of ivfflat which requires special setup
    __table_args__ = (
        db.Index('idx_document_chunks_embedding', embedding),
    )

class GeneratedContent(db.Model):
    __tablename__ = 'generated_contents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(64), nullable=False)  # Policy, Best Practice, etc.
    content = db.Column(db.Text, nullable=False)
    llm_model_used = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rag_used = db.Column(db.Boolean, default=False)
    validation_score = db.Column(db.Float)
    validation_feedback = db.Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="generated_contents")
    validation_results = relationship("ValidationResult", back_populates="generated_content")

# Association table for many-to-many relationship between documents and generated contents
class DocumentContentAssociation(db.Model):
    __tablename__ = 'document_content_association'
    
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('generated_contents.id'), primary_key=True)
    relevance_score = db.Column(db.Float)  # How relevant was this document to the generation

class ValidationResult(db.Model):
    __tablename__ = 'validation_results'
    
    id = db.Column(db.Integer, primary_key=True)
    generated_content_id = db.Column(db.Integer, db.ForeignKey('generated_contents.id'), nullable=False)
    validator_model = db.Column(db.String(128), nullable=False)
    consistency_score = db.Column(db.Float)
    clinical_relevance_score = db.Column(db.Float)
    language_tone_score = db.Column(db.Float)
    nz_compliance_score = db.Column(db.Float)
    validation_details = db.Column(JSONB)  # Detailed feedback
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="validation_results")
