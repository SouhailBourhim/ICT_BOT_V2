"""Gestion de la fenêtre de contexte"""
from typing import List, Dict, Any


class ContextWindow:
    """Gestion du contexte conversationnel"""
    
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
    
    def get_context(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Récupère les derniers messages pour le contexte"""
        return messages[-self.max_messages:]
    
    def format_for_llm(self, messages: List[Dict[str, Any]]) -> str:
        """Formate les messages pour le LLM"""
        formatted = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n\n".join(formatted)
