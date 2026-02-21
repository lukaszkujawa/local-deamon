"""Mathematical operation tools"""
from localdeamon.tool_registry import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


@tool
def factorial(n: int) -> int:
    """Calculate factorial of a number"""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
