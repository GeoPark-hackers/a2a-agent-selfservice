"""Calculator tools for mathematical operations."""

import math
import operator
from typing import Any

from .registry import register_tool


# Safe operators for expression evaluation
SAFE_OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "//": operator.floordiv,
    "%": operator.mod,
    "**": operator.pow,
}

SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
}


@register_tool()
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.
    
    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)")
    
    Returns:
        The result of the calculation as a string.
    """
    try:
        # Use a restricted eval with only safe functions
        result = eval(expression, {"__builtins__": {}}, SAFE_FUNCTIONS)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


@register_tool()
def add(a: float, b: float) -> str:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The sum as a string.
    """
    result = a + b
    return f"{a} + {b} = {result}"


@register_tool()
def subtract(a: float, b: float) -> str:
    """Subtract two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The difference as a string.
    """
    result = a - b
    return f"{a} - {b} = {result}"


@register_tool()
def multiply(a: float, b: float) -> str:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        The product as a string.
    """
    result = a * b
    return f"{a} × {b} = {result}"


@register_tool()
def divide(a: float, b: float) -> str:
    """Divide two numbers.
    
    Args:
        a: Dividend (number to be divided)
        b: Divisor (number to divide by)
    
    Returns:
        The quotient as a string.
    """
    if b == 0:
        return "Error: Cannot divide by zero"
    result = a / b
    return f"{a} ÷ {b} = {result}"


@register_tool()
def convert_units(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between common units.
    
    Args:
        value: The value to convert
        from_unit: Source unit (km, miles, celsius, fahrenheit, kg, lbs)
        to_unit: Target unit
    
    Returns:
        The converted value as a string.
    """
    conversions: dict[tuple[str, str], Any] = {
        ("km", "miles"): lambda x: x * 0.621371,
        ("miles", "km"): lambda x: x * 1.60934,
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("kg", "lbs"): lambda x: x * 2.20462,
        ("lbs", "kg"): lambda x: x / 2.20462,
        ("meters", "feet"): lambda x: x * 3.28084,
        ("feet", "meters"): lambda x: x / 3.28084,
    }
    
    key = (from_unit.lower(), to_unit.lower())
    if key in conversions:
        result = conversions[key](value)
        return f"{value} {from_unit} = {result:.4f} {to_unit}"
    
    return f"Conversion from {from_unit} to {to_unit} is not supported"
