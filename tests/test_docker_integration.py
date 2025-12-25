"""Integration tests for Docker container functionality"""
import pytest
import subprocess
import sys
import docker
import os
from pathlib import Path
from typing import Dict, Any
import tempfile
import shutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class DockerIntegrationTester:
    """Helper class for Docker integration testing"""
    
    def __init__(self):
        self.docker_client = None
        self.container = None
        self.app_root = Path(__file__).parent.parent
        self.image_name = "inpt-rag-test"
        self.container_name = "inpt-rag-test-container"
        
    def setup_docker_client(self):
        """Setup Docker client for testing"""
        try:
            self.docker_client = docker.from_env()
            return True
        except Exception as e:
            print(f"Docker client setup failed: {e}")
            return False
    
    def cleanup_container(self):
        """Cleanup test container and image"""
        try:
            if self.docker_client:
                # Stop and remove container
                try:
                    container = self.docker_client.containers.get(self.container_name)
                    container.stop(timeout=10)
                    container.remove()
                except docker.errors.NotFound:
                    pass
                
                # Remove image
                try:
                    self.docker_client.images.remove(self.image_name, force=True)
                except docker.errors.ImageNotFound:
                    pass
        except Exception as e:
            print(f"Cleanup warning: {e}")
    
    def check_dockerfile_exists(self) -> bool:
        """Check if Dockerfile exists and is valid"""
        dockerfile_path = self.app_root / "docker" / "Dockerfile"
        return dockerfile_path.exists()
    
    def check_docker_compose_exists(self) -> bool:
        """Check if docker-compose.yml exists"""
        compose_path = self.app_root / "docker" / "docker-compose.yml"
        return compose_path.exists()
    
    def build_docker_image(self) -> Dict[str, Any]:
        """Build Docker image for testing"""
        if not self.setup_docker_client():
            return {"success": False, "error": "Docker client unavailable"}
        
        try:
            # Build the image
            dockerfile_path = self.app_root / "docker" / "Dockerfile"
            
            # Use docker build command instead of docker-py for better compatibility
            build_cmd = [
                "docker", "build",
                "-f", str(dockerfile_path),
                "-t", self.image_name,
                str(self.app_root)
            ]
            
            result = subprocess.run(
                build_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "image_built": True,
                    "build_output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": f"Build failed: {result.stderr}",
                    "build_output": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Build timeout (5 minutes)",
                "image_built": False
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "image_built": False
            }
    
    def test_container_startup(self) -> Dict[str, Any]:
        """Test container startup without full service dependencies"""
        if not self.setup_docker_client():
            return {"success": False, "error": "Docker client unavailable"}
        
        try:
            # Create a simple test to verify the container can start
            # We'll use a command that doesn't require Ollama to be running
            test_cmd = ["python", "-c", "import sys; print('Container startup test passed'); sys.exit(0)"]
            
            container = self.docker_client.containers.run(
                self.image_name,
                command=test_cmd,
                detach=True,
                name=f"{self.container_name}-startup-test",
                remove=True,
                environment={
                    'PYTHONPATH': '/app',
                    'PYTHONUNBUFFERED': '1'
                }
            )
            
            # Wait for container to complete
            result = container.wait(timeout=30)
            logs = container.logs().decode('utf-8')
            
            return {
                "success": result['StatusCode'] == 0,
                "exit_code": result['StatusCode'],
                "logs": logs,
                "container_started": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "container_started": False
            }
    
    def test_application_imports(self) -> Dict[str, Any]:
        """Test that the application can import all required modules"""
        if not self.setup_docker_client():
            return {"success": False, "error": "Docker client unavailable"}
        
        try:
            # Test import of main application modules
            import_test_cmd = [
                "python", "-c", """
import sys
sys.path.append('/app')

try:
    # Test core imports
    from src.config.settings import settings
    from src.document_processing.parser import DocumentParser
    from src.conversation.manager import ConversationManager
    from app.components.math_renderer import render_math_content
    
    print('All imports successful')
    sys.exit(0)
except ImportError as e:
    print(f'Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Other error: {e}')
    sys.exit(2)
"""
            ]
            
            container = self.docker_client.containers.run(
                self.image_name,
                command=import_test_cmd,
                detach=True,
                name=f"{self.container_name}-import-test",
                remove=True,
                environment={
                    'PYTHONPATH': '/app',
                    'PYTHONUNBUFFERED': '1'
                }
            )
            
            # Wait for container to complete
            result = container.wait(timeout=60)
            logs = container.logs().decode('utf-8')
            
            return {
                "success": result['StatusCode'] == 0,
                "exit_code": result['StatusCode'],
                "logs": logs,
                "imports_working": result['StatusCode'] == 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "imports_working": False
            }


