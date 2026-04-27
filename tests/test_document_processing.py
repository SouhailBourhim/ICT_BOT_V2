from src.document_processing.parser import DocumentParser
import src.document_processing.chunker as chunker_module


def test_parser_extracts_txt_metadata(tmp_path):
    file_path = tmp_path / "lesson.txt"
    file_path.write_text("Machine learning\nest un sujet Smart ICT.", encoding="utf-8")

    parsed = DocumentParser().parse(file_path)

    assert "Machine learning" in parsed.content
    assert parsed.metadata["filename"] == "lesson.txt"
    assert parsed.metadata["format"] == "txt"


def test_chunker_uses_fallback_without_model_download(monkeypatch):
    monkeypatch.setattr(chunker_module, "LANGCHAIN_AVAILABLE", False)
    monkeypatch.setattr(chunker_module, "LangChainSemanticChunker", None)

    chunker = chunker_module.SemanticChunker(
        chunk_size=80,
        chunk_overlap=10,
        min_chunk_size=20,
    )
    text = "Introduction. " + ("Les réseaux intelligents utilisent des capteurs. " * 8)

    chunks = chunker.chunk_text(
        text,
        doc_metadata={"filename": "lesson.txt", "format": "txt"},
    )

    assert chunks
    assert all(chunk.content for chunk in chunks)
    assert all(chunk.metadata["filename"] == "lesson.txt" for chunk in chunks)
