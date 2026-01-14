# Implementation Plan: Zeabur Deployment Fix

## Overview

This implementation plan fixes the 502 SERVICE_UNAVAILABLE error by implementing a proper web server layer that reads Zeabur's PORT environment variable, binds to all interfaces (0.0.0.0), and provides health check endpoints. The implementation will work with or without aiohttp, ensuring maximum compatibility.

## Tasks

- [ ] 1. Create port configuration module
  - Create `src/utils/server_config.py` with `get_server_config()` function
  - Read PORT environment variable (Zeabur standard)
  - Fall back to OPENAGENTS_PORT if PORT not set
  - Default to 8000 if neither is set
  - Always return host as "0.0.0.0" for cloud deployment
  - Add logging for configuration values
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ]* 1.1 Write property test for port configuration
  - **Property 1: Port Configuration Reading**
  - **Validates: Requirements 2.1, 2.2**

- [ ]* 1.2 Write unit tests for port configuration edge cases
  - Test default port when no env vars set
  - Test invalid port values
  - Test host is always 0.0.0.0
  - _Requirements: 2.3, 2.4_

- [ ] 2. Implement web server with health check endpoint
  - [ ] 2.1 Create `src/utils/web_server.py` with WebServer class
    - Implement aiohttp-based server with /health endpoint
    - Implement / (root) endpoint with status page
    - Add proper error handling and logging
    - Bind to host and port from configuration
    - _Requirements: 3.1, 3.2, 4.1_

  - [ ]* 2.2 Write property test for health check verification
    - **Property 5: Health Check Component Verification**
    - **Validates: Requirements 4.2**

  - [ ] 2.3 Create fallback SimpleWebServer for when aiohttp unavailable
    - Use Python's built-in http.server module
    - Implement basic /health endpoint
    - Implement basic / endpoint
    - _Requirements: 3.1, 6.2_

  - [ ]* 2.4 Write unit tests for health endpoint
    - Test /health returns 200 when agents ready
    - Test /health returns 503 when agents not ready
    - Test health response format
    - _Requirements: 4.1, 4.3, 4.4_

- [ ] 3. Implement API query endpoint
  - [ ] 3.1 Add POST /api/query endpoint to WebServer
    - Parse JSON request body
    - Extract query field
    - Call router agent with query
    - Return JSON response with result
    - Handle errors with appropriate status codes
    - _Requirements: 3.4_

  - [ ]* 3.2 Write property test for API routing
    - **Property 4: API Request Routing**
    - **Validates: Requirements 3.4**

  - [ ]* 3.3 Write unit tests for API endpoint
    - Test valid query request
    - Test missing query field
    - Test invalid JSON
    - Test response format
    - _Requirements: 3.4_

- [ ] 4. Update main.py to use new web server
  - [ ] 4.1 Import and use get_server_config() function
    - Replace hardcoded port configuration
    - Use PORT environment variable
    - Log configuration on startup
    - _Requirements: 2.1, 2.2_

  - [ ] 4.2 Update start_openagents_mode() to use WebServer class
    - Create WebServer instance
    - Pass YouGameExplorer instance to server
    - Start server with correct host and port
    - Handle server startup errors
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 4.3 Write property test for port binding errors
    - **Property 3: Port Binding Error Handling**
    - **Validates: Requirements 2.5**

- [ ] 5. Implement error recovery and retry logic
  - [ ] 5.1 Create retry utility in `src/utils/retry.py`
    - Implement exponential backoff function
    - Add configurable max attempts
    - Add logging for each retry attempt
    - _Requirements: 6.1_

  - [ ]* 5.2 Write property test for retry backoff
    - **Property 8: Initialization Retry with Backoff**
    - **Validates: Requirements 6.1**

  - [ ] 5.3 Add retry logic to agent initialization
    - Wrap agent initialization in retry logic
    - Log failures and retry attempts
    - Continue with degraded functionality if max retries exceeded
    - _Requirements: 6.1, 6.2_

  - [ ]* 5.4 Write property test for graceful degradation
    - **Property 9: Graceful Degradation**
    - **Validates: Requirements 6.2**

- [ ] 6. Implement exception handling and logging
  - [ ] 6.1 Add global exception handler to web server
    - Catch all unhandled exceptions in request handlers
    - Log full traceback to stdout
    - Return 500 error response with error details
    - Keep server running after exceptions
    - _Requirements: 6.4_

  - [ ]* 6.2 Write property test for exception recovery
    - **Property 10: Exception Logging and Recovery**
    - **Validates: Requirements 6.4**

  - [ ] 6.3 Configure logging to output to stdout
    - Update logger configuration in common.py
    - Ensure all logs go to stdout
    - Add structured logging format
    - _Requirements: 5.5_

  - [ ]* 6.4 Write property test for stdout logging
    - **Property 7: Stdout Logging**
    - **Validates: Requirements 5.5**

- [ ] 7. Update Zeabur deployment files
  - [ ] 7.1 Update zeabur-start.py to use PORT environment variable
    - Remove OPENAGENTS_PORT default
    - Let application read PORT from Zeabur
    - Remove hardcoded port configuration
    - _Requirements: 2.1, 2.2, 5.2_

  - [ ] 7.2 Update Dockerfile health check
    - Use PORT environment variable in health check
    - Increase timeout for cloud environment
    - _Requirements: 4.1, 5.3_

  - [ ]* 7.3 Write property test for environment variable reading
    - **Property 6: Environment Variable Reading**
    - **Validates: Requirements 5.2**

- [ ] 8. Checkpoint - Test deployment locally
  - Build Docker image locally
  - Run with PORT environment variable set
  - Verify server starts and binds to correct port
  - Verify /health endpoint responds
  - Verify / endpoint shows status page
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Create integration tests
  - [ ]* 9.1 Write full server startup test
    - Start server with real configuration
    - Verify all endpoints accessible
    - Verify agents initialized
    - Shutdown cleanly
    - _Requirements: 3.1, 3.2, 3.3, 4.1_

  - [ ]* 9.2 Write Zeabur environment simulation test
    - Set Zeabur-like environment variables
    - Start application
    - Verify correct port binding
    - Verify health checks pass
    - _Requirements: 2.1, 2.2, 2.4, 4.1, 5.2_

- [ ] 10. Final checkpoint - Verify deployment readiness
  - Run all tests (unit, property, integration)
  - Verify Docker build succeeds
  - Verify health check works
  - Review logs for any warnings
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties with minimum 100 iterations
- Unit tests validate specific examples and edge cases
- The implementation prioritizes getting the service working on Zeabur first, then adding comprehensive testing