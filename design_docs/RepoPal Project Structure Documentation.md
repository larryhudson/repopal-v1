# RepoPal Project Structure Documentation

## 1. Project Overview

RepoPal is a Python-based system that automates code changes and repository management tasks in response to events from various services (GitHub, Slack, Linear, etc.). The project uses:
- Flask for the web application and API endpoints
- Celery for asynchronous task processing
- SQLAlchemy for database management
- LLM integration for request analysis and command generation
- Docker for isolated command execution

## 2. Directory Structure

```
repopal/
├── alembic/                    # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
│
├── docker/                     # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
├── repopal/                    # Main package
│   ├── __init__.py
│   ├── app.py                 # Flask application factory
│   ├── celery_app.py          # Celery configuration
│   ├── config.py              # Configuration management
│   ├── extensions.py          # Flask extensions
│   │
│   ├── api/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── routes.py         # General API routes
│   │   └── webhooks.py       # Webhook handlers
│   │
│   ├── commands/              # Command system
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base command
│   │   ├── registry.py       # Command registry
│   │   ├── factory.py        # Command factory
│   │   └── implementations/   # Concrete commands
│   │       ├── __init__.py
│   │       ├── srgn.py
│   │       └── [other_commands].py
│   │
│   ├── core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── event_router.py
│   │   ├── action_dispatcher.py
│   │   ├── command_processor.py
│   │   ├── result_processor.py
│   │   ├── repo_manager.py
│   │   └── types/            # Shared types
│   │       ├── __init__.py
│   │       ├── events.py
│   │       ├── commands.py
│   │       └── results.py
│   │
│   ├── llm/                   # LLM integration
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── command_selector.py
│   │   ├── arg_generator.py
│   │   └── prompts/
│   │       ├── __init__.py
│   │       ├── command_selection.py
│   │       └── arg_generation.py
│   │
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── service.py
│   │   ├── repository.py
│   │   └── execution.py
│   │
│   ├── services/            # Service integrations
│   │   ├── __init__.py
│   │   ├── base.py         # Base service interface
│   │   ├── factory.py      # Service factory
│   │   ├── github.py
│   │   ├── slack.py
│   │   └── linear.py
│   │
│   ├── tasks/              # Celery tasks
│   │   ├── __init__.py
│   │   ├── event_processing.py
│   │   └── command_execution.py
│   │
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── docker.py
│       ├── security.py
│       └── logging.py
│
├── tests/                  # Test suite
│   ├── conftest.py
│   ├── factories/
│   │   ├── __init__.py
│   │   └── model_factories.py
│   ├── test_api/
│   ├── test_commands/
│   ├── test_core/
│   └── test_services/
│
├── config/               # Configuration files
│   ├── development.py
│   ├── production.py
│   └── testing.py
│
└── scripts/             # Utility scripts
    ├── setup.sh
    ├── test.sh
    └── lint.sh
```

## 3. Core Components and Their Responsibilities

### 3.1 Event Processing Pipeline

1. **Event Router** (`core/event_router.py`)
   - Standardizes events from different sources
   - Routes events to appropriate handlers
   - Maintains mapping of event types to handlers

2. **Action Dispatcher** (`core/action_dispatcher.py`)
   - Analyzes user requests using LLM
   - Selects appropriate commands
   - Generates command arguments
   - Creates executable command requests

3. **Command Processor** (`core/command_processor.py`)
   - Manages command execution lifecycle
   - Sets up isolated environments
   - Executes commands and captures results
   - Handles cleanup and resource management

4. **Result Processor** (`core/result_processor.py`)
   - Processes command execution results
   - Creates pull requests when needed
   - Prepares notification data
   - Delegates to service-specific notifiers

### 3.2 Service Layer

1. **Base Service Interface** (`services/base.py`)
   - Defines standard service interface
   - Implements common service functionality
   - Provides notification methods

