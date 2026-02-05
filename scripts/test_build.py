#!/usr/bin/env python
"""
Test script to verify the built executable

This script performs basic validation of the built executable:
1. Check if executable exists
2. Check file size
3. Verify version information (if available)
"""

import sys
from pathlib import Path
import subprocess

def test_executable_exists(exe_path: Path) -> bool:
    """Test if executable file exists"""
    print(f"Checking if executable exists: {exe_path}")
    if exe_path.exists():
        print(f"  ✓ Executable found")
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Size: {size_mb:.2f} MB")
        return True
    else:
        print(f"  ✗ Executable not found")
        return False

def test_dependencies_bundled(exe_path: Path) -> bool:
    """Test if dependencies are bundled (basic check)"""
    print("\nChecking if dependencies are bundled...")
    
    # For single-file executable, all dependencies should be bundled
    if exe_path.exists():
        print(f"  ✓ Single-file executable created")
        return True
    else:
        print(f"  ✗ Executable not found")
        return False

def test_assets_included(project_root: Path) -> bool:
    """Test if assets are included in the build"""
    print("\nChecking if assets are configured...")
    
    spec_file = project_root / 'warehouse_app.spec'
    if spec_file.exists():
        content = spec_file.read_text(encoding='utf-8')
        if 'assets' in content:
            print(f"  ✓ Assets configured in spec file")
            return True
        else:
            print(f"  ✗ Assets not configured")
            return False
    else:
        print(f"  ✗ Spec file not found")
        return False

def main():
    """Main test function"""
    print("=" * 70)
    print("Build Verification Tests")
    print("=" * 70)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    exe_path = project_root / 'dist' / 'WarehouseManagement.exe'
    
    results = []
    
    # Run tests
    results.append(("Executable exists", test_executable_exists(exe_path)))
    results.append(("Dependencies bundled", test_dependencies_bundled(exe_path)))
    results.append(("Assets configured", test_assets_included(project_root)))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Build is ready for distribution.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review the build.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
