import flet as ft
import os
import sys

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main as original_main

def main_debug(page: ft.Page):
    # Chạy original main
    try:
        original_main(page)
        
        # Sau khi main chạy, kiểm tra xem có FilePicker nào trong controls không
        def check_controls(controls, path="page"):
            for i, c in enumerate(controls):
                c_type = type(c).__name__
                if "FilePicker" in c_type:
                    print(f"!!! FOUND FilePicker in {path}.controls[{i}] !!!")
                
                # Đệ quy kiểm tra các control con
                if hasattr(c, "controls") and c.controls:
                    check_controls(c.controls, f"{path}.{c_type}[{i}]")
                if hasattr(c, "content") and c.content:
                    check_controls([c.content], f"{path}.{c_type}[{i}].content")
        
        print("Checking for misplaced FilePicker controls...")
        check_controls(page.controls)
        print("Check completed.")
        
    except Exception as e:
        print(f"Error during main: {e}")

if __name__ == "__main__":
    ft.run(main_debug)
