import traceback
import sys
import flet as ft
import os

# Disable Flet's custom logging/terminal handling if possible
os.environ["FLET_LOG_LEVEL"] = "CRITICAL"

def main_wrapper():
    try:
        from main import main
        # We want to catch the error DURING main initialization
        # main(page) is called by ft.run
        ft.run(target=main)
    except Exception:
        with open("error_log.txt", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()

if __name__ == "__main__":
    main_wrapper()
