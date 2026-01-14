"""
Base LLM interface for different providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Standard response format for all LLM providers."""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('client', '')
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM provider is available."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        pass