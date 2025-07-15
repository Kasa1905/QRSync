#!/usr/bin/env python3
"""
QR Code Attendance System - Package Creator
===========================================
Creates deployment packages for the QR Code Attendance System.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import json
from datetime import datetime

def create_portable_package():
    """Create a portable package with minimal files"""
    print("📦 Creating portable package...")
    
    # Files needed for portable version
    portable_files = [
        'app.py',
        'new-creds.json.template',
        'requirements.txt',
        'setup.py',
        'README.md',
        'SETUP_INSTRUCTIONS.md'
    ]
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, 'qrsync_portable')
        os.makedirs(package_dir)
        
        # Copy files
        for file in portable_files:
            if os.path.exists(file):
                shutil.copy2(file, package_dir)
                print(f"✅ Added {file}")
            else:
                print(f"⚠️  Warning: {file} not found")
        
        # Create installation instructions
        install_instructions = """# QR Code Attendance System - Portable Version

## Quick Installation

1. Install Python 3.8+ if not already installed
2. Run the setup script:
   ```
   python setup.py
   ```
3. Configure your credentials:
   ```
   cp new-creds.json.template new-creds.json
   # Edit new-creds.json with your Google Sheets credentials
   ```
4. Run the application:
   ```
   python app.py
   ```

## Files Included
- app.py - Main application
- setup.py - Installation script
- requirements.txt - Python dependencies
- new-creds.json.template - Credentials template
- README.md - Full documentation
- SETUP_INSTRUCTIONS.md - Detailed setup guide

For full documentation, see README.md
"""
        
        with open(os.path.join(package_dir, 'INSTALL.md'), 'w') as f:
            f.write(install_instructions)
        
        # Create zip file
        zip_filename = 'qrsync_portable.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Portable package created: {zip_filename}")
        return zip_filename

def create_full_package():
    """Create a full package with all project files"""
    print("📦 Creating full package...")
    
    # Files to include in full package
    full_files = [
        'app.py',
        'setup.py',
        'requirements.txt',
        'new-creds.json.template',
        'README.md',
        'PROJECT_README.md',
        'SETUP_INSTRUCTIONS.md',
        'DEPLOYMENT_GUIDE.md',
        'verify_security.py',
        'LICENSE',
        '.gitignore'
    ]
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, 'qrsync_full')
        os.makedirs(package_dir)
        
        # Copy files
        for file in full_files:
            if os.path.exists(file):
                shutil.copy2(file, package_dir)
                print(f"✅ Added {file}")
            else:
                print(f"⚠️  Warning: {file} not found")
        
        # Create package info
        package_info = {
            "name": "QR Code Attendance System",
            "version": "1.0.0",
            "description": "Cross-platform QR code attendance tracking system",
            "author": "TED Event Team",
            "created": datetime.now().isoformat(),
            "platform": "cross-platform",
            "python_version": "3.8+",
            "files": full_files
        }
        
        with open(os.path.join(package_dir, 'package_info.json'), 'w') as f:
            json.dump(package_info, f, indent=2)
        
        # Create zip file
        zip_filename = 'qrsync_full.zip'
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✅ Full package created: {zip_filename}")
        return zip_filename

def create_executable():
    """Create a standalone executable using PyInstaller"""
    print("🔧 Creating standalone executable...")
    
    try:
        import PyInstaller.__main__
        
        # PyInstaller arguments
        args = [
            '--onefile',
            '--windowed',
            '--name=QRSync',
            '--add-data=new-creds.json.template:.',
            '--hidden-import=cv2',
            '--hidden-import=gspread',
            '--hidden-import=oauth2client',
            '--hidden-import=pandas',
            '--hidden-import=numpy',
            '--hidden-import=PIL',
            'app.py'
        ]
        
        PyInstaller.__main__.run(args)
        print("✅ Executable created in dist/ folder")
        
    except ImportError:
        print("⚠️  PyInstaller not installed. Install with: pip install pyinstaller")
        return False
    
    return True

def verify_packages():
    """Verify created packages"""
    print("🔍 Verifying packages...")
    
    packages = ['qrsync_portable.zip', 'qrsync_full.zip']
    
    for package in packages:
        if os.path.exists(package):
            size = os.path.getsize(package)
            print(f"✅ {package} - {size:,} bytes")
            
            # List contents
            with zipfile.ZipFile(package, 'r') as zipf:
                files = zipf.namelist()
                print(f"   Contains {len(files)} files:")
                for file in sorted(files)[:10]:  # Show first 10 files
                    print(f"   - {file}")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more files")
        else:
            print(f"❌ {package} not found")

def main():
    """Main function"""
    print("🚀 QR Code Attendance System - Package Creator")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'portable':
            create_portable_package()
        elif command == 'full':
            create_full_package()
        elif command == 'executable':
            create_executable()
        elif command == 'all':
            create_portable_package()
            create_full_package()
            create_executable()
            verify_packages()
        else:
            print("❌ Unknown command. Use: portable, full, executable, or all")
            sys.exit(1)
    else:
        # Interactive mode
        print("Select package type:")
        print("1. Portable package (minimal files)")
        print("2. Full package (all files)")
        print("3. Standalone executable")
        print("4. All packages")
        print("5. Verify existing packages")
        
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            create_portable_package()
        elif choice == '2':
            create_full_package()
        elif choice == '3':
            create_executable()
        elif choice == '4':
            create_portable_package()
            create_full_package()
            create_executable()
        elif choice == '5':
            verify_packages()
        else:
            print("❌ Invalid choice")
            sys.exit(1)
    
    print("\n✅ Package creation completed!")

if __name__ == '__main__':
    main()
