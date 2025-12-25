"""Tests pour le LLM"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm.prompt_templates import PromptBuilder


def test_prompt_templates():
    """Test des templates de prompts"""
    builder = PromptBuilder()
    
    # Test chunks
    chunks = [
        {
            'text': "Test context content",
            'metadata': {'filename': 'test.pdf', 'page_number': 1}
        }
    ]
    
    question = "Test question"
    
    system_prompt, user_prompt = builder.build_rag_prompt(question, chunks)
    
    assert "Test context content" in user_prompt
    assert "Test question" in user_prompt
    assert "assistant" in system_prompt.lower()
