import logging
import requests
from app import db
from db_models import ValidationResult, GeneratedContent
from config import HUGGINGFACE_API_KEY, VALIDATION_MODEL

logger = logging.getLogger(__name__)

class ValidationService:
    """
    LLM Output Validation Engine:
    1. Runs generated content through a secondary LLM
    2. Validates for consistency, clinical relevance, language tone, etc.
    3. Creates validation records and updates content scores
    """
    
    def __init__(self):
        self.api_key = HUGGINGFACE_API_KEY
        self.validation_model = VALIDATION_MODEL
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set. Using demo API which has rate limits.")
    
    def validate_content(self, content_id):
        """
        Validate generated content using a secondary LLM
        
        Args:
            content_id: ID of the GeneratedContent to validate
            
        Returns:
            Validation ID if successful, None otherwise
        """
        try:
            # Retrieve the content to validate
            content = db.session.query(GeneratedContent).get(content_id)
            
            if not content:
                logger.error(f"Content ID {content_id} not found")
                return None
            
            # Construct validation prompt
            validation_prompt = self._construct_validation_prompt(content)
            
            # Call validation model
            validation_response = self._call_huggingface_api(validation_prompt)
            
            if not validation_response:
                return None
            
            # Parse validation results
            validation_scores, validation_details = self._parse_validation_response(validation_response)
            
            # Create validation record
            validation = ValidationResult(
                generated_content_id=content_id,
                validator_model=self.validation_model,
                consistency_score=validation_scores.get('consistency', 0),
                clinical_relevance_score=validation_scores.get('clinical_relevance', 0),
                language_tone_score=validation_scores.get('language_tone', 0),
                nz_compliance_score=validation_scores.get('nz_compliance', 0),
                validation_details=validation_details
            )
            
            db.session.add(validation)
            
            # Update content's validation score (average of all scores)
            scores = [score for score in validation_scores.values() if score is not None]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            content.validation_score = avg_score
            content.validation_feedback = validation_details
            
            db.session.commit()
            return validation.id
            
        except Exception as e:
            logger.error(f"Error validating content: {str(e)}")
            db.session.rollback()
            return None
    
    def _construct_validation_prompt(self, content):
        """Construct a prompt for validation"""
        
        validation_prompt = f"""As a New Zealand healthcare expert, evaluate the following {content.content_type}. 
        
CONTENT TO EVALUATE:
"{content.content}"

Evaluate the content based on these criteria:
1. Consistency: Is the content internally consistent without contradictions?
2. Clinical Relevance: Is the content clinically relevant and accurate for New Zealand healthcare?
3. Language Tone: Is the language formal, concise, and appropriate for medical professionals?
4. NZ Compliance: Does the content comply with New Zealand healthcare regulations?

For each criterion, provide:
- A score from 0.0 to 1.0 (where 1.0 is perfect)
- A brief explanation of your scoring
- Specific issues or recommendations

FORMAT YOUR RESPONSE EXACTLY LIKE THIS EXAMPLE:
{{
  "scores": {{
    "consistency": 0.85,
    "clinical_relevance": 0.92,
    "language_tone": 0.78,
    "nz_compliance": 0.90
  }},
  "details": {{
    "consistency": "The document is mostly consistent, but section 2 contradicts section 4 regarding patient follow-up procedures.",
    "clinical_relevance": "The clinical information is accurate and relevant for NZ healthcare settings, particularly in primary care.",
    "language_tone": "Generally formal, but uses some colloquial expressions that should be replaced with medical terminology.",
    "nz_compliance": "Complies with most NZ regulations, but needs to reference the updated 2023 Health and Disability Services Standards."
  }},
  "recommendations": [
    "Resolve contradiction between sections 2 and 4",
    "Replace colloquial terms with proper medical terminology",
    "Add reference to 2023 Health and Disability Services Standards"
  ]
}}

Provide ONLY the JSON response without any additional text.
"""
        return validation_prompt
    
    def _call_huggingface_api(self, prompt):
        """Call the Hugging Face Inference API for validation"""
        api_url = f"https://api-inference.huggingface.co/models/{self.validation_model}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Set parameters for the API call
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.3,  # Lower temperature for more deterministic responses
                "top_p": 0.95,
                "return_full_text": False
            }
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"Validation API error: {response.status_code} - {response.text}")
                return None
            
            # Parse the response
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "generated_text" in result:
                return result["generated_text"]
            else:
                logger.error(f"Unexpected validation API response format: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling validation API: {str(e)}")
            return None
    
    def _parse_validation_response(self, response_text):
        """Parse the validation response JSON"""
        import json
        import re
        
        try:
            # Try to extract JSON from the response text
            # Sometimes the model might return text before/after the JSON
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
                validation_data = json.loads(json_str)
                
                # Extract scores and details
                scores = validation_data.get('scores', {})
                details = validation_data.get('details', {})
                
                # Add recommendations to details if present
                if 'recommendations' in validation_data:
                    details['recommendations'] = validation_data['recommendations']
                
                return scores, details
            else:
                logger.error("Could not extract JSON from validation response")
                return {}, {"error": "Could not parse validation response"}
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing validation JSON: {str(e)}")
            return {}, {"error": f"Invalid JSON format: {str(e)}"}
        except Exception as e:
            logger.error(f"Error processing validation response: {str(e)}")
            return {}, {"error": f"Processing error: {str(e)}"}
