#!/usr/bin/env python3
"""
Update all stock API files to use akshare_client
"""
import re
import os

# Files to update
api_files = [
    'stock_a_share_api_complete.py',
    'stock_historical_data_api.py',
    'stock_individual_info_api.py',
    'stock_minute_data_api.py',
    'stock_quotes_api.py',
    'stock_realtime_data_api.py',
    'stock_tick_data_api.py',
]

def add_import(content):
    """Add import for akshare_client"""
    # Find the import section
    import_pattern = r'(import requests\nimport pandas as pd)'
    replacement = r'\1\nfrom akshare_client import call_aktools_api'
    return re.sub(import_pattern, replacement, content)

def update_function_call(content):
    """Replace hardcoded URLs with call_aktools_api"""
    # Pattern 1: Simple GET requests without params
    pattern1 = r'''url = "http://127\.0\.0\.1:8080(/api/public/[^"]+)"\s+try:\s+response = requests\.get\(url\)\s+response\.raise_for_status\(\)\s+data = response\.json\(\)\s+return pd\.DataFrame\(data\)\s+except requests\.exceptions\.RequestException as e:\s+print\(f"请求失败: \{e\}"\)\s+return pd\.DataFrame\(\)'''

    # Pattern 2: GET requests with params
    pattern2 = r'''url = "http://127\.0\.0\.1:8080(/api/public/[^"]+)"\s+params = \{([^}]+)\}\s+try:\s+response = requests\.get\(url, params=params\)\s+response\.raise_for_status\(\)\s+data = response\.json\(\)\s+return pd\.DataFrame\(data\)\s+except requests\.exceptions\.RequestException as e:\s+print\(f"请求失败: \{e\}"\)\s+return pd\.DataFrame\(\)'''

    # Replace pattern 1
    content = re.sub(pattern1, r'return call_aktools_api("\1")', content, flags=re.DOTALL)

    # Replace pattern 2
    content = re.sub(pattern2, r'return call_aktools_api("\1", params={\2})', content, flags=re.DOTALL)

    return content

def process_file(filepath):
    """Process a single API file"""
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already updated
    if 'from akshare_client import call_aktools_api' in content:
        print(f"  → Already updated, skipping")
        return

    # Add import
    content = add_import(content)

    # Update function calls
    content = update_function_call(content)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  → Updated successfully")

def main():
    os.chdir('/srv/samba/Shared/Projects/akshare-api')
    for filename in api_files:
        filepath = f'/srv/samba/Shared/Projects/akshare-api/{filename}'
        if os.path.exists(filepath):
            process_file(filepath)
        else:
            print(f"File not found: {filepath}")

if __name__ == '__main__':
    main()
