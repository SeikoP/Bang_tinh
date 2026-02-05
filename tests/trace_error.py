"""Trace lỗi FilePicker"""
import flet as ft
import sys
import traceback

# Monkey patch để bắt mọi lần append vào overlay
original_append = list.append

def traced_append(self, item):
    if hasattr(item, '__class__') and 'FilePicker' in item.__class__.__name__:
        print(f"\n=== FilePicker APPEND DETECTED ===")
        print(f"Item: {item}")
        print(f"List: {id(self)}")
        traceback.print_stack()
        print("=" * 50)
    return original_append(self, item)

list.append = traced_append

# Import main sau khi patch
from main import main

if __name__ == "__main__":
    ft.run(main)
