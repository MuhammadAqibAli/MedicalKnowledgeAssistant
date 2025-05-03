import os
import logging
import tempfile
import re
from hashlib import md5
import numpy as np
from app import db
from models import Document, DocumentChunk
from config import CHUNK_SIZE, CHUNK_OVERLAP, UPLOAD_FOLDER

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles document processing pipeline:
    1. Parse uploaded documents (PDF/DOCX)
    2. Extract text
    3. Split into chunks
    4. Generate simple embeddings
    5. Store in database
    """
    
    def __init__(self):
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
    def process_document(self, file, title, doc_type, user_id):
        """
        Process an uploaded document file
        
        Args:
            file: FileStorage object from request.files
            title: Document title
            doc_type: Document type (Policy, Best Practice, etc.)
            user_id: ID of the user who uploaded the document
            
        Returns:
            Document ID if successful, None otherwise
        """
        try:
            # Save original file
            filename = file.filename
            file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ""
            
            if file_extension not in ['pdf', 'docx']:
                logger.error(f"Unsupported file extension: {file_extension}")
                return None
                
            save_path = os.path.join(UPLOAD_FOLDER, f"{title.replace(' ', '_')}_{user_id}.{file_extension}")
            file.save(save_path)
            
            # Create document record
            document = Document(
                title=title,
                doc_type=doc_type,
                file_path=save_path,
                original_filename=filename,
                file_extension=file_extension,
                user_id=user_id,
                doc_metadata={}
            )
            
            db.session.add(document)
            db.session.commit()
            
            # Extract text based on file type
            if file_extension == 'pdf':
                text = self._extract_text_from_pdf(save_path)
            elif file_extension == 'docx':
                text = self._extract_text_from_docx(save_path)
            else:
                raise ValueError(f"Unsupported file extension: {file_extension}")
            
            # Split text into chunks
            chunks = self._split_text(text)
            
            # Process and store chunks
            self._process_chunks(chunks, document.id)
            
            return document.id
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            db.session.rollback()
            # Delete the file if it was saved
            if 'save_path' in locals() and os.path.exists(save_path):
                os.remove(save_path)
            return None
    
    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        try:
            # Import inside function to avoid loading at startup
            import fitz  # PyMuPDF
            
            text = ""
            pdf = fitz.open(file_path)
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                text += page.get_text()
            return text
        except ImportError:
            # If PyMuPDF is not available, use a simple fallback
            logger.warning("PyMuPDF not available. Using fallback PDF text extraction.")
            return f"PDF text extraction not available for {file_path}. Install PyMuPDF package for full functionality."
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            # Import inside function to avoid loading at startup
            import docx
            
            text = ""
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except ImportError:
            # If python-docx is not available, use a simple fallback
            logger.warning("python-docx not available. Using fallback DOCX text extraction.")
            return f"DOCX text extraction not available for {file_path}. Install python-docx package for full functionality."
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            raise
    
    def _split_text(self, text):
        """Split text into manageable chunks"""
        # Simple chunking by paragraphs and then by size
        paragraphs = text.split('\n\n')
        chunks = []
        
        current_chunk = ""
        current_metadata = {"start_para": 0, "end_para": 0}
        
        for i, para in enumerate(paragraphs):
            # If adding this paragraph would exceed chunk size, save the chunk and start a new one
            if len(current_chunk) + len(para) > CHUNK_SIZE and current_chunk:
                chunks.append({"page_content": current_chunk, "metadata": current_metadata})
                current_chunk = para
                current_metadata = {"start_para": i, "end_para": i}
            else:
                if not current_chunk:
                    current_metadata["start_para"] = i
                current_chunk += "\n\n" + para if current_chunk else para
                current_metadata["end_para"] = i
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append({"page_content": current_chunk, "metadata": current_metadata})
        
        return chunks
    
    def _generate_embedding(self, text):
        """
        Generate a simple hash-based embedding for a text chunk.
        This is a very basic implementation to avoid requiring heavy ML libraries.
        """
        # Create a simple character-level hash-based embedding
        # This is not a real embedding but a placeholder
        # In a real implementation, we would use a proper embedding model
        embedding = []
        for i in range(100):  # Create a 100-dimensional vector
            hash_input = text + str(i)
            hash_val = int(md5(hash_input.encode()).hexdigest(), 16)
            # Normalize to [-1, 1] range
            embedding.append((hash_val % 1000) / 500 - 1)
            
        return np.array(embedding, dtype=np.float32)
    
    def _process_chunks(self, chunks, document_id):
        """Process and store document chunks with embeddings"""
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding for the chunk
                embedding = self._generate_embedding(chunk["page_content"])
                
                # Create chunk record
                document_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    text_content=chunk["page_content"],
                    embedding=embedding.tolist(),  # Convert numpy array to list for storage
                    chunk_metadata=chunk["metadata"]
                )
                
                db.session.add(document_chunk)
                
            except Exception as e:
                logger.error(f"Error processing chunk {i}: {str(e)}")
                raise
        
        db.session.commit()
