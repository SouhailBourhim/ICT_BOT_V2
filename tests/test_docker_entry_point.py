"""Example tests for Docker container entry point correctness"""
import pytest
import subprocess
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any
import docker
import os
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import settings


class DockerEntryPointTester:
    """Helper class for testing Docker entry point functionality"""
    
    def __init__(self):
        self.docker_client = None
        self.container = None
        self.dockerfile_path = Path(__file__).parent.parent / "docker" / "Dockerfile"
        self.app_entry_point = Path(__file__).parent.parent / "app" / "chat.py"
        
    def setup_docker_client(self):
        """Setup Docker client for testing"""
        try:
            self.docker_client = docker.from_env()
            return True
        except Exception:
            return False
    
    def check_entry_point_file_exists(self) -> bool:
        """Check if the correct entry point file exists"""
        return self.app_entry_point.exists()
    
    def check_dockerfile_entry_point(self) -> Dict[str, Any]:
        """Check Dockerfile configuration for correct entry point"""
        if not self.dockerfile_path.exists():
            return {"valid": False, "error": "Dockerfile not found"}
        
        with open(self.dockerfile_path, 'r') as f:
            dockerfile_content = f.read()
        
        # Check for correct CMD configuration
        has_correct_cmd = "app/chat.py" in dockerfile_content
        has_streamlit_run = "streamlit" in dockerfile_content and "run" in dockerfile_content
        has_correct_port = "8501" in dockerfile_content
        
        return {
            "valid": has_correct_cmd and has_streamlit_run and has_correct_port,
            "has_correct_entry_point": has_correct_cmd,
            "has_streamlit_command": has_streamlit_run,
            "has_correct_port": has_correct_port,
            "content": dockerfile_content
        }
    
    def check_application_imports(self) -> Dict[str, Any]:
        """Check if the entry point file has all required imports for enhanced features"""
        if not self.app_entry_point.exists():
            return {"valid": False, "error": "Entry point file not found"}
        
        with open(self.app_entry_point, 'r') as f:
            content = f.read()
        
        # Check for enhanced feature imports
        required_imports = {
            "math_rendering": "math_renderer" in content,
            "conversation_management": "ConversationManager" in content,
            "document_processing": "DocumentParser" in content,
            "vector_store": "VectorStore" in content,
            "llm_integration": "OllamaClient" in content,
            "streamlit": "import streamlit" in content
        }
        
        all_imports_present = all(required_imports.values())
        
        return {
            "valid": all_imports_present,
            "imports": required_imports,
            "missing_imports": [k for k, v in required_imports.items() if not v]
        }
    
    def check_application_initialization(self) -> Dict[str, Any]:
        """Check if the application properly initializes all components"""
        if not self.app_entry_point.exists():
            return {"valid": False, "error": "Entry point file not found"}
        
        with open(self.app_entry_point, 'r') as f:
            content = f.read()
        
        # Check for component initialization in initialize_system function
        required_components = {
            "vector_store": "VectorStore(" in content,
            "embedding_generator": "EmbeddingGenerator(" in content,
            "hybrid_search": "HybridSearchEngine(" in content,
            "ollama_client": "OllamaClient(" in content,
            "response_generator": "ResponseGenerator(" in content,
            "conversation_manager": "ConversationManager(" in content
        }
        
        all_components_initialized = all(required_components.values())
        
        return {
            "valid": all_components_initialized,
            "components": required_components,
            "missing_components": [k for k, v in required_components.items() if not v]
        }
    
    def simulate_container_startup(self) -> Dict[str, Any]:
        """Simulate container startup to test entry point behavior"""
        # Mock the container environment
        with patch.dict(os.environ, {
            'PYTHONPATH': '/app',
            'STREAMLIT_SERVER_PORT': '8501',
            'STREAMLIT_SERVER_ADDRESS': '0.0.0.0'
        }):
            try:
                # Test if the entry point file can be imported without errors
                import importlib.util
                spec = importlib.util.spec_from_file_location("chat", self.app_entry_point)
                
                if spec is None:
                    return {"valid": False, "error": "Cannot create module spec"}
                
                # Check if the module can be loaded (without executing main)
                module = importlib.util.module_from_spec(spec)
                
                # Mock streamlit to avoid actual execution
                with patch('streamlit.set_page_config'), \
                     patch('streamlit.markdown'), \
                     patch('streamlit.cache_resource'), \
                     patch('streamlit.sidebar'), \
                     patch('streamlit.chat_message'), \
                     patch('streamlit.chat_input'):
                    
                    # Try to load the module
                    spec.loader.exec_module(module)
                    
                    # Check if required functions exist
                    required_functions = [
                        'initialize_system',
                        'render_sidebar', 
                        'render_main_chat',
                        'main'
                    ]
                    
                    missing_functions = []
                    for func_name in required_functions:
                        if not hasattr(module, func_name):
                            missing_functions.append(func_name)
                    
                    return {
                        "valid": len(missing_functions) == 0,
                        "functions_present": len(missing_functions) == 0,
                        "missing_functions": missing_functions,
                        "module_loaded": True
                    }
                    
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Module loading failed: {str(e)}",
                    "module_loaded": False
                }


