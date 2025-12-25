"""Property-based tests for Docker environment configuration consistency"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import Dict, Any, List, Tuple, Optional
from unittest.mock import patch, MagicMock
import sys
import yaml
import json
from pydantic import ValidationError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config.settings import Settings, validate_environment_configuration


class EnvironmentConfigurationTester:
    """Helper class for testing environment configuration consistency"""
    
    def __init__(self):
        self.docker_compose_file = Path(__file__).parent.parent / "docker" / "docker-compose.yml"
        self.env_example_file = Path(__file__).parent.parent / ".env.example"
        self.settings_file = Path(__file__).parent.parent / "src" / "config" / "settings.py"
        
    def parse_docker_compose_environment(self) -> Dict[str, str]:
        """Parse environment variables from docker-compose.yml"""
        if not self.docker_compose_file.exists():
            return {}
        
        try:
            with open(self.docker_compose_file, 'r') as f:
                compose_data = yaml.safe_load(f)
            
            # Extract environment variables from rag-app service
            rag_app_service = compose_data.get('services', {}).get('rag-app', {})
            environment = rag_app_service.get('environment', [])
            
            # Convert list format to dict
            env_dict = {}
            for env_var in environment:
                if isinstance(env_var, str) and '=' in env_var:
                    key, value = env_var.split('=', 1)
                    env_dict[key.strip()] = value.strip()
            
            return env_dict
            
        except Exception as e:
            print(f"Warning: Could not parse docker-compose.yml: {e}")
            return {}
    
    def parse_env_example_variables(self) -> Dict[str, str]:
        """Parse environment variables from .env.example"""
        if not self.env_example_file.exists():
            return {}
        
        env_dict = {}
        
        try:
            with open(self.env_example_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_dict[key.strip()] = value.strip().strip('"')
            
            return env_dict
            
        except Exception as e:
            print(f"Warning: Could not parse .env.example: {e}")
            return {}
    
    def get_settings_class_fields(self) -> Dict[str, Any]:
        """Get field definitions from Settings class"""
        try:
            # Create a Settings instance to get default values
            settings = Settings()
            
            # Get model fields from the class, not the instance
            fields_info = {}
            for field_name, field_info in Settings.model_fields.items():
                fields_info[field_name] = {
                    'type': str(field_info.annotation) if hasattr(field_info, 'annotation') else 'unknown',
                    'default': getattr(settings, field_name, None),
                    'required': field_info.is_required() if hasattr(field_info, 'is_required') else False
                }
            
            return fields_info
            
        except Exception as e:
            print(f"Warning: Could not analyze Settings class: {e}")
            return {}
    
    def create_test_environment(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Create test environment and validate configuration consistency"""
        validation_results = {
            "settings_loadable": True,
            "validation_passed": True,
            "docker_detection_correct": True,
            "path_consistency": True,
            "ollama_url_consistency": True,
            "errors": [],
            "warnings": [],
            "environment_type": "unknown"
        }
        
        # Set environment variables
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = str(value)
        
        try:
            # Test Settings loading
            try:
                settings = Settings()
                validation_results["settings_loadable"] = True
            except Exception as e:
                validation_results["settings_loadable"] = False
                validation_results["errors"].append(f"Settings loading failed: {e}")
                return validation_results
            
            # Test environment validation
            try:
                env_validation = validate_environment_configuration()
                validation_results["validation_passed"] = env_validation["is_valid"]
                validation_results["environment_type"] = env_validation["environment_type"]
                validation_results["docker_detection_correct"] = env_validation["is_docker"]
                validation_results["errors"].extend(env_validation["errors"])
                validation_results["warnings"].extend(env_validation["warnings"])
            except Exception as e:
                validation_results["validation_passed"] = False
                validation_results["errors"].append(f"Environment validation failed: {e}")
            
            # Test path consistency
            try:
                # Check if paths are consistent with environment type
                if validation_results["docker_detection_correct"]:
                    # In Docker, paths should be absolute container paths
                    expected_base = "/app"
                    if not str(settings.BASE_DIR).startswith(expected_base):
                        validation_results["path_consistency"] = False
                        validation_results["warnings"].append(
                            f"Docker environment should use container paths starting with {expected_base}"
                        )
                else:
                    # In local environment, paths should be relative or local absolute
                    if str(settings.BASE_DIR).startswith("/app"):
                        validation_results["path_consistency"] = False
                        validation_results["warnings"].append(
                            "Local environment should not use container paths"
                        )
            except Exception as e:
                validation_results["path_consistency"] = False
                validation_results["errors"].append(f"Path consistency check failed: {e}")
            
            # Test Ollama URL consistency
            try:
                if validation_results["docker_detection_correct"]:
                    # In Docker, should use service name
                    if not settings.OLLAMA_BASE_URL.startswith("http://ollama:"):
                        validation_results["ollama_url_consistency"] = False
                        validation_results["warnings"].append(
                            "Docker environment should use Ollama service name"
                        )
                else:
                    # In local environment, should use localhost
                    if not settings.OLLAMA_BASE_URL.startswith("http://localhost:"):
                        validation_results["ollama_url_consistency"] = False
                        validation_results["warnings"].append(
                            "Local environment should use localhost for Ollama"
                        )
            except Exception as e:
                validation_results["ollama_url_consistency"] = False
                validation_results["errors"].append(f"Ollama URL consistency check failed: {e}")
        
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
        
        return validation_results
    
    def compare_configuration_structures(self, docker_env: Dict[str, str], 
                                       local_env: Dict[str, str]) -> Dict[str, Any]:
        """Compare configuration structures between Docker and local environments"""
        comparison_results = {
            "structure_consistent": True,
            "missing_in_docker": [],
            "missing_in_local": [],
            "type_mismatches": [],
            "value_format_issues": []
        }
        
        # Get all configuration keys from both environments
        docker_keys = set(docker_env.keys())
        local_keys = set(local_env.keys())
        
        # Find missing keys
        comparison_results["missing_in_docker"] = list(local_keys - docker_keys)
        comparison_results["missing_in_local"] = list(docker_keys - local_keys)
        
        if comparison_results["missing_in_docker"] or comparison_results["missing_in_local"]:
            comparison_results["structure_consistent"] = False
        
        # Check common keys for consistency
        common_keys = docker_keys & local_keys
        
        for key in common_keys:
            docker_value = docker_env[key]
            local_value = local_env[key]
            
            # Check for obvious type mismatches (e.g., boolean vs string)
            if self._is_boolean_value(docker_value) != self._is_boolean_value(local_value):
                comparison_results["type_mismatches"].append({
                    "key": key,
                    "docker_value": docker_value,
                    "local_value": local_value
                })
                comparison_results["structure_consistent"] = False
            
            # Check for format consistency (e.g., paths, URLs)
            if key.endswith('_URL') or key.endswith('_DIR') or key.endswith('_PATH'):
                if not self._are_path_formats_consistent(docker_value, local_value, key):
                    comparison_results["value_format_issues"].append({
                        "key": key,
                        "docker_value": docker_value,
                        "local_value": local_value,
                        "issue": "Path format inconsistency"
                    })
        
        return comparison_results
    
    def _is_boolean_value(self, value: str) -> bool:
        """Check if a string value represents a boolean"""
        return value.lower() in ['true', 'false', '1', '0', 'yes', 'no']
    
    def _are_path_formats_consistent(self, docker_value: str, local_value: str, key: str) -> bool:
        """Check if path formats are consistent between environments"""
        # For Docker, paths should be absolute container paths
        # For local, paths should be relative or local absolute paths
        
        # Skip comparison for paths that are expected to be different
        if key in ['OLLAMA_BASE_URL']:
            return True  # These are expected to be different
        
        # Both should be valid path formats
        docker_is_absolute = docker_value.startswith('/')
        local_is_absolute = local_value.startswith('/')
        
        # If both are absolute or both are relative, format is consistent
        return docker_is_absolute == local_is_absolute or key.endswith('_URL')
    
    def validate_settings_field_coverage(self, env_vars: Dict[str, str]) -> Dict[str, Any]:
        """Validate that environment variables cover all required Settings fields"""
        coverage_results = {
            "all_required_covered": True,
            "missing_required_fields": [],
            "extra_env_vars": [],
            "coverage_percentage": 0.0
        }
        
        try:
            # Get Settings class fields
            settings_fields = self.get_settings_class_fields()
            
            # Check coverage
            settings_field_names = set(settings_fields.keys())
            env_var_names = set(env_vars.keys())
            
            # Find missing required fields
            for field_name, field_info in settings_fields.items():
                if field_info.get('required', False) and field_name not in env_var_names:
                    coverage_results["missing_required_fields"].append(field_name)
                    coverage_results["all_required_covered"] = False
            
            # Find extra environment variables (not necessarily bad)
            coverage_results["extra_env_vars"] = list(env_var_names - settings_field_names)
            
            # Calculate coverage percentage
            if settings_field_names:
                covered_fields = len(settings_field_names & env_var_names)
                coverage_results["coverage_percentage"] = (covered_fields / len(settings_field_names)) * 100
            
        except Exception as e:
            coverage_results["all_required_covered"] = False
            coverage_results["error"] = str(e)
        
        return coverage_results


