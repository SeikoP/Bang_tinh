import flet as ft
import os
import sys

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main as original_main

def main_debug(page: ft.Page):
    try:
        original_main(page)
        
        def check_controls(controls, path="page"):
            for i, c in enumerate(controls):
                c_type = type(c).__name__
                if "FilePicker" in c_type:
                    print(f"!!! FOUND FilePicker in {path}.controls[{i}] !!!")
                
                if hasattr(c, "controls") and c.controls:
                    check_controls(c.controls, f"{path}.{c_type}[{i}]")
                if hasattr(c, "content") and c.content:
                    check_controls([c.content], f"{path}.{c_type}[{i}].content")
        
        print("Checking page.controls...")
        check_controls(page.controls, "page")
        print("Checking page.overlay...")
        check_controls(page.overlay, "page.overlay")
        
        # Check if overlay controls are correctly added
        for i, c in enumerate(page.overlay):
            print(f"Overlay item {i}: {type(c).__name__}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ft.run(main_debug)
