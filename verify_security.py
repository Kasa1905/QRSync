#!/usr/bin/env python3
"""
Security Verification Script
============================
Checks that no sensitive data is present in the public repository.
"""

import os
import re
import json

def check_file_for_sensitive_data(filepath):
    """Check a file for sensitive data patterns"""
    sensitive_patterns = [
        r'[0-9]{12,}',  # Long numbers (could be IDs)
        r'[A-Za-z0-9]{20,}',  # Long alphanumeric strings
        r'-----BEGIN [A-Z]+ KEY-----',  # Private keys (more specific)
        r'\"private_key\":\s*\"[^\"]+\"',  # Private key in JSON
        r'\.iam\.gserviceaccount\.com',  # Service account emails
        r'1[A-Za-z0-9_-]{43}',  # Google Sheet IDs pattern
    ]
    
    whitelist_patterns = [
        r'YOUR_.*_HERE',  # Our placeholder text
        r'your-.*',  # Our placeholder text
        r'-----BEGIN.*KEY-----',  # Pattern itself (in this security script)
        r'sensitive_patterns',  # Variable name in security script
        r'\"private_key\":\s*\"',  # Pattern definition in security script
        r'example\.com',  # Example domains
        r'ServiceAccountCredentials',  # Import statement
        r'oauth2client\.service_account',  # Import path
    ]
    
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # Check if it's whitelisted
                    is_whitelisted = any(re.search(wp, match) for wp in whitelist_patterns)
                    if not is_whitelisted:
                        issues.append(f"Line {line_num}: Potential sensitive data: {match}")
    
    except Exception as e:
        issues.append(f"Error reading file: {e}")
    
    return issues

def verify_repository_security():
    """Verify that the repository contains no sensitive data"""
    print("🔍 Verifying repository security...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to check
    files_to_check = [
        'app.py',
        'setup.py',
        'create_package.py',
        'README.md',
        'PROJECT_README.md',
        'SETUP_INSTRUCTIONS.md',
        'DEPLOYMENT_GUIDE.md',
        'requirements.txt',
        'verify_security.py'
    ]
    
    # Files that should NOT exist
    sensitive_files = [
        'new-creds.json',
        'creds.json',
        'credentials.json',
        'service-account.json',
        'attendance_system.log',
        '.env',
        'config.py'
    ]
    
    # Check for sensitive files
    print("\n📁 Checking for sensitive files...")
    for sensitive_file in sensitive_files:
        filepath = os.path.join(script_dir, sensitive_file)
        if os.path.exists(filepath):
            print(f"❌ SECURITY ISSUE: Found sensitive file: {sensitive_file}")
        else:
            print(f"✅ OK: No sensitive file: {sensitive_file}")
    
    # Check file contents
    print("\n📄 Checking file contents...")
    total_issues = 0
    
    for filename in files_to_check:
        filepath = os.path.join(script_dir, filename)
        if os.path.exists(filepath):
            issues = check_file_for_sensitive_data(filepath)
            if issues:
                print(f"❌ ISSUES in {filename}:")
                for issue in issues:
                    print(f"    {issue}")
                total_issues += len(issues)
            else:
                print(f"✅ OK: {filename}")
        else:
            print(f"⚠️ Missing: {filename}")
    
    # Check for required template files
    print("\n📋 Checking for required template files...")
    required_templates = [
        'new-creds.json.template',
        '.gitignore',
        'LICENSE'
    ]
    
    for template in required_templates:
        filepath = os.path.join(script_dir, template)
        if os.path.exists(filepath):
            print(f"✅ OK: {template}")
        else:
            print(f"❌ Missing: {template}")
    
    # Final summary
    print("\n" + "="*50)
    if total_issues == 0:
        print("🎉 SECURITY VERIFICATION PASSED!")
        print("✅ Repository is clean and ready for public release")
    else:
        print(f"❌ SECURITY VERIFICATION FAILED!")
        print(f"Found {total_issues} potential security issues")
        print("Please review and fix before publishing")
    
    return total_issues == 0

if __name__ == "__main__":
    verify_repository_security()
