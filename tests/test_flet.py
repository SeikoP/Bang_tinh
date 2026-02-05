import flet as ft

def main(page: ft.Page):
    try:
        page.add(ft.TextButton("Test"))
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ft.run(target=main)
