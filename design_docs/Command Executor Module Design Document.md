# Command Executor Module Design Document

## 1. Overview

The Command Executor module is responsible for executing commands in isolated environments based on input from the Action Dispatcher. It handles repository setup, command execution in Docker containers, and captures execution results for further processing.

## 2. System Context

### 2.1 Position in System Architecture
- Receives commands from Action Dispatcher
- Uses GitHub App authentication for repository access
- Provides execution results to Result Processor
- Uses Docker for isolated command execution

### 2.2 Dependencies
- GitHub App Authentication system
- Docker Engine
- Git command line tools
- Command Library (for command configurations)

## 3. Input Contract

### 3.1 Command Request
```python
@dataclass
class CommandRequest:
    command_name: str                # Name of command to execute
    arguments: CommandArguments      # Command arguments and environment
    execution_context: ExecutionContext  # Execution parameters

@dataclass
class CommandArguments:
    required: Dict[str, Any]         # Required command arguments
    optional: Dict[str, Any]         # Optional command arguments

@dataclass
class ExecutionContext:
    target_branch: str              # Branch for changes
    base_branch: str               # Starting branch
    repository_name: str           # Full repo name (owner/repo)
    installation_id: int           # GitHub App installation ID
    allow_writes: bool            # Whether writes are permitted
```

## 4. Output Contract

### 4.1 Execution Result
```python
@dataclass
class ExecutionResult:
    status: ExecutionStatus          # Success/failure and exit code
    output: CommandOutput           # Command output streams
    changes: ChangeSet              # Detected file changes
    workspace: ExecutionWorkspace   # Workspace information

@dataclass
class ExecutionStatus:
    success: bool                   # Whether execution succeeded
    exit_code: int                 # Command exit code
    error: Optional[str]           # Error message if failed

@dataclass
class CommandOutput:
    stdout: str                    # Standard output
    stderr: str                    # Standard error
    logs: List[LogEntry]           # Execution logs

@dataclass
class ChangeSet:
    files: List[FileChange]        # Changed files
    original_commit: str           # Starting commit SHA
    final_commit: Optional[str]    # Ending commit SHA

@dataclass
class FileChange:
    path: str                      # File path
    status: str                    # modified/added/deleted
```

## 5. Core Components

### 5.1 Command Executor
Primary class responsible for managing the execution flow:
```python
class CommandExecutor:
    def __init__(self, github_auth: GitHubAppAuth):
        self.github_auth = github_auth

    async def execute_command(
        self, 
        command_request: CommandRequest
    ) -> ExecutionResult:
        # Main execution flow
```

### 5.2 Workspace Manager
Handles temporary workspace creation and cleanup:
```python
class WorkspaceManager:
    async def create_workspace(
        self,
        command_request: CommandRequest
    ) -> ExecutionWorkspace:
        # Setup workspace

    async def cleanup_workspace(
        self,
        workspace: ExecutionWorkspace
    ):
        # Cleanup resources
```

### 5.3 Container Manager
Manages Docker container lifecycle:
```python
class ContainerManager:
    async def run_container(
        self,
        command_request: CommandRequest,
        workspace: ExecutionWorkspace
    ) -> ContainerResult:
        # Container execution
```

## 6. Key Operations

### 6.1 Execution Flow
1. Create temporary workspace
2. Clone repository using GitHub App token
3. Setup Docker container with mounted workspace
4. Execute command in container
5. Capture changes and results
6. Clean up resources

### 6.2 Repository Operations
- Clone operations occur on host system
- Use GitHub App installation tokens
- Capture original and final commit SHAs
- Track file changes

### 6.3 Container Operations
- Use pre-built images from Command Library
- Mount workspace as read-write
- Run as non-root user
- Capture command output
- Handle resource cleanup

## 7. Error Handling

### 7.1 Error Categories
```python
class CommandExecutionError(Exception):
    """Base class for execution errors"""

class WorkspaceError(CommandExecutionError):
    """Workspace setup/cleanup errors"""

class ContainerError(CommandExecutionError):
    """Container operations errors"""

class GitOperationError(CommandExecutionError):
    """Git operation errors"""
```

### 7.2 Error Recovery
- Clean up workspace on failures
- Remove containers on errors
- Capture error details in result
- Maintain audit trail

## 8. Security Considerations

### 8.1 Repository Access
- GitHub App tokens never exposed to containers
- Tokens cached with expiration
- Clean credential cleanup

### 8.2 Container Security
- Run commands as non-root user
- Limited container capabilities
- Resource limits enforced
- Network access controlled

## 9. Performance Considerations

### 9.1 Resource Management
- Workspace disk usage limits
- Container memory limits
- CPU allocation controls
- Network bandwidth limits

### 9.2 Optimization
- Reuse Docker images
- Efficient workspace cleanup
- Parallel execution support
- Resource pooling

## 10. Integration Points

### 10.1 Action Dispatcher Integration
- Receives complete command configuration
- No command selection logic
- Validates input contract

### 10.2 Result Processor Integration
- Provides detailed change information
- Raw command output
- Execution metadata
- No PR creation logic

## 11. Configuration

### 11.1 Required Configuration
```python
@dataclass
class CommandExecutorConfig:
    workspace_root: Path           # Base path for workspaces
    max_workspace_size: int        # Maximum workspace size
    container_memory_limit: str    # Container memory limit
    container_cpu_limit: float     # Container CPU limit
    execution_timeout: int         # Command timeout in seconds
    cleanup_timeout: int          # Cleanup timeout in seconds
```

### 11.2 Environment Variables
- `GITHUB_APP_ID`: GitHub App identifier
- `GITHUB_PRIVATE_KEY`: GitHub App private key
- `DOCKER_HOST`: Docker daemon address
- `WORKSPACE_ROOT`: Base path for workspaces

## 12. Testing Strategy

### 12.1 Unit Tests
- Mock Docker operations
- Mock Git operations
- Test error handling
- Validate contracts

### 12.2 Integration Tests
- Test with real Docker
- Test with test repositories
- Verify cleanup
- Measure performance

## 13. Limitations

1. Single host execution
2. Synchronous Git operations
3. Local Docker daemon requirement
4. Workspace disk space requirements

## 14. Future Improvements

1. Distributed execution support
2. Cached workspace support
3. Pre-warmed containers
4. Remote Docker support
5. Workspace compression
6. Incremental cloning