# **Feature: docker-modernization, Property 1: Application Feature Completeness**
class TestDockerEntryPointCorrectness:
    """Example tests for Docker entry point correctness"""
    
    def test_correct_entry_point_file_exists(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The correct Streamlit entry point file (app/chat.py) should exist
        and be accessible for Docker container startup.
        """
        tester = DockerEntryPointTester()
        
        # Test that the entry point file exists
        assert tester.check_entry_point_file_exists(), \
            "Entry point file app/chat.py must exist for Docker container to start correctly"
        
        # Verify it's a Python file
        assert tester.app_entry_point.suffix == '.py', \
            "Entry point must be a Python file"
        
        # Verify it's not empty
        assert tester.app_entry_point.stat().st_size > 0, \
            "Entry point file must not be empty"
    
    def test_dockerfile_uses_correct_entry_point(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The Dockerfile should specify the correct entry point (app/chat.py)
        in its CMD instruction.
        """
        tester = DockerEntryPointTester()
        
        dockerfile_check = tester.check_dockerfile_entry_point()
        
        assert dockerfile_check["valid"], \
            f"Dockerfile must use correct entry point. Issues: {dockerfile_check}"
        
        assert dockerfile_check["has_correct_entry_point"], \
            "Dockerfile CMD must reference app/chat.py as entry point"
        
        assert dockerfile_check["has_streamlit_command"], \
            "Dockerfile CMD must use 'streamlit' and 'run' commands"
        
        assert dockerfile_check["has_correct_port"], \
            "Dockerfile must expose port 8501 for Streamlit"
    
    def test_entry_point_has_enhanced_feature_imports(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The entry point file should import all components needed
        for enhanced features (math rendering, analytics, conversation management).
        """
        tester = DockerEntryPointTester()
        
        imports_check = tester.check_application_imports()
        
        assert imports_check["valid"], \
            f"Entry point must import all enhanced features. Missing: {imports_check['missing_imports']}"
        
        # Verify specific enhanced features are imported
        assert imports_check["imports"]["math_rendering"], \
            "Entry point must import math rendering components"
        
        assert imports_check["imports"]["conversation_management"], \
            "Entry point must import conversation management components"
        
        assert imports_check["imports"]["document_processing"], \
            "Entry point must import document processing components"
        
        assert imports_check["imports"]["streamlit"], \
            "Entry point must import Streamlit framework"
    
    def test_entry_point_initializes_all_components(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The entry point should properly initialize all system components
        required for the RAG application to function correctly.
        """
        tester = DockerEntryPointTester()
        
        init_check = tester.check_application_initialization()
        
        assert init_check["valid"], \
            f"Entry point must initialize all components. Missing: {init_check['missing_components']}"
        
        # Verify core components are initialized
        assert init_check["components"]["vector_store"], \
            "Entry point must initialize VectorStore component"
        
        assert init_check["components"]["ollama_client"], \
            "Entry point must initialize OllamaClient component"
        
        assert init_check["components"]["conversation_manager"], \
            "Entry point must initialize ConversationManager component"
        
        assert init_check["components"]["response_generator"], \
            "Entry point must initialize ResponseGenerator component"
    
    def test_entry_point_module_loads_correctly(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The entry point module should load without errors and contain
        all required functions for proper application startup.
        """
        tester = DockerEntryPointTester()
        
        startup_check = tester.simulate_container_startup()
        
        assert startup_check["valid"], \
            f"Entry point module must load correctly. Error: {startup_check.get('error', 'Unknown error')}"
        
        assert startup_check["module_loaded"], \
            "Entry point module must be loadable without import errors"
        
        assert startup_check["functions_present"], \
            f"Entry point must contain all required functions. Missing: {startup_check.get('missing_functions', [])}"
    
    def test_entry_point_streamlit_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.1**
        
        Example test: The entry point should properly configure Streamlit with
        correct page settings for the RAG application.
        """
        tester = DockerEntryPointTester()
        
        if not tester.app_entry_point.exists():
            pytest.skip("Entry point file not found")
        
        with open(tester.app_entry_point, 'r') as f:
            content = f.read()
        
        # Check for Streamlit page configuration
        assert "st.set_page_config" in content, \
            "Entry point must configure Streamlit page settings"
        
        # Check for proper page title configuration
        assert "page_title" in content, \
            "Entry point must set page title"
        
        # Check for layout configuration
        assert "layout" in content, \
            "Entry point must configure page layout"
        
        # Check for main function
        assert "def main():" in content, \
            "Entry point must have main() function"
        
        # Check for proper execution guard
        assert 'if __name__ == "__main__":' in content, \
            "Entry point must have proper execution guard"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])