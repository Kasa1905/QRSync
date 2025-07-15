"""
QR Code Attendance Tracking System
==================================
A robust, offline-capable attendance system using QR codes and Google Sheets.
Handles all kinds of errors gracefully and works seamlessly offline.

PORTABLE VERSION - Works on any device with just app.py and credentials file

Author: TED Event Team
Date: July 2025
"""

import cv2
import time
import gspread
import numpy as np
import csv
import os
import threading
import queue
import sys
import traceback
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import logging
import tempfile
import platform

# ========== Auto-Detection of File Paths (PORTABLE) ==========
def get_script_directory():
    """Get the directory where the script is located"""
    if getattr(sys, 'frozen', False):
        # If running from PyInstaller bundle
        return os.path.dirname(sys.executable)
    else:
        # If running from script
        return os.path.dirname(os.path.abspath(__file__))

def find_credentials_file():
    """Find the credentials file in the script directory"""
    script_dir = get_script_directory()
    
    # Common credential file names
    cred_names = [
        'new-creds.json',
        'creds.json', 
        'credentials.json',
        'service-account.json'
    ]
    
    for cred_name in cred_names:
        cred_path = os.path.join(script_dir, cred_name)
        if os.path.exists(cred_path):
            return cred_path
    
    return None

# ========== Cross-Platform Logging Setup ==========
def setup_logging():
    """Setup logging that works on any platform"""
    script_dir = get_script_directory()
    log_path = os.path.join(script_dir, 'attendance_system.log')
    
    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Setup file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.CRITICAL)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

# Initialize logging
setup_logging()

# ========== Configuration and Global Variables ==========
# Google Sheets IDs - Update these with your actual sheet IDs
SHEET1_ID = "YOUR_SHEET1_ID_HERE"  # Daily attendance sheet
SHEET2_ID = "YOUR_SHEET2_ID_HERE"  # Master attendance sheet
SHEET2_NAME = "Master"  # Name of the master sheet tab

# ========== Cross-Platform Display Configuration ==========
def get_display_config():
    """Get display configuration based on platform and screen size"""
    try:
        # Try to get screen resolution
        import tkinter as tk
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        # Fallback to common resolutions
        screen_width = 1920
        screen_height = 1080
    
    # Calculate optimal sizes
    video_width = min(int(screen_width * 0.7), 1200)  # Max 1200px width
    video_height = min(screen_height - 100, 800)      # Leave space for taskbar
    log_width = min(screen_width - video_width, 400)  # Max 400px sidebar
    
    return {
        'screen_width': screen_width,
        'screen_height': screen_height,
        'video_width': video_width,
        'video_height': video_height,
        'log_width': log_width
    }

# Global flags and data structures for system state management
OFFLINE_MODE = False  # Flag to track if system is operating offline
sheet_cache = {}  # Cache for Google Sheets data to reduce API calls
update_queue = queue.Queue()  # Queue for background Google Sheets updates
connection_retry_count = 0  # Track connection retry attempts
MAX_RETRY_ATTEMPTS = 3  # Maximum retries before going offline
last_online_check = 0  # Track last time we checked for online status
AUTO_SYNC_INTERVAL = 30  # Check for sync every 30 seconds

