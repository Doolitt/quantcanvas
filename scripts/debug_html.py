#!/usr/bin/env python3
"""
Debug HTML structure of Econoday page
"""

import requests
from bs4 import BeautifulSoup
import re

def fetch_and_debug():
    url = "https://us.econoday.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching page...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Save full HTML for inspection
    with open('/tmp/econoday_full.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))
    print("Full HTML saved to /tmp/econoday_full.html")
    
    # Look for eventstable div
    print("\n=== Searching for 'eventstable' ===")
    eventstable = soup.find('div', class_='eventstable')
    if eventstable:
        print("Found eventstable div")
        print(f"Classes: {eventstable.get('class', [])}")
        print(f"Sample content (first 500 chars):")
        print(str(eventstable)[:500])
    else:
        print("No eventstable div found")
        # Look for any div with event in class
        all_divs = soup.find_all('div')
        for div in all_divs:
            classes = div.get('class', [])
            if classes and any('event' in str(c).lower() for c in classes):
                print(f"Found div with event-related class: {classes}")
                print(f"Content sample: {div.get_text(strip=True)[:100]}...")
                break
    
    # Look for date headers
    print("\n=== Searching for date headers ===")
    date_headers = soup.find_all(['span', 'div'], class_=re.compile(r'.*date.*', re.I))
    for dh in date_headers[:10]:
        print(f"Date header: classes={dh.get('class', [])}, text={dh.get_text(strip=True)[:50]}")
    
    # Look for econoevents
    print("\n=== Searching for econoevents ===")
    econoevents = soup.find_all(class_=re.compile(r'.*econoevents.*', re.I))
    print(f"Found {len(econoevents)} elements with econoevents in class")
    for i, ee in enumerate(econoevents[:5]):
        classes = ee.get('class', [])
        text = ee.get_text(strip=True)
        print(f"{i+1}. Classes: {classes}")
        print(f"   Text: {text[:80]}...")
    
    # Look for the main calendar table/container
    print("\n=== Looking for main container ===")
    # Check for tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    for i, table in enumerate(tables[:3]):
        print(f"Table {i+1}: classes={table.get('class', [])}")
        # Get first row sample
        first_row = table.find('tr')
        if first_row:
            print(f"  First row: {first_row.get_text(strip=True)[:100]}...")
    
    # Check for specific IDs
    print("\n=== Checking for specific IDs ===")
    for elem in soup.find_all(id=True):
        elem_id = elem.get('id', '')
        if any(keyword in elem_id.lower() for keyword in ['calendar', 'event', 'economic', 'table']):
            print(f"Found ID: {elem_id}, tag: {elem.name}")
            print(f"  Sample: {elem.get_text(strip=True)[:100]}...")

if __name__ == "__main__":
    fetch_and_debug()