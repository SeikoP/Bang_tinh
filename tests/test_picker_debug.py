import flet as ft

def main(page: ft.Page):
    page.title = "Debug Picker"
    
    result_text = ft.Text("Ready")
    
    def on_result(e: ft.FilePickerResultEvent):
        print(f"Result: {e}")
        if e.files:
            result_text.value = f"Selected: {e.files[0].name}"
        else:
            result_text.value = "Cancelled"
        page.update()
    
    # Create FilePicker once at page level
    file_picker = ft.FilePicker()
    file_picker.on_result = on_result
    page.overlay.append(file_picker)
    
    def pick_click(e):
        try:
            print("Calling pick_files...")
            file_picker.pick_files(allowed_extensions=["html"])
            print("pick_files called")
        except Exception as ex:
            print(f"Error: {ex}")
            import traceback
            traceback.print_exc()
            result_text.value = f"Error: {ex}"
            page.update()
    
    page.add(
        ft.Button("Pick File", on_click=pick_click),
        result_text
    )

if __name__ == "__main__":
    ft.run(main)
