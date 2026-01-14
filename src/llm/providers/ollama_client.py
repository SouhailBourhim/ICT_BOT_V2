"""
Ollama client implementation using the base LLM interface.
"""
import asyncio
from typing import Dict, Any, Optional, List
import requests
import json
from loguru import logger

from ..base_llm import BaseLLM, LLMResponse


class OllamaClient(BaseLLM):
    """Ollama local LLM client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        self.base_url = config.get('base_url', 'http://localhost:11434').rstrip('/')
        self.model = config.get('model', 'llama3.2:3b')
        self.timeout = config.get('timeout', 120)
        
        logger.info(f"Ollama client initialized: {self.model} @ {self.base_url}")
        
        # Check connection on initialization
        self._check_connection()
    
    def _check_connection(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                logger.success(f"✅ Ollama connected ({len(models)} models available)")
                return True
            else:
                logger.warning(f"⚠️ Ollama responds but with code {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            return False
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate response using Ollama."""
        try:
            # Combine context and prompt
            full_prompt = prompt
            if context:
                full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
            
            # System prompt from kwargs
            system_prompt = kwargs.get('system_prompt')
            
            endpoint = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens or 2000,
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(endpoint, json=payload, timeout=self.timeout)
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            content = result.get('response', '')
            
            # Extract usage info
            usage = None
            if 'total_duration' in result:
                usage = {
                    'total_duration_ns': result.get('total_duration', 0),
                    'load_duration_ns': result.get('load_duration', 0),
                    'prompt_eval_count': result.get('prompt_eval_count', 0),
                    'eval_count': result.get('eval_count', 0),
                    'eval_duration_ns': result.get('eval_duration', 0)
                }
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider='ollama',
                usage=usage,
                metadata={
                    'done': result.get('done', False),
                    'context': result.get('context', [])
                }
            )
            
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self._check_connection()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information."""
        try:
            models = self.list_models()
            current_model = next((m for m in models if m.get('name') == self.model), {})
            
            return {
                'provider': 'ollama',
                'model': self.model,
                'type': 'local',
                'supports_streaming': True,
                'size': current_model.get('size', 'Unknown'),
                'modified_at': current_model.get('modified_at'),
                'available_models': [m.get('name') for m in models]
            }
        except Exception:
            return {
                'provider': 'ollama',
                'model': self.model,
                'type': 'local',
                'supports_streaming': True,
                'status': 'unavailable'
            }
    
    def list_models(self) -> List[Dict]:
        """List all available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json().get('models', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str:
        """
        Synchronous generate method for compatibility with existing code.
        
        Args:
            prompt: User prompt
            system: System prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            stream: Whether to stream (not implemented)
            
        Returns:
            Generated text content
        """
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            logger.error(f"Generate error: {e}")
            raise Exception(f"Ollama generation failed: {str(e)}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Chat mode with conversation history."""
        endpoint = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(endpoint, json=payload, timeout=self.timeout)
            
            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            message = result.get('message', {})
            return message.get('content', '')
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise