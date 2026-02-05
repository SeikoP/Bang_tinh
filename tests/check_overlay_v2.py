import flet as ft

def main(page: ft.Page):
    print(f"OVERLAY_TYPE: {type(page.overlay)}", flush=True)
    if hasattr(page.overlay, "controls"):
        print("OVERLAY_HAS_CONTROLS", flush=True)
    else:
        print("OVERLAY_NO_CONTROLS", flush=True)
    page.window.destroy()

if __name__ == "__main__":
    ft.run(main)
