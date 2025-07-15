#!/usr/bin/env python3
"""
QR Code Attendance System - Portable Installation Script
========================================================
This script sets up the QR Code Attendance System on any platform.
"""

import sys
import os
import platform
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Upgrade pip first
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Install from requirements.txt if it exists
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Install core dependencies manually
            deps = [
                "opencv-python>=4.8.0",
                "gspread>=5.12.0", 
                "oauth2client>=4.1.3",
                "pandas>=1.5.0",
                "numpy>=1.24.0",
                "Pillow>=10.0.0"
            ]
            
            for dep in deps:
                print(f"Installing {dep}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_camera():
    """Check if camera is available"""
    print("📷 Checking camera availability...")
    
    try:
        import cv2
        
        # Try to open camera
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                print("✅ Camera is working")
                return True
            else:
                print("⚠️ Camera opened but cannot read frames")
                return False
        else:
            print("⚠️ Cannot open camera")
            return False
            
    except Exception as e:
        print(f"❌ Camera check failed: {e}")
        return False

def check_credentials():
    """Check if credentials file exists"""
    print("🔐 Checking credentials file...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cred_files = [
        'new-creds.json',
        'creds.json',
        'credentials.json',
        'service-account.json'
    ]
    
    for cred_file in cred_files:
        cred_path = os.path.join(script_dir, cred_file)
        if os.path.exists(cred_path):
            print(f"✅ Found credentials file: {cred_file}")
            return True
    
    print("⚠️ No credentials file found")
    print("Please follow these steps:")
    print("1. Create Google Cloud Platform project")
    print("2. Enable Google Sheets API")
    print("3. Create service account credentials")
    print("4. Download JSON credentials file")
    print("5. Rename to 'new-creds.json' and place in this directory")
    print("6. Update SHEET1_ID and SHEET2_ID in app.py")
    print("\nFor detailed instructions, see SETUP_INSTRUCTIONS.md")
    return False

def system_info():
    """Display system information"""
    print("🖥️ System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {sys.version}")
    print(f"   Script directory: {os.path.dirname(os.path.abspath(__file__))}")

def main():
    """Main setup function"""
    print("🚀 QR Code Attendance System - Portable Setup")
    print("=" * 50)
    
    # Display system info
    system_info()
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Check camera
    camera_ok = check_camera()
    
    # Check credentials
    creds_ok = check_credentials()
    
    print("\n" + "=" * 50)
    print("📋 Setup Summary:")
    print(f"   ✅ Python version: OK")
    print(f"   ✅ Dependencies: OK")
    print(f"   {'✅' if camera_ok else '⚠️'} Camera: {'OK' if camera_ok else 'Check needed'}")
    print(f"   {'✅' if creds_ok else '⚠️'} Credentials: {'OK' if creds_ok else 'Missing'}")
    
    if camera_ok and creds_ok:
        print("\n🎉 Setup complete! You can now run:")
        print("   python app.py")
    else:
        print("\n⚠️ Setup completed with warnings. Please address the issues above.")
        if not camera_ok:
            print("   - Check camera permissions and connection")
        if not creds_ok:
            print("   - Add your Google Sheets credentials file")
    
    print("\n📚 For support, check the README.md file")

if __name__ == "__main__":
    main()
