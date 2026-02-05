import flet as ft

def main(page: ft.Page):
    fp = ft.FilePicker()
    # This SHOULD cause "Unknown control: FilePicker"
    page.add(ft.Column([fp]))

if __name__ == "__main__":
    ft.run(main)
