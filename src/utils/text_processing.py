"""Traitement de texte pour le français"""
import re
from typing import List


class TextProcessor:
    """Traitement de texte spécifique au français"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Nettoie le texte"""
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        # Supprimer les caractères spéciaux
        text = re.sub(r'[^\w\s\.,;:!?àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ-]', '', text)
        return text.strip()
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalise le texte"""
        text = text.lower()
        text = TextProcessor.clean_text(text)
        return text
    
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        """Découpe en phrases"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
