import flet as ft

# Print Tabs signature
import inspect
print("Tabs signature:")
sig = inspect.signature(ft.Tabs.__init__)
for name, param in sig.parameters.items():
    print(f"  {name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'} = {param.default if param.default != inspect.Parameter.empty else 'required'}")

print("\nTab signature:")
sig2 = inspect.signature(ft.Tab.__init__)
for name, param in sig2.parameters.items():
    print(f"  {name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'} = {param.default if param.default != inspect.Parameter.empty else 'required'}")