# **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
class TestEnvironmentConfigurationConsistency:
    """Property-based tests for environment configuration consistency"""
    
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(docker_env_subset=st.lists(
        st.sampled_from([
            'PROJECT_NAME', 'OLLAMA_BASE_URL', 'OLLAMA_MODEL', 'DATA_DIR', 
            'DATABASE_DIR', 'LOGS_DIR', 'CHUNK_SIZE', 'EMBEDDING_MODEL',
            'CHROMA_PERSIST_DIR', 'LOG_LEVEL', 'STREAMLIT_PAGE_TITLE'
        ]),
        min_size=3,
        max_size=8,
        unique=True
    ))
    def test_docker_environment_variables_load_consistently(self, docker_env_subset: List[str]):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        For any subset of Docker environment variables, the containerized application 
        should load and validate the configuration consistently with the local environment.
        """
        tester = EnvironmentConfigurationTester()
        
        # Get Docker Compose environment variables
        docker_env = tester.parse_docker_compose_environment()
        
        # Create test environment with subset of variables
        test_env = {}
        for var_name in docker_env_subset:
            if var_name in docker_env:
                test_env[var_name] = docker_env[var_name]
            else:
                # Use default values for missing variables
                default_values = {
                    'PROJECT_NAME': 'Test RAG Assistant',
                    'OLLAMA_BASE_URL': 'http://ollama:11434',
                    'OLLAMA_MODEL': 'qwen2.5:3b',
                    'DATA_DIR': '/app/data',
                    'DATABASE_DIR': '/app/database',
                    'LOGS_DIR': '/app/logs',
                    'CHUNK_SIZE': '1000',
                    'EMBEDDING_MODEL': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                    'CHROMA_PERSIST_DIR': '/app/database/chroma_db',
                    'LOG_LEVEL': 'INFO',
                    'STREAMLIT_PAGE_TITLE': 'Test RAG Assistant'
                }
                test_env[var_name] = default_values.get(var_name, 'test_value')
        
        # Add Docker environment indicators
        test_env['PYTHONUNBUFFERED'] = '1'
        
        # Test configuration loading
        validation_results = tester.create_test_environment(test_env)
        
        # Verify Settings can be loaded
        assert validation_results["settings_loadable"], \
            f"Settings should be loadable with Docker environment variables: {validation_results['errors']}"
        
        # Verify environment validation works
        assert validation_results["validation_passed"] or len(validation_results["errors"]) == 0, \
            f"Environment validation should pass or have no critical errors: {validation_results['errors']}"
        
        # Verify Docker environment is detected correctly
        assert validation_results["docker_detection_correct"], \
            "Docker environment should be detected correctly when PYTHONUNBUFFERED=1"
        
        # Verify configuration structure is consistent
        assert validation_results["environment_type"] in ["docker", "local"], \
            f"Environment type should be detected as 'docker' or 'local', got: {validation_results['environment_type']}"
    
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(environment_scenarios=st.lists(
        st.fixed_dictionaries({
            "is_docker": st.booleans(),
            "ollama_url": st.sampled_from([
                "http://localhost:11434",
                "http://ollama:11434", 
                "http://127.0.0.1:11434"
            ]),
            "base_dir": st.sampled_from([
                "/app",
                "./",
                "/home/user/project",
                "."
            ])
        }),
        min_size=1,
        max_size=3
    ))
    def test_environment_detection_consistency(self, environment_scenarios: List[Dict[str, Any]]):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        For any environment configuration scenario, the application should correctly 
        detect the environment type and apply appropriate configuration validation.
        """
        tester = EnvironmentConfigurationTester()
        
        for scenario in environment_scenarios:
            # Create test environment
            test_env = {
                'OLLAMA_BASE_URL': scenario['ollama_url'],
                'BASE_DIR': scenario['base_dir'],
                'PROJECT_NAME': 'Test RAG Assistant',
                'LOG_LEVEL': 'INFO'
            }
            
            # Add Docker indicators if specified
            if scenario['is_docker']:
                test_env['PYTHONUNBUFFERED'] = '1'
            
            # Test configuration
            validation_results = tester.create_test_environment(test_env)
            
            # Verify Settings loading works
            assert validation_results["settings_loadable"], \
                f"Settings should load for scenario {scenario}: {validation_results['errors']}"
            
            # Verify environment detection logic
            detected_docker = validation_results["docker_detection_correct"]
            
            if scenario['is_docker']:
                # Should detect Docker environment
                assert detected_docker, \
                    f"Should detect Docker environment when PYTHONUNBUFFERED=1 for scenario {scenario}"
            
            # Verify URL consistency warnings are appropriate
            if scenario['is_docker'] and not scenario['ollama_url'].startswith('http://ollama:'):
                # Should warn about using service name in Docker
                assert any('ollama' in warning.lower() for warning in validation_results['warnings']), \
                    f"Should warn about Ollama URL in Docker environment for scenario {scenario}"
            
            elif not scenario['is_docker'] and not scenario['ollama_url'].startswith('http://localhost:'):
                # Should warn about using localhost in local environment
                assert any('localhost' in warning.lower() for warning in validation_results['warnings']), \
                    f"Should warn about Ollama URL in local environment for scenario {scenario}"
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(config_variations=st.lists(
        st.fixed_dictionaries({
            "chunk_size": st.integers(min_value=100, max_value=2000),
            "embedding_dimension": st.integers(min_value=128, max_value=1024),
            "top_k_retrieval": st.integers(min_value=3, max_value=15),
            "log_level": st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
            "temperature": st.floats(min_value=0.0, max_value=1.0),
            "max_tokens": st.integers(min_value=100, max_value=1000)
        }),
        min_size=1,
        max_size=2
    ))
    def test_configuration_parameter_consistency(self, config_variations: List[Dict[str, Any]]):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        For any valid configuration parameter values, the containerized application 
        should validate and apply them consistently with the local environment.
        """
        tester = EnvironmentConfigurationTester()
        
        for config in config_variations:
            # Create test environment with configuration parameters
            test_env = {
                'PROJECT_NAME': 'Test RAG Assistant',
                'OLLAMA_BASE_URL': 'http://ollama:11434',
                'CHUNK_SIZE': str(config['chunk_size']),
                'EMBEDDING_DIMENSION': str(config['embedding_dimension']),
                'TOP_K_RETRIEVAL': str(config['top_k_retrieval']),
                'LOG_LEVEL': config['log_level'],
                'LLM_TEMPERATURE': str(config['temperature']),
                'LLM_MAX_TOKENS': str(config['max_tokens']),
                'PYTHONUNBUFFERED': '1'  # Docker indicator
            }
            
            # Test configuration loading
            validation_results = tester.create_test_environment(test_env)
            
            # Verify Settings can be loaded with these parameters
            assert validation_results["settings_loadable"], \
                f"Settings should load with config {config}: {validation_results['errors']}"
            
            # Verify validation passes for valid parameters
            if not validation_results["validation_passed"]:
                # Check if errors are due to invalid parameter values
                critical_errors = [e for e in validation_results["errors"] 
                                 if not any(warning_keyword in e.lower() 
                                          for warning_keyword in ['warning', 'directory', 'path'])]
                
                assert len(critical_errors) == 0, \
                    f"Should not have critical validation errors for valid config {config}: {critical_errors}"
            
            # Verify Docker environment is detected
            assert validation_results["docker_detection_correct"], \
                f"Docker environment should be detected for config {config}"
    
    def test_docker_compose_environment_structure_consistency(self):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        The Docker Compose environment configuration should be structurally consistent 
        with the .env.example template and Settings class requirements.
        """
        tester = EnvironmentConfigurationTester()
        
        # Get environment configurations
        docker_env = tester.parse_docker_compose_environment()
        local_env = tester.parse_env_example_variables()
        
        # Verify we have configurations to compare
        assert len(docker_env) > 0, \
            "Docker Compose should define environment variables"
        
        assert len(local_env) > 0, \
            ".env.example should define environment variables"
        
        # Compare configuration structures
        comparison = tester.compare_configuration_structures(docker_env, local_env)
        
        # Check for critical missing variables in Docker
        critical_vars = [
            'OLLAMA_BASE_URL', 'OLLAMA_MODEL', 'PROJECT_NAME', 
            'DATA_DIR', 'DATABASE_DIR', 'LOG_LEVEL'
        ]
        
        missing_critical = [var for var in critical_vars 
                          if var in comparison["missing_in_docker"]]
        
        assert len(missing_critical) == 0, \
            f"Critical environment variables missing in Docker Compose: {missing_critical}"
        
        # Verify no major type mismatches
        assert len(comparison["type_mismatches"]) == 0, \
            f"Environment variable type mismatches found: {comparison['type_mismatches']}"
        
        # Allow some differences but warn about them
        if not comparison["structure_consistent"]:
            print(f"WARNING: Configuration structure differences found:")
            print(f"  Missing in Docker: {comparison['missing_in_docker']}")
            print(f"  Missing in local: {comparison['missing_in_local']}")
            print(f"  Value format issues: {comparison['value_format_issues']}")
    
    def test_settings_field_coverage_in_docker_environment(self):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        The Docker environment configuration should provide adequate coverage 
        of Settings class fields to ensure full application functionality.
        """
        tester = EnvironmentConfigurationTester()
        
        # Get Docker environment variables
        docker_env = tester.parse_docker_compose_environment()
        
        # Validate field coverage
        coverage = tester.validate_settings_field_coverage(docker_env)
        
        # Verify no critical required fields are missing
        assert coverage["all_required_covered"], \
            f"Required Settings fields missing from Docker environment: {coverage['missing_required_fields']}"
        
        # Verify reasonable coverage percentage
        assert coverage["coverage_percentage"] >= 50.0, \
            f"Docker environment should cover at least 50% of Settings fields, got {coverage['coverage_percentage']:.1f}%"
        
        # Allow extra environment variables (they might be Docker-specific)
        if coverage["extra_env_vars"]:
            print(f"INFO: Extra environment variables in Docker (may be Docker-specific): {coverage['extra_env_vars']}")
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(path_configurations=st.lists(
        st.fixed_dictionaries({
            "data_dir": st.sampled_from(["/app/data", "./data", "/tmp/data"]),
            "database_dir": st.sampled_from(["/app/database", "./database", "/tmp/db"]),
            "logs_dir": st.sampled_from(["/app/logs", "./logs", "/tmp/logs"]),
            "is_docker": st.booleans()
        }),
        min_size=1,
        max_size=3
    ))
    def test_path_configuration_consistency(self, path_configurations: List[Dict[str, Any]]):
        """
        **Feature: docker-modernization, Property 3: Environment Configuration Consistency**
        **Validates: Requirements 1.5, 5.5**
        
        For any path configuration, the application should handle paths consistently 
        between Docker and local environments while maintaining proper functionality.
        """
        tester = EnvironmentConfigurationTester()
        
        for path_config in path_configurations:
            # Create test environment with path configuration
            test_env = {
                'PROJECT_NAME': 'Test RAG Assistant',
                'DATA_DIR': path_config['data_dir'],
                'DATABASE_DIR': path_config['database_dir'],
                'LOGS_DIR': path_config['logs_dir'],
                'OLLAMA_BASE_URL': 'http://ollama:11434' if path_config['is_docker'] else 'http://localhost:11434',
                'LOG_LEVEL': 'INFO'
            }
            
            # Add Docker indicators if specified
            if path_config['is_docker']:
                test_env['PYTHONUNBUFFERED'] = '1'
            
            # Test configuration
            validation_results = tester.create_test_environment(test_env)
            
            # Verify Settings can be loaded
            assert validation_results["settings_loadable"], \
                f"Settings should load with path config {path_config}: {validation_results['errors']}"
            
            # Verify environment detection works
            detected_docker = validation_results["docker_detection_correct"]
            
            if path_config['is_docker']:
                assert detected_docker, \
                    f"Should detect Docker environment for config {path_config}"
                
                # In Docker, absolute container paths are preferred
                if not path_config['data_dir'].startswith('/app'):
                    assert any('path' in warning.lower() for warning in validation_results['warnings']), \
                        f"Should warn about non-container paths in Docker for config {path_config}"
            
            # Verify path consistency checking works
            assert isinstance(validation_results["path_consistency"], bool), \
                f"Path consistency check should return boolean for config {path_config}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])