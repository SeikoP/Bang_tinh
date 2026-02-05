import flet as ft

def main(page: ft.Page):
    page.title = "Test"
    
    # Try using TabBar instead of Tabs
    tab1_content = ft.Container(content=ft.Text("Tab 1 Content"), expand=True)
    tab2_content = ft.Container(content=ft.Text("Tab 2 Content"), expand=True)
    
    current_tab = ft.Ref[ft.Container]()
    
    def on_tab_change(e):
        idx = e.control.selected_index
        if idx == 0:
            current_tab.current.content = tab1_content
        else:
            current_tab.current.content = tab2_content
        page.update()
    
    page.add(
        ft.Column([
            ft.Row([
                ft.TextButton("Tab 1", on_click=lambda e: None),
                ft.TextButton("Tab 2", on_click=lambda e: None),
            ]),
            ft.Container(ref=current_tab, content=tab1_content, expand=True),
        ], expand=True)
    )
    print("Success!")

if __name__ == "__main__":
    ft.run(main)
