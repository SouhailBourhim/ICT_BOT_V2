"""
Google Gemini API client implementation.
"""
import os
import asyncio
from typing import Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..base_llm import BaseLLM, LLMResponse


class GeminiClient(BaseLLM):
    """Google Gemini API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configure API key
        api_key = config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable.")
        
        genai.configure(api_key=api_key)
        
        # Model configuration
        self.model_name = config.get('model', 'gemini-1.5-flash')
        self.model = genai.GenerativeModel(self.model_name)
        
        # Safety settings - more permissive for academic use
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Gemini API."""
        try:
            # Combine context and prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
            
            # Generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                candidate_count=1,
            )
            
            # Generate response in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
            )
            
            # Extract content
            if response.candidates and response.candidates[0].content.parts:
                content = response.candidates[0].content.parts[0].text
            else:
                content = "No response generated."
            
            # Extract usage info if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0),
                    'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                provider='gemini',
                usage=usage,
                metadata={
                    'finish_reason': getattr(response.candidates[0], 'finish_reason', None) if response.candidates else None,
                    'safety_ratings': [
                        {
                            'category': rating.category.name,
                            'probability': rating.probability.name
                        }
                        for rating in (response.candidates[0].safety_ratings if response.candidates else [])
                    ]
                }
            )
            
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        try:
            # Simple test to check API connectivity
            test_response = self.model.generate_content("Hello")
            return bool(test_response.candidates)
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Gemini model information."""
        return {
            'provider': 'gemini',
            'model': self.model_name,
            'type': 'api',
            'supports_streaming': False,
            'max_context_length': self._get_context_length(),
            'pricing': self._get_pricing_info()
        }
    
    def _get_context_length(self) -> int:
        """Get context length for the model."""
        context_lengths = {
            'gemini-2.5-flash': 1048576,  # 1M tokens
            'gemini-2.5-pro': 2097152,   # 2M tokens
            'gemini-flash-latest': 1048576,  # 1M tokens
            # Legacy models
            'gemini-1.5-flash': 1048576,  # 1M tokens
            'gemini-1.5-pro': 2097152,   # 2M tokens
            'gemini-1.0-pro': 32768,     # 32K tokens
        }
        return context_lengths.get(self.model_name, 32768)
    
    def _get_pricing_info(self) -> Dict[str, str]:
        """Get pricing information for the model."""
        pricing = {
            'gemini-2.5-flash': {'input': '$0.075/1M tokens', 'output': '$0.30/1M tokens'},
            'gemini-2.5-pro': {'input': '$1.25/1M tokens', 'output': '$5.00/1M tokens'},
            'gemini-flash-latest': {'input': '$0.075/1M tokens', 'output': '$0.30/1M tokens'},
            # Legacy models (if still used)
            'gemini-1.5-flash': {'input': '$0.075/1M tokens', 'output': '$0.30/1M tokens'},
            'gemini-1.5-pro': {'input': '$3.50/1M tokens', 'output': '$10.50/1M tokens'},
            'gemini-1.0-pro': {'input': '$0.50/1M tokens', 'output': '$1.50/1M tokens'},
        }
        return pricing.get(self.model_name, {'input': 'Unknown', 'output': 'Unknown'})