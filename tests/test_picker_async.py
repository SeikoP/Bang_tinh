import flet as ft

def main(page: ft.Page):
    page.title = "Async Picker Test"
    
    result_text = ft.Text("No file selected")
    
    def on_result(e: ft.FilePickerResultEvent):
        print(f"on_result called: {e}")
        if e.files:
            result_text.value = f"Selected: {e.files[0].name}"
        else:
            result_text.value = "No file selected"
        page.update()
    
    # Create FilePicker and set on_result after
    file_picker = ft.FilePicker()
    file_picker.on_result = on_result
    page.overlay.append(file_picker)
    
    def pick_click(e):
        print("Pick button clicked")
        file_picker.pick_files(allowed_extensions=["html"])
    
    page.add(
        ft.Button("Pick File", on_click=pick_click),
        result_text
    )

if __name__ == "__main__":
    ft.run(main)
