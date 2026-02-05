import flet as ft

def main(page: ft.Page):
    page.title = "Minimal FilePicker Test"
    fp = ft.FilePicker()
    page.overlay.append(fp)
    page.update()
    
    page.add(
        ft.ElevatedButton("Pick", on_click=lambda _: fp.pick_files())
    )

if __name__ == "__main__":
    ft.run(main)
