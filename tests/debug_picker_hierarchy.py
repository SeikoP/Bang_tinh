import flet as ft
import os
import sys

# Thêm đường dẫn dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main as original_main

def main_debug(page: ft.Page):
    try:
        # Chạy main
        original_main(page)
        
        # Hàm duyệt tất cả các control tìm FilePicker
        misplaced = []
        
        def find_misplaced(controls, path="page"):
            for i, c in enumerate(controls):
                c_type = type(c).__name__
                if "FilePicker" in c_type:
                    # FilePicker chỉ được phép ở trong overlay
                    if "overlay" not in path:
                        misplaced.append(f"{path}.controls[{i}] ({c_type})")
                
                # Duyệt con
                if hasattr(c, "controls") and c.controls:
                    find_misplaced(c.controls, f"{path}.{c_type}[{i}]")
                if hasattr(c, "content") and c.content:
                    find_misplaced([c.content], f"{path}.{c_type}[{i}].content")
                if hasattr(c, "tabs") and c.tabs:
                    # Trường hợp ft.Tabs
                    for j, tab in enumerate(c.tabs):
                        if hasattr(tab, "content") and tab.content:
                            find_misplaced([tab.content], f"{path}.Tabs[{i}].tabs[{j}].content")

        print("\n--- DEBUG: STARTING SCAN ---")
        find_misplaced(page.controls, "page")
        find_misplaced(page.overlay, "page.overlay")
        
        if misplaced:
            print("\n!!! MISPLACED FILEPICKER FOUND !!!")
            for m in misplaced:
                print(f"ERROR: FilePicker at {m}")
        else:
            print("\nSUCCESS: No misplaced FilePicker found in page.controls.")
            
        print(f"\nTotal items in overlay: {len(page.overlay)}")
        for i, c in enumerate(page.overlay):
            print(f"Overlay[{i}]: {type(c).__name__}")
        
    except Exception as e:
        print(f"Debug Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Chạy ở mode web hoặc desktop tùy ý, ở đây dùng desktop để dễ nhìn output
    ft.run(main_debug)