# ========== Google Sheets Connection with Robust Error Handling ==========
def initialize_google_sheets():
    """
    Initialize Google Sheets connection with comprehensive error handling.
    Returns: tuple (success: bool, error_message: str)
    """
    global OFFLINE_MODE, client, spreadsheet1, spreadsheet2, sheet1, sheet2, template_sheet
    
    try:
        logging.info("Attempting to connect to Google Sheets...")
        
        # Define the scope for Google Sheets API access
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Check if credentials file exists
        creds_path = find_credentials_file()
        if not creds_path:
            raise FileNotFoundError("Credentials file not found. Please place 'new-creds.json' in the same directory as app.py")
        
        # Load credentials and authenticate
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        logging.info("✅ Successfully authenticated with Google Sheets")
        
        # Open the spreadsheets by their IDs
        try:
            spreadsheet1 = client.open_by_key(SHEET1_ID)
            spreadsheet2 = client.open_by_key(SHEET2_ID)
            logging.info("✅ Successfully opened both spreadsheets")
        except gspread.exceptions.SpreadsheetNotFound as e:
            raise Exception(f"Spreadsheet not found. Check your SHEET_IDs: {e}")
        except Exception as e:
            raise Exception(f"Error opening spreadsheets: {e}")
        
        # Get or create template sheet
        try:
            template_sheet = spreadsheet1.worksheet("Temp")
            logging.info("✅ Found template sheet 'Temp'")
        except gspread.exceptions.WorksheetNotFound:
            logging.warning("⚠️ Template sheet 'Temp' not found")
            raise Exception("Template sheet 'Temp' is required but not found")
        
        # Create or access today's attendance sheet
        SHEET1_NAME = datetime.now().strftime("%-m/%-d/%Y").lstrip("0")
        try:
            sheet1 = spreadsheet1.worksheet(SHEET1_NAME)
            logging.info(f"✅ Found existing sheet for today: {SHEET1_NAME}")
        except gspread.exceptions.WorksheetNotFound:
            try:
                logging.info(f"Creating new sheet for today: {SHEET1_NAME}")
                sheet1 = template_sheet.duplicate(new_sheet_name=SHEET1_NAME)
                time.sleep(3)  # Wait for Google to process the duplication
                logging.info(f"✅ Successfully created today's sheet: {SHEET1_NAME}")
            except Exception as e:
                raise Exception(f"Failed to create today's sheet: {e}")
        
        # Access the master sheet
        try:
            sheet2 = spreadsheet2.worksheet(SHEET2_NAME)
            logging.info(f"✅ Successfully accessed master sheet: {SHEET2_NAME}")
        except gspread.exceptions.WorksheetNotFound:
            raise Exception(f"Master sheet '{SHEET2_NAME}' not found in spreadsheet2")
        
        OFFLINE_MODE = False
        return True, "Successfully connected to Google Sheets"
        
    except FileNotFoundError as e:
        error_msg = f"Credentials file error: {e}"
        logging.info(error_msg)
        return False, error_msg
    except gspread.exceptions.APIError as e:
        error_msg = f"Google Sheets API error: {e}"
        logging.info(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error connecting to Google Sheets: {e}"
        logging.info(error_msg)
        logging.info(f"Full traceback: {traceback.format_exc()}")
        return False, error_msg

# Initialize Google Sheets connection
try:
    success, error_message = initialize_google_sheets()
    if not success:
        logging.warning(f"Google Sheets initialization failed: {error_message}")
        OFFLINE_MODE = True
        # Initialize None values for offline mode
        client = None
        spreadsheet1 = None
        spreadsheet2 = None
        sheet1 = None
        sheet2 = None
        template_sheet = None
except Exception as e:
    logging.info(f"Critical error during initialization: {e}")
    OFFLINE_MODE = True
    client = spreadsheet1 = spreadsheet2 = sheet1 = sheet2 = template_sheet = None

# ========== Local Data Storage Setup ==========
# Create daily CSV log file with error handling
def setup_csv_logging():
    """Setup CSV logging that works on any platform"""
    script_dir = get_script_directory()
    log_filename = datetime.now().strftime("%Y-%m-%d") + "_scans.csv"
    log_filepath = os.path.join(script_dir, log_filename)
    
    # Ensure CSV file exists with proper headers
    try:
        if not os.path.exists(log_filepath):
            with open(log_filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Timestamp1"])  # Basic headers
            logging.info(f"✅ Created new CSV log file: {log_filepath}")
        else:
            logging.info(f"✅ Using existing CSV log file: {log_filepath}")
    except Exception as e:
        logging.error(f"❌ Failed to create/access CSV file: {e}")
        # Create fallback in temp directory
        log_filepath = os.path.join(tempfile.gettempdir(), log_filename)
        logging.info(f"Using fallback CSV location: {log_filepath}")
        
        try:
            if not os.path.exists(log_filepath):
                with open(log_filepath, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Timestamp1"])
        except Exception as e2:
            logging.error(f"❌ Failed to create fallback CSV: {e2}")
    
    return log_filepath

# Initialize CSV logging
log_filepath = setup_csv_logging()

# ========== Background Worker for Async Google Sheets Operations ==========
def async_sheets_worker():
    """
    Background worker thread to handle Google Sheets updates asynchronously.
    This prevents the main UI from freezing during API calls.
    """
    while True:
        try:
            # Check if we're in offline mode - if so, just wait
            if OFFLINE_MODE:
                time.sleep(1)
                continue
                
            # Get update request from queue (timeout prevents indefinite blocking)
            try:
                update_data = update_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            # Check for shutdown signal
            if update_data is None:
                logging.info("Background worker received shutdown signal")
                break
                
            # Process the update request
            update_type, data = update_data
            
            if update_type == 'sheet1_update':
                unique_id, timestamp = data
                logging.info(f"Background: Processing Sheet1 update for {unique_id} at {timestamp}")
                # Additional async update logic can be added here
                
            elif update_type == 'sheet2_update':
                unique_id = data
                logging.info(f"Background: Processing Sheet2 update for {unique_id}")
                # Additional async update logic can be added here
                
            elif update_type == 'cache_refresh':
                logging.info("Background: Refreshing sheet cache")
                cache_sheet_data()
                
            # Mark task as completed
            update_queue.task_done()
            
        except queue.Empty:
            # Normal timeout - continue looping
            continue
        except Exception as e:
            logging.info(f"Background worker error: {e}")
            logging.info(f"Traceback: {traceback.format_exc()}")
            # Continue running even if individual operations fail

# Start background worker thread only if we're online
if not OFFLINE_MODE:
    try:
        worker_thread = threading.Thread(target=async_sheets_worker, daemon=True)
        worker_thread.start()
        logging.info("✅ Background worker thread started")
    except Exception as e:
        logging.info(f"Failed to start background worker: {e}")

# ========== Utility Functions ==========
def get_session_columns(_):
    """Legacy function for compatibility - returns scan time column info"""
    return "Scan Time", ""

def safe_sheet_operation(operation_func, *args, **kwargs):
    """
    Wrapper function to safely execute Google Sheets operations with retry logic.
    
    Args:
        operation_func: The function to execute
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        tuple: (success: bool, result: any, error_message: str)
    """
    global OFFLINE_MODE, connection_retry_count
    
    if OFFLINE_MODE:
        return False, None, "System is in offline mode"
    
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            result = operation_func(*args, **kwargs)
            connection_retry_count = 0  # Reset retry count on success
            return True, result, ""
        except gspread.exceptions.APIError as e:
            logging.warning(f"API error on attempt {attempt + 1}: {e}")
            if attempt == MAX_RETRY_ATTEMPTS - 1:
                OFFLINE_MODE = True
                logging.info("Max retries reached - switching to offline mode")
                return False, None, f"API error after {MAX_RETRY_ATTEMPTS} attempts: {e}"
            time.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logging.info(f"Unexpected error in sheet operation: {e}")
            return False, None, str(e)
    
    return False, None, "Operation failed"

def cache_sheet_data():
    """
    Cache frequently accessed sheet data to reduce API calls and improve performance.
    This function safely retrieves data from Google Sheets and stores it locally.
    """
    if OFFLINE_MODE:
        logging.info("Offline mode - skipping sheet data caching")
        return
        
    try:
        logging.info("Starting sheet data caching...")
        
        # Cache Sheet2 (Master) headers if not already cached
        if 'sheet2_headers' not in sheet_cache:
            success, headers, error = safe_sheet_operation(sheet2.row_values, 1)
            if success:
                sheet_cache['sheet2_headers'] = headers
                logging.info("✅ Cached Sheet2 headers")
            else:
                logging.info(f"Failed to cache Sheet2 headers: {error}")
        
        # Cache Sheet2 (Master) all records if not already cached
        if 'sheet2_records' not in sheet_cache:
            success, records, error = safe_sheet_operation(sheet2.get_all_values)
            if success:
                sheet_cache['sheet2_records'] = records
                logging.info("✅ Cached Sheet2 records")
            else:
                logging.info(f"Failed to cache Sheet2 records: {error}")
        
        # Cache Sheet1 (Daily) headers if not already cached
        if 'sheet1_headers' not in sheet_cache:
            success, headers, error = safe_sheet_operation(sheet1.row_values, 1)
            if success:
                sheet_cache['sheet1_headers'] = headers
                logging.info("✅ Cached Sheet1 headers")
            else:
                logging.info(f"Failed to cache Sheet1 headers: {error}")
                
        logging.info("Sheet data caching completed")
        
    except Exception as e:
        logging.info(f"Critical error during sheet caching: {e}")
        logging.info(f"Traceback: {traceback.format_exc()}")

def mark_present_in_sheet2(unique_id):
    """
    Mark 'Present' in Sheet2 (Master) under today's date for the given unique_id.
    This function handles all possible errors gracefully and continues operation.
    
    Args:
        unique_id (str): The unique identifier of the person to mark present
    """
    if OFFLINE_MODE:
        logging.info(f"Offline mode: Would mark {unique_id} present in Sheet2")
        return
        
    try:
        # Get today's date in the same format as sheet headers
        current_date_str = datetime.now().strftime("%-m/%-d/%Y").lstrip("0")
        logging.info(f"Marking {unique_id} present for date: {current_date_str}")
        
        # Use cached headers if available, otherwise fetch fresh data
        if 'sheet2_headers' in sheet_cache:
            headers = sheet_cache['sheet2_headers']
        else:
            success, headers, error = safe_sheet_operation(sheet2.row_values, 1)
            if not success:
                logging.info(f"Failed to get Sheet2 headers: {error}")
                return
            sheet_cache['sheet2_headers'] = headers

        # Find the ID column index
        try:
            id_col_index = headers.index("ID")
        except ValueError:
            logging.info("ID column not found in Sheet2 headers")
            logging.info(f"Available headers: {headers}")
            return

        # Find today's date column index
        try:
            date_col_index = headers.index(current_date_str)
        except ValueError:
            logging.info(f"Date column '{current_date_str}' not found in Sheet2")
            logging.info(f"Available headers: {headers}")
            return

        # Use cached records if available, otherwise fetch fresh data
        if 'sheet2_records' in sheet_cache:
            records = sheet_cache['sheet2_records']
        else:
            success, records, error = safe_sheet_operation(sheet2.get_all_values)
            if not success:
                logging.info(f"Failed to get Sheet2 records: {error}")
                return
            sheet_cache['sheet2_records'] = records
            
        # Skip header row and extract IDs
        data_records = records[1:] if len(records) > 1 else []
        ids = [row[id_col_index] if len(row) > id_col_index else "" for row in data_records]

        # Find the person's row and update if found
        if unique_id in ids:
            row_index = ids.index(unique_id) + 2  # +2 for 1-based indexing and header row
            
            # Check current value before updating
            success, current_value, error = safe_sheet_operation(
                sheet2.cell, row_index, date_col_index + 1
            )
            
            if success:
                current_val = current_value.value if hasattr(current_value, 'value') else str(current_value)
                if not current_val or not current_val.strip():
                    # Update the cell to "Present"
                    success, _, error = safe_sheet_operation(
                        sheet2.update_cell, row_index, date_col_index + 1, "Present"
                    )
                    
                    if success:
                        logging.info(f"✅ Marked {unique_id} as Present in Sheet2")
                        # Update cache
                        if 'sheet2_records' in sheet_cache and row_index-2 < len(sheet_cache['sheet2_records']):
                            if len(sheet_cache['sheet2_records'][row_index-1]) > date_col_index:
                                sheet_cache['sheet2_records'][row_index-1][date_col_index] = "Present"
                    else:
                        logging.info(f"Failed to update Sheet2 for {unique_id}: {error}")
                else:
                    logging.info(f"{unique_id} already marked present for today")
            else:
                logging.info(f"Failed to check current value for {unique_id}: {error}")
        else:
            logging.warning(f"ID {unique_id} not found in Sheet2")
                    
    except Exception as e:
        logging.info(f"Critical error marking present in Sheet2 for {unique_id}: {e}")
        logging.info(f"Traceback: {traceback.format_exc()}")
        # Continue execution even if this fails

def update_attendance(unique_id):
    """
    Update timestamp in Sheet1 (Daily) and log scan to CSV.
    This is the core function that handles attendance recording with full error handling.
    
    Args:
        unique_id (str): The unique identifier from the scanned QR code
        
    Returns:
        bool: True if this is the first scan for this ID, False if it's a repeat scan
    """
    global OFFLINE_MODE, connection_retry_count
    
    if not unique_id or not unique_id.strip():
        logging.warning("Empty or invalid unique_id provided")
        return False

    # Get current time and format it
    try:
        current_time = datetime.now()
        current_time_str = current_time.strftime("%H:%M:%S")
        logging.info(f"Processing attendance for {unique_id} at {current_time_str}")
    except Exception as e:
        logging.info(f"Error getting current time: {e}")
        current_time_str = "ERROR"

    # ========== CSV LOGGING (Primary backup - always executed) ==========
    is_first_scan = True  # Default assumption
    try:
        # Check if CSV file exists and read it
        if os.path.exists(log_filepath):
            try:
                df = pd.read_csv(log_filepath)
            except Exception as e:
                logging.info(f"Error reading CSV file: {e}")
                # Create new DataFrame if reading fails
                df = pd.DataFrame(columns=["ID"])
        else:
            df = pd.DataFrame(columns=["ID"])

        # Check if this ID already exists in CSV
        if unique_id in df["ID"].values:
            # Existing ID - add new timestamp column
            row_index = df[df["ID"] == unique_id].index[0]
            existing_row = df.loc[row_index]
            
            # Find the next available timestamp column
            next_col_index = 1
            while f"Timestamp{next_col_index}" in df.columns and pd.notna(existing_row.get(f"Timestamp{next_col_index}", None)):
                next_col_index += 1
            
            next_col = f"Timestamp{next_col_index}"
            df.loc[row_index, next_col] = current_time_str
            is_first_scan = False
            logging.info(f"Added additional timestamp for {unique_id} in column {next_col}")
        else:
            # New ID - create new row
            new_row = {"ID": unique_id, "Timestamp1": current_time_str}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            is_first_scan = True
            logging.info(f"Created new entry for {unique_id}")

        # Save to CSV with error handling
        try:
            df.to_csv(log_filepath, index=False)
            logging.info(f"✅ CSV updated successfully for {unique_id}")
        except Exception as e:
            logging.info(f"❌ Failed to save CSV: {e}")
            # Try to save with backup filename
            try:
                backup_path = log_filepath.replace('.csv', '_backup.csv')
                df.to_csv(backup_path, index=False)
                logging.info(f"✅ Saved to backup CSV: {backup_path}")
            except Exception as backup_error:
                logging.info(f"❌ Failed to save backup CSV: {backup_error}")
        
    except Exception as e:
        logging.info(f"Critical error in CSV logging for {unique_id}: {e}")
        logging.info(f"Traceback: {traceback.format_exc()}")
        # Continue with Google Sheets update even if CSV fails

    # ========== GOOGLE SHEETS UPDATE (Secondary - only if online) ==========
    if not OFFLINE_MODE:
        try:
            logging.info(f"Updating Google Sheets for {unique_id}")
            
            # Get Sheet1 headers with caching
            if 'sheet1_headers' in sheet_cache:
                headers = sheet_cache['sheet1_headers']
            else:
                success, headers, error = safe_sheet_operation(sheet1.row_values, 1)
                if not success:
                    logging.info(f"Failed to get Sheet1 headers: {error}")
                    raise Exception(f"Cannot get headers: {error}")
                sheet_cache['sheet1_headers'] = headers
                
            # Get all records from Sheet1
            success, all_records, error = safe_sheet_operation(sheet1.get_all_values)
            if not success:
                logging.info(f"Failed to get Sheet1 records: {error}")
                # Clear cache and try again
                if 'sheet1_headers' in sheet_cache:
                    del sheet_cache['sheet1_headers']
                raise Exception(f"Cannot get records: {error}")
                
            records = all_records[1:] if len(all_records) > 1 else []  # Exclude headers
            logging.info(f"Retrieved {len(records)} records from Sheet1")

            # Find ID column index
            try:
                id_col_index = headers.index("ID")
            except ValueError:
                logging.info("ID column not found in Sheet1 headers")
                logging.info(f"Available headers: {headers}")
                raise Exception("ID column not found")
                
            # Extract all IDs from records
            ids = [row[id_col_index] if len(row) > id_col_index else "" for row in records]

            # Check if ID already exists in Sheet1
            if unique_id in ids:
                # Existing ID - update with new timestamp
                row_index = ids.index(unique_id) + 2  # +2 for 1-based indexing and header row
                
                # Get current row data (force fresh read)
                success, row_data, error = safe_sheet_operation(sheet1.row_values, row_index)
                if not success:
                    logging.info(f"Failed to get row data for {unique_id}: {error}")
                    # Try to clear cache and get fresh data
                    if 'sheet1_headers' in sheet_cache:
                        del sheet_cache['sheet1_headers']
                    raise Exception(f"Cannot get row data: {error}")
                
                logging.info(f"Retrieved row data for {unique_id}: length={len(row_data)}, data={row_data[:10]}...")

                # Find the first empty cell after the ID column
                first_empty_col = None
                
                # Ensure we have enough columns in the row data
                if len(row_data) <= id_col_index + 1:
                    # If row is too short, add timestamp to the next column
                    first_empty_col = id_col_index + 2  # +1 for next column, +1 for 1-based indexing
                    logging.info(f"Row too short, adding timestamp to column {first_empty_col}")
                else:
                    # Look for first empty column starting after ID column
                    for col_index in range(id_col_index + 1, len(row_data)):
                        if not row_data[col_index].strip():
                            first_empty_col = col_index + 1  # +1 for 1-based indexing
                            break
                    
                    # If no empty column found within existing data, add to the end
                    if first_empty_col is None:
                        first_empty_col = len(row_data) + 1
                
                logging.info(f"Adding timestamp for {unique_id} to column {first_empty_col} (row {row_index})")
                logging.info(f"Current row data: {row_data[:10]}...")  # Log first 10 columns for debugging

                # Update the cell with new timestamp
                success, _, error = safe_sheet_operation(
                    sheet1.update_cell, row_index, first_empty_col, current_time_str
                )
                
                # Add a small delay to ensure the API has time to process
                time.sleep(0.5)
                
                if success:
                    logging.info(f"✅ Updated existing entry in Sheet1 for {unique_id} at column {first_empty_col}")
                    
                    # Verify the update worked by reading back the cell
                    success_verify, cell_value, error_verify = safe_sheet_operation(
                        sheet1.cell, row_index, first_empty_col
                    )
                    if success_verify:
                        actual_value = cell_value.value if hasattr(cell_value, 'value') else str(cell_value)
                        logging.info(f"Verification: Cell now contains '{actual_value}'")
                    else:
                        logging.warning(f"Could not verify cell update: {error_verify}")
                    
                    mark_present_in_sheet2(unique_id)  # Mark present in master sheet
                    
                    # Clear cache to ensure fresh data on next scan
                    if 'sheet1_headers' in sheet_cache:
                        del sheet_cache['sheet1_headers']
                else:
                    logging.info(f"❌ Failed to update Sheet1 cell at row {row_index}, col {first_empty_col}: {error}")
                    # Try to clear the sheet cache in case data is stale
                    if 'sheet1_headers' in sheet_cache:
                        del sheet_cache['sheet1_headers']
                    
            else:
                # New ID - insert new row
                new_row = [""] * len(headers)
                new_row[id_col_index] = unique_id
                row_index = len(records) + 2  # +2 for 1-based indexing and header row
                
                # Insert the new row
                success, _, error = safe_sheet_operation(sheet1.insert_row, new_row, row_index)
                if not success:
                    logging.info(f"Failed to insert new row: {error}")
                    raise Exception(f"Cannot insert row: {error}")
                
                # Update ID cell (redundant but ensures data integrity)
                success, _, error = safe_sheet_operation(
                    sheet1.update_cell, row_index, id_col_index + 1, unique_id
                )
                
                # Update first timestamp cell
                success, _, error = safe_sheet_operation(
                    sheet1.update_cell, row_index, id_col_index + 2, current_time_str
                )
                
                if success:
                    logging.info(f"✅ Created new entry in Sheet1 for {unique_id}")
                    mark_present_in_sheet2(unique_id)  # Mark present in master sheet
                else:
                    logging.info(f"Failed to update new row cells: {error}")
                
        except Exception as e:
            logging.info(f"Error updating Google Sheets for {unique_id}: {e}")
            logging.info(f"Traceback: {traceback.format_exc()}")
            logging.info("Google Sheets update failed - data is still saved in CSV")
            
            # Check if we should go offline
            connection_retry_count += 1
            if connection_retry_count >= MAX_RETRY_ATTEMPTS:
                OFFLINE_MODE = True
                logging.warning("Too many consecutive failures - switching to offline mode")
    else:
        logging.info(f"Offline mode: Skipped Google Sheets update for {unique_id}")

    return is_first_scan

def sync_offline_data():
    """
    Sync local CSV data to Google Sheets when connection is restored.
    This function attempts to upload all offline data to Google Sheets.
    """
    if OFFLINE_MODE or not os.path.exists(log_filepath):
        logging.info("No offline data to sync or still in offline mode")
        return False
    
    try:
        df = pd.read_csv(log_filepath)
        logging.info(f"Starting sync of {len(df)} records to Google Sheets...")
        
        sync_success_count = 0
        sync_error_count = 0
        
        # Create a backup of current CSV before syncing
        backup_path = log_filepath.replace('.csv', '_pre_sync_backup.csv')
        try:
            df.to_csv(backup_path, index=False)
            logging.info(f"Created backup at: {backup_path}")
        except Exception as e:
            logging.info(f"Failed to create backup: {e}")
        
        # Add sync tracking columns if they don't exist
        if 'Synced_Sheet1' not in df.columns:
            df['Synced_Sheet1'] = False
        if 'Synced_Sheet2' not in df.columns:
            df['Synced_Sheet2'] = False
        
        for index, row in df.iterrows():
            try:
                unique_id = row['ID']
                if pd.isna(unique_id) or not str(unique_id).strip():
                    continue
                
                unique_id = str(unique_id).strip()
                
                # Sync to Sheet1 (Daily attendance)
                if not row.get('Synced_Sheet1', False):
                    try:
                        # Process each timestamp column for this ID
                        timestamps = []
                        for col in df.columns:
                            if col.startswith('Timestamp') and pd.notna(row[col]):
                                timestamps.append(str(row[col]))
                        
                        if timestamps:
                            success = sync_to_sheet1(unique_id, timestamps)
                            if success:
                                df.loc[index, 'Synced_Sheet1'] = True
                                sync_success_count += 1
                                logging.info(f"✅ Synced {unique_id} to Sheet1 with {len(timestamps)} timestamps")
                            else:
                                logging.info(f"❌ Failed to sync {unique_id} to Sheet1")
                                sync_error_count += 1
                    except Exception as e:
                        logging.info(f"Error syncing {unique_id} to Sheet1: {e}")
                        sync_error_count += 1
                
                # Sync to Sheet2 (Master attendance) - only mark present
                if not row.get('Synced_Sheet2', False):
                    try:
                        success = sync_to_sheet2(unique_id)
                        if success:
                            df.loc[index, 'Synced_Sheet2'] = True
                            logging.info(f"✅ Synced {unique_id} to Sheet2 (marked present)")
                        else:
                            logging.info(f"❌ Failed to sync {unique_id} to Sheet2")
                            sync_error_count += 1
                    except Exception as e:
                        logging.info(f"Error syncing {unique_id} to Sheet2: {e}")
                        sync_error_count += 1
                        
            except Exception as e:
                logging.info(f"Error processing row for {unique_id}: {e}")
                sync_error_count += 1
        
        # Save the updated CSV with sync status
        try:
            df.to_csv(log_filepath, index=False)
            logging.info("✅ Updated CSV with sync status")
        except Exception as e:
            logging.info(f"❌ Failed to save updated CSV: {e}")
        
        logging.info(f"Offline data sync completed: {sync_success_count} successful, {sync_error_count} errors")
        
        # If all data is synced, create a synced backup
        if sync_error_count == 0:
            try:
                synced_backup_path = log_filepath.replace('.csv', '_synced_backup.csv')
                df.to_csv(synced_backup_path, index=False)
                logging.info(f"Created synced backup at: {synced_backup_path}")
            except Exception as e:
                logging.info(f"Failed to create synced backup: {e}")
        
        return sync_error_count == 0
        
    except Exception as e:
        logging.info(f"Critical error syncing offline data: {e}")
        logging.info(f"Traceback: {traceback.format_exc()}")
        return False

def sync_to_sheet1(unique_id, timestamps):
    """
    Sync a specific ID and its timestamps to Sheet1 (Daily attendance).
    
    Args:
        unique_id (str): The ID to sync
        timestamps (list): List of timestamp strings
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get Sheet1 headers
        success, headers, error = safe_sheet_operation(sheet1.row_values, 1)
        if not success:
            logging.info(f"Failed to get Sheet1 headers for sync: {error}")
            return False
        
        # Get all records from Sheet1
        success, all_records, error = safe_sheet_operation(sheet1.get_all_values)
        if not success:
            logging.info(f"Failed to get Sheet1 records for sync: {error}")
            return False
        
        records = all_records[1:] if len(all_records) > 1 else []
        
        # Find ID column index
        try:
            id_col_index = headers.index("ID")
        except ValueError:
            logging.info("ID column not found in Sheet1 headers during sync")
            return False
        
        # Extract all IDs from records
        ids = [row[id_col_index] if len(row) > id_col_index else "" for row in records]
        
        # Check if ID already exists
        if unique_id in ids:
            # Update existing row
            row_index = ids.index(unique_id) + 2  # +2 for 1-based indexing and header row
            
            # Get current row data
            success, row_data, error = safe_sheet_operation(sheet1.row_values, row_index)
            if not success:
                logging.info(f"Failed to get row data for sync: {error}")
                return False
            
            # Add timestamps to empty cells
            timestamp_index = 0
            for col_index in range(id_col_index + 1, len(headers)):
                if timestamp_index < len(timestamps):
                    if col_index < len(row_data):
                        if not row_data[col_index].strip():
                            success, _, error = safe_sheet_operation(
                                sheet1.update_cell, row_index, col_index + 1, timestamps[timestamp_index]
                            )
                            if success:
                                timestamp_index += 1
                            else:
                                logging.info(f"Failed to update cell during sync: {error}")
                    else:
                        # Cell doesn't exist, create it
                        success, _, error = safe_sheet_operation(
                            sheet1.update_cell, row_index, col_index + 1, timestamps[timestamp_index]
                        )
                        if success:
                            timestamp_index += 1
                        else:
                            logging.info(f"Failed to create cell during sync: {error}")
                else:
                    break
            
            # If we have more timestamps than available columns, add them to the end
            if timestamp_index < len(timestamps):
                start_col = len(row_data) + 1
                for i in range(timestamp_index, len(timestamps)):
                    success, _, error = safe_sheet_operation(
                        sheet1.update_cell, row_index, start_col + i - timestamp_index, timestamps[i]
                    )
                    if not success:
                        logging.info(f"Failed to add extra timestamp during sync: {error}")
                        return False
        else:
            # Create new row
            new_row = [""] * len(headers)
            new_row[id_col_index] = unique_id
            
            # Add timestamps
            for i, timestamp in enumerate(timestamps):
                if id_col_index + 1 + i < len(new_row):
                    new_row[id_col_index + 1 + i] = timestamp
            
            row_index = len(records) + 2
            success, _, error = safe_sheet_operation(sheet1.insert_row, new_row, row_index)
            if not success:
                logging.info(f"Failed to insert new row during sync: {error}")
                return False
        
        return True
        
    except Exception as e:
        logging.info(f"Error in sync_to_sheet1 for {unique_id}: {e}")
        return False

def sync_to_sheet2(unique_id):
    """
    Mark an ID as present in Sheet2 (Master attendance) for today's date.
    
    Args:
        unique_id (str): The ID to mark present
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get today's date in the same format as sheet headers
        current_date_str = datetime.now().strftime("%-m/%-d/%Y").lstrip("0")
        
        # Get Sheet2 headers
        success, headers, error = safe_sheet_operation(sheet2.row_values, 1)
        if not success:
            logging.info(f"Failed to get Sheet2 headers for sync: {error}")
            return False
        
        # Find the ID column index
        try:
            id_col_index = headers.index("ID")
        except ValueError:
            logging.info("ID column not found in Sheet2 headers during sync")
            return False
        
        # Find today's date column index
        try:
            date_col_index = headers.index(current_date_str)
        except ValueError:
            logging.info(f"Date column '{current_date_str}' not found in Sheet2 during sync")
            return False
        
        # Get all records from Sheet2
        success, records, error = safe_sheet_operation(sheet2.get_all_values)
        if not success:
            logging.info(f"Failed to get Sheet2 records for sync: {error}")
            return False
        
        data_records = records[1:] if len(records) > 1 else []
        ids = [row[id_col_index] if len(row) > id_col_index else "" for row in data_records]
        
        # Find the person's row and update if found
        if unique_id in ids:
            row_index = ids.index(unique_id) + 2  # +2 for 1-based indexing and header row
            
            # Check current value before updating
            success, current_value, error = safe_sheet_operation(
                sheet2.cell, row_index, date_col_index + 1
            )
            
            if success:
                current_val = current_value.value if hasattr(current_value, 'value') else str(current_value)
                if not current_val or not current_val.strip():
                    # Update the cell to "Present"
                    success, _, error = safe_sheet_operation(
                        sheet2.update_cell, row_index, date_col_index + 1, "Present"
                    )
                    return success
                else:
                    # Already marked present
                    return True
            else:
                logging.info(f"Failed to check current value for {unique_id} during sync: {error}")
                return False
        else:
            logging.info(f"ID {unique_id} not found in Sheet2 during sync")
            return False
            
    except Exception as e:
        logging.info(f"Error in sync_to_sheet2 for {unique_id}: {e}")
        return False

def check_online_status():
    """
    Check if the system can reconnect to Google Sheets and attempt auto-sync.
    
    Returns:
        bool: True if successfully reconnected, False otherwise
    """
    global OFFLINE_MODE, connection_retry_count, last_online_check
    
    current_time = time.time()
    
    # Only check periodically to avoid spam
    if current_time - last_online_check < AUTO_SYNC_INTERVAL:
        return not OFFLINE_MODE
    
    last_online_check = current_time
    
    if not OFFLINE_MODE:
        return True  # Already online
    
    try:
        logging.info("Checking if system can reconnect to Google Sheets...")
        
        # Try to reconnect to Google Sheets
        success, error_message = initialize_google_sheets()
        
        if success:
            logging.info("✅ Successfully reconnected to Google Sheets")
            OFFLINE_MODE = False
            connection_retry_count = 0
            
            # Attempt to sync offline data
            logging.info("🔄 Attempting to sync offline data...")
            sync_result = sync_offline_data()
            
            if sync_result:
                logging.info("✅ Successfully synced all offline data")
                print("🔄 Offline data synced successfully!")
            else:
                logging.info("⚠️ Some offline data may not have synced completely")
                print("⚠️ Partial sync completed - check logs for details")
            
            return True
        else:
            logging.info(f"Still offline: {error_message}")
            return False
            
    except Exception as e:
        logging.info(f"Error checking online status: {e}")
        return False
# ========== QR Code Scanning and Camera Management ==========
# Global variables for scan management
last_scanned_time = {}  # Track last scan time for each ID to prevent spam

def scan_qr():
    """
    Main QR code scanning function with comprehensive error handling.
    This function manages the camera, QR detection, and user interface.
    """
    # Cache sheet data at startup if we're online
    if not OFFLINE_MODE:
        cache_sheet_data()
        
    # ========== Cross-Platform Camera Initialization ==========
    def initialize_camera():
        """Initialize camera with cross-platform compatibility"""
        cap = None
        try:
            logging.info("Initializing camera...")
            
            # Try different camera backends based on platform
            system = platform.system()
            
            if system == "Windows":
                # Windows: Try DirectShow first, then default
                backends = [cv2.CAP_DSHOW, cv2.CAP_ANY]
            elif system == "Darwin":  # macOS
                # macOS: Try AVFoundation first, then default
                backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
            else:  # Linux
                # Linux: Try V4L2 first, then default
                backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            # Try each backend with different camera indices
            for backend in backends:
                for camera_index in range(0, 3):  # Try first 3 cameras
                    try:
                        cap = cv2.VideoCapture(camera_index, backend)
                        if cap.isOpened():
                            # Test if camera actually works
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                logging.info(f"✅ Camera {camera_index} initialized with backend {backend}")
                                return cap
                            else:
                                cap.release()
                    except Exception as e:
                        logging.info(f"Failed camera {camera_index} with backend {backend}: {e}")
                        if cap:
                            cap.release()
                        continue
            
            # If all else fails, try basic initialization
            for camera_index in range(0, 5):
                try:
                    cap = cv2.VideoCapture(camera_index)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            logging.info(f"✅ Camera {camera_index} initialized (fallback)")
                            return cap
                        else:
                            cap.release()
                except Exception:
                    if cap:
                        cap.release()
                    continue
            
            raise Exception("No working camera found on this system")
            
        except Exception as e:
            if cap:
                cap.release()
            raise e
    
    # Initialize camera
    cap = initialize_camera()
    
    # Set optimal camera properties for QR scanning
    try:
        display_config = get_display_config()
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, display_config['video_width'])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, display_config['video_height'])
        cap.set(cv2.CAP_PROP_FPS, 30)
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
        cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
        logging.info("✅ Camera properties optimized for QR scanning")
    except Exception as e:
        logging.info(f"⚠️ Could not optimize camera properties: {e}")
        # Continue anyway with default settings
        
    except Exception as e:
        error_msg = f"Failed to initialize camera: {e}"
        logging.info(error_msg)
        print(f"❌ {error_msg}")
        return
        
    # ========== QR Code Detector Initialization ==========
    try:
        qr_detector = cv2.QRCodeDetector()
        logging.info("✅ QR detector initialized")
    except Exception as e:
        logging.info(f"Failed to initialize QR detector: {e}")
        if cap:
            cap.release()
        return

    # ========== Cross-Platform Window Setup ==========
    def setup_display_window():
        """Setup display window with cross-platform compatibility"""
        try:
            window_name = "QR Scanner"
            cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
            
            # Try to set fullscreen (may not work on all systems)
            try:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                logging.info("✅ Fullscreen mode enabled")
            except Exception as e:
                logging.info(f"⚠️ Fullscreen not available: {e}")
                # Try to maximize window instead
                try:
                    display_config = get_display_config()
                    cv2.resizeWindow(window_name, display_config['screen_width'], display_config['screen_height'])
                    logging.info("✅ Window maximized")
                except Exception as e2:
                    logging.info(f"⚠️ Window resize failed: {e2}")
            
            return window_name
            
        except Exception as e:
            logging.error(f"Failed to create display window: {e}")
            # Create basic window as fallback
            window_name = "QR Scanner"
            cv2.namedWindow(window_name)
            return window_name
    
    # Setup display window
    window_name = setup_display_window()

    # ========== Display Configuration ==========
    print("🎥 QR Scanner Ready")
    if OFFLINE_MODE:
        print("📶 OFFLINE MODE")
    
    # Get display configuration
    display_config = get_display_config()
    logging.info(f"Display config: {display_config}")
    
    # Performance optimization variables
    frame_skip_counter = 0
    qr_detection_cooldown = 0
    fps_counter = 0
    fps_start_time = time.time()
    
    # Message display variables for side panel custom messages
    display_message = ""
    message_start_time = 0

    # ========== Main Scanning Loop ==========
    try:
        while True:
            # Read frame from camera with error handling
            try:
                ret, frame = cap.read()
                if not ret:
                    logging.info("Failed to read frame from camera")
                    break
            except Exception as e:
                logging.info(f"Camera read error: {e}")
                break

            # Frame skipping for performance optimization
            frame_skip_counter += 1
            if frame_skip_counter % 2 != 0:  # Process every other frame
                continue

            try:
                # Resize and enhance frame for better QR detection
                frame_resized = cv2.resize(frame, (display_config['video_width'], display_config['video_height']))
                frame_resized = cv2.convertScaleAbs(frame_resized, alpha=1.1, beta=10)
            except Exception as e:
                logging.info(f"Frame processing error: {e}")
                continue

            # Create log panel for displaying information
            try:
                log_panel = np.zeros((display_config['video_height'], display_config['log_width'], 3), dtype=np.uint8)
                log_panel[:] = (30, 30, 30)  # Dark gray background
            except Exception as e:
                logging.info(f"Log panel creation error: {e}")
                log_panel = np.zeros((display_config['video_height'], 200, 3), dtype=np.uint8)

            current_time = time.time()
            
            # ========== Check Online Status and Auto-Sync ==========
            # Periodically check if we can reconnect and sync offline data
            if OFFLINE_MODE:
                try:
                    online_status = check_online_status()
                    if online_status:
                        # Successfully reconnected and synced
                        logging.info("System reconnected to Google Sheets")
                except Exception as e:
                    logging.info(f"Error checking online status: {e}")
            
            # QR Code Detection with Cooldown Management
            if qr_detection_cooldown > 0:
                qr_detection_cooldown -= 1
            else:
                try:
                    # Attempt QR code detection
                    data, points, _ = qr_detector.detectAndDecode(frame_resized)

                    if points is not None and len(points) > 0 and data:
                        unique_id = data.strip()
                        
                        if not unique_id:  # Skip empty QR codes
                            continue
                            
                        qr_detection_cooldown = 10  # Set cooldown to prevent spam detection

                        # Check if this ID was scanned recently (anti-spam protection)
                        if unique_id in last_scanned_time:
                            elapsed_time = current_time - last_scanned_time[unique_id]
                            if elapsed_time < 18:  # 18 seconds cooldown
                                # Display cooldown warning message in side panel
                                display_message = f"Kam kar {unique_id}"
                                message_start_time = current_time
                                # Only show ID in main terminal
                                print(f"{unique_id}")
                                continue

                        # Update last scanned time
                        last_scanned_time[unique_id] = current_time

                        # Process the attendance update
                        try:
                            is_first_scan = update_attendance(unique_id)
                            
                            # Set custom messages for side panel display
                            if is_first_scan:
                                display_message = f"Ha {unique_id} lagai teri Attendence kam pe lag chal"
                            else:
                                display_message = f"Chal nikal pehli fursat mai nikal {unique_id}"
                            
                            message_start_time = current_time
                            
                            # Only show ID in main terminal after processing
                            print(f"{unique_id}")
                                
                        except Exception as e:
                            logging.info(f"Error processing attendance for {unique_id}: {e}")
                            # Show ID in main terminal even on error
                            print(f"{unique_id}")

                        # Draw green bounding box around detected QR code
                        if points is not None and len(points) > 0:
                            try:
                                points_int = np.int32(points).reshape(-1, 2)
                                cv2.polylines(frame_resized, [points_int], isClosed=True, 
                                            color=(0, 255, 0), thickness=3)
                            except Exception as e:
                                logging.info(f"Error drawing QR bounding box: {e}")

                except Exception as e:
                    logging.info(f"QR detection error: {e}")

            # ========== Display Information on Screen ==========
            try:                
                # Display custom message in side panel if available
                y_offset = 50
                if display_message:
                    # Display the custom message permanently at top of side panel
                    try:
                        # Determine message color based on content
                        if "Kam kar" in display_message:
                            msg_color = (0, 0, 255)  # Red for cooldown warning
                        elif "lagai teri" in display_message:
                            msg_color = (0, 255, 0)  # Green for first scan
                        else:
                            msg_color = (0, 165, 255)  # Orange for repeat scan
                        
                        # Split long message into multiple lines if needed
                        words = display_message.split()
                        lines = []
                        current_line = ""
                        max_chars = 25  # Adjust based on panel width
                        
                        for word in words:
                            if len(current_line + " " + word) <= max_chars:
                                current_line += " " + word if current_line else word
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                        if current_line:
                            lines.append(current_line)
                        
                        # Display message lines permanently
                        for i, line in enumerate(lines):
                            cv2.putText(log_panel, line, (10, y_offset + i * 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, msg_color, 2)
                        
                    except Exception as e:
                        logging.info(f"Error displaying custom message: {e}")
                
                # No scan history display - removed as requested
                # Custom message remains visible until next scan
                
                # Display system status on main camera view (not side panel)
                mode_text = "OFFLINE" if OFFLINE_MODE else "ONLINE"
                status_color = (0, 165, 255) if OFFLINE_MODE else (0, 255, 0)  # Orange if offline, green if online
                
                cv2.putText(frame_resized, f"Status: {mode_text}", (10, 40), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)
                
                # Show sync status if offline
                if OFFLINE_MODE:
                    cv2.putText(frame_resized, "Auto-sync enabled", (10, 200), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
                    cv2.putText(frame_resized, "Press 's' for manual sync", (10, 230), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                else:
                    cv2.putText(frame_resized, "Data synced", (10, 200), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
                
                cv2.putText(frame_resized, "Ready to scan", (10, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (231, 76, 60), 2)
                
                # Display total scans counter on camera view  
                # We'll use a simple counter instead of tracking history
                cv2.putText(frame_resized, "Scans: Active", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                # FPS counter (for performance monitoring)
                fps_counter += 1
                if fps_counter % 30 == 0:  # Update FPS every 30 frames
                    current_fps = 30 / (time.time() - fps_start_time)
                    fps_start_time = time.time()
                    cv2.putText(frame_resized, f"FPS: {current_fps:.1f}", (10, 160), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 1)

            except Exception as e:
                # Log error to file only, don't spam terminal
                logging.info(f"Error updating display information: {e}")
                # Continue running even if display fails

            # ========== Display Combined Frame ==========
            try:
                combined_display = np.hstack((frame_resized, log_panel))
                cv2.imshow(window_name, combined_display)
            except Exception as e:
                logging.info(f"Error displaying combined frame: {e}")
                # Try to display just the camera frame
                try:
                    cv2.imshow(window_name, frame_resized)
                except Exception as e2:
                    logging.info(f"Error displaying camera frame: {e2}")
                    break
            
            # ========== Handle User Input ==========
            try:
                key = cv2.waitKey(30) & 0xFF  # 30ms wait for better responsiveness
                if key == ord("q") or key == 27:  # 'q' or ESC key
                    break
                elif key == ord("s"):  # 's' key - manual sync trigger
                    if OFFLINE_MODE:
                        logging.info("Manual sync triggered by user")
                        print("🔄 Manual sync initiated...")
                        try:
                            online_status = check_online_status()
                            if online_status:
                                print("✅ Manual sync completed successfully!")
                            else:
                                print("❌ Still offline - cannot sync")
                        except Exception as e:
                            logging.info(f"Error in manual sync: {e}")
                            print("❌ Manual sync failed")
                    else:
                        print("ℹ️ Already online - no sync needed")
            except Exception as e:
                logging.info(f"Error handling user input: {e}")

    except KeyboardInterrupt:
        logging.info("Scanner stopped by keyboard interrupt")
    except Exception as e:
        logging.info(f"Critical error in main scanning loop: {e}")
        logging.info(f"Traceback: {traceback.format_exc()}")
        print(f"❌ Scanner error: {e}")
    finally:
        # ========== Cleanup ==========
        try:
            if cap:
                cap.release()
                logging.info("✅ Camera released")
        except Exception as e:
            logging.info(f"Error releasing camera: {e}")
        
        try:
            cv2.destroyAllWindows()
            logging.info("✅ Display windows closed")
        except Exception as e:
            logging.info(f"Error closing windows: {e}")
        
        print("📹 Scanner stopped")
        logging.info("QR scanner stopped successfully")
# ========== Application Entry Point ==========
if __name__ == "__main__":
    try:
        print("🚀 Starting QR Attendance System...")
        if OFFLINE_MODE:
            print("⚠️ Offline mode - CSV only")
            print("🔄 Auto-sync will activate when connection is restored")
            print("💡 Press 's' during scanning for manual sync attempt")
        else:
            print("✅ Online - CSV + Google Sheets")
            
        scan_qr()
        
    except KeyboardInterrupt:
        print("🛑 Stopped")
        logging.info("Application stopped by user (Ctrl+C)")
    except Exception as e:
        logging.info(f"Unexpected error in main application: {e}")
        logging.info(f"Full traceback: {traceback.format_exc()}")
        print(f"❌ Error: {e}")
    finally:
        # ========== Cleanup and Shutdown ==========
        try:
            # Signal background worker to stop
            if not OFFLINE_MODE and 'update_queue' in globals():
                update_queue.put(None)
                logging.info("Background worker shutdown signal sent")
        except Exception as cleanup_error:
            logging.info(f"Error during cleanup: {cleanup_error}")
            
        logging.info("Application shutdown completed")