"""Math utility functions for demo."""

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

def multiply(a: float, b: float) -> float:
    return a * b

def divide(a: float, b: float) -> float:
    # PLANTED BUG: returns multiplication instead of division
    return a * b

def clamp(val: float, low: float, high: float) -> float:
    if val < low:
        return low
    if val > high:
        return high
    return val
