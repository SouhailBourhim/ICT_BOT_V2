from types import SimpleNamespace

from src.llm.prompt_templates import PromptBuilder
from src.llm.response_generator import ResponseGenerator


class FakeSearch:
    def search(self, query, top_k, filters=None):
        return [
            SimpleNamespace(
                text="Le machine learning apprend des modèles à partir des données.",
                metadata={"filename": "cours_ml.pdf", "page_number": 2},
                score=0.9,
            )
        ]


class FakeOllama:
    def __init__(self):
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return "Le machine learning apprend des modèles à partir des données."


def test_prompt_builder_formats_rag_prompt():
    system, user = PromptBuilder().build_rag_prompt(
        question="Qu'est-ce que le machine learning ?",
        context_chunks=[
            {
                "text": "Le machine learning apprend des modèles à partir des données.",
                "metadata": {"filename": "cours_ml.pdf", "page_number": 2},
            }
        ],
    )

    assert "contexte fourni" in system.lower()
    assert "cours_ml.pdf" in user
    assert "machine learning" in user.lower()


def test_response_generator_uses_mocked_ollama_and_configured_max_tokens():
    fake_ollama = FakeOllama()
    generator = ResponseGenerator(
        hybrid_search=FakeSearch(),
        ollama_client=fake_ollama,
        prompt_builder=PromptBuilder(),
        min_confidence=0.4,
        max_sources=1,
        top_k_retrieval=3,
        max_tokens=123,
    )

    response = generator.generate_response("Définis le machine learning", temperature=0.2)

    assert response.answer
    assert response.sources[0]["name"] == "cours_ml.pdf"
    assert fake_ollama.calls[0]["max_tokens"] == 123
    assert fake_ollama.calls[0]["temperature"] == 0.2
