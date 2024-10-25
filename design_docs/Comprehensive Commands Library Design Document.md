# Comprehensive Commands Library Design Document

## 1. Introduction

The Commands Library is a core component of our application, designed to provide a flexible and extensible system for executing various operations within our project. It allows for easy addition of new functionalities through a modular command system, with each command encapsulating its own logic, dependencies, and execution requirements.

## 2. System Overview

The Commands Library integrates with the larger application as follows:

1. **Configuration**: Commands are defined and enabled/disabled through a configuration file.
2. **Command Registry**: Manages the collection of available commands.
3. **Command Execution**: Triggered by the application's main logic or user input.
4. **Docker Integration**: Allows for containerized execution with dynamic dependency management.
5. **Environment Management**: Ensures required environment variables are set for enabled commands.

## 3. Core Components

### 3.1 Base Command Class

The `Command` abstract base class serves as the foundation for all command implementations:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Command(ABC):
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    @abstractmethod
    def execute(self, repo_path: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_context(self) -> str:
        pass

    @abstractmethod
    def get_documentation(self) -> str:
        pass

    @abstractmethod
    def validate_args(self, **kwargs) -> bool:
        pass

    def get_dependencies(self) -> List[str]:
        return []

    def get_required_env_variables(self) -> List[str]:
        return []

    def is_enabled(self) -> bool:
        return self.enabled

    @abstractmethod
    def get_installation_instructions(self) -> List[str]:
        pass

    @abstractmethod
    def get_initialization_instructions(self) -> List[str]:
        pass
```

### 3.2 Command Implementation

Here's an example of how a specific command (SrgnCommand) might be implemented:

```python
import subprocess
from typing import Dict, Any, List

class SrgnCommand(Command):
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.env_variables = ["RUST_LOG"]

    def execute(self, repo_path: str, issue: str, **kwargs) -> Dict[str, Any]:
        if not self.validate_args(issue=issue, **kwargs):
            raise ValueError("Invalid arguments")
        
        srgn_cmd = ["srgn"]
        if kwargs.get("glob"):
            srgn_cmd.extend(["--glob", kwargs["glob"]])
        if kwargs.get("verbose"):
            srgn_cmd.append("--verbose")
        srgn_cmd.extend([issue])
        
        try:
            result = subprocess.run(srgn_cmd, cwd=repo_path, capture_output=True, text=True, check=True)
            return {
                "status": "success",
                "message": "srgn command executed successfully",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"srgn command failed with exit code {e.returncode}",
                "stdout": e.stdout,
                "stderr": e.stderr
            }

    def get_context(self) -> str:
        return "Use this command to leverage the srgn code surgery tool for resolving issues and implementing code changes"

    def get_documentation(self) -> str:
        return """
        Executes the srgn code surgery tool to resolve issues and implement code changes.
        
        Arguments:
        - issue (str): The issue or code change request to be addressed by srgn
        
        Optional Arguments:
        - glob (str): Glob pattern for files to process
        - verbose (bool): Enable verbose output from srgn
        
        Returns:
        - Dictionary containing execution status, message, and command output
        
        Required Environment Variables:
        - RUST_LOG: Optional, controls the log level for srgn
        """

    def validate_args(self, **kwargs) -> bool:
        return "issue" in kwargs and isinstance(kwargs["issue"], str)

    def get_required_env_variables(self) -> List[str]:
        return self.env_variables

    def get_installation_instructions(self) -> List[str]:
        return [
            "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
            "source $HOME/.cargo/env",
            "cargo install srgn"
        ]

    def get_initialization_instructions(self) -> List[str]:
        return ["srgn --version"]
```

### 3.3 Command Registry

The `CommandRegistry` manages the collection of available commands:

```python
from typing import Dict, List, Type
from commands import Command

class CommandRegistry:
    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(self, name: str, command: Type[Command], enabled: bool = True):
        if not issubclass(command, Command):
            raise TypeError(f"{command.__name__} is not a subclass of Command")
        self._commands[name] = command(enabled=enabled)

    def get_command(self, name: str) -> Command:
        command = self._commands.get(name)
        if not command:
            raise ValueError(f"Command '{name}' not found in registry")
        return command

    def list_enabled_commands(self) -> List[str]:
        return [name for name, cmd in self._commands.items() if cmd.is_enabled()]

    def get_enabled_installation_instructions(self) -> Dict[str, List[str]]:
        return {name: cmd.get_installation_instructions() 
                for name, cmd in self._commands.items() 
                if cmd.is_enabled()}

    def get_enabled_initialization_instructions(self) -> Dict[str, List[str]]:
        return {name: cmd.get_initialization_instructions() 
                for name, cmd in self._commands.items() 
                if cmd.is_enabled()}

    # Additional methods for managing and querying commands...
```

### 3.4 Command Factory

The `CommandFactory` creates command instances based on configuration:

```python
import importlib
import yaml
from typing import Dict
from commands import Command

class CommandFactory:
    @staticmethod
    def create_command(name: str, config: Dict) -> Command:
        module_name = config.get('module', 'commands')
        class_name = config.get('class', f"{name.capitalize()}Command")
        enabled = config.get('enabled', True)
        
        try:
            module = importlib.import_module(module_name)
            command_class = getattr(module, class_name)
            return command_class(enabled=enabled)
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to create command '{name}': {str(e)}")

    @staticmethod
    def load_commands_from_config(config_path: str) -> Dict[str, Command]:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        commands = {}
        for cmd_name, cmd_config in config['commands'].items():
            commands[cmd_name] = CommandFactory.create_command(cmd_name, cmd_config)
        
        return commands
```

## 4. Configuration

Commands are configured using a YAML file:

```yaml
commands:
  srgn:
    enabled: true
    module: commands
    class: SrgnCommand
  other_command:
    enabled: false
    module: commands
    class: OtherCommand
```

## 5. Docker Integration

### 5.1 Dockerfile Generation

A Python script generates the Dockerfile based on enabled commands:

```python
from command_registry import CommandRegistry

def generate_dockerfile(registry: CommandRegistry) -> str:
    dockerfile = """
FROM python:3.9

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt
"""

    # Add installation instructions for enabled commands
    installation_instructions = registry.get_enabled_installation_instructions()
    for cmd_name, instructions in installation_instructions.items():
        dockerfile += f"\n# Install {cmd_name}\n"
        for instruction in instructions:
            dockerfile += f"RUN {instruction}\n"

    # Add initialization instructions for enabled commands
    init_instructions = registry.get_enabled_initialization_instructions()
    for cmd_name, instructions in init_instructions.items():
        dockerfile += f"\n# Initialize {cmd_name}\n"
        for instruction in instructions:
            dockerfile += f"RUN {instruction}\n"

    dockerfile += "\n# ... rest of your Dockerfile\n"

    return dockerfile

# Usage
registry = CommandRegistry()
# Load and register commands from config...
dockerfile_content = generate_dockerfile(registry)

with open('Dockerfile', 'w') as f:
    f.write(dockerfile_content)
```

### 5.2 Environment Variable Validation

A script to validate required environment variables for enabled commands:

```python
import os
from command_registry import CommandRegistry

def validate_env(registry: CommandRegistry):
    all_required_vars = set()
    for cmd_name in registry.list_enabled_commands():
        cmd = registry.get_command(cmd_name)
        all_required_vars.update(cmd.get_required_env_variables())
    
    missing_vars = [var for var in all_required_vars if var not in os.environ]
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Usage
registry = CommandRegistry()
# Load and register commands from config...
validate_env(registry)
```

## 6. Adding New Commands

To add a new command to the project:

1. Create a new class that inherits from the `Command` base class.
2. Implement all required methods, including `execute`, `get_context`, `get_documentation`, `validate_args`, `get_installation_instructions`, and `get_initialization_instructions`.
3. If the command requires any dependencies or environment variables, implement `get_dependencies` and `get_required_env_variables`.
4. Add the new command to the configuration file (`config.yaml`).
5. If necessary, update the `CommandFactory` to handle any special instantiation logic for the new command.

Example of adding a new command:

```python
class NewCommand(Command):
    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.env_variables = ["NEW_COMMAND_API_KEY"]

    def execute(self, repo_path: str, **kwargs) -> Dict[str, Any]:
        # Implementation of the command's logic
        pass

    def get_context(self) -> str:
        return "Use this command to perform a new operation"

    def get_documentation(self) -> str:
        return "Detailed documentation of the new command"

    def validate_args(self, **kwargs) -> bool:
        # Validate arguments specific to this command
        return True

    def get_required_env_variables(self) -> List[str]:
        return self.env_variables

    def get_installation_instructions(self) -> List[str]:
        return [
            "pip install new-command-dependency"
        ]

    def get_initialization_instructions(self) -> List[str]:
        return ["new-command --version"]
```

Then, add the new command to the configuration:

```yaml
commands:
  # ... existing commands ...
  new_command:
    enabled: true
    module: commands
    class: NewCommand
```

## 7. Best Practices

1. **Separation of Concerns**: Each command should have a single, well-defined responsibility.
2. **Error Handling**: Implement robust error handling within each command's `execute` method.
3. **Logging**: Add logging to each command for better traceability and debugging.
4. **Testing**: Write unit tests for each command, including tests for argument validation, execution, and environment setup.
5. **Documentation**: Maintain comprehensive documentation for each command, including usage examples and required environment variables.
6. **Versioning**: Consider implementing a versioning system for commands to manage changes over time.
7. **Performance**: For commands that may take a long time to execute, consider implementing them as asynchronous operations.
8. **Security**: Be cautious with environment variables containing sensitive information. Ensure they are properly secured in your deployment environment.
9. **Flexibility**: Design commands to be flexible in terms of their dependencies and installation methods.
10. **Conditional Dependencies**: Design your system to only install and initialize dependencies for enabled commands.
11. **Dynamic Configuration**: Use configuration files to control which commands are enabled, allowing for easy customization without code changes.
12. **Dockerfile Generation**: Generate Dockerfiles dynamically based on your configuration to ensure only necessary dependencies are included.

## 8. Conclusion

The Commands Library provides a flexible and extensible framework for managing and executing various operations within the project. By encapsulating command logic, dependencies, and execution requirements, it allows for easy addition of new functionalities and efficient management of the application's capabilities. The integration with Docker ensures that the deployment environment is optimized for the specific set of enabled commands, while the configuration-driven approach allows for easy customization and maintenance.

This design promotes modularity, reusability, and maintainability, making it easier to evolve the application's capabilities over time while keeping the core structure stable and efficient.