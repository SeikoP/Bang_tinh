import flet as ft

def main(page: ft.Page):
    page.title = "Test NavigationBar"
    
    # Contents for each tab
    contents = {
        0: ft.Container(ft.Text("Bảng tính content", size=20), expand=True, padding=20),
        1: ft.Container(ft.Text("Kho hàng content", size=20), expand=True, padding=20),
        2: ft.Container(ft.Text("Sản phẩm content", size=20), expand=True, padding=20),
    }
    
    content_area = ft.Container(content=contents[0], expand=True)
    
    def on_nav_change(e):
        content_area.content = contents[e.control.selected_index]
        page.update()
    
    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.CALCULATE, label="Bảng tính"),
            ft.NavigationBarDestination(icon=ft.Icons.INVENTORY, label="Kho hàng"),
            ft.NavigationBarDestination(icon=ft.Icons.CATEGORY, label="Sản phẩm"),
        ],
    )
    
    page.add(
        ft.Column([
            content_area,
            nav_bar,
        ], expand=True)
    )
    print("Success!")

if __name__ == "__main__":
    ft.run(main)
