import logging
import re
import numpy as np
from hashlib import md5
from collections import Counter
import string
from sqlalchemy import text
from app import db
from models import DocumentChunk, Document
from config import TOP_K_RESULTS

logger = logging.getLogger(__name__)

class RAGEngine:
    """
    Simplified Retrieval-Augmented Generation (RAG) engine:
    1. Uses keyword search instead of embeddings
    2. Searches for relevant document chunks
    3. Returns context for LLM prompting if relevant results found
    """
    
    def __init__(self):
        # Pre-compile some regex patterns
        self.tokenize_pattern = re.compile(r'\w+')
    
    def generate_query_embedding(self, query_text):
        """
        Generate a simple tf-idf-like vector for query text.
        This is a very basic implementation to avoid requiring heavy ML libraries.
        """
        # Simple tokenization (remove punctuation, lowercase, split by whitespace)
        tokens = self._tokenize_text(query_text)
        
        # Create a simple character-level hash-based embedding
        # This is not a real embedding but a placeholder
        # In a real implementation, we would use a proper embedding model
        embedding = []
        for i in range(100):  # Create a 100-dimensional vector
            hash_input = query_text + str(i)
            hash_val = int(md5(hash_input.encode()).hexdigest(), 16)
            # Normalize to [-1, 1] range
            embedding.append((hash_val % 1000) / 500 - 1)
            
        return np.array(embedding, dtype=np.float32)
    
    def _tokenize_text(self, text):
        """Simple tokenization function"""
        # Convert to lowercase
        text = text.lower()
        # Find all word tokens
        tokens = self.tokenize_pattern.findall(text)
        return tokens
    
    def retrieve_relevant_chunks(self, query_text, doc_type=None):
        """
        Retrieve relevant document chunks for a query using keyword matching
        
        Args:
            query_text: The user's query text
            doc_type: Optional filter for document type
            
        Returns:
            Tuple of (relevant_chunks, document_ids, relevance_scores)
        """
        try:
            # Tokenize the query
            query_tokens = self._tokenize_text(query_text)
            
            # Create search terms for SQL LIKE query
            search_terms = []
            for token in query_tokens:
                if len(token) > 3:  # Only use tokens longer than 3 chars
                    search_terms.append(f"%{token}%")
            
            if not search_terms:
                # If no good search terms, use the original query
                search_terms = [f"%{query_text}%"]
            
            # Build the SQL query using keyword search with ILIKE
            sql = """
                SELECT dc.id, dc.text_content, dc.document_id,
                       0.8 as similarity
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE 
            """
            
            # Add conditions for each search term
            conditions = []
            for i, term in enumerate(search_terms):
                param_name = f"term_{i}"
                conditions.append(f"dc.text_content ILIKE :{param_name}")
            
            sql += " OR ".join(conditions)
            
            # Create parameters dict
            params = {}
            for i, term in enumerate(search_terms):
                params[f"term_{i}"] = term
            
            # Add doc_type filter if specified
            if doc_type:
                sql += " AND d.doc_type = :doc_type"
                params["doc_type"] = doc_type
            
            sql += " LIMIT :limit"
            params["limit"] = TOP_K_RESULTS
            
            # Execute query
            result = db.session.execute(text(sql), params)
            
            # Process results
            relevant_chunks = []
            document_ids = []
            relevance_scores = []
            
            for row in result:
                relevant_chunks.append(row.text_content)
                document_ids.append(row.document_id)
                relevance_scores.append(float(row.similarity))
            
            return relevant_chunks, document_ids, relevance_scores
            
        except Exception as e:
            logger.error(f"Error retrieving relevant chunks: {str(e)}")
            return [], [], []
    
    def get_rag_context(self, query_text, doc_type=None):
        """
        Get RAG context for a query
        
        Args:
            query_text: The user's query text
            doc_type: Optional filter for document type
            
        Returns:
            Dictionary with context, document_ids, has_relevant_context, and relevance_scores
        """
        relevant_chunks, document_ids, relevance_scores = self.retrieve_relevant_chunks(query_text, doc_type)
        
        has_relevant_context = len(relevant_chunks) > 0
        
        if has_relevant_context:
            # Combine chunks into a single context string
            context = "\n\n".join([f"Document Chunk {i+1}:\n{chunk}" for i, chunk in enumerate(relevant_chunks)])
        else:
            context = ""
        
        return {
            "context": context,
            "document_ids": document_ids,
            "has_relevant_context": has_relevant_context,
            "relevance_scores": relevance_scores
        }
