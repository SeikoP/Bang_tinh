"""Test các cách khác nhau để dùng FilePicker"""
import flet as ft

def test_method_1(page: ft.Page):
    """Method 1: FilePicker trong overlay (cách cũ)"""
    page.title = "Method 1: Overlay"
    
    picker = ft.FilePicker()
    page.overlay.append(picker)
    
    page.add(
        ft.ElevatedButton("Pick File", on_click=lambda _: picker.pick_files())
    )

def test_method_2(page: ft.Page):
    """Method 2: FilePicker visible trong page"""
    page.title = "Method 2: Visible in page"
    
    def on_result(e: ft.FilePickerResultEvent):
        if e.files:
            result_text.value = f"Selected: {e.files[0].name}"
            page.update()
    
    result_text = ft.Text("No file selected")
    picker = ft.FilePicker(on_result=on_result)
    
    page.add(
        ft.Column([
            picker,  # Add picker as normal control
            ft.ElevatedButton("Pick File", on_click=lambda _: picker.pick_files()),
            result_text,
        ])
    )

def test_method_3(page: ft.Page):
    """Method 3: Không dùng FilePicker, dùng TextField với hint"""
    page.title = "Method 3: Manual input"
    
    file_path = ft.TextField(
        label="File path",
        hint_text="Paste file path here or drag & drop",
        width=400,
    )
    
    page.add(
        ft.Column([
            ft.Text("Enter file path manually:"),
            file_path,
            ft.ElevatedButton("Process", on_click=lambda _: print(file_path.value)),
        ])
    )

# Test method 2 (most likely to work)
if __name__ == "__main__":
    ft.app(target=test_method_2)