2. **Service Implementations**
   - GitHub (`services/github.py`)
     - Repository operations
     - PR management
     - Issue tracking
   - Slack (`services/slack.py`)
     - Message formatting
     - Thread management
     - Interactive components
   - Linear (`services/linear.py`)
     - Issue tracking
     - Status management
     - Workflow automation

3. **Service Factory** (`services/factory.py`)
   - Creates service instances
   - Manages service configuration
   - Handles service lifecycle

### 3.3 Command System

1. **Base Command** (`commands/base.py`)
   - Abstract command interface
   - Common command functionality
   - Execution environment requirements

2. **Command Registry** (`commands/registry.py`)
   - Manages available commands
   - Handles command registration
   - Provides command metadata

3. **Command Factory** (`commands/factory.py`)
   - Creates command instances
   - Manages command configuration
   - Handles dependencies

## 4. Data Flow

### 4.1 Request Processing Flow
```mermaid
graph TD
    A[Webhook] --> B[Event Router]
    B --> C[Action Dispatcher]
    C --> |Analysis| D[LLM]
    D --> C
    C --> E[Command Processor]
    E --> F[Result Processor]
    F --> G[Service Notifier]
```

### 4.2 Type System

Core types defined in `core/types/`:

```python
# events.py
@dataclass
class StandardizedEvent:
    source: str
    type: str
    context: Dict[str, Any]
    data: Dict[str, Any]

# commands.py
@dataclass
class CommandRequest:
    command: str
    arguments: Dict[str, Any]
    context: Dict[str, Any]

# results.py
@dataclass
class CommandResult:
    status: str
    output: str
    changes: Dict[str, Any]
    error: str = None
    has_changes: bool = False

@dataclass
class ProcessedResult:
    status: str
    changes: Dict[str, Any]
    pr_data: Dict[str, Any] = None
    notification_data: Dict[str, Any] = None
```

## 5. Module Dependencies

### 5.1 Internal Dependencies
```mermaid
graph TD
    A[API Layer] --> B[Core]
    B --> C[Commands]
    B --> D[Services]
    B --> E[LLM]
    C --> F[Utils]
    D --> F
    B --> G[Tasks]
    G --> C
    G --> D
```

### 5.2 External Dependencies

```toml
[production]
flask = "^2.0.0"
celery = "^5.3.0"
sqlalchemy = "^2.0.0"
slack-sdk = "^3.19.0"
PyGithub = "^1.58.0"
linear-client = "^1.0.0"
openai = "^1.0.0"
anthropic = "^0.3.0"
docker = "^6.1.0"

[development]
pytest = "^7.3.0"
black = "^23.3.0"
mypy = "^1.3.0"
```

## 6. Configuration

### 6.1 Environment Variables
```bash
# Application
FLASK_APP=repopal.app:create_app()
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Infrastructure
DATABASE_URL=postgresql://user:pass@localhost/repopal
REDIS_URL=redis://localhost:6379/0

# Services
GITHUB_APP_ID=your-github-app-id
SLACK_BOT_TOKEN=your-slack-token
LINEAR_API_KEY=your-linear-key

# LLM
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 6.2 Configuration Classes
```python
class Config:
    """Base configuration."""
    pass

class DevelopmentConfig(Config):
    """Development configuration."""
    pass

class ProductionConfig(Config):
    """Production configuration."""
    pass

class TestingConfig(Config):
    """Testing configuration."""
    pass
```

## 7. Testing Strategy

### 7.1 Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── factories/               # Test data factories
├── test_api/               # API tests
├── test_commands/          # Command tests
├── test_core/             # Core component tests
└── test_services/         # Service integration tests
```

### 7.2 Testing Guidelines
- Unit tests for all components
- Integration tests for workflows
- Mock external services
- Use factory_boy for test data
- Maintain 90%+ coverage

### 7.3 Key Test Areas
1. Event processing pipeline
2. Command execution
3. Service integrations
4. LLM interactions
5. Error handling
6. Notification delivery