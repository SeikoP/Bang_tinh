#!/usr/bin/env python
"""
Build automation script for Warehouse Management Application

This script automates the build process:
1. Clean previous build artifacts
2. Build executable using PyInstaller
3. Create installer package (optional)

Usage:
    python scripts/build.py [--clean-only] [--no-installer]
"""

import subprocess
import shutil
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'build_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class BuildError(Exception):
    """Custom exception for build errors"""
    pass


class Builder:
    """Handles the build process for the application"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / 'build'
        self.dist_dir = project_root / 'dist'
        self.spec_file = project_root / 'warehouse_app.spec'
    
    def clean(self):
        """Remove previous build artifacts"""
        logger.info("Cleaning build directories...")
        
        dirs_to_clean = [
            self.build_dir,
            self.dist_dir,
            self.project_root / '__pycache__',
        ]
        
        # Also clean __pycache__ in subdirectories
        for pycache in self.project_root.rglob('__pycache__'):
            dirs_to_clean.append(pycache)
        
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"  Removed: {dir_path.relative_to(self.project_root)}")
                except Exception as e:
                    logger.warning(f"  Failed to remove {dir_path}: {e}")
        
        # Clean .pyc files
        for pyc_file in self.project_root.rglob('*.pyc'):
            try:
                pyc_file.unlink()
            except Exception as e:
                logger.warning(f"  Failed to remove {pyc_file}: {e}")
        
        logger.info("Clean completed successfully")
    
    def validate_prerequisites(self):
        """Validate that all prerequisites are met"""
        logger.info("Validating prerequisites...")
        
        # Check if spec file exists
        if not self.spec_file.exists():
            raise BuildError(f"Spec file not found: {self.spec_file}")
        
        # Check if main.py exists
        main_file = self.project_root / 'main.py'
        if not main_file.exists():
            raise BuildError(f"Main file not found: {main_file}")
        
        # Check if PyInstaller is installed
        try:
            result = subprocess.run(
                ['pyinstaller', '--version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"  PyInstaller version: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise BuildError("PyInstaller is not installed. Install it with: pip install pyinstaller")
        
        # Check if assets directory exists
        assets_dir = self.project_root / 'assets'
        if not assets_dir.exists():
            logger.warning(f"  Assets directory not found: {assets_dir}")
        
        logger.info("Prerequisites validated successfully")
    
    def build_executable(self):
        """Build executable using PyInstaller"""
        logger.info("Building executable with PyInstaller...")
        
        try:
            # Run PyInstaller with the spec file
            result = subprocess.run(
                ['pyinstaller', str(self.spec_file), '--clean', '--noconfirm'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("PyInstaller output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
            
            # Verify executable was created
            exe_path = self.dist_dir / 'WarehouseManagement.exe'
            if not exe_path.exists():
                raise BuildError(f"Executable not found at: {exe_path}")
            
            # Get file size
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            logger.info(f"Build completed successfully!")
            logger.info(f"  Executable: {exe_path}")
            logger.info(f"  Size: {size_mb:.2f} MB")
            
            return exe_path
            
        except subprocess.CalledProcessError as e:
            logger.error("PyInstaller failed:")
            logger.error(e.stderr)
            raise BuildError(f"PyInstaller build failed with exit code {e.returncode}")
    
    def create_installer(self):
        """Create installer using Inno Setup"""
        logger.info("Creating installer with Inno Setup...")
        
        # Check if Inno Setup is installed
        inno_setup_paths = [
            Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
            Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        ]
        
        iscc_exe = None
        for path in inno_setup_paths:
            if path.exists():
                iscc_exe = path
                break
        
        if not iscc_exe:
            logger.warning("Inno Setup not found. Skipping installer creation.")
            logger.warning("Install Inno Setup from: https://jrsoftware.org/isdl.php")
            return None
        
        # Check if setup script exists
        setup_script = self.project_root / 'installer' / 'setup.iss'
        if not setup_script.exists():
            logger.warning(f"Installer script not found: {setup_script}")
            logger.warning("Skipping installer creation.")
            return None
        
        try:
            result = subprocess.run(
                [str(iscc_exe), str(setup_script)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("Inno Setup output:")
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
            
            # Find the created installer
            installer_pattern = 'WarehouseManagement-Setup-*.exe'
            installers = list(self.dist_dir.glob(installer_pattern))
            
            if installers:
                installer_path = installers[0]
                size_mb = installer_path.stat().st_size / (1024 * 1024)
                logger.info(f"Installer created successfully!")
                logger.info(f"  Installer: {installer_path}")
                logger.info(f"  Size: {size_mb:.2f} MB")
                return installer_path
            else:
                logger.warning("Installer file not found after build")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error("Inno Setup failed:")
            logger.error(e.stderr)
            logger.warning("Installer creation failed, but executable is still available")
            return None


def main():
    """Main entry point for the build script"""
    parser = argparse.ArgumentParser(
        description='Build automation script for Warehouse Management Application'
    )
    parser.add_argument(
        '--clean-only',
        action='store_true',
        help='Only clean build artifacts without building'
    )
    parser.add_argument(
        '--no-installer',
        action='store_true',
        help='Skip installer creation'
    )
    
    args = parser.parse_args()
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    logger.info("=" * 70)
    logger.info("Warehouse Management Application - Build Script")
    logger.info("=" * 70)
    logger.info(f"Project root: {project_root}")
    logger.info("")
    
    builder = Builder(project_root)
    
    try:
        # Always clean first
        builder.clean()
        
        if args.clean_only:
            logger.info("Clean-only mode: Exiting without building")
            return 0
        
        # Validate prerequisites
        builder.validate_prerequisites()
        
        # Build executable
        exe_path = builder.build_executable()
        
        # Create installer (unless skipped)
        if not args.no_installer:
            installer_path = builder.create_installer()
        else:
            logger.info("Skipping installer creation (--no-installer flag)")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("BUILD SUCCESSFUL")
        logger.info("=" * 70)
        logger.info(f"Executable: {exe_path}")
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Test the executable on a clean Windows machine")
        logger.info("  2. Verify all dependencies are bundled correctly")
        logger.info("  3. Test the installer (if created)")
        logger.info("")
        
        return 0
        
    except BuildError as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("BUILD FAILED")
        logger.error("=" * 70)
        logger.error(str(e))
        logger.error("")
        return 1
    
    except Exception as e:
        logger.exception("Unexpected error during build:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
