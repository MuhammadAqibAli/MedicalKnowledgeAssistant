from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, Table
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from flask_login import UserMixin

# Create a base class for SQLAlchemy models
Base = declarative_base()

# Association table for many-to-many relationship
document_content_association = Table(
    'document_content_association',
    Base.metadata,
    Column('document_id', Integer, ForeignKey('documents.id'), primary_key=True),
    Column('content_id', Integer, ForeignKey('generated_contents.id'), primary_key=True),
    Column('relevance_score', Float)
)

class User(UserMixin, Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    organization = Column(String(128))
    role = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user")
    generated_contents = relationship("GeneratedContent", back_populates="user")

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    doc_type = Column(String(64), nullable=False)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_extension = Column(String(10), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    doc_metadata = Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")
    generated_contents = relationship("GeneratedContent", secondary=document_content_association)

class DocumentChunk(Base):
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    embedding = Column(ARRAY(Float))
    chunk_metadata = Column(JSONB)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

class GeneratedContent(Base):
    __tablename__ = 'generated_contents'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    llm_model_used = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rag_used = Column(Boolean, default=False)
    validation_score = Column(Float)
    validation_feedback = Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="generated_contents")
    validation_results = relationship("ValidationResult", back_populates="generated_content")

class ValidationResult(Base):
    __tablename__ = 'validation_results'
    
    id = Column(Integer, primary_key=True)
    generated_content_id = Column(Integer, ForeignKey('generated_contents.id'), nullable=False)
    validator_model = Column(String(128), nullable=False)
    consistency_score = Column(Float)
    clinical_relevance_score = Column(Float)
    language_tone_score = Column(Float)
    nz_compliance_score = Column(Float)
    validation_details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    generated_content = relationship("GeneratedContent", back_populates="validation_results")
