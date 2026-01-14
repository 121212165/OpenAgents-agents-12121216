# Design Document: Zeabur Deployment Fix

## Overview

The YouGame application successfully initializes all agents but fails with a 502 SERVICE_UNAVAILABLE error on Zeabur because the web server is not properly configured to accept external connections. The root cause is a mismatch between Zeabur's expected `PORT` environment variable and the application's use of `OPENAGENTS_PORT`, combined with the web server only starting when aiohttp is available.

This design implements a robust web server layer that:
1. Reads the correct PORT environment variable from Zeabur
2. Always starts an HTTP server regardless of aiohttp availability
3. Provides health check endpoints for platform monitoring
4. Serves a basic web interface for user interaction
5. Handles errors gracefully with proper logging

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Zeabur Platform                       │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Load Balancer (expects PORT env var)              │ │
│  └──────────────────┬─────────────────────────────────┘ │
│                     │ HTTP Requests                      │
└─────────────────────┼────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────┐
│              YouGame Application Container               │
│  ┌────────────────────────────────────────────────────┐ │
│  │         Web Server Layer (aiohttp/http.server)     │ │
│  │  ┌──────────────────────────────────────────────┐  │ │
│  │  │  Health Check Endpoint (/health)             │  │ │
│  │  │  Status Page (/)                             │  │ │
│  │  │  API Endpoints (/api/*)                      │  │ │
│  │  └──────────────────────────────────────────────┘  │ │
│  └──────────────────┬─────────────────────────────────┘ │
│                     │                                    │
│  ┌──────────────────▼─────────────────────────────────┐ │
│  │           Router Agent (Request Handler)           │ │
│  └──────────────────┬─────────────────────────────────┘ │
│                     │                                    │
│  ┌──────────────────▼─────────────────────────────────┐ │
│  │  LiveMonitor │ BriefingAgent │ DataSourceAgent     │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Port Configuration Flow

```
Zeabur assigns PORT → Application reads PORT env var → 
Web server binds to 0.0.0.0:PORT → Health checks pass → 
Service becomes available
```

## Components and Interfaces

### 1. Port Configuration Module

**Purpose**: Centralize port and host configuration reading

**Interface**:
```python
def get_server_config() -> tuple[str, int]:
    """
    Get server host and port configuration.
    
    Returns:
        tuple: (host, port) where host is '0.0.0.0' and port is from environment
    
    Priority:
        1. PORT (Zeabur standard)
        2. OPENAGENTS_PORT (fallback)
        3. 8000 (default)
    """
```

### 2. Web Server Module

**Purpose**: Provide HTTP server that works with or without aiohttp

**Primary Implementation** (aiohttp available):
```python
class WebServer:
    async def start(self, host: str, port: int, app: YouGameExplorer):
        """Start aiohttp web server with all endpoints"""
        
    async def stop(self):
        """Gracefully shutdown web server"""
```

**Fallback Implementation** (aiohttp unavailable):
```python
class SimpleWebServer:
    def start(self, host: str, port: int, app: YouGameExplorer):
        """Start basic HTTP server using http.server module"""
```

### 3. Health Check Handler

**Purpose**: Provide platform health monitoring

**Endpoint**: `GET /health`

**Response Format**:
```json
{
  "status": "healthy" | "unhealthy",
  "timestamp": 1234567890.123,
  "agents": {
    "router": true,
    "live_monitor": true,
    "briefing_agent": true,
    "data_source_agent": true
  },
  "version": "1.0.0"
}
```

**Status Codes**:
- 200: All agents operational
- 503: One or more agents not initialized

### 4. Status Page Handler

**Purpose**: Provide human-readable service status

**Endpoint**: `GET /`

**Response**: HTML page showing:
- Service name and version
- Agent status
- Available endpoints
- Quick start guide

### 5. API Endpoints

**Purpose**: Handle user queries via HTTP

**Endpoint**: `POST /api/query`

**Request Format**:
```json
{
  "query": "Uzi 直播了吗？"
}
```

**Response Format**:
```json
{
  "response": "...",
  "agent": "live_monitor",
  "timestamp": 1234567890.123
}
```

## Data Models

### ServerConfig
```python
@dataclass
class ServerConfig:
    host: str  # Always "0.0.0.0" for cloud deployment
    port: int  # From PORT env var
    enable_cors: bool  # True for web access
    log_requests: bool  # True for debugging
```

### HealthStatus
```python
@dataclass
class HealthStatus:
    status: str  # "healthy" or "unhealthy"
    timestamp: float
    agents: dict[str, bool]
    version: str
```

### QueryRequest
```python
@dataclass
class QueryRequest:
    query: str
    context: Optional[dict] = None
```

### QueryResponse
```python
@dataclass
class QueryResponse:
    response: str
    agent: str
    timestamp: float
    error: Optional[str] = None
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system - essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Port Configuration Reading

*For any* valid PORT environment variable value, when the application reads server configuration, it should use that PORT value for binding.

**Validates: Requirements 2.1, 2.2**

### Property 2: Host Binding to All Interfaces

*For any* server configuration, when the web server binds to a port, it should always bind to 0.0.0.0 (all interfaces) not localhost.

**Validates: Requirements 2.4**

### Property 3: Port Binding Error Handling

*For any* port binding failure (invalid port, port in use), the application should log the specific error and exit with non-zero status code.

**Validates: Requirements 2.5**

### Property 4: API Request Routing

*For any* valid API request to /api/query, the web server should route it to the router agent and return a response with the expected structure.

**Validates: Requirements 3.4**

### Property 5: Health Check Component Verification

*For any* agent initialization state (all ready, some ready, none ready), the health check endpoint should correctly report the status of each agent.

**Validates: Requirements 4.2**

### Property 6: Environment Variable Reading

*For any* Zeabur-provided environment variable (PORT, OPENAI_API_KEY, etc.), the application should correctly read and use the value.

**Validates: Requirements 5.2**

### Property 7: Stdout Logging

*For any* log message generated by the application, it should be output to stdout (not just files) for platform log collection.

**Validates: Requirements 5.5**

### Property 8: Initialization Retry with Backoff

*For any* failed initialization operation, the system should retry with exponentially increasing delays (1s, 2s, 4s, etc.) up to a maximum number of attempts.

**Validates: Requirements 6.1**

### Property 9: Graceful Degradation

*For any* missing optional dependency (aiohttp, external API), the system should continue operating with reduced functionality rather than crashing.

**Validates: Requirements 6.2**

### Property 10: Exception Logging and Recovery

*For any* unhandled exception in request processing, the system should log the full traceback and return an error response without crashing the server.

**Validates: Requirements 6.4**

## Error Handling

### Port Binding Errors
- **Cause**: Port already in use, invalid port number, insufficient permissions
- **Handling**: Log detailed error with port number, suggest alternatives, exit with code 1
- **User Message**: "Failed to bind to port {port}: {error}. Please check if port is available."

### Agent Initialization Errors
- **Cause**: Missing configuration, LLM API failures, dependency issues
- **Handling**: Retry with exponential backoff (max 3 attempts), log each attempt, continue with degraded functionality if possible
- **User Message**: "Agent {name} initialization failed: {error}. Retrying in {delay}s..."

### HTTP Request Errors
- **Cause**: Invalid request format, agent processing errors, timeouts
- **Handling**: Return appropriate HTTP status code (400, 500, 503), include error details in response
- **User Message**: JSON response with error field: `{"error": "description", "status": "error"}`

### Health Check Failures
- **Cause**: Agents not initialized, system overloaded, dependencies unavailable
- **Handling**: Return 503 status with details of which components are unhealthy
- **User Message**: `{"status": "unhealthy", "agents": {...}, "error": "description"}`

### Missing Dependencies
- **Cause**: aiohttp not installed, optional packages missing
- **Handling**: Fall back to basic HTTP server, log warning, disable affected features
- **User Message**: "Optional dependency {name} not available. Using fallback implementation."

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples, edge cases, and error conditions:

1. **Port Configuration Tests**
   - Test reading PORT from environment
   - Test fallback to OPENAGENTS_PORT
   - Test default port when neither is set
   - Test invalid port values (negative, too large, non-numeric)

2. **Health Endpoint Tests**
   - Test /health returns 200 when all agents ready
   - Test /health returns 503 when agents not initialized
   - Test health response includes all agent status
   - Test health response format matches schema

3. **Status Page Tests**
   - Test / returns HTML content
   - Test status page includes service information
   - Test status page renders correctly

4. **API Endpoint Tests**
   - Test /api/query with valid request
   - Test /api/query with missing query field
   - Test /api/query with invalid JSON
   - Test /api/query response format

5. **Error Handling Tests**
   - Test port binding failure logging
   - Test agent initialization retry logic
   - Test exception handling in request processing
   - Test graceful degradation with missing dependencies

### Property-Based Tests

Property tests will verify universal properties across all inputs using the Hypothesis library for Python. Each test will run a minimum of 100 iterations.

1. **Property Test: Port Configuration Reading**
   - **Feature: zeabur-deployment-fix, Property 1**: Port configuration reading
   - Generate random valid port numbers (1024-65535)
   - Set PORT environment variable
   - Verify application reads and uses that port

2. **Property Test: Host Binding**
   - **Feature: zeabur-deployment-fix, Property 2**: Host binding to all interfaces
   - Generate random server configurations
   - Verify host is always "0.0.0.0"

3. **Property Test: Port Binding Errors**
   - **Feature: zeabur-deployment-fix, Property 3**: Port binding error handling
   - Generate invalid port values (negative, 0, >65535, occupied ports)
   - Verify error logging and non-zero exit

4. **Property Test: API Routing**
   - **Feature: zeabur-deployment-fix, Property 4**: API request routing
   - Generate random valid query strings
   - Verify all get routed and return expected response structure

5. **Property Test: Health Check Verification**
   - **Feature: zeabur-deployment-fix, Property 5**: Health check component verification
   - Generate random agent initialization states
   - Verify health check correctly reports each state

6. **Property Test: Environment Variables**
   - **Feature: zeabur-deployment-fix, Property 6**: Environment variable reading
   - Generate random environment variable values
   - Verify application reads them correctly

7. **Property Test: Stdout Logging**
   - **Feature: zeabur-deployment-fix, Property 7**: Stdout logging
   - Generate random log messages
   - Verify all appear in stdout

8. **Property Test: Retry Backoff**
   - **Feature: zeabur-deployment-fix, Property 8**: Initialization retry with backoff
   - Simulate random initialization failures
   - Verify retry delays follow exponential backoff pattern

9. **Property Test: Graceful Degradation**
   - **Feature: zeabur-deployment-fix, Property 9**: Graceful degradation
   - Simulate random missing dependencies
   - Verify system continues operating

10. **Property Test: Exception Recovery**
    - **Feature: zeabur-deployment-fix, Property 10**: Exception logging and recovery
    - Generate random exceptions during request processing
    - Verify logging occurs and server continues running

### Integration Tests

1. **Full Server Startup Test**
   - Start server with real configuration
   - Verify all endpoints accessible
   - Verify agents initialized
   - Shutdown cleanly

2. **Zeabur Environment Simulation**
   - Set Zeabur-like environment variables
   - Start application
   - Verify correct port binding
   - Verify health checks pass

3. **Load Test**
   - Send multiple concurrent requests
   - Verify all get responses
   - Verify no crashes or hangs

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **hypothesis**: Property-based testing library
- **aiohttp.test_utils**: HTTP client for testing
- **unittest.mock**: Mocking for isolated tests