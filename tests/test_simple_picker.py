import flet as ft

def main(page: ft.Page):
    page.title = "Simple FilePicker Test"
    
    # Create FilePicker
    picker = ft.FilePicker()
    page.overlay.append(picker)
    
    # Add a button
    page.add(
        ft.ElevatedButton(
            "Pick File",
            on_click=lambda _: picker.pick_files()
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
