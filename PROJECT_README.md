# QR Code Attendance System

A robust, cross-platform attendance tracking system using QR codes and Google Sheets with offline capabilities and automatic synchronization.

## ✨ Features

### 🚀 Core Features
- **QR Code Scanning**: Real-time QR code detection and processing
- **Google Sheets Integration**: Automatic sync with Google Sheets
- **Offline Mode**: Works without internet, syncs when reconnected
- **Cross-Platform**: Windows, macOS, Linux support
- **Auto-Sync**: Automatic offline data synchronization
- **Error Resilient**: Comprehensive error handling and recovery

### 🛡️ Reliability
- **Dual Storage**: CSV + Google Sheets backup
- **Automatic Fallback**: Seamless offline operation
- **Data Integrity**: Multiple backup mechanisms
- **Error Recovery**: Graceful handling of failures

### 🔧 Portability
- **Minimal Setup**: Just 2 files needed (app.py + credentials)
- **Auto-Detection**: Smart file and hardware detection
- **Platform Adaptive**: Optimizes for each operating system
- **Easy Deployment**: Copy-and-run simplicity

## 🚀 Quick Start

1. **Setup Google Sheets** (see `SETUP_INSTRUCTIONS.md`)
2. **Install dependencies**: `python setup.py`
3. **Configure credentials**: Edit `new-creds.json`
4. **Run**: `python app.py`

## 📁 Project Structure

```
QRSync/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── setup.py                 # Installation helper
├── new-creds.json.template  # Credentials template
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
├── README.md               # User documentation
├── PROJECT_README.md       # This file (project overview)
├── SETUP_INSTRUCTIONS.md   # Detailed setup guide
├── DEPLOYMENT_GUIDE.md     # Deployment information
├── verify_security.py      # Security verification
└── create_package.py       # Package creator
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Camera/webcam
- Google Cloud Platform account

### Quick Install
```bash
git clone [your-repo-url]
cd attendence-public
python setup.py
python app.py
```

### Manual Install
```bash
pip install opencv-python gspread oauth2client pandas numpy pillow
# Configure credentials and Sheet IDs
python app.py
```

## 🎯 Usage

### Basic Operation
1. **Start application**: `python app.py`
2. **Scan QR codes**: Point camera at QR codes
3. **View status**: Check online/offline status on screen
4. **Manual sync**: Press 's' key when offline
5. **Quit**: Press 'q' or ESC

### Controls
- **Q/ESC**: Quit application
- **S**: Manual sync (when offline)

### Visual Indicators
- **Green "ONLINE"**: Connected to Google Sheets
- **Orange "OFFLINE"**: Offline mode active
- **"Auto-sync enabled"**: Automatic sync active
- **"Data synced"**: All data synchronized

## 🔧 Configuration

### Sheet IDs
Update in `app.py`:
```python
SHEET1_ID = "your-daily-sheet-id"
SHEET2_ID = "your-master-sheet-id"
```

### Credentials
Create `new-creds.json` from template with your Google Cloud credentials.

## 📊 Data Storage

### CSV Files (Local)
- Format: `YYYY-MM-DD_scans.csv`
- Columns: ID, Timestamp1, Timestamp2, ..., Synced_Sheet1, Synced_Sheet2
- Auto-backup and sync tracking

### Google Sheets (Online)
- **Sheet1**: Daily attendance with timestamps
- **Sheet2**: Master attendance with Present/Absent status

## 🛠️ Development

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Code Structure
- **Modular design**: Clear separation of concerns
- **Error handling**: Comprehensive error recovery
- **Cross-platform**: Platform-specific optimizations
- **Documentation**: Detailed inline comments

## 📋 System Requirements

### Minimum
- Python 3.8+
- 512MB RAM
- 50MB storage
- Basic camera

### Recommended
- Python 3.9+
- 1GB RAM
- 100MB storage
- HD camera

## 🔒 Security

### Data Protection
- Credentials never stored in code
- Local data encrypted in transit
- API keys secured
- Access logging

### Best Practices
- Use environment variables for production
- Regular credential rotation
- Limit service account permissions
- Monitor API usage

## 🐛 Troubleshooting

### Common Issues
- **Camera not working**: Check permissions
- **Google Sheets connection failed**: Verify credentials
- **Dependencies missing**: Run `python setup.py`
- **Sync issues**: Check internet connection

### Debug Mode
Enable detailed logging in `app.py` for troubleshooting.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Support

For issues and questions:
1. Check `SETUP_INSTRUCTIONS.md`
2. Review error logs
3. Verify configuration
4. Create GitHub issue

## 🏆 Acknowledgments

- OpenCV for computer vision
- gspread for Google Sheets API
- pandas for data processing
- TED Event Team for requirements and testing

---

**Made with ❤️ for seamless attendance tracking**
