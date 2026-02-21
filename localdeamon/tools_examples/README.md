# Tool System Usage

## Quick Start

Define a tool with the `@tool` decorator - it automatically registers:

```python
from localdeamon.tools import tool

@tool
def my_function(param: str) -> str:
    """Description of what this tool does"""
    return f"Result: {param}"
```

## Retrieving Tools

```python
from localdeamon.tools import Tool

# Get all registered tools
all_tools = Tool.all()

# Get specific tool by name
my_tool = Tool.get("my_function")

# Get list of tool names
names = Tool.names()
```

## Organizing Tools

Create separate modules for different tool categories:

**file_tools.py:**
```python
from localdeamon.tools import tool

@tool
def read_file(path: str) -> str:
    """Read contents of a file"""
    return open(path).read()
```

**math_tools.py:**
```python
from localdeamon.tools import tool

@tool
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b
```

**Import them:**
```python
from localdeamon.tools import Tool
from localdeamon.tools_examples import file_tools, math_tools

# All tools now registered!
print(Tool.names())  # ['read_file', 'add', ...]
```

## Using with LangChain Agents

```python
from localdeamon.tools import Tool
from localdeamon.llm import get_llm
from langchain.agents import create_react_agent

# Import your tool modules
from localdeamon.tools_examples import file_tools, math_tools

# Get LLM
llm = get_llm()

# Create agent with all registered tools
agent = create_react_agent(
    llm=llm,
    tools=Tool.all(),  # Auto-discovered!
    prompt=agent_prompt
)
```

## Benefits

- ✅ **No manual tool lists** - Auto-registration on decorator
- ✅ **Centralized registry** - Access tools from anywhere
- ✅ **Module organization** - Split tools into logical files
- ✅ **LangChain compatible** - Direct integration
- ✅ **Type-safe** - Full type hints
- ✅ **Zero boilerplate** - Just decorate and go
