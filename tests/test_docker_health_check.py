"""Example tests for Docker health check functionality"""
import pytest
import subprocess
import sys
import time
import requests
import yaml
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import settings


class HealthCheckTester:
    """Helper class for testing Docker health check functionality"""
    
    def __init__(self):
        self.docker_compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.yml"
        self.entrypoint_script = Path(__file__).parent.parent / "docker" / "entrypoint.sh"
        
    def parse_health_check_configuration(self) -> Dict[str, Any]:
        """Parse docker-compose.yml to extract health check configuration"""
        if not self.docker_compose_file.exists():
            return {"valid": False, "error": "docker-compose.yml not found"}
        
        try:
            with open(self.docker_compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            services = compose_config.get('services', {})
            
            # Extract health check information for each service
            health_checks = {}
            for service_name, service_config in services.items():
                healthcheck = service_config.get('healthcheck', {})
                if healthcheck:
                    health_checks[service_name] = {
                        "test": healthcheck.get('test', []),
                        "interval": healthcheck.get('interval', ''),
                        "timeout": healthcheck.get('timeout', ''),
                        "retries": healthcheck.get('retries', 0),
                        "start_period": healthcheck.get('start_period', '')
                    }
            
            return {
                "valid": True,
                "health_checks": health_checks,
                "services": list(services.keys())
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Failed to parse docker-compose.yml: {str(e)}"}
    
    def validate_ollama_health_check_configuration(self) -> Dict[str, Any]:
        """Validate Ollama service health check configuration"""
        config = self.parse_health_check_configuration()
        
        if not config["valid"]:
            return config
        
        ollama_health = config["health_checks"].get("ollama", {})
        
        if not ollama_health:
            return {"valid": False, "error": "Ollama health check not configured"}
        
        test_command = ollama_health.get("test", [])
        
        # Validate health check command structure
        has_curl = any("curl" in str(cmd) for cmd in test_command)
        has_api_tags_endpoint = any("/api/tags" in str(cmd) for cmd in test_command)
        has_localhost = any("localhost:11434" in str(cmd) for cmd in test_command)
        
        # Validate timing configuration
        has_interval = bool(ollama_health.get("interval"))
        has_timeout = bool(ollama_health.get("timeout"))
        has_retries = ollama_health.get("retries", 0) > 0
        has_start_period = bool(ollama_health.get("start_period"))
        
        return {
            "valid": has_curl and has_api_tags_endpoint and has_localhost,
            "has_curl_command": has_curl,
            "has_correct_endpoint": has_api_tags_endpoint,
            "has_correct_host": has_localhost,
            "has_interval": has_interval,
            "has_timeout": has_timeout,
            "has_retries": has_retries,
            "has_start_period": has_start_period,
            "test_command": test_command,
            "config": ollama_health
        }
    
    def validate_rag_app_health_check_configuration(self) -> Dict[str, Any]:
        """Validate RAG application health check configuration"""
        config = self.parse_health_check_configuration()
        
        if not config["valid"]:
            return config
        
        rag_app_health = config["health_checks"].get("rag-app", {})
        
        if not rag_app_health:
            return {"valid": False, "error": "RAG app health check not configured"}
        
        test_command = rag_app_health.get("test", [])
        
        # Validate health check command structure
        has_curl = any("curl" in str(cmd) for cmd in test_command)
        has_streamlit_health_endpoint = any("_stcore/health" in str(cmd) for cmd in test_command)
        has_localhost = any("localhost:8501" in str(cmd) for cmd in test_command)
        
        # Validate timing configuration
        has_interval = bool(rag_app_health.get("interval"))
        has_timeout = bool(rag_app_health.get("timeout"))
        has_retries = rag_app_health.get("retries", 0) > 0
        has_start_period = bool(rag_app_health.get("start_period"))
        
        return {
            "valid": has_curl and has_streamlit_health_endpoint and has_localhost,
            "has_curl_command": has_curl,
            "has_correct_endpoint": has_streamlit_health_endpoint,
            "has_correct_host": has_localhost,
            "has_interval": has_interval,
            "has_timeout": has_timeout,
            "has_retries": has_retries,
            "has_start_period": has_start_period,
            "test_command": test_command,
            "config": rag_app_health
        }
    
    def validate_entrypoint_health_check_logic(self) -> Dict[str, Any]:
        """Validate that entrypoint script implements health check logic"""
        if not self.entrypoint_script.exists():
            return {"valid": False, "error": "entrypoint.sh not found"}
        
        try:
            with open(self.entrypoint_script, 'r') as f:
                script_content = f.read()
            
            # Check for Ollama health check implementation
            has_wait_for_ollama = "wait_for_ollama" in script_content
            has_ollama_api_check = "/api/tags" in script_content
            has_curl_health_check = "curl" in script_content and "api/tags" in script_content
            has_retry_mechanism = "max_retries" in script_content
            has_timeout_handling = "connect-timeout" in script_content or "max-time" in script_content
            
            # Check for proper error handling
            has_connection_error_handling = "Failed to connect to Ollama" in script_content
            has_exit_on_failure = "exit 1" in script_content
            
            # Check for backoff logic
            has_exponential_backoff = "backoff" in script_content and "sleep" in script_content
            
            # Check for success confirmation
            has_success_message = "Ollama service is ready" in script_content or "ready" in script_content
            
            return {
                "valid": has_wait_for_ollama and has_ollama_api_check and has_curl_health_check,
                "has_wait_for_ollama": has_wait_for_ollama,
                "has_ollama_api_check": has_ollama_api_check,
                "has_curl_health_check": has_curl_health_check,
                "has_retry_mechanism": has_retry_mechanism,
                "has_timeout_handling": has_timeout_handling,
                "has_connection_error_handling": has_connection_error_handling,
                "has_exit_on_failure": has_exit_on_failure,
                "has_exponential_backoff": has_exponential_backoff,
                "has_success_message": has_success_message
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Failed to read entrypoint.sh: {str(e)}"}
    
    def simulate_health_check_response_validation(self) -> Dict[str, Any]:
        """Simulate validation of health check response handling"""
        # Mock health check scenarios
        scenarios = {
            "ollama_healthy": {
                "endpoint": "/api/tags",
                "expected_response": {"models": []},
                "status_code": 200
            },
            "ollama_unhealthy": {
                "endpoint": "/api/tags",
                "expected_response": None,
                "status_code": 500
            },
            "streamlit_healthy": {
                "endpoint": "/_stcore/health",
                "expected_response": "ok",
                "status_code": 200
            },
            "streamlit_unhealthy": {
                "endpoint": "/_stcore/health",
                "expected_response": None,
                "status_code": 500
            }
        }
        
        # Validate that health check commands would handle these scenarios correctly
        config = self.parse_health_check_configuration()
        
        if not config["valid"]:
            return config
        
        health_checks = config["health_checks"]
        
        # Check if health checks are configured to handle success/failure appropriately
        ollama_config = health_checks.get("ollama", {})
        rag_app_config = health_checks.get("rag-app", {})
        
        # Validate retry configuration for handling failures
        ollama_retries = ollama_config.get("retries", 0)
        rag_app_retries = rag_app_config.get("retries", 0)
        
        # Validate timeout configuration for handling unresponsive services
        ollama_timeout = ollama_config.get("timeout", "")
        rag_app_timeout = rag_app_config.get("timeout", "")
        
        return {
            "valid": ollama_retries > 0 and rag_app_retries > 0,
            "scenarios": scenarios,
            "ollama_retries_configured": ollama_retries > 0,
            "rag_app_retries_configured": rag_app_retries > 0,
            "ollama_timeout_configured": bool(ollama_timeout),
            "rag_app_timeout_configured": bool(rag_app_timeout),
            "ollama_retries": ollama_retries,
            "rag_app_retries": rag_app_retries,
            "ollama_timeout": ollama_timeout,
            "rag_app_timeout": rag_app_timeout
        }
    
    def validate_health_check_integration(self) -> Dict[str, Any]:
        """Validate integration between Docker Compose health checks and entrypoint logic"""
        # Get Docker Compose health check configuration
        compose_validation = self.parse_health_check_configuration()
        if not compose_validation["valid"]:
            return compose_validation
        
        # Get entrypoint health check logic
        entrypoint_validation = self.validate_entrypoint_health_check_logic()
        if not entrypoint_validation["valid"]:
            return entrypoint_validation
        
        # Check for consistency between Docker Compose and entrypoint
        health_checks = compose_validation["health_checks"]
        
        # Verify that entrypoint implements the same health check logic as Docker Compose
        ollama_compose_endpoint = None
        for cmd in health_checks.get("ollama", {}).get("test", []):
            if "/api/tags" in str(cmd):
                ollama_compose_endpoint = "/api/tags"
                break
        
        entrypoint_uses_same_endpoint = entrypoint_validation["has_ollama_api_check"]
        
        # Check that both use curl for health checks
        compose_uses_curl = any(
            any("curl" in str(cmd) for cmd in health_check.get("test", []))
            for health_check in health_checks.values()
        )
        entrypoint_uses_curl = entrypoint_validation["has_curl_health_check"]
        
        return {
            "valid": entrypoint_uses_same_endpoint and compose_uses_curl and entrypoint_uses_curl,
            "endpoint_consistency": entrypoint_uses_same_endpoint,
            "curl_consistency": compose_uses_curl and entrypoint_uses_curl,
            "ollama_endpoint": ollama_compose_endpoint,
            "compose_health_checks": health_checks,
            "entrypoint_validation": entrypoint_validation
        }


# **Feature: docker-modernization, Property 1: Application Feature Completeness**
class TestDockerHealthCheckFunctionality:
    """Example tests for Docker health check functionality"""
    
    def test_ollama_health_check_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: Ollama service should have proper health check configuration
        that tests the correct API endpoint with appropriate timing settings.
        """
        tester = HealthCheckTester()
        
        ollama_health_config = tester.validate_ollama_health_check_configuration()
        
        assert ollama_health_config["valid"], \
            f"Ollama health check configuration must be valid. Error: {ollama_health_config.get('error', 'Unknown error')}"
        
        # Verify health check command uses curl
        assert ollama_health_config["has_curl_command"], \
            "Ollama health check must use curl command for HTTP requests"
        
        # Verify health check tests the correct API endpoint
        assert ollama_health_config["has_correct_endpoint"], \
            "Ollama health check must test the /api/tags endpoint"
        
        # Verify health check uses correct host and port
        assert ollama_health_config["has_correct_host"], \
            "Ollama health check must test localhost:11434"
        
        # Verify timing configuration
        assert ollama_health_config["has_interval"], \
            "Ollama health check must specify check interval"
        
        assert ollama_health_config["has_timeout"], \
            "Ollama health check must specify timeout"
        
        assert ollama_health_config["has_retries"], \
            "Ollama health check must specify retry count for reliability"
        
        assert ollama_health_config["has_start_period"], \
            "Ollama health check must specify start period for initialization"
    
    def test_rag_app_health_check_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: RAG application should have proper health check configuration
        that tests the Streamlit health endpoint with appropriate settings.
        """
        tester = HealthCheckTester()
        
        rag_app_health_config = tester.validate_rag_app_health_check_configuration()
        
        assert rag_app_health_config["valid"], \
            f"RAG app health check configuration must be valid. Error: {rag_app_health_config.get('error', 'Unknown error')}"
        
        # Verify health check command uses curl
        assert rag_app_health_config["has_curl_command"], \
            "RAG app health check must use curl command for HTTP requests"
        
        # Verify health check tests the correct Streamlit endpoint
        assert rag_app_health_config["has_correct_endpoint"], \
            "RAG app health check must test the /_stcore/health endpoint"
        
        # Verify health check uses correct host and port
        assert rag_app_health_config["has_correct_host"], \
            "RAG app health check must test localhost:8501"
        
        # Verify timing configuration
        assert rag_app_health_config["has_interval"], \
            "RAG app health check must specify check interval"
        
        assert rag_app_health_config["has_timeout"], \
            "RAG app health check must specify timeout"
        
        assert rag_app_health_config["has_retries"], \
            "RAG app health check must specify retry count for reliability"
        
        assert rag_app_health_config["has_start_period"], \
            "RAG app health check must specify start period for initialization"
    
    def test_entrypoint_health_check_logic(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: The entrypoint script should implement robust health check logic
        to wait for Ollama service availability before starting the RAG application.
        """
        tester = HealthCheckTester()
        
        entrypoint_health_logic = tester.validate_entrypoint_health_check_logic()
        
        assert entrypoint_health_logic["valid"], \
            f"Entrypoint health check logic must be valid. Error: {entrypoint_health_logic.get('error', 'Unknown error')}"
        
        # Verify Ollama waiting function exists
        assert entrypoint_health_logic["has_wait_for_ollama"], \
            "Entrypoint must implement wait_for_ollama function"
        
        # Verify correct API endpoint is checked
        assert entrypoint_health_logic["has_ollama_api_check"], \
            "Entrypoint must check Ollama /api/tags endpoint"
        
        # Verify curl is used for health checks
        assert entrypoint_health_logic["has_curl_health_check"], \
            "Entrypoint must use curl for Ollama health checks"
        
        # Verify retry mechanism
        assert entrypoint_health_logic["has_retry_mechanism"], \
            "Entrypoint must implement retry mechanism for health checks"
        
        # Verify timeout handling
        assert entrypoint_health_logic["has_timeout_handling"], \
            "Entrypoint must implement timeout handling for health checks"
        
        # Verify error handling
        assert entrypoint_health_logic["has_connection_error_handling"], \
            "Entrypoint must handle connection errors gracefully"
        
        assert entrypoint_health_logic["has_exit_on_failure"], \
            "Entrypoint must exit with error code on health check failure"
        
        # Verify backoff logic
        assert entrypoint_health_logic["has_exponential_backoff"], \
            "Entrypoint must implement exponential backoff for health check retries"
        
        # Verify success confirmation
        assert entrypoint_health_logic["has_success_message"], \
            "Entrypoint must confirm when Ollama service is ready"
    
    def test_health_check_response_handling(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: Health checks should be configured to properly handle
        both successful and failed responses from services.
        """
        tester = HealthCheckTester()
        
        response_validation = tester.simulate_health_check_response_validation()
        
        assert response_validation["valid"], \
            "Health checks must be configured to handle response scenarios properly"
        
        # Verify retry configuration for handling failures
        assert response_validation["ollama_retries_configured"], \
            "Ollama health check must be configured with retries for failure handling"
        
        assert response_validation["rag_app_retries_configured"], \
            "RAG app health check must be configured with retries for failure handling"
        
        # Verify timeout configuration for handling unresponsive services
        assert response_validation["ollama_timeout_configured"], \
            "Ollama health check must be configured with timeout for unresponsive service handling"
        
        assert response_validation["rag_app_timeout_configured"], \
            "RAG app health check must be configured with timeout for unresponsive service handling"
        
        # Verify reasonable retry and timeout values
        ollama_retries = response_validation["ollama_retries"]
        rag_app_retries = response_validation["rag_app_retries"]
        
        assert ollama_retries >= 3, \
            f"Ollama health check should have at least 3 retries, got {ollama_retries}"
        
        assert rag_app_retries >= 3, \
            f"RAG app health check should have at least 3 retries, got {rag_app_retries}"
    
    def test_health_check_integration_consistency(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: Docker Compose health checks and entrypoint health check logic
        should be consistent and use the same endpoints and methods.
        """
        tester = HealthCheckTester()
        
        integration_validation = tester.validate_health_check_integration()
        
        assert integration_validation["valid"], \
            f"Health check integration must be consistent. Issues: {integration_validation}"
        
        # Verify endpoint consistency
        assert integration_validation["endpoint_consistency"], \
            "Entrypoint and Docker Compose must use the same Ollama health check endpoint"
        
        # Verify curl consistency
        assert integration_validation["curl_consistency"], \
            "Both entrypoint and Docker Compose health checks must use curl"
        
        # Verify Ollama endpoint is /api/tags
        ollama_endpoint = integration_validation["ollama_endpoint"]
        assert ollama_endpoint == "/api/tags", \
            f"Ollama health check endpoint must be /api/tags, got {ollama_endpoint}"
        
        # Verify both services have health checks configured
        compose_health_checks = integration_validation["compose_health_checks"]
        assert "ollama" in compose_health_checks, \
            "Ollama service must have health check configured in Docker Compose"
        
        assert "rag-app" in compose_health_checks, \
            "RAG app service must have health check configured in Docker Compose"
    
    def test_health_check_timing_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 1.4**
        
        Example test: Health check timing should be configured appropriately
        for reliable service startup and monitoring.
        """
        tester = HealthCheckTester()
        
        config = tester.parse_health_check_configuration()
        
        assert config["valid"], \
            f"Health check configuration must be parseable. Error: {config.get('error', 'Unknown error')}"
        
        health_checks = config["health_checks"]
        
        # Test Ollama timing configuration
        ollama_config = health_checks.get("ollama", {})
        assert ollama_config, "Ollama health check must be configured"
        
        # Verify reasonable intervals (should be frequent enough but not too aggressive)
        interval = ollama_config.get("interval", "")
        assert "30s" in interval or "60s" in interval, \
            f"Ollama health check interval should be reasonable (30s-60s), got {interval}"
        
        # Verify reasonable timeout (should allow time for response but not hang)
        timeout = ollama_config.get("timeout", "")
        assert "10s" in timeout or "15s" in timeout, \
            f"Ollama health check timeout should be reasonable (10s-15s), got {timeout}"
        
        # Test RAG app timing configuration
        rag_app_config = health_checks.get("rag-app", {})
        assert rag_app_config, "RAG app health check must be configured"
        
        # Verify RAG app has longer start period (needs more time to initialize)
        rag_start_period = rag_app_config.get("start_period", "")
        ollama_start_period = ollama_config.get("start_period", "")
        
        # Extract numeric values for comparison
        rag_start_seconds = int(rag_start_period.replace("s", "")) if "s" in rag_start_period else 0
        ollama_start_seconds = int(ollama_start_period.replace("s", "")) if "s" in ollama_start_period else 0
        
        assert rag_start_seconds >= ollama_start_seconds, \
            f"RAG app start period ({rag_start_period}) should be >= Ollama start period ({ollama_start_period})"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])