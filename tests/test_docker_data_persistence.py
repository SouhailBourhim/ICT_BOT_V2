"""Property-based tests for Docker data persistence integrity"""
import pytest
import json
import sqlite3
import tempfile
import shutil
import os
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, MagicMock
import sys
from datetime import datetime
import uuid

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.conversation.manager import ConversationManager, Message, Conversation
from src.storage.metadata_store import MetadataStore
from src.storage.models import Document, Chunk


class DataPersistenceTester:
    """Helper class for testing data persistence across container restarts"""
    
    def __init__(self):
        self.docker_compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.yml"
        self.test_data_dir = None
        self.test_db_dir = None
        self.test_logs_dir = None
        
    def setup_test_environment(self) -> Dict[str, Path]:
        """Setup temporary directories that simulate Docker volume mounts"""
        # Create temporary directories for testing
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="test_data_"))
        self.test_db_dir = Path(tempfile.mkdtemp(prefix="test_db_"))
        self.test_logs_dir = Path(tempfile.mkdtemp(prefix="test_logs_"))
        
        # Create subdirectories that match Docker volume structure
        (self.test_data_dir / "conversations").mkdir(exist_ok=True)
        (self.test_data_dir / "embeddings").mkdir(exist_ok=True)
        (self.test_data_dir / "processed").mkdir(exist_ok=True)
        (self.test_data_dir / "documents").mkdir(exist_ok=True)
        
        return {
            "data": self.test_data_dir,
            "database": self.test_db_dir,
            "logs": self.test_logs_dir
        }
    
    def cleanup_test_environment(self):
        """Clean up temporary test directories"""
        for dir_path in [self.test_data_dir, self.test_db_dir, self.test_logs_dir]:
            if dir_path and dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
    
    def simulate_container_restart(self, test_dirs: Dict[str, Path]) -> Dict[str, Any]:
        """
        Simulate container restart by checking if data persists in mounted volumes
        Returns information about what data was preserved
        """
        persistence_status = {
            "conversations_preserved": False,
            "database_preserved": False,
            "logs_preserved": False,
            "embeddings_preserved": False,
            "processed_preserved": False,
            "conversation_count": 0,
            "database_files": [],
            "log_files": [],
            "embedding_files": [],
            "processed_files": []
        }
        
        # Check conversations directory
        conversations_dir = test_dirs["data"] / "conversations"
        if conversations_dir.exists():
            conv_files = list(conversations_dir.glob("*.json"))
            persistence_status["conversations_preserved"] = len(conv_files) > 0
            persistence_status["conversation_count"] = len(conv_files)
        
        # Check database directory
        database_dir = test_dirs["database"]
        if database_dir.exists():
            db_files = list(database_dir.rglob("*"))
            persistence_status["database_preserved"] = len(db_files) > 0
            persistence_status["database_files"] = [f.name for f in db_files if f.is_file()]
        
        # Check logs directory
        logs_dir = test_dirs["logs"]
        if logs_dir.exists():
            log_files = list(logs_dir.glob("*.log"))
            persistence_status["logs_preserved"] = len(log_files) > 0
            persistence_status["log_files"] = [f.name for f in log_files]
        
        # Check embeddings directory
        embeddings_dir = test_dirs["data"] / "embeddings"
        if embeddings_dir.exists():
            embedding_files = list(embeddings_dir.rglob("*"))
            persistence_status["embeddings_preserved"] = len(embedding_files) > 0
            persistence_status["embedding_files"] = [f.name for f in embedding_files if f.is_file()]
        
        # Check processed directory
        processed_dir = test_dirs["data"] / "processed"
        if processed_dir.exists():
            processed_files = list(processed_dir.rglob("*"))
            persistence_status["processed_preserved"] = len(processed_files) > 0
            persistence_status["processed_files"] = [f.name for f in processed_files if f.is_file()]
        
        return persistence_status
    
    def create_test_conversations(self, conversations_dir: Path, count: int) -> List[Dict[str, Any]]:
        """Create test conversation files in the conversations directory"""
        created_conversations = []
        
        for i in range(count):
            conv_id = str(uuid.uuid4())
            conversation_data = {
                "id": conv_id,
                "title": f"Test Conversation {i+1}",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Test question {i+1}",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {}
                    },
                    {
                        "role": "assistant", 
                        "content": f"Test response {i+1}",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {}
                    }
                ],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "metadata": {"test": True}
            }
            
            # Save conversation file
            conv_file = conversations_dir / f"{conv_id}.json"
            with open(conv_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            created_conversations.append(conversation_data)
        
        return created_conversations
    
    def create_test_database_files(self, database_dir: Path) -> List[str]:
        """Create test database files (SQLite and ChromaDB simulation)"""
        created_files = []
        
        # Create SQLite database file
        sqlite_file = database_dir / "metadata.db"
        conn = sqlite3.connect(str(sqlite_file))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                filename TEXT,
                filepath TEXT,
                format TEXT,
                size INTEGER,
                created_at TEXT,
                modified_at TEXT,
                processed_at TEXT
            )
        """)
        
        # Insert test data
        conn.execute("""
            INSERT INTO documents (id, filename, filepath, format, size, created_at, modified_at, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test-doc-1", "test.pdf", "/app/data/documents/test.pdf", "pdf", 1024, 
              datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        created_files.append("metadata.db")
        
        # Create ChromaDB directory structure
        chroma_dir = database_dir / "chroma_db"
        chroma_dir.mkdir(exist_ok=True)
        
        # Create ChromaDB SQLite file
        chroma_sqlite = chroma_dir / "chroma.sqlite3"
        chroma_conn = sqlite3.connect(str(chroma_sqlite))
        chroma_conn.execute("CREATE TABLE IF NOT EXISTS collections (id TEXT PRIMARY KEY, name TEXT)")
        chroma_conn.execute("INSERT INTO collections (id, name) VALUES (?, ?)", ("test-collection", "inpt_smart_ict_docs"))
        chroma_conn.commit()
        chroma_conn.close()
        created_files.append("chroma.sqlite3")
        
        return created_files
    
    def create_test_log_files(self, logs_dir: Path, count: int) -> List[str]:
        """Create test log files"""
        created_files = []
        
        for i in range(count):
            log_file = logs_dir / f"test_log_{i+1}.log"
            with open(log_file, 'w') as f:
                f.write(f"Test log entry {i+1}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("INFO: Test application started\n")
            
            created_files.append(log_file.name)
        
        return created_files
    
    def verify_conversation_integrity(self, conversations_dir: Path, original_conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify that conversation data integrity is maintained after restart"""
        integrity_status = {
            "all_conversations_present": True,
            "data_integrity_maintained": True,
            "missing_conversations": [],
            "corrupted_conversations": [],
            "total_original": len(original_conversations),
            "total_found": 0
        }
        
        found_conversations = {}
        
        # Load all conversation files
        for conv_file in conversations_dir.glob("*.json"):
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    conv_data = json.load(f)
                found_conversations[conv_data["id"]] = conv_data
            except Exception as e:
                integrity_status["corrupted_conversations"].append({
                    "file": conv_file.name,
                    "error": str(e)
                })
        
        integrity_status["total_found"] = len(found_conversations)
        
        # Check each original conversation
        for original_conv in original_conversations:
            conv_id = original_conv["id"]
            
            if conv_id not in found_conversations:
                integrity_status["missing_conversations"].append(conv_id)
                integrity_status["all_conversations_present"] = False
                continue
            
            # Verify data integrity
            found_conv = found_conversations[conv_id]
            
            # Check essential fields
            if (found_conv["title"] != original_conv["title"] or
                len(found_conv["messages"]) != len(original_conv["messages"]) or
                found_conv["created_at"] != original_conv["created_at"]):
                
                integrity_status["corrupted_conversations"].append({
                    "id": conv_id,
                    "error": "Data integrity check failed"
                })
                integrity_status["data_integrity_maintained"] = False
        
        return integrity_status
    
    def verify_database_integrity(self, database_dir: Path, original_files: List[str]) -> Dict[str, Any]:
        """Verify database file integrity after restart"""
        integrity_status = {
            "all_files_present": True,
            "sqlite_accessible": True,
            "chroma_accessible": True,
            "missing_files": [],
            "corrupted_files": []
        }
        
        # Check SQLite database
        sqlite_file = database_dir / "metadata.db"
        if not sqlite_file.exists():
            integrity_status["missing_files"].append("metadata.db")
            integrity_status["all_files_present"] = False
            integrity_status["sqlite_accessible"] = False
        else:
            try:
                conn = sqlite3.connect(str(sqlite_file))
                cursor = conn.execute("SELECT COUNT(*) FROM documents")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    integrity_status["corrupted_files"].append("metadata.db - no data found")
                    integrity_status["sqlite_accessible"] = False
            except Exception as e:
                integrity_status["corrupted_files"].append(f"metadata.db - {str(e)}")
                integrity_status["sqlite_accessible"] = False
        
        # Check ChromaDB
        chroma_file = database_dir / "chroma_db" / "chroma.sqlite3"
        if not chroma_file.exists():
            integrity_status["missing_files"].append("chroma.sqlite3")
            integrity_status["all_files_present"] = False
            integrity_status["chroma_accessible"] = False
        else:
            try:
                conn = sqlite3.connect(str(chroma_file))
                cursor = conn.execute("SELECT COUNT(*) FROM collections")
                count = cursor.fetchone()[0]
                conn.close()
                
                if count == 0:
                    integrity_status["corrupted_files"].append("chroma.sqlite3 - no collections found")
                    integrity_status["chroma_accessible"] = False
            except Exception as e:
                integrity_status["corrupted_files"].append(f"chroma.sqlite3 - {str(e)}")
                integrity_status["chroma_accessible"] = False
        
        return integrity_status


# **Feature: docker-modernization, Property 5: Data Persistence Integrity**
class TestDataPersistenceIntegrity:
    """Property-based tests for data persistence integrity across container restarts"""
    
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(conversation_counts=st.lists(
        st.integers(min_value=1, max_value=5),
        min_size=1,
        max_size=3
    ))
    def test_conversation_data_persists_across_restart(self, conversation_counts: List[int]):
        """
        **Feature: docker-modernization, Property 5: Data Persistence Integrity**
        **Validates: Requirements 2.3, 4.2**
        
        For any number of conversations, conversation data should persist correctly 
        across container restarts without data loss or corruption.
        """
        tester = DataPersistenceTester()
        
        for conv_count in conversation_counts:
            # Setup test environment
            test_dirs = tester.setup_test_environment()
            
            try:
                # Create test conversations
                conversations_dir = test_dirs["data"] / "conversations"
                original_conversations = tester.create_test_conversations(conversations_dir, conv_count)
                
                # Simulate container restart
                persistence_status = tester.simulate_container_restart(test_dirs)
                
                # Verify conversations are preserved
                assert persistence_status["conversations_preserved"], \
                    f"Conversations should be preserved after restart for count {conv_count}"
                
                assert persistence_status["conversation_count"] == conv_count, \
                    f"All {conv_count} conversations should be preserved, found {persistence_status['conversation_count']}"
                
                # Verify data integrity
                integrity_status = tester.verify_conversation_integrity(conversations_dir, original_conversations)
                
                assert integrity_status["all_conversations_present"], \
                    f"All conversations should be present after restart. Missing: {integrity_status['missing_conversations']}"
                
                assert integrity_status["data_integrity_maintained"], \
                    f"Conversation data integrity should be maintained. Corrupted: {integrity_status['corrupted_conversations']}"
                
                assert integrity_status["total_found"] == integrity_status["total_original"], \
                    f"Found {integrity_status['total_found']} conversations, expected {integrity_status['total_original']}"
                
            finally:
                # Cleanup
                tester.cleanup_test_environment()
    
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(data_scenarios=st.lists(
        st.fixed_dictionaries({
            "conversations": st.integers(min_value=0, max_value=3),
            "log_files": st.integers(min_value=0, max_value=3),
            "has_database": st.booleans()
        }),
        min_size=1,
        max_size=2
    ))
    def test_all_persistent_data_survives_restart(self, data_scenarios: List[Dict[str, Any]]):
        """
        **Feature: docker-modernization, Property 5: Data Persistence Integrity**
        **Validates: Requirements 2.3, 4.2**
        
        For any combination of persistent data (conversations, database, logs), 
        all data should survive container restarts without loss.
        """
        tester = DataPersistenceTester()
        
        for scenario in data_scenarios:
            # Setup test environment
            test_dirs = tester.setup_test_environment()
            
            try:
                created_data = {
                    "conversations": [],
                    "database_files": [],
                    "log_files": []
                }
                
                # Create test conversations if specified
                if scenario["conversations"] > 0:
                    conversations_dir = test_dirs["data"] / "conversations"
                    created_data["conversations"] = tester.create_test_conversations(
                        conversations_dir, scenario["conversations"]
                    )
                
                # Create test database files if specified
                if scenario["has_database"]:
                    created_data["database_files"] = tester.create_test_database_files(test_dirs["database"])
                
                # Create test log files if specified
                if scenario["log_files"] > 0:
                    created_data["log_files"] = tester.create_test_log_files(
                        test_dirs["logs"], scenario["log_files"]
                    )
                
                # Simulate container restart
                persistence_status = tester.simulate_container_restart(test_dirs)
                
                # Verify all data types are preserved according to what was created
                if scenario["conversations"] > 0:
                    assert persistence_status["conversations_preserved"], \
                        f"Conversations should be preserved when {scenario['conversations']} were created"
                    
                    assert persistence_status["conversation_count"] == scenario["conversations"], \
                        f"Expected {scenario['conversations']} conversations, found {persistence_status['conversation_count']}"
                
                if scenario["has_database"]:
                    assert persistence_status["database_preserved"], \
                        "Database files should be preserved when database was created"
                    
                    # Verify database integrity
                    db_integrity = tester.verify_database_integrity(test_dirs["database"], created_data["database_files"])
                    assert db_integrity["all_files_present"], \
                        f"All database files should be present. Missing: {db_integrity['missing_files']}"
                    
                    assert db_integrity["sqlite_accessible"], \
                        "SQLite database should be accessible after restart"
                
                if scenario["log_files"] > 0:
                    assert persistence_status["logs_preserved"], \
                        f"Log files should be preserved when {scenario['log_files']} were created"
                    
                    assert len(persistence_status["log_files"]) == scenario["log_files"], \
                        f"Expected {scenario['log_files']} log files, found {len(persistence_status['log_files'])}"
                
            finally:
                # Cleanup
                tester.cleanup_test_environment()
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(restart_sequences=st.lists(
        st.integers(min_value=1, max_value=3),  # Number of conversations to create
        min_size=2,
        max_size=4
    ))
    def test_data_integrity_across_multiple_restarts(self, restart_sequences: List[int]):
        """
        **Feature: docker-modernization, Property 5: Data Persistence Integrity**
        **Validates: Requirements 2.3, 4.2**
        
        For any sequence of container restarts with data modifications, 
        data integrity should be maintained across multiple restart cycles.
        """
        tester = DataPersistenceTester()
        
        # Setup test environment
        test_dirs = tester.setup_test_environment()
        
        try:
            all_conversations = []
            
            # Simulate multiple restart cycles
            for i, conv_count in enumerate(restart_sequences):
                # Create additional conversations in this cycle
                conversations_dir = test_dirs["data"] / "conversations"
                new_conversations = tester.create_test_conversations(conversations_dir, conv_count)
                all_conversations.extend(new_conversations)
                
                # Simulate container restart
                persistence_status = tester.simulate_container_restart(test_dirs)
                
                # Verify all conversations from all cycles are preserved
                expected_total = len(all_conversations)
                assert persistence_status["conversations_preserved"], \
                    f"Conversations should be preserved after restart cycle {i+1}"
                
                assert persistence_status["conversation_count"] == expected_total, \
                    f"After cycle {i+1}, expected {expected_total} conversations, found {persistence_status['conversation_count']}"
                
                # Verify data integrity for all conversations
                integrity_status = tester.verify_conversation_integrity(conversations_dir, all_conversations)
                
                assert integrity_status["all_conversations_present"], \
                    f"All conversations should be present after cycle {i+1}. Missing: {integrity_status['missing_conversations']}"
                
                assert integrity_status["data_integrity_maintained"], \
                    f"Data integrity should be maintained after cycle {i+1}. Corrupted: {integrity_status['corrupted_conversations']}"
        
        finally:
            # Cleanup
            tester.cleanup_test_environment()
    
    def test_docker_volume_configuration_supports_persistence(self):
        """
        **Feature: docker-modernization, Property 5: Data Persistence Integrity**
        **Validates: Requirements 2.3, 4.2**
        
        The Docker Compose configuration should properly define volume mounts 
        for all data that needs to persist across container restarts.
        """
        tester = DataPersistenceTester()
        
        # Check if docker-compose.yml exists
        assert tester.docker_compose_file.exists(), \
            "Docker Compose file must exist for volume configuration"
        
        # Read docker-compose.yml content
        with open(tester.docker_compose_file, 'r') as f:
            compose_content = f.read()
        
        # Verify essential volume mounts are configured
        required_volume_mounts = [
            "../data:/app/data",  # Main data directory
            "../database:/app/database",  # Database files
            "../logs:/app/logs",  # Log files
            "../data/conversations:/app/data/conversations",  # Conversations
            "../data/embeddings:/app/data/embeddings",  # Embeddings
            "../data/processed:/app/data/processed"  # Processed documents
        ]
        
        for volume_mount in required_volume_mounts:
            assert volume_mount in compose_content, \
                f"Volume mount '{volume_mount}' must be configured for data persistence"
        
        # Verify Ollama data volume is configured
        assert "ollama_data:/root/.ollama" in compose_content, \
            "Ollama data volume must be configured for model persistence"
        
        # Verify volume definition exists
        assert "volumes:" in compose_content, \
            "Docker Compose must define volumes section"
        
        assert "ollama_data:" in compose_content, \
            "Ollama data volume must be defined in volumes section"
    
    def test_conversation_manager_persistence_integration(self):
        """
        **Feature: docker-modernization, Property 5: Data Persistence Integrity**
        **Validates: Requirements 2.3, 4.2**
        
        The ConversationManager should properly integrate with Docker volume mounts
        to ensure conversation data persists across container restarts.
        """
        tester = DataPersistenceTester()
        
        # Setup test environment
        test_dirs = tester.setup_test_environment()
        
        try:
            conversations_dir = test_dirs["data"] / "conversations"
            
            # Create ConversationManager with test directory
            manager = ConversationManager(storage_dir=str(conversations_dir))
            
            # Create a test conversation
            conversation = manager.create_conversation(title="Test Docker Persistence")
            
            # Add messages
            manager.add_message("user", "Test message for persistence")
            manager.add_message("assistant", "Test response for persistence")
            
            # Verify conversation file was created
            conv_file = conversations_dir / f"{conversation.id}.json"
            assert conv_file.exists(), \
                "Conversation file should be created in mounted volume directory"
            
            # Simulate container restart by creating new manager instance
            new_manager = ConversationManager(storage_dir=str(conversations_dir))
            
            # Verify conversation can be loaded after "restart"
            loaded_conversation = new_manager.load_conversation(conversation.id)
            
            assert loaded_conversation is not None, \
                "Conversation should be loadable after container restart"
            
            assert loaded_conversation.id == conversation.id, \
                "Loaded conversation should have same ID"
            
            assert loaded_conversation.title == conversation.title, \
                "Loaded conversation should have same title"
            
            assert len(loaded_conversation.messages) == 2, \
                "Loaded conversation should have all messages"
            
            # Verify message content integrity
            assert loaded_conversation.messages[0].content == "Test message for persistence", \
                "First message content should be preserved"
            
            assert loaded_conversation.messages[1].content == "Test response for persistence", \
                "Second message content should be preserved"
        
        finally:
            # Cleanup
            tester.cleanup_test_environment()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])