from src.conversation.manager import ConversationManager


def test_conversation_manager_persists_messages_and_metadata(tmp_path):
    manager = ConversationManager(storage_dir=str(tmp_path), max_history_length=2)
    conversation = manager.create_conversation()

    manager.add_message("user", "Bonjour", conversation_id=conversation.id)
    manager.add_message(
        "assistant",
        "Réponse",
        metadata={"sources": [{"name": "cours.pdf"}]},
        conversation_id=conversation.id,
    )

    reloaded = ConversationManager(storage_dir=str(tmp_path)).load_conversation(conversation.id)

    assert reloaded is not None
    assert len(reloaded.messages) == 2
    assert reloaded.messages[1].metadata["sources"][0]["name"] == "cours.pdf"


def test_context_window_limits_recent_messages(tmp_path):
    manager = ConversationManager(storage_dir=str(tmp_path), max_history_length=2)
    conversation = manager.create_conversation()

    manager.add_message("user", "one", conversation_id=conversation.id)
    manager.add_message("assistant", "two", conversation_id=conversation.id)
    manager.add_message("user", "three", conversation_id=conversation.id)

    history = manager.get_context_window(conversation.id)

    assert [message["content"] for message in history] == ["two", "three"]
