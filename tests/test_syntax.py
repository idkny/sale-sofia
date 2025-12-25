#!/usr/bin/env python3
"""Quick syntax check for tasks.py"""
import sys
import py_compile

try:
    py_compile.compile('/home/wow/Projects/sale-sofia/proxies/tasks.py', doraise=True)
    print("SUCCESS: tasks.py syntax is valid")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
