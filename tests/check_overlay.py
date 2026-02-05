import flet as ft

def main(page: ft.Page):
    print(f"page.overlay type: {type(page.overlay)}")
    print(f"page.overlay dir: {dir(page.overlay)}")
    page.window.close()

if __name__ == "__main__":
    ft.run(main)
