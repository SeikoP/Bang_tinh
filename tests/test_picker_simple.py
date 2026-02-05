import flet as ft

def main(page: ft.Page):
    page.title = "Simple Picker Test"
    
    # Test 1: Create and add to overlay
    picker = ft.FilePicker()
    page.overlay.append(picker)
    page.update()
    
    print(f"Picker type: {type(picker)}")
    print(f"Picker in overlay: {picker in page.overlay}")
    
    def pick_file(e):
        print("Pick button clicked")
        try:
            result = picker.pick_files(allowed_extensions=["html"])
            print(f"Result: {result}")
            if result:
                page.add(ft.Text(f"Selected: {result[0].name}"))
            else:
                page.add(ft.Text("No file selected"))
        except Exception as ex:
            print(f"Error: {ex}")
            import traceback
            traceback.print_exc()
            page.add(ft.Text(f"Error: {ex}"))
        page.update()
    
    page.add(
        ft.Button("Pick File", on_click=pick_file),
        ft.Text("Click button to test")
    )

if __name__ == "__main__":
    ft.run(main)
