# System Architecture Overview

## 1. System Overview

The system is designed to automate code changes and repository management tasks in response to events from various services (GitHub, Slack, Linear, etc.). It uses GitHub for repository management and authentication while allowing integration with multiple service providers for triggering actions and receiving notifications.

## 2. Core Processing Components

### 2.1 Event Reception & Routing
- **Webhook Server**: Central entry point for all service events
- **Event Router**: Routes events to appropriate service-specific handlers
- **Service Handlers**: Transform service-specific events into standardized format

### 2.2 Action Dispatcher
The Action Dispatcher is the central orchestration component that:
- Receives standardized events from service handlers
- Coordinates with LLM instances:
  1. **Command Selection LLM**: 
     - Input: Available commands, command contexts, and event details
     - Output: Selected most appropriate command
  2. **Argument Generation LLM**:
     - Input: Selected command documentation and event context
     - Output: Generated command arguments
- Manages repository preparation through the Repo Cloner
- Delegates to service-specific handlers through ServiceFactory
- Maintains service-agnostic core logic

### 2.3 Commands Library
- Repository of available commands and their implementations
- Each command includes:
  - Execution logic
  - Documentation
  - Context for when to use
  - Required arguments
  - Installation requirements
  - Environment variable requirements
  - Service-agnostic result format specification

### 2.4 Command Executor
- Receives command and arguments from Action Dispatcher
- Manages command execution environment
- Handles command dependencies
- Executes commands in isolated environments
- Captures command output and execution status
- Returns standardized result format for cross-service compatibility
- Manages execution timeouts and resource limits

### 2.5 Result Processor
- Service-agnostic core processor that:
  - Analyzes command execution results
  - Validates results against expected formats
  - Routes notifications to appropriate service handlers
  - Manages error conditions and retries
- Delegates service-specific operations:
  - PR creation to GitHub service
  - Notification formatting to individual services
  - Status updates to respective services

### 2.6 Service Layer
- Implements BaseService interface for all integrated services
- Service-specific implementations:
  - Slack: Rich message formatting and thread management
  - GitHub: Issue comments and PR management
  - Linear: Issue tracking and status updates
- Components:
  - ServiceFactory for service instance management
  - Service-specific authentication and API handling
  - Custom notification formatting for each platform
  - Platform-specific feature implementations

## 3. Authentication & User Management

### 3.1 User Authentication
- GitHub OAuth-based authentication
- User session management
- Secure credential storage
- Permission management

### 3.2 Service Connections
- Service-specific OAuth or API key authentication
- Mapping between services and repositories
- Configuration management for service integrations

## 4. Core Workflows

### 4.1 Initial Setup Flow
1. User authenticates via GitHub OAuth
2. User creates and configures service apps
3. User connects services through dashboard
4. System validates service connections
5. User maps repositories to service integrations
6. System verifies required permissions for each service

### 4.2 Event Processing Flow
1. Event received by Webhook Server
2. Event Router directs to appropriate service handler
3. Service Handler standardizes event
4. Action Dispatcher:
   - Resolves repository context
   - Selects appropriate command
   - Generates command arguments
5. Command Executor:
   - Prepares execution environment
   - Runs command with arguments
6. Result Processor:
   - Analyzes command output
   - Routes to appropriate service handler
   - Delegates notification formatting
7. Service Handler:
   - Formats notifications according to service requirements
   - Creates PRs or updates if needed
   - Sends platform-specific notifications

### 4.3 Multi-Service Integration Flow
1. User makes code change request via Slack
2. System processes request and creates PR
3. Notifications sent to:
   - Slack: Threaded reply with rich formatting
   - GitHub: PR creation and issue comments
   - Linear: Issue status update and comments
4. Each service receives appropriately formatted updates

## 5. Data Model

### 5.1 Core Entities
```
User {
    id: UUID
    github_id: String
    github_username: String
    email: String
}

ServiceConnection {
    id: UUID
    user_id: UUID
    service_type: Enum
    credentials: EncryptedJSON
    settings: JSON
    notification_preferences: JSON
}

RepositoryMapping {
    id: UUID
    user_id: UUID
    github_repo_id: String
    service_connection_id: UUID
    service_specific_id: String
    settings: JSON
    notification_rules: JSON
}

CommandExecution {
    id: UUID
    user_id: UUID
    repository_id: String
    command: String
    arguments: JSON
    status: Enum
    result: JSON
    notifications_sent: JSON
    created_at: Timestamp
}
```

## 6. Service Integration

### 6.1 Service Interface Requirements
- Must implement BaseService interface
- Standard notification methods:
  - notify_success()
  - notify_error()
- Service-specific formatting handlers
- Custom feature implementations

### 6.2 Service-Specific Implementations
1. GitHub Integration:
   - Repository access
   - PR creation and management
   - Issue comment formatting
   - Status updates
   - Markdown-based notifications

2. Slack Integration:
   - Bot user setup
   - Command handling
   - Rich block message formatting
   - Thread management
   - Interactive components

3. Linear Integration:
   - Issue tracking
   - Status synchronization
   - Comment formatting
   - Workflow state management
   - Automated status updates

### 6.3 Cross-Service Communication
- Standardized event format
- Service-agnostic core processing
- Platform-specific notification delivery
- Unified error handling
- Consistent status tracking

## 7. Security & Performance

### 7.1 Security Measures
- Encrypted credential storage
- Secure webhook validation
- Rate limiting
- Access control
- Audit logging

### 7.2 Performance Considerations
- Asynchronous event processing
- Command execution timeouts
- Resource limits
- Caching strategies
- Horizontal scaling capability

## 8. Development & Operations

### 8.1 Development Guidelines
- Service handler implementation requirements
- BaseService interface compliance
- Notification format standards
- Testing requirements for service integrations
- Documentation standards for service-specific features

### 8.2 Operational Requirements
- Monitoring
- Logging
- Backup procedures
- Scaling considerations

## 9. Future Extensibility

### 9.1 New Service Integration
- Standard integration interface
- Event handling templates
- Documentation requirements

### 9.2 Command System Extension
- Command interface definition
- LLM prompt templates
- Testing framework

## 10. Error Handling

### 10.1 Error Categories
- Authentication errors
- Command execution errors
- Service integration errors
- Repository operation errors

### 10.2 Error Recovery
- Retry strategies
- Fallback procedures
- User notification protocols
- System recovery procedures