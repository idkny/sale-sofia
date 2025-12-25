#!/usr/bin/env python3
"""Simple syntax checker for main.py"""

import py_compile
import sys

try:
    py_compile.compile('main.py', doraise=True)
    print("✓ main.py syntax is valid")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error in main.py:")
    print(e)
    sys.exit(1)
