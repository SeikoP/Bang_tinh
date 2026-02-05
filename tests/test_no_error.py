"""Test xem lỗi có còn không"""
import flet as ft

def main(page: ft.Page):
    page.title = "Test No Error"
    
    # Tắt error banner
    page.on_error = lambda e: print(f"Suppressed error: {e.data}")
    
    # Tạo FilePicker
    picker = ft.FilePicker()
    page.overlay.append(picker)
    
    # Add button
    page.add(
        ft.Button(
            "Pick File",
            on_click=lambda _: picker.pick_files()
        )
    )
    
    page.update()

if __name__ == "__main__":
    ft.run(main)
