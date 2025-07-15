# QR Code Attendance System - PORTABLE VERSION

**Works on any device with just 2 files: `app.py` and `new-creds.json`**

## � Quick Start

### Requirements
- Python 3.8 or higher
- Camera/webcam
- Google Cloud Platform account with Sheets API enabled
- Internet connection (for Google Sheets sync)

### Installation

1. **Setup Google Sheets and Credentials:**
   - Follow instructions in `SETUP_INSTRUCTIONS.md`
   - Create `new-creds.json` from the template
   - Update Sheet IDs in `app.py`

2. **Install dependencies:**
   ```bash
   # Option 1: Using setup script (recommended)
   python setup.py
   
   # Option 2: Manual installation
   pip install opencv-python gspread oauth2client pandas numpy pillow
   
   # Option 3: Using requirements file
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

### 🖥️ Cross-Platform Compatibility

The system automatically detects your platform and optimizes settings:

- **Windows**: Uses DirectShow camera backend
- **macOS**: Uses AVFoundation camera backend  
- **Linux**: Uses V4L2 camera backend
- **All platforms**: Fallback to generic backends if needed

### 📁 File Structure (Minimal)
```
QRSync/
├── app.py              # Main application (required)
├── new-creds.json      # Google Sheets credentials (required)
└── requirements.txt    # Dependencies (optional)
```

### 📁 Complete File Structure
```
QRSync/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── setup.py                 # Installation helper
├── new-creds.json.template  # Credentials template
├── .gitignore              # Git ignore rules
├── LICENSE                 # MIT License
├── README.md               # User documentation
├── PROJECT_README.md       # Project overview
├── SETUP_INSTRUCTIONS.md   # Detailed setup guide
├── DEPLOYMENT_GUIDE.md     # Deployment information
├── verify_security.py      # Security verification
└── create_package.py       # Package creator
```
├── requirements.txt    # Dependencies (optional)
├── setup.py           # Installation helper (optional)
└── YYYY-MM-DD_scans.csv # Auto-generated data files
```

### 🚀 Performance Optimizations
- **Frame Skipping**: Processes every other frame for better performance
- **Caching**: Caches Google Sheets data to reduce API calls
- **Async Operations**: Background thread for Google Sheets updates
- **QR Cooldown**: Prevents spam detection with 10-frame cooldown

### 📡 Offline Mode Support
- **Automatic Fallback**: Switches to offline mode if Google Sheets unavailable
- **Local CSV Backup**: All data saved locally regardless of connection
- **Graceful Degradation**: Continues working without internet
- **Auto-Sync**: Automatically syncs offline data when connection restored
- **Manual Sync**: Press 's' key for manual sync attempt
- **Sync Tracking**: CSV columns track sync status for each record

### 🔄 Auto-Sync Capabilities
- **Online Detection**: Checks for connectivity every 30 seconds when offline
- **Automatic Reconnection**: Re-establishes Google Sheets connection when possible
- **Data Synchronization**: Syncs all offline CSV data to Google Sheets
- **Backup Creation**: Creates backup files before and after sync operations
- **Error Recovery**: Robust error handling with automatic retry mechanisms
- **Status Indicators**: Visual feedback on sync status and progress

