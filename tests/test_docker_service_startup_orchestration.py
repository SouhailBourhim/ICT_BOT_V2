"""Example tests for Docker service startup orchestration"""
import pytest
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import settings


class ServiceStartupOrchestrationTester:
    """Helper class for testing Docker service startup orchestration"""
    
    def __init__(self):
        self.docker_compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.yml"
        self.entrypoint_script = Path(__file__).parent.parent / "docker" / "entrypoint.sh"
        
    def parse_docker_compose_configuration(self) -> Dict[str, Any]:
        """Parse docker-compose.yml to extract service configuration"""
        if not self.docker_compose_file.exists():
            return {"valid": False, "error": "docker-compose.yml not found"}
        
        try:
            with open(self.docker_compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            services = compose_config.get('services', {})
            
            # Extract service information
            service_info = {}
            for service_name, service_config in services.items():
                service_info[service_name] = {
                    "depends_on": service_config.get('depends_on', {}),
                    "healthcheck": service_config.get('healthcheck', {}),
                    "restart": service_config.get('restart', 'no'),
                    "ports": service_config.get('ports', []),
                    "environment": service_config.get('environment', {}),
                    "image": service_config.get('image', ''),
                    "build": service_config.get('build', {})
                }
            
            return {
                "valid": True,
                "services": service_info,
                "version": compose_config.get('version', ''),
                "volumes": compose_config.get('volumes', {})
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Failed to parse docker-compose.yml: {str(e)}"}
    
    def validate_service_dependency_configuration(self) -> Dict[str, Any]:
        """Validate that services are configured with proper dependencies"""
        compose_config = self.parse_docker_compose_configuration()
        
        if not compose_config["valid"]:
            return compose_config
        
        services = compose_config["services"]
        
        # Check if both required services exist
        has_ollama = "ollama" in services
        has_rag_app = "rag-app" in services
        
        if not (has_ollama and has_rag_app):
            return {
                "valid": False,
                "error": f"Missing required services. Has ollama: {has_ollama}, Has rag-app: {has_rag_app}"
            }
        
        # Check dependency configuration
        rag_app_config = services["rag-app"]
        depends_on = rag_app_config.get("depends_on", {})
        
        # Validate that rag-app depends on ollama
        ollama_dependency_configured = "ollama" in depends_on
        
        # Check if health condition is specified
        health_condition_configured = False
        if isinstance(depends_on, dict) and "ollama" in depends_on:
            ollama_dep_config = depends_on["ollama"]
            if isinstance(ollama_dep_config, dict):
                health_condition_configured = ollama_dep_config.get("condition") == "service_healthy"
            elif depends_on == ["ollama"] or "ollama" in depends_on:
                health_condition_configured = True
        
        return {
            "valid": ollama_dependency_configured,
            "ollama_dependency_configured": ollama_dependency_configured,
            "health_condition_configured": health_condition_configured,
            "depends_on_config": depends_on,
            "services": list(services.keys())
        }
    
    def validate_health_check_configuration(self) -> Dict[str, Any]:
        """Validate that services have proper health checks configured"""
        compose_config = self.parse_docker_compose_configuration()
        
        if not compose_config["valid"]:
            return compose_config
        
        services = compose_config["services"]
        
        # Check Ollama health check
        ollama_config = services.get("ollama", {})
        ollama_healthcheck = ollama_config.get("healthcheck", {})
        
        ollama_has_healthcheck = bool(ollama_healthcheck)
        ollama_healthcheck_valid = False
        
        if ollama_has_healthcheck:
            test_command = ollama_healthcheck.get("test", [])
            if isinstance(test_command, list) and len(test_command) > 0:
                # Check if health check tests the correct endpoint
                test_str = " ".join(test_command)
                ollama_healthcheck_valid = "/api/tags" in test_str and "curl" in test_str
        
        # Check RAG app health check
        rag_app_config = services.get("rag-app", {})
        rag_app_healthcheck = rag_app_config.get("healthcheck", {})
        
        rag_app_has_healthcheck = bool(rag_app_healthcheck)
        rag_app_healthcheck_valid = False
        
        if rag_app_has_healthcheck:
            test_command = rag_app_healthcheck.get("test", [])
            if isinstance(test_command, list) and len(test_command) > 0:
                # Check if health check tests the correct endpoint
                test_str = " ".join(test_command)
                rag_app_healthcheck_valid = "_stcore/health" in test_str and "curl" in test_str
        
        return {
            "valid": ollama_has_healthcheck and rag_app_has_healthcheck,
            "ollama_has_healthcheck": ollama_has_healthcheck,
            "ollama_healthcheck_valid": ollama_healthcheck_valid,
            "rag_app_has_healthcheck": rag_app_has_healthcheck,
            "rag_app_healthcheck_valid": rag_app_healthcheck_valid,
            "ollama_healthcheck_config": ollama_healthcheck,
            "rag_app_healthcheck_config": rag_app_healthcheck
        }
    
    def validate_entrypoint_orchestration_logic(self) -> Dict[str, Any]:
        """Validate that entrypoint script implements proper service orchestration"""
        if not self.entrypoint_script.exists():
            return {"valid": False, "error": "entrypoint.sh not found"}
        
        try:
            with open(self.entrypoint_script, 'r') as f:
                script_content = f.read()
            
            # Check for Ollama waiting logic
            has_ollama_wait = "wait_for_ollama" in script_content
            has_ollama_health_check = "/api/tags" in script_content
            has_retry_logic = "max_retries" in script_content or "counter" in script_content
            has_backoff_logic = "backoff" in script_content or "sleep" in script_content
            
            # Check for model management
            has_model_management = "manage_ollama_model" in script_content
            has_model_download = "api/pull" in script_content
            
            # Check for configuration validation
            has_config_validation = "validate_configuration" in script_content
            has_required_vars_check = "required_vars" in script_content
            
            # Check for proper initialization sequence
            has_initialization_sequence = (
                "wait_for_ollama" in script_content and
                "manage_ollama_model" in script_content and
                "initialize_directories" in script_content
            )
            
            # Check for error handling
            has_error_handling = "log_error" in script_content and "exit 1" in script_content
            
            return {
                "valid": has_ollama_wait and has_initialization_sequence,
                "has_ollama_wait": has_ollama_wait,
                "has_ollama_health_check": has_ollama_health_check,
                "has_retry_logic": has_retry_logic,
                "has_backoff_logic": has_backoff_logic,
                "has_model_management": has_model_management,
                "has_model_download": has_model_download,
                "has_config_validation": has_config_validation,
                "has_required_vars_check": has_required_vars_check,
                "has_initialization_sequence": has_initialization_sequence,
                "has_error_handling": has_error_handling
            }
            
        except Exception as e:
            return {"valid": False, "error": f"Failed to read entrypoint.sh: {str(e)}"}
    
    def simulate_startup_sequence_validation(self) -> Dict[str, Any]:
        """Simulate validation of the startup sequence"""
        # Validate Docker Compose configuration
        dependency_validation = self.validate_service_dependency_configuration()
        if not dependency_validation["valid"]:
            return {
                "valid": False,
                "error": "Service dependency configuration invalid",
                "details": dependency_validation
            }
        
        # Validate health check configuration
        healthcheck_validation = self.validate_health_check_configuration()
        if not healthcheck_validation["valid"]:
            return {
                "valid": False,
                "error": "Health check configuration invalid",
                "details": healthcheck_validation
            }
        
        # Validate entrypoint orchestration
        entrypoint_validation = self.validate_entrypoint_orchestration_logic()
        if not entrypoint_validation["valid"]:
            return {
                "valid": False,
                "error": "Entrypoint orchestration logic invalid",
                "details": entrypoint_validation
            }
        
        return {
            "valid": True,
            "dependency_validation": dependency_validation,
            "healthcheck_validation": healthcheck_validation,
            "entrypoint_validation": entrypoint_validation
        }
    
    def validate_environment_variable_orchestration(self) -> Dict[str, Any]:
        """Validate that environment variables support proper service orchestration"""
        compose_config = self.parse_docker_compose_configuration()
        
        if not compose_config["valid"]:
            return compose_config
        
        services = compose_config["services"]
        rag_app_config = services.get("rag-app", {})
        environment = rag_app_config.get("environment", {})
        
        # Convert list format to dict if needed
        if isinstance(environment, list):
            env_dict = {}
            for env_var in environment:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_dict[key] = value
            environment = env_dict
        
        # Check for required orchestration environment variables
        required_orchestration_vars = {
            "OLLAMA_BASE_URL": "http://ollama:11434",  # Should use container networking
            "OLLAMA_MODEL": None,  # Should be specified
            "OLLAMA_TIMEOUT": None,  # Should be specified
        }
        
        orchestration_vars_configured = {}
        for var, expected_pattern in required_orchestration_vars.items():
            var_value = environment.get(var)
            orchestration_vars_configured[var] = {
                "configured": var_value is not None,
                "value": var_value,
                "matches_pattern": expected_pattern is None or (var_value and expected_pattern in var_value)
            }
        
        all_orchestration_vars_valid = all(
            var_info["configured"] and var_info["matches_pattern"]
            for var_info in orchestration_vars_configured.values()
        )
        
        return {
            "valid": all_orchestration_vars_valid,
            "orchestration_vars": orchestration_vars_configured,
            "environment": environment
        }


# **Feature: docker-modernization, Property 1: Application Feature Completeness**
class TestDockerServiceStartupOrchestration:
    """Example tests for Docker service startup orchestration"""
    
    def test_docker_compose_service_dependency_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: Docker Compose should configure RAG application to depend on 
        Ollama service with proper health check conditions for startup orchestration.
        """
        tester = ServiceStartupOrchestrationTester()
        
        dependency_config = tester.validate_service_dependency_configuration()
        
        assert dependency_config["valid"], \
            f"Service dependency configuration must be valid. Error: {dependency_config.get('error', 'Unknown error')}"
        
        assert dependency_config["ollama_dependency_configured"], \
            "RAG application must be configured to depend on Ollama service"
        
        assert dependency_config["health_condition_configured"], \
            "RAG application must wait for Ollama service to be healthy before starting"
        
        # Verify both services are present
        services = dependency_config["services"]
        assert "ollama" in services, \
            "Ollama service must be defined in docker-compose.yml"
        
        assert "rag-app" in services, \
            "RAG application service must be defined in docker-compose.yml"
    
    def test_service_health_check_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: Both Ollama and RAG application services should have proper 
        health checks configured to enable reliable startup orchestration.
        """
        tester = ServiceStartupOrchestrationTester()
        
        healthcheck_config = tester.validate_health_check_configuration()
        
        assert healthcheck_config["valid"], \
            "Both services must have health checks configured for proper orchestration"
        
        # Verify Ollama health check
        assert healthcheck_config["ollama_has_healthcheck"], \
            "Ollama service must have health check configured"
        
        assert healthcheck_config["ollama_healthcheck_valid"], \
            "Ollama health check must test the correct API endpoint (/api/tags)"
        
        # Verify RAG app health check
        assert healthcheck_config["rag_app_has_healthcheck"], \
            "RAG application must have health check configured"
        
        assert healthcheck_config["rag_app_healthcheck_valid"], \
            "RAG app health check must test the correct Streamlit endpoint (/_stcore/health)"
        
        # Verify health check configurations have proper intervals
        ollama_healthcheck = healthcheck_config["ollama_healthcheck_config"]
        assert "interval" in ollama_healthcheck, \
            "Ollama health check must specify check interval"
        
        rag_app_healthcheck = healthcheck_config["rag_app_healthcheck_config"]
        assert "interval" in rag_app_healthcheck, \
            "RAG app health check must specify check interval"
    
    def test_entrypoint_service_orchestration_logic(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: The entrypoint script should implement proper service 
        orchestration logic to wait for Ollama before starting the RAG application.
        """
        tester = ServiceStartupOrchestrationTester()
        
        entrypoint_config = tester.validate_entrypoint_orchestration_logic()
        
        assert entrypoint_config["valid"], \
            f"Entrypoint orchestration logic must be valid. Error: {entrypoint_config.get('error', 'Unknown error')}"
        
        # Verify Ollama waiting logic
        assert entrypoint_config["has_ollama_wait"], \
            "Entrypoint must implement Ollama service waiting logic"
        
        assert entrypoint_config["has_ollama_health_check"], \
            "Entrypoint must check Ollama health endpoint (/api/tags)"
        
        assert entrypoint_config["has_retry_logic"], \
            "Entrypoint must implement retry logic for service availability"
        
        assert entrypoint_config["has_backoff_logic"], \
            "Entrypoint must implement backoff logic to avoid overwhelming services"
        
        # Verify initialization sequence
        assert entrypoint_config["has_initialization_sequence"], \
            "Entrypoint must implement proper initialization sequence"
        
        # Verify error handling
        assert entrypoint_config["has_error_handling"], \
            "Entrypoint must implement proper error handling for orchestration failures"
        
        # Verify model management
        assert entrypoint_config["has_model_management"], \
            "Entrypoint must implement Ollama model management"
        
        assert entrypoint_config["has_config_validation"], \
            "Entrypoint must validate configuration before starting services"
    
    def test_startup_sequence_integration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: The complete startup sequence should integrate Docker Compose 
        dependencies, health checks, and entrypoint orchestration for reliable service startup.
        """
        tester = ServiceStartupOrchestrationTester()
        
        startup_validation = tester.simulate_startup_sequence_validation()
        
        assert startup_validation["valid"], \
            f"Complete startup sequence must be valid. Error: {startup_validation.get('error', 'Unknown error')}"
        
        # Verify all components are properly configured
        dependency_validation = startup_validation["dependency_validation"]
        assert dependency_validation["ollama_dependency_configured"], \
            "Service dependencies must be properly configured"
        
        healthcheck_validation = startup_validation["healthcheck_validation"]
        assert healthcheck_validation["ollama_has_healthcheck"], \
            "Ollama health checks must be configured"
        assert healthcheck_validation["rag_app_has_healthcheck"], \
            "RAG app health checks must be configured"
        
        entrypoint_validation = startup_validation["entrypoint_validation"]
        assert entrypoint_validation["has_initialization_sequence"], \
            "Entrypoint initialization sequence must be implemented"
    
    def test_environment_variable_orchestration_support(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: Environment variables should be configured to support 
        service orchestration with proper container networking URLs.
        """
        tester = ServiceStartupOrchestrationTester()
        
        env_validation = tester.validate_environment_variable_orchestration()
        
        assert env_validation["valid"], \
            "Environment variables must be configured for proper service orchestration"
        
        orchestration_vars = env_validation["orchestration_vars"]
        
        # Verify Ollama URL uses container networking
        ollama_url_config = orchestration_vars["OLLAMA_BASE_URL"]
        assert ollama_url_config["configured"], \
            "OLLAMA_BASE_URL must be configured"
        
        assert ollama_url_config["matches_pattern"], \
            "OLLAMA_BASE_URL must use container networking (http://ollama:11434)"
        
        # Verify model is specified
        ollama_model_config = orchestration_vars["OLLAMA_MODEL"]
        assert ollama_model_config["configured"], \
            "OLLAMA_MODEL must be specified for proper orchestration"
        
        # Verify timeout is configured
        ollama_timeout_config = orchestration_vars["OLLAMA_TIMEOUT"]
        assert ollama_timeout_config["configured"], \
            "OLLAMA_TIMEOUT must be configured for reliable service communication"
    
    def test_service_restart_policy_configuration(self):
        """
        **Feature: docker-modernization, Property 1: Application Feature Completeness**
        **Validates: Requirements 2.1**
        
        Example test: Services should be configured with appropriate restart policies 
        to ensure reliable orchestration during container restarts.
        """
        tester = ServiceStartupOrchestrationTester()
        
        compose_config = tester.parse_docker_compose_configuration()
        
        assert compose_config["valid"], \
            f"Docker Compose configuration must be valid. Error: {compose_config.get('error', 'Unknown error')}"
        
        services = compose_config["services"]
        
        # Check Ollama restart policy
        ollama_config = services.get("ollama", {})
        ollama_restart = ollama_config.get("restart", "no")
        
        assert ollama_restart in ["unless-stopped", "always", "on-failure"], \
            f"Ollama service must have appropriate restart policy, got: {ollama_restart}"
        
        # Check RAG app restart policy
        rag_app_config = services.get("rag-app", {})
        rag_app_restart = rag_app_config.get("restart", "no")
        
        assert rag_app_restart in ["unless-stopped", "always", "on-failure"], \
            f"RAG app service must have appropriate restart policy, got: {rag_app_restart}"
        
        # Verify both services have the same restart policy for consistency
        assert ollama_restart == rag_app_restart, \
            "Both services should have consistent restart policies for reliable orchestration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])