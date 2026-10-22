"""Tests for mathutils."""
import pytest
from mathutils import add, subtract, multiply, divide, clamp

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 4) == -4

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6

def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-5, 0, 10) == 0
    assert clamp(15, 0, 10) == 10

def test_divide():
    assert divide(6, 2) == 3
    assert divide(10, 5) == 2
