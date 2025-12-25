# Docker Modernization Design Document

## Overview

This design document outlines the modernization of the Docker configuration for the INPT RAG Assistant to align with the current application structure and enhanced features. The current Docker setup references outdated entry points (`app/streamlit_app.py`) while the actual application uses `app/chat.py`. Additionally, the configuration needs to support new features like math rendering, analytics, conversation management, and the updated settings structure.

The modernization will ensure that the containerized application provides the same functionality as the local development environment while maintaining production-ready deployment capabilities.

## Architecture

### Container Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Ollama LLM    │    │        RAG Application         │ │
│  │   Container     │    │         Container              │ │
│  │                 │    │                                │ │
│  │ - Model Storage │◄───┤ - Streamlit App (chat.py)     │ │
│  │ - API Server    │    │ - Math Rendering               │ │
│  │ - Health Checks │    │ - Analytics Dashboard          │ │
│  └─────────────────┘    │ - Conversation Management      │ │
│                         │ - Document Processing          │ │
│                         │ - Vector Store Integration     │ │
│                         └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Persistent Volumes                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐  │
│  │   Documents     │ │   Conversations │ │     Logs     │  │
│  │   & Database    │ │   & Analytics   │ │  & Metrics   │  │
│  └─────────────────┘ └─────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Network Architecture
- **Internal Network**: Docker Compose creates an isolated network for service communication
- **Service Discovery**: Containers communicate using service names (e.g., `ollama:11434`)
- **Port Mapping**: Only necessary ports are exposed to the host (8501 for Streamlit, 11434 for Ollama)
- **Health Checks**: Both services implement health checks for reliable startup orchestration

## Components and Interfaces

### 1. Updated Dockerfile
**Purpose**: Build optimized container image with current application structure
**Key Changes**:
- Correct entry point: `app/chat.py` instead of `app/streamlit_app.py`
- Updated dependency installation for enhanced features
- Proper directory structure creation
- Optimized layer caching for development workflow

### 2. Docker Compose Configuration
**Purpose**: Orchestrate multi-service deployment with proper dependencies
**Services**:
- **Ollama Service**: LLM inference engine with model persistence
- **RAG Application**: Main Streamlit application with all current features
- **Volume Management**: Persistent storage for data, conversations, and logs

### 3. Enhanced Entry Point Script
**Purpose**: Robust initialization and health checking
**Features**:
- Ollama service availability checking
- Model download automation
- Directory initialization
- Configuration validation
- Graceful error handling

### 4. Environment Configuration
**Purpose**: Flexible configuration management
**Variables**:
- Ollama connection settings
- Model configuration
- Feature toggles
- Performance tuning parameters

## Data Models

### Container Configuration Model
```python
class ContainerConfig:
    base_image: str = "python:3.11-slim"
    working_directory: str = "/app"
    exposed_ports: List[int] = [8501]
    health_check_endpoint: str = "/_stcore/health"
    environment_variables: Dict[str, str]
```

### Service Orchestration Model
```python
class ServiceConfig:
    name: str
    image: str
    ports: List[str]
    volumes: List[str]
    environment: Dict[str, str]
    depends_on: List[str]
    health_check: HealthCheckConfig
```

### Volume Mapping Model
```python
class VolumeMapping:
    host_path: str
    container_path: str
    read_only: bool = False
    type: str = "bind"  # bind, volume, tmpfs
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Application Feature Completeness
*For any* containerized deployment, all enhanced features (math rendering, analytics, conversation management) should be accessible and functional
**Validates: Requirements 1.2, 4.1, 4.3, 4.5**

### Property 2: Dependency Satisfaction
*For any* container build, all required packages and dependencies for current features should be installed and importable
**Validates: Requirements 1.3, 3.2**

### Property 3: Environment Configuration Consistency
*For any* set of environment variables, the containerized application should use the same configuration structure as the local development environment
**Validates: Requirements 1.5, 5.5**

### Property 4: Inter-Service Communication
*For any* service startup sequence, the RAG application should successfully connect to the Ollama service using container networking
**Validates: Requirements 2.2**

### Property 5: Data Persistence Integrity
*For any* container restart or update, data, conversations, and logs should persist correctly across the restart
**Validates: Requirements 2.3, 4.2**

### Property 6: Service Recovery Resilience
*For any* service restart or failure, the system should recover properly and maintain data integrity
**Validates: Requirements 2.5**

### Property 7: Runtime Environment Correctness
*For any* container execution, the system should have proper permissions and directory structure for all operations
**Validates: Requirements 3.5**

### Property 8: Document Processing Functionality
*For any* document upload in the containerized environment, the document should be processed using the current processing pipeline
**Validates: Requirements 4.4**

## Error Handling

### Container Startup Errors
- **Ollama Unavailable**: Retry mechanism with exponential backoff
- **Model Missing**: Automatic model download with progress indication
- **Port Conflicts**: Clear error messages with resolution suggestions
- **Volume Mount Issues**: Permission and path validation

### Runtime Errors
- **Service Communication Failures**: Automatic reconnection attempts
- **Resource Exhaustion**: Graceful degradation and logging
- **Configuration Errors**: Validation with helpful error messages
- **Health Check Failures**: Service restart with state preservation

### Recovery Mechanisms
- **Automatic Restarts**: Docker Compose restart policies
- **Data Backup**: Volume snapshot capabilities
- **Rollback Support**: Tagged image versions for quick rollback
- **Monitoring Integration**: Health check endpoints for external monitoring

## Testing Strategy

### Unit Testing
- **Configuration Validation**: Test environment variable parsing and validation
- **Service Integration**: Test individual service startup and configuration
- **Volume Mounting**: Test data persistence and file permissions
- **Network Configuration**: Test service discovery and communication

### Property-Based Testing
The testing approach will use **pytest** with **hypothesis** for property-based testing to verify universal properties across different configurations and inputs.

**Property-based testing requirements**:
- Each property-based test will run a minimum of 100 iterations
- Tests will be tagged with comments referencing the design document properties
- Tag format: `**Feature: docker-modernization, Property {number}: {property_text}**`

**Integration Testing**:
- **End-to-End Deployment**: Test complete Docker Compose stack deployment
- **Feature Verification**: Test all application features in containerized environment
- **Performance Testing**: Verify acceptable performance in containerized deployment
- **Upgrade Testing**: Test update and rollback procedures

**Container Testing**:
- **Image Security**: Scan for vulnerabilities and security issues
- **Resource Usage**: Monitor memory and CPU usage patterns
- **Startup Time**: Measure and optimize container startup performance
- **Health Check Validation**: Verify health check endpoints work correctly

### Testing Tools
- **pytest**: Primary testing framework
- **hypothesis**: Property-based testing library
- **docker-py**: Docker API integration for testing
- **testcontainers**: Container testing utilities
- **requests**: HTTP endpoint testing