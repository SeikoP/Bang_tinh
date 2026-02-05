import sys
import traceback

try:
    print("Starting import...", flush=True)
    import flet as ft
    print("Flet imported successfully", flush=True)
    
    from database.connection import init_db
    print("Database imported", flush=True)
    init_db()
    print("Database initialized", flush=True)
    
    from ui.views.calculation_view import CalculationView
    print("CalculationView imported", flush=True)
    
    def test_main(page: ft.Page):
        print("In test_main", flush=True)
        page.title = "Test"
        try:
            view = CalculationView(page, is_dark=False)
            print("CalculationView created successfully", flush=True)
            page.add(ft.Text("Success!"))
        except Exception as e:
            print(f"Error creating view: {e}", flush=True)
            traceback.print_exc()
            page.add(ft.Text(f"Error: {e}"))
    
    print("Starting Flet app...", flush=True)
    ft.run(test_main)
    
except Exception as e:
    print(f"Error: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)
