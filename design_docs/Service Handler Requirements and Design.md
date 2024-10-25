# Service Handler Requirements and Design

## 1. Overview

The Service Handler is responsible for translating service-specific events (GitHub, Slack, Linear, etc.) into a standardized format that can be processed by the Action Dispatcher. It serves as the critical adaptation layer between external services and our internal processing pipeline.

## 2. Core Responsibilities

1. Event Reception
   - Validate incoming webhooks/events
   - Parse service-specific payload formats
   - Authenticate and authorize requests
   - Handle rate limiting and quotas

2. Event Translation
   - Extract relevant information from service-specific formats
   - Normalize data into standardized format
   - Filter out unnecessary service-specific details
   - Ensure consistent data structures across services

3. Context Resolution
   - Resolve repository information
   - Determine user permissions
   - Identify relevant branches
   - Extract file references

## 3. Required Interfaces

### 3.1 Base Service Handler
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseServiceHandler(ABC):
    @abstractmethod
    async def validate_webhook(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        """Validate webhook authenticity and authorization"""
        pass
    
    @abstractmethod
    async def process_event(self, event_type: str, payload: Dict[str, Any]) -> StandardizedEvent:
        """Process raw event into standardized format"""
        pass
    
    @abstractmethod
    async def resolve_repository_context(self, payload: Dict[str, Any]) -> RepositoryContext:
        """Extract repository information from event"""
        pass
    
    @abstractmethod
    async def resolve_user_permissions(self, user_id: str, repository: str) -> bool:
        """Determine user's permissions for the repository"""
        pass
```

### 3.2 Required Output Format
```python
@dataclass
class StandardizedEvent:
    request: UserRequest
    repository: RepositoryContext
    environment: ExecutionEnvironment

# These must be populated by the service handler
@dataclass
class UserRequest:
    content: str                     # The actual request text
    referenced_files: List[str]      # Files mentioned in request
    referenced_branches: List[str]    # Branches mentioned in request

@dataclass
class RepositoryContext:
    name: str              # Repository name
    default_branch: str    # Default branch name
    primary_language: str  # Main programming language
    can_write: bool       # Write permission flag
    can_read: bool        # Read permission flag

@dataclass
class ExecutionEnvironment:
    target_branch: str     # Target branch for changes
    base_branch: str       # Base branch to work from
    is_production: bool    # Production environment flag
```

## 4. Implementation Requirements

### 4.1 Text Processing Requirements
```python
class TextProcessingRequirements:
    """Requirements for processing user request text"""
    
    def clean_user_request(self, raw_text: str) -> str:
        """
        Must:
        1. Remove service-specific formatting (e.g., Slack markup, GitHub markdown)
        2. Remove mentions and bot triggers
        3. Remove irrelevant metadata
        4. Normalize whitespace
        5. Handle unicode characters appropriately
        6. Preserve code blocks and technical content
        """
        pass
    
    def extract_file_references(self, text: str) -> List[str]:
        """
        Must detect:
        1. Direct file mentions
        2. File paths in code blocks
        3. Common file reference patterns
        4. Extended glob patterns
        """
        pass
    
    def extract_branch_references(self, text: str) -> List[str]:
        """
        Must detect:
        1. Direct branch mentions
        2. Branch names in commands
        3. Common git reference patterns
        """
        pass
```

### 4.2 Repository Resolution Requirements
```python
class RepositoryResolutionRequirements:
    """Requirements for resolving repository information"""
    
    async def resolve_repository_info(self, service_data: Dict[str, Any]) -> RepositoryContext:
        """
        Must:
        1. Identify repository from service event
        2. Handle repository aliases/references
        3. Validate repository access
        4. Determine repository settings
        5. Cache repository information when appropriate
        """
        pass
    
    async def determine_environment(self, repository: str) -> ExecutionEnvironment:
        """
        Must:
        1. Identify production vs non-production
        2. Determine appropriate target branch
        3. Handle branch protection rules
        4. Consider repository settings
        """
        pass
```

## 5. Service-Specific Implementations

### 5.1 GitHub Handler Example
```python
class GitHubServiceHandler(BaseServiceHandler):
    async def validate_webhook(self, headers: Dict[str, str], body: Dict[str, Any]) -> bool:
        # Validate GitHub webhook signature
        # Check event type
        # Verify repository access
        pass
    
    async def process_event(self, event_type: str, payload: Dict[str, Any]) -> StandardizedEvent:
        # Extract user request
        content = self._clean_github_markdown(payload['comment']['body'])
        
        # Resolve repository context
        repo_context = await self.resolve_repository_context(payload)
        
        # Determine environment
        env = await self.determine_environment(repo_context.name)
        
        return StandardizedEvent(
            request=UserRequest(
                content=content,
                referenced_files=self.extract_file_references(content),
                referenced_branches=self.extract_branch_references(content)
            ),
            repository=repo_context,
            environment=env
        )
```

### 5.2 Slack Handler Example
```python
class SlackServiceHandler(BaseServiceHandler):
    async def process_event(self, event_type: str, payload: Dict[str, Any]) -> StandardizedEvent:
        # Extract user request
        content = self._clean_slack_markup(payload['text'])
        
        # Resolve repository from channel/conversation
        repo_context = await self.resolve_repository_from_channel(
            payload['channel_id']
        )
        
        # Determine environment
        env = await self.determine_environment(repo_context.name)
        
        return StandardizedEvent(
            request=UserRequest(
                content=content,
                referenced_files=self.extract_file_references(content),
                referenced_branches=self.extract_branch_references(content)
            ),
            repository=repo_context,
            environment=env
        )
```

## 6. Error Handling Requirements

### 6.1 Required Error Cases
```python
class ServiceHandlerError(Exception):
    """Base class for service handler errors"""
    pass

class WebhookValidationError(ServiceHandlerError):
    """Webhook validation failed"""
    pass

class RepositoryResolutionError(ServiceHandlerError):
    """Unable to resolve repository"""
    pass

class PermissionError(ServiceHandlerError):
    """User lacks required permissions"""
    pass

class InvalidEventError(ServiceHandlerError):
    """Event format or type is invalid"""
    pass
```

## 7. Testing Requirements

### 7.1 Required Test Cases
1. Webhook Validation
   - Valid webhook signatures
   - Invalid signatures
   - Missing headers
   - Malformed payloads

2. Text Processing
   - Service-specific markup removal
   - File reference extraction
   - Branch reference extraction
   - Special character handling

3. Repository Resolution
   - Direct repository references
   - Channel-based resolution
   - Missing repositories
   - Permission checking

4. Event Translation
   - All supported event types
   - Edge cases and error conditions
   - Data normalization
   - Permission scenarios

## 8. Performance Requirements

1. Webhook Processing
   - Maximum processing time: 2 seconds
   - Maximum memory usage: 256MB
   - Concurrent webhook handling

2. Repository Resolution
   - Cache frequently accessed repository data
   - Maximum resolution time: 1 second
   - Handle repository aliases efficiently

3. Error Handling
   - Fast failure detection
   - Efficient error reporting
   - Minimal impact on webhook processing

## 9. Security Requirements

1. Authentication
   - Validate all webhook signatures
   - Verify API tokens
   - Check request origins

2. Authorization
   - Verify repository access
   - Check user permissions
   - Validate operation permissions

3. Data Handling
   - Sanitize user input
   - Validate file paths
   - Prevent command injection
