""" 
Example module used in unit tests

Notes
-----
This module includes tags to identify source code
         
"""
from __future__ import annotations

# --- Variations of import statements
import sys
import os as operating_system
from math import sqrt
from collections import (
    defaultdict,
    namedtuple as nt,
)
from functools import wraps


# --- Module level constants
PI = 3.14159


# --- Simple function ---
# <func_square>
def square(x):
    """Return the square of x."""
    return x * x
# </func_square>


# --- Decorator ---
def trace(func):
    """A simple decorator that prints before and after the call."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Done with {func.__name__}")
        return result
    return wrapper

# --- Decorated function ---
# <func_say_hello>
@trace
def say_hello(name="World"):
    """Print a greeting."""
    print(f"Hello, {name}!")
# </func_say_hello>


# --- Simple class with method ---
class Greeter:
    """A simple greeter class."""

    def __init__(self, name):
        self.name = name

    def greet(self):
        """Return a greeting message."""
        return f"Hello, {self.name}!"

# --- function with import statements ---
def func_with_import(text="some_text"):
    import pprint as pp
    return pp.pformat(text)

def func_with_vardef(x):
    y = x
    return y

if __name__ == "__main__":
    square(x=1)