class TestDockerIntegration:
    """Integration tests for Docker container functionality"""
    
    @pytest.fixture(scope="class")
    def docker_tester(self):
        """Setup Docker tester and cleanup after tests"""
        tester = DockerIntegrationTester()
        yield tester
        tester.cleanup_container()
    
    def test_docker_files_exist(self, docker_tester):
        """
        Test that required Docker files exist
        Requirements: 1.1, 2.1
        """
        assert docker_tester.check_dockerfile_exists(), \
            "Dockerfile must exist for container builds"
        
        assert docker_tester.check_docker_compose_exists(), \
            "docker-compose.yml must exist for service orchestration"
    
    @pytest.mark.slow
    def test_docker_image_builds_successfully(self, docker_tester):
        """
        Test that Docker image builds successfully with all dependencies
        Requirements: 1.3, 3.1, 3.2
        """
        # Skip if Docker is not available
        if not docker_tester.setup_docker_client():
            pytest.skip("Docker not available for testing")
        
        build_result = docker_tester.build_docker_image()
        
        assert build_result["success"], \
            f"Docker image must build successfully. Error: {build_result.get('error', 'Unknown')}"
        
        assert build_result["image_built"], \
            "Docker image must be created during build process"
    
    @pytest.mark.slow
    def test_container_starts_without_errors(self, docker_tester):
        """
        Test that container starts without errors
        Requirements: 1.1, 1.4
        """
        # Skip if Docker is not available
        if not docker_tester.setup_docker_client():
            pytest.skip("Docker not available for testing")
        
        # First build the image
        build_result = docker_tester.build_docker_image()
        if not build_result["success"]:
            pytest.skip(f"Cannot test startup - build failed: {build_result.get('error')}")
        
        startup_result = docker_tester.test_container_startup()
        
        assert startup_result["success"], \
            f"Container must start successfully. Error: {startup_result.get('error', 'Unknown')}"
        
        assert startup_result["container_started"], \
            "Container startup process must complete successfully"
        
        # Check that exit code is 0 (success)
        assert startup_result["exit_code"] == 0, \
            f"Container must exit with code 0, got {startup_result['exit_code']}"
    
    @pytest.mark.slow
    def test_application_modules_importable_in_container(self, docker_tester):
        """
        Test that all application modules can be imported in container
        Requirements: 1.2, 1.3
        """
        # Skip if Docker is not available
        if not docker_tester.setup_docker_client():
            pytest.skip("Docker not available for testing")
        
        # First build the image
        build_result = docker_tester.build_docker_image()
        if not build_result["success"]:
            pytest.skip(f"Cannot test imports - build failed: {build_result.get('error')}")
        
        import_result = docker_tester.test_application_imports()
        
        assert import_result["success"], \
            f"Application modules must be importable. Error: {import_result.get('error', 'Unknown')}"
        
        assert import_result["imports_working"], \
            f"All required imports must work in container. Logs: {import_result.get('logs', 'No logs')}"
        
        # Check that exit code is 0 (success)
        assert import_result["exit_code"] == 0, \
            f"Import test must exit with code 0, got {import_result['exit_code']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])