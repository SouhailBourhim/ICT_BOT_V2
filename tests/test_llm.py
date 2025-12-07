"""Tests pour le LLM"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm import PromptTemplates


def test_prompt_templates():
    """Test des templates de prompts"""
    context = "Test context"
    question = "Test question"
    
    prompt = PromptTemplates.format_rag_prompt(context, question)
    
    assert "Test context" in prompt
    assert "Test question" in prompt
    assert "français" in prompt.lower()
