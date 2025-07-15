# QR Code Attendance System - Deployment Guide

## 🚀 Deployment Options

### Option 1: Portable Deployment (Recommended)
The simplest way to deploy this system is using the portable version that requires only 2 files:

1. **Required Files:**
   - `app.py` - Main application
   - `new-creds.json` - Google Sheets credentials

2. **Deployment Steps:**
   ```bash
   # 1. Copy files to target system
   cp app.py new-creds.json /path/to/deployment/
   
   # 2. Install dependencies
   python setup.py
   
   # 3. Run the application
   python app.py
   ```

### Option 2: Full Project Deployment

1. **Clone or copy the entire project:**
   ```bash
   git clone https://github.com/Kasa1905/QRSync.git
   cd QRSync
   ```

2. **Install dependencies:**
   ```bash
   # Option A: Use setup script
   python setup.py
   
   # Option B: Use requirements.txt
   pip install -r requirements.txt
   ```

3. **Configure credentials:**
   ```bash
   cp new-creds.json.template new-creds.json
   # Edit new-creds.json with your Google Sheets credentials
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

## 🖥️ Platform-Specific Deployment

### Windows
```cmd
# Install Python 3.8+ from python.org
python -m pip install --upgrade pip
python setup.py
python app.py
```

### macOS
```bash
# Install using Homebrew (recommended)
brew install python
python3 setup.py
python3 app.py
```

### Linux (Ubuntu/Debian)
```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip
python3 setup.py
python3 app.py
```

## 🐳 Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   COPY app.py new-creds.json ./
   
   CMD ["python", "app.py"]
   ```

2. **Build and run:**
   ```bash
   docker build -t qrsync .
   docker run -it --device=/dev/video0 qrsync
   ```

## 📦 Creating Portable Packages

Use the `create_package.py` script to create deployment packages:

```bash
python create_package.py
```

This creates:
- `qrsync_portable.zip` - Minimal portable version
- `qrsync_full.zip` - Complete project package

## 🔧 Configuration

### Google Sheets Setup
1. Create Google Cloud project
2. Enable Google Sheets API
3. Create service account
4. Download credentials JSON
5. Share sheets with service account email

### Environment Variables (Optional)
```bash
export GOOGLE_SHEETS_CREDS=/path/to/credentials.json
export ATTENDANCE_SHEET_ID=your_sheet_id
export MASTER_SHEET_ID=your_master_sheet_id
```

## 🛡️ Security Considerations

1. **Credential Security:**
   - Never commit credentials to version control
   - Use environment variables in production
   - Restrict service account permissions

2. **Network Security:**
   - Use HTTPS for all API calls
   - Implement rate limiting
   - Monitor API usage

3. **Data Privacy:**
   - Encrypt sensitive data at rest
   - Use secure communication channels
   - Implement proper access controls

## 🔍 Troubleshooting

### Common Issues:

1. **Camera not found:**
   - Check camera permissions
   - Verify camera is not used by another application
   - Try different camera backends

2. **Google Sheets API errors:**
   - Verify credentials file path
   - Check internet connection
   - Ensure sheets are shared with service account

3. **Dependency issues:**
   - Update pip: `python -m pip install --upgrade pip`
   - Install system dependencies for OpenCV
   - Use virtual environment

### Debug Mode:
```bash
python app.py --debug
```

## 📊 Monitoring and Maintenance

1. **Log Monitoring:**
   - Check application logs regularly
   - Monitor Google Sheets API quotas
   - Track attendance data integrity

2. **Updates:**
   - Keep dependencies updated
   - Monitor for security updates
   - Test updates in staging environment

3. **Backup:**
   - Regular backup of attendance data
   - Backup Google Sheets
   - Version control configuration files

## 🚀 Production Deployment

### Systemd Service (Linux)
```ini
[Unit]
Description=QR Code Attendance System
After=network.target

[Service]
Type=simple
User=qrsync
WorkingDirectory=/opt/qrsync
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Auto-start on Boot
- **Windows:** Use Task Scheduler
- **macOS:** Use launchd
- **Linux:** Use systemd or cron

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review logs for error messages
3. Verify system requirements
4. Test in minimal environment

## 🔄 Updates and Maintenance

### Regular Maintenance Tasks:
- Update dependencies monthly
- Review and rotate credentials quarterly
- Monitor disk space for CSV files
- Check Google Sheets API quotas

### Version Control:
- Tag releases for stable deployments
- Use semantic versioning
- Maintain deployment documentation
- Test before production deployment
