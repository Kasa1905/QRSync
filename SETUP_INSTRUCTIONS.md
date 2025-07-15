# QR Code Attendance System - Setup Instructions

## 🚀 Quick Setup Guide

### 1. Prerequisites
- Python 3.8 or higher
- Camera/webcam
- Google Cloud Platform account
- Google Sheets access

### 2. Google Sheets Setup

#### Step 1: Create Google Sheets
1. Create two Google Sheets:
   - **Sheet 1**: Daily attendance tracking
   - **Sheet 2**: Master attendance sheet
2. Note down the Sheet IDs from the URLs

#### Step 2: Set up Google Cloud Platform
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create service account credentials
5. Download the JSON credentials file

#### Step 3: Configure Sheets Access
1. Share both Google Sheets with your service account email
2. Give "Editor" permissions to the service account
3. Make sure the master sheet has a "Master" tab

### 3. Application Setup

#### Step 1: Download Files
```bash
git clone [your-repo-url]
cd attendence-public
```

#### Step 2: Install Dependencies
```bash
# Option 1: Using setup script (recommended)
python setup.py

# Option 2: Manual installation
pip install -r requirements.txt
```

#### Step 3: Configure Application
1. **Rename credentials file**:
   ```bash
   mv new-creds.json.template new-creds.json
   ```

2. **Edit credentials file**:
   - Replace all placeholder values with your actual credentials
   - Use the JSON file downloaded from Google Cloud Console

3. **Update Sheet IDs in app.py**:
   ```python
   SHEET1_ID = "your-daily-sheet-id"
   SHEET2_ID = "your-master-sheet-id"
   ```

#### Step 4: Run the Application
```bash
python app.py
```

### 4. Sheet Structure Requirements

#### Daily Attendance Sheet (Sheet1)
- Must have "ID" column
- Must have "Temp" worksheet for template
- Columns: ID, Timestamp1, Timestamp2, ...

#### Master Attendance Sheet (Sheet2)
- Must have "ID" column
- Must have date columns (format: M/D/YYYY)
- Must have "Master" worksheet
- Columns: ID, 1/1/2025, 1/2/2025, ...

### 5. Security Setup

#### File Permissions
```bash
chmod 600 new-creds.json  # Secure credentials file
chmod 644 app.py          # Application file
```

#### Firewall (if needed)
- Allow Python through firewall
- Allow camera access

### 6. Testing

#### Test Camera
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

#### Test Google Sheets Connection
```bash
python -c "from app import initialize_google_sheets; print(initialize_google_sheets())"
```

### 7. Troubleshooting

#### Common Issues
- **Camera not working**: Check permissions and drivers
- **Google Sheets connection failed**: Verify credentials and sheet sharing
- **Import errors**: Install missing dependencies
- **Permission denied**: Check file permissions

#### Debug Mode
Enable detailed logging by setting log level to DEBUG in app.py

### 8. Production Deployment

#### System Service (Linux)
Create systemd service for automatic startup:
```ini
[Unit]
Description=QR Attendance System
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/attendence-public
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Startup Script (Windows)
Create batch file for automatic startup:
```batch
@echo off
cd /d "C:\path\to\attendence-public"
python app.py
```

### 9. Security Considerations

#### Credentials Security
- Never commit credentials to version control
- Use environment variables for production
- Rotate credentials regularly
- Limit service account permissions

#### Network Security
- Use HTTPS for all Google API calls
- Consider VPN for remote access
- Monitor API usage

### 10. Support

For issues and support:
1. Check the logs in `attendance_system.log`
2. Verify all setup steps
3. Check Google Cloud Console for API limits
4. Ensure all dependencies are installed

## 📋 Checklist

- [ ] Python 3.8+ installed
- [ ] Google Cloud Platform account created
- [ ] Google Sheets API enabled
- [ ] Service account created and credentials downloaded
- [ ] Google Sheets created and shared with service account
- [ ] Application configured with correct Sheet IDs
- [ ] Credentials file properly configured
- [ ] Dependencies installed
- [ ] Camera permissions granted
- [ ] Application tested and working

## 🔧 Configuration Files

### Required Files
- `app.py` - Main application
- `new-creds.json` - Google Sheets credentials
- `requirements.txt` - Python dependencies

### Optional Files
- `setup.py` - Installation helper
- `create_package.py` - Deployment package creator
- `README.md` - User documentation
- `PROJECT_README.md` - Project overview
- `DEPLOYMENT_GUIDE.md` - Deployment information
- `verify_security.py` - Security verification
- `.gitignore` - Git ignore rules
- `LICENSE` - MIT License

Your QR Code Attendance System is now ready for deployment! 🚀