### 🛡️ Error Handling
- **Connection Resilience**: Handles network failures gracefully
- **Comprehensive Logging**: Detailed logs for debugging
- **Safe Shutdowns**: Proper cleanup on exit
- **Exception Handling**: Prevents crashes from API errors

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Ensure camera permissions are granted
# On macOS: System Preferences > Security & Privacy > Camera
```

## Usage

```bash
python app.py
```

### Controls
- **Space/Enter**: Continue scanning
- **Q**: Quit application
- **S**: Manual sync attempt (when offline)

### Visual Indicators
- **Green Border**: QR code detected successfully
- **Red Warning**: Cooldown period active
- **Status Display**: Shows ONLINE/OFFLINE mode with sync status
- **Scan History**: Last 10 scans displayed
- **Sync Status**: "Auto-sync enabled" when offline, "Data synced" when online

## Data Storage

### CSV Files (Always Active)
- Format: `YYYY-MM-DD_scans.csv`
- Columns: ID, Timestamp1, Timestamp2, ..., Synced_Sheet1, Synced_Sheet2
- Location: Same directory as script
- Backup files: Created before and after sync operations

### Google Sheets (When Online)
- **Sheet1**: Daily attendance with timestamps
- **Sheet2**: Master attendance with Present/Absent status
- **Auto-Sync**: Offline data automatically synced when connection restored

## Troubleshooting

### Common Issues

1. **Camera not detected**
   - Check camera permissions
   - Ensure no other app is using camera

2. **Google Sheets connection failed**
   - Verify `new-creds.json` exists and is valid
   - Check internet connection
   - System will automatically switch to offline mode

3. **QR codes not detected**
   - Ensure good lighting
   - Hold QR code steady
   - Check QR code quality

4. **Auto-sync issues**
   - Check internet connection and Google Sheets permissions
   - Verify `new-creds.json` exists and is valid
   - Check `attendance_system.log` for detailed sync errors
   - Use manual sync ('s' key) to force sync attempt

5. **Partial sync completed**
   - Some data may sync while others fail
   - Check logs for specific error details
   - Backup files are created for data safety
   - Retry sync after fixing connection issues

### Offline Mode
When offline mode is active:
- All scans saved to CSV files
- No Google Sheets updates
- System remains fully functional
- **Auto-sync**: Automatically syncs data when connection restored
- **Manual sync**: Press 's' key to attempt manual sync
- **Sync tracking**: CSV tracks which records have been synced

### Log Files
- `attendance_system.log`: Detailed sync operation logs and system events
- CSV backup files: Data safety during sync operations
- Error messages with timestamps and stack traces
- Sync progress and completion status

## Auto-Sync Features

### Automatic Synchronization
- **Online Detection**: System checks for connectivity every 30 seconds
- **Automatic Reconnection**: Re-establishes Google Sheets connection when possible
- **Data Sync**: Syncs all offline CSV data to both daily and master sheets
- **Status Tracking**: Tracks sync status for each record in CSV

### Sync Process Flow
1. **Detection**: Check for Google Sheets connectivity
2. **Reconnection**: Re-establish API connection if possible
3. **Data Reading**: Read unsynced data from CSV
4. **Sheet1 Sync**: Upload timestamps to daily attendance sheet
5. **Sheet2 Sync**: Mark present in master attendance sheet
6. **Status Update**: Mark records as synced in CSV
7. **Backup Creation**: Create synced backup files

### Data Integrity & Safety
- **Atomic Operations**: All sync operations complete or rollback
- **Backup Files**: Multiple backup files created for safety
- **Error Recovery**: Robust error handling with automatic retry
- **Comprehensive Logging**: Detailed logs for troubleshooting

### User Interface
- **Visual Status**: Clear online/offline indicators on camera view
- **Sync Messages**: Real-time sync progress and completion status
- **Manual Control**: Press 's' key for manual sync attempt
- **Terminal Feedback**: Detailed sync results in terminal output

## Configuration Options

### Timing Settings
- `AUTO_SYNC_INTERVAL`: 30 seconds (configurable)
- `MAX_RETRY_ATTEMPTS`: 3 attempts before going offline
- Connection timeout and retry logic

### File Management
- CSV files with date-based naming
- Backup files with descriptive suffixes
- Automatic cleanup of old backup files (optional)

## Performance Tips

1. **Optimal Environment**
   - Good lighting for QR detection
   - Stable camera mount
   - Fast CPU for real-time processing

2. **System Requirements**
   - Python 3.8+
   - OpenCV compatible camera
   - 4GB+ RAM recommended

3. **Network Optimization**
   - Stable internet for Google Sheets
   - Local network preferred over mobile data

## Benefits

### Reliability
- **No Data Loss**: All attendance data preserved regardless of network status
- **Automatic Recovery**: System handles reconnection and sync automatically
- **Multiple Backups**: Backup files created for data safety
- **Atomic Operations**: All sync operations complete or rollback safely

### User Experience
- **Seamless Operation**: Works perfectly both online and offline
- **Clear Visual Feedback**: Status indicators show sync progress
- **Manual Override**: Users can trigger sync manually with 's' key
- **Real-time Updates**: Terminal shows sync progress and results

### Data Integrity
- **Complete Audit Trail**: All operations logged and tracked
- **Sync Status Tracking**: CSV tracks which records have been synced
- **Error Recovery**: Robust error handling with automatic retry
- **Backup Safety**: Multiple backup files prevent data loss

## Future Enhancements
- Configurable sync intervals
- Selective sync options (Sheet1 only, Sheet2 only)
- Sync progress indicators with percentage completion
- Historical sync reports and analytics
- Advanced error recovery mechanisms
- Batch sync optimizations for large datasets
