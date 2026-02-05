import flet as ft

def main(page: ft.Page):
    page.title = "FilePicker Test"
    
    result_text = ft.Text("No file selected")
    
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            result_text.value = f"Selected: {e.files[0].name}"
        else:
            result_text.value = "No file selected"
        page.update()
    
    # Create FilePicker without on_result
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    
    # Try to set on_result after creation
    if hasattr(file_picker, 'on_result'):
        file_picker.on_result = on_file_result
    
    page.add(
        ft.ElevatedButton(
            "Pick File",
            on_click=lambda _: file_picker.pick_files()
        ),
        result_text
    )

if __name__ == "__main__":
    ft.run(main)
