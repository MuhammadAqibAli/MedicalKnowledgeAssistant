import os
import logging
import requests
from app import db
from db_models import GeneratedContent, document_content_association
from config import HUGGINGFACE_API_KEY, LLM_MODELS, DEFAULT_LLM_MODEL

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM Model service for generating content:
    1. Selects appropriate LLM model
    2. Constructs prompt with or without RAG context
    3. Calls Hugging Face Inference API
    4. Processes and returns the response
    """
    
    def __init__(self):
        self.api_key = HUGGINGFACE_API_KEY
        self.models = LLM_MODELS
        self.default_model = DEFAULT_LLM_MODEL
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set. Using demo API which has rate limits.")
    
    def generate_content(self, topic, content_type, user_id, model_choice=None, rag_context=None):
        """
        Generate content using the selected LLM model
        
        Args:
            topic: The main topic for content generation
            content_type: Type of content (Policy, Best Practice, etc.)
            user_id: User ID requesting the generation
            model_choice: Which LLM model to use (defaults to self.default_model)
            rag_context: RAG context dictionary from RAGEngine if available
            
        Returns:
            Generated content ID if successful, None otherwise
        """
        try:
            # Select model
            model_key = model_choice if model_choice in self.models else self.default_model
            model = self.models[model_key]
            
            # Determine if using RAG
            using_rag = rag_context and rag_context["has_relevant_context"]
            
            # Construct appropriate prompt
            prompt = self._construct_prompt(topic, content_type, rag_context)
            
            # Call the LLM API
            generated_text = self._call_huggingface_api(model, prompt)
            
            if not generated_text:
                return None
            
            # Create record in database
            generated_content = GeneratedContent(
                title=f"{content_type}: {topic}",
                content_type=content_type,
                content=generated_text,
                llm_model_used=model,
                user_id=user_id,
                rag_used=using_rag
            )
            
            db.session.add(generated_content)
            db.session.flush()  # Get ID without committing
            
            # If RAG was used, create associations with source documents
            if using_rag:
                unique_doc_ids = set(rag_context["document_ids"])
                doc_relevance = {}
                
                # Calculate average relevance score per document
                for i, doc_id in enumerate(rag_context["document_ids"]):
                    if doc_id not in doc_relevance:
                        doc_relevance[doc_id] = []
                    doc_relevance[doc_id].append(rag_context["relevance_scores"][i])
                
                # Create associations
                for doc_id, scores in doc_relevance.items():
                    avg_relevance = sum(scores) / len(scores)
                    association = DocumentContentAssociation(
                        document_id=doc_id,
                        content_id=generated_content.id,
                        relevance_score=avg_relevance
                    )
                    db.session.add(association)
            
            db.session.commit()
            return generated_content.id
            
        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            db.session.rollback()
            return None
    
    def _construct_prompt(self, topic, content_type, rag_context=None):
        """Construct a prompt for the LLM with or without RAG context"""
        
        # Base prompt template for NZ healthcare content
        base_prompt = f"""You are a helpful assistant specialized in New Zealand healthcare standards.
Generate a {content_type} about "{topic}".

Your response should:
1. Be written in a formal, professional, and concise tone
2. Use terminology appropriate for New Zealand healthcare professionals
3. Comply with all applicable New Zealand healthcare regulations
4. Be structured with clear sections and headings
5. Include relevant medical information but avoid unnecessary jargon

"""

        # Add RAG context if available
        if rag_context and rag_context["has_relevant_context"]:
            rag_prompt = f"""Use the following context from official documents to inform your response:

{rag_context["context"]}

Based on the above context and your knowledge of New Zealand healthcare standards, generate a {content_type} about "{topic}".
"""
            return base_prompt + rag_prompt
        
        # No RAG context available
        return base_prompt + f"""Generate a comprehensive and accurate {content_type} about "{topic}" based on your knowledge of New Zealand healthcare standards."""
    
    def _call_huggingface_api(self, model, prompt):
        """Call the Hugging Face Inference API"""
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Set parameters for the API call
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.95,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
            
            # Parse the response
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                logger.error(f"Unexpected API response format: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Hugging Face API: {str(e)}")
            return None
