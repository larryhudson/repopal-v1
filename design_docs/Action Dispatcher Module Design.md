# Action Dispatcher Module Design

## 1. Service-Agnostic Input Design

### 1.1 Standardized Event
```python
@dataclass
class StandardizedEvent:
    # Core request information
    request: UserRequest
    
    # Repository context
    repository: RepositoryContext
    
    # Execution environment information
    environment: ExecutionEnvironment

@dataclass
class UserRequest:
    # The actual request text from the user
    content: str
    
    # Any specific files or paths mentioned in the request
    referenced_files: List[str] = field(default_factory=list)
    
    # Any specific branch names mentioned in the request
    referenced_branches: List[str] = field(default_factory=list)

@dataclass
class RepositoryContext:
    # Essential repository information
    name: str              # Repository name
    default_branch: str    # Default branch name
    primary_language: str  # Main programming language
    
    # Access and permissions
    can_write: bool       # Whether changes can be made
    can_read: bool        # Whether content can be read

@dataclass
class ExecutionEnvironment:
    # Target branch for changes
    target_branch: str
    
    # Base branch to work from
    base_branch: str
    
    # Whether this is a production environment
    is_production: bool = False
```

### 1.2 Command Request Output
```python
@dataclass
class CommandRequest:
    # Selected command to execute
    command_name: str
    
    # Arguments for the command
    arguments: CommandArguments
    
    # Execution context
    execution_context: ExecutionContext

@dataclass
class CommandArguments:
    # Required arguments for the command
    required: Dict[str, Any]
    
    # Optional arguments that were determined to be relevant
    optional: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExecutionContext:
    # Target branch for the changes
    target_branch: str
    
    # Base branch to work from
    base_branch: str
    
    # Repository information needed for execution
    repository_name: str
    
    # Whether writes are allowed
    allow_writes: bool
```

## 2. Example Usage

### 2.1 Event Handler Translation
```python
# In the GitHub Event Handler
def translate_to_standardized_event(github_event: GitHubIssueComment) -> StandardizedEvent:
    return StandardizedEvent(
        request=UserRequest(
            content=github_event.comment.body,
            referenced_files=extract_file_references(github_event.comment.body),
            referenced_branches=extract_branch_references(github_event.comment.body)
        ),
        repository=RepositoryContext(
            name=github_event.repository.full_name,
            default_branch=github_event.repository.default_branch,
            primary_language=github_event.repository.language,
            can_write=github_event.sender.permissions.push,
            can_read=github_event.sender.permissions.pull
        ),
        environment=ExecutionEnvironment(
            target_branch=github_event.repository.default_branch,
            base_branch=github_event.repository.default_branch,
            is_production=is_production_repo(github_event.repository)
        )
    )

# In the Slack Event Handler
def translate_to_standardized_event(slack_event: SlackMessage) -> StandardizedEvent:
    repo_info = get_repository_from_channel(slack_event.channel)
    return StandardizedEvent(
        request=UserRequest(
            content=slack_event.text,
            referenced_files=extract_file_references(slack_event.text),
            referenced_branches=extract_branch_references(slack_event.text)
        ),
        repository=RepositoryContext(
            name=repo_info.name,
            default_branch=repo_info.default_branch,
            primary_language=repo_info.language,
            can_write=check_user_permissions(slack_event.user, repo_info),
            can_read=True
        ),
        environment=ExecutionEnvironment(
            target_branch=repo_info.default_branch,
            base_branch=repo_info.default_branch,
            is_production=is_production_repo(repo_info)
        )
    )
```

### 2.2 Action Dispatcher Usage
```python
class ActionDispatcher:
    async def dispatch(self, event: StandardizedEvent) -> CommandRequest:
        # Select command based on user request
        command_name = await self.command_selector.select_command(
            user_request=event.request.content,
            available_commands=self.command_registry.list_enabled_commands()
        )
        
        # Get command instance
        command = self.command_registry.get_command(command_name)
        
        # Generate arguments based on request and command documentation
        arguments = await self.arg_generator.generate_arguments(
            command=command,
            user_request=event.request.content,
            referenced_files=event.request.referenced_files,
            referenced_branches=event.request.referenced_branches
        )
        
        return CommandRequest(
            command_name=command_name,
            arguments=CommandArguments(
                required=arguments.required,
                optional=arguments.optional
            ),
            execution_context=ExecutionContext(
                target_branch=event.environment.target_branch,
                base_branch=event.environment.base_branch,
                repository_name=event.repository.name,
                allow_writes=event.repository.can_write
            )
        )
```

## 3. Key Benefits of This Design

1. **True Service Agnosticism**
   - No service-specific information in the standardized event
   - Event handlers handle all service-specific translation
   - Action Dispatcher works with pure domain concepts

2. **Clear Responsibility Boundaries**
   - Event handlers: Transform service-specific events to standardized format
   - Action Dispatcher: Command selection and argument generation
   - Command Executor: Command execution in proper context

3. **Minimal Required Information**
   - Only includes information needed for command selection and execution
   - No leaked implementation details from services
   - Clear, focused data structures

4. **Flexible and Extensible**
   - Easy to add new event sources without changing Action Dispatcher
   - Clear contract for event handlers to implement
   - Simple to extend with new fields if needed

5. **Security-Conscious Design**
   - Explicit permission checks in context
   - Clear separation of read/write capabilities
   - Environment awareness for safety checks