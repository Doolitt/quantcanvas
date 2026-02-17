#!/usr/bin/env python3
"""
Test script to fix URLs and fetch event details from Econoday
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time

def fix_relative_url(url: str) -> str:
    """Convert relative URL to absolute URL"""
    if not url:
        return ""
    
    BASE_URL = "https://us.econoday.com/"
    
    # If already absolute, return as-is
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    # If starts with /, prepend base URL
    if url.startswith('/'):
        return BASE_URL.rstrip('/') + url
    
    # If it's like "byevent?fid=...", prepend base URL
    if url.startswith('byevent') or url.startswith('byshoweventarticle'):
        return BASE_URL.rstrip('/') + '/' + url
    
    # Otherwise return as-is (might be invalid)
    return url

def fetch_event_details_test(event_url: str):
    """Test fetching details from an event page"""
    if not event_url:
        print("No URL provided")
        return {}
    
    # Fix URL if needed
    event_url = fix_relative_url(event_url)
    print(f"Fetching: {event_url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(event_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize result dict
        details = {
            'forecast': '',
            'actual': '', 
            'previous': '',
            'unit': '',
            'description': ''
        }
        
        # Look for eventdescription
        desc_div = soup.find('div', class_='eventdescription')
        if desc_div:
            details['description'] = desc_div.get_text(strip=True)[:500]
        
        # Look for data in tables - Econoday has specific table structure
        # Try to find the main data table
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables on page")
        
        for table_idx, table in enumerate(tables):
            # Check if this looks like a data table
            rows = table.find_all('tr')
            
            # Look for forecast, actual, previous in table cells
            for row in rows:
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Check if this row contains forecast/actual/previous data
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True).lower()
                    
                    if 'forecast' in cell_text and i + 1 < len(cells):
                        details['forecast'] = cells[i + 1].get_text(strip=True)
                    elif 'actual' in cell_text and i + 1 < len(cells):
                        details['actual'] = cells[i + 1].get_text(strip=True)
                    elif 'previous' in cell_text and i + 1 < len(cells):
                        details['previous'] = cells[i + 1].get_text(strip=True)
                    elif 'unit' in cell_text and i + 1 < len(cells):
                        details['unit'] = cells[i + 1].get_text(strip=True)
        
        # Also check for specific Econoday data structure
        # Look for elements with class 'data'
        data_elements = soup.find_all(class_=lambda x: x and 'data' in str(x).lower())
        for elem in data_elements:
            elem_text = elem.get_text(strip=True)
            parent_text = elem.parent.get_text(strip=True) if elem.parent else ""
            
            # Try to extract forecast/actual from text patterns
            if 'forecast' in parent_text.lower() and not details['forecast']:
                details['forecast'] = elem_text
            elif 'actual' in parent_text.lower() and not details['actual']:
                details['actual'] = elem_text
            elif 'previous' in parent_text.lower() and not details['previous']:
                details['previous'] = elem_text
        
        print(f"Extracted details: {details}")
        return details
        
    except Exception as e:
        print(f"Error fetching details: {e}")
        return {}

def test_url_fixing():
    """Test URL fixing function"""
    test_urls = [
        "",
        "byevent?fid=684873&year=2026&lid=0#top",
        "/byevent?fid=684873&year=2026&lid=0#top", 
        "https://us.econoday.com/byshoweventarticle?fid=684807&year=2026&lid=0#top",
        "byshoweventarticle?fid=684807&year=2026&lid=0#top"
    ]
    
    print("=== Testing URL Fixing ===")
    for url in test_urls:
        fixed = fix_relative_url(url)
        print(f"Original: {url}")
        print(f"Fixed:    {fixed}")
        print()

def test_detail_fetching():
    """Test fetching details from sample event pages"""
    print("\n=== Testing Detail Fetching ===")
    
    # Test with a few sample URLs
    sample_urls = [
        "byevent?fid=667186&year=2026&lid=0#top",  # Retail Sales
        "byevent?fid=671173&year=2026&lid=0#top",  # Empire State Manufacturing
        "https://us.econoday.com/byshoweventarticle?fid=684807&year=2026&lid=0#top"  # Global Economics
    ]
    
    for url in sample_urls:
        print(f"\n--- Testing: {url} ---")
        details = fetch_event_details_test(url)
        print(f"Results: {details}")
        time.sleep(2)  # Be polite

def main():
    """Main test function"""
    test_url_fixing()
    test_detail_fetching()

if __name__ == "__main__":
    main()