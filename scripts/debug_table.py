#!/usr/bin/env python3
"""
Debug the exact table structure to understand event positioning
"""

import requests
from bs4 import BeautifulSoup

def debug_table_structure():
    url = "https://us.econoday.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching page...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for table_idx, table in enumerate(tables):
        print(f"\n=== Table {table_idx + 1} ===")
        
        # Get table classes
        table_classes = table.get('class', [])
        print(f"Classes: {table_classes}")
        
        # Check table structure
        rows = table.find_all('tr')
        print(f"Number of rows: {len(rows)}")
        
        # Analyze first few rows
        for row_idx, row in enumerate(rows[:10]):
            print(f"\nRow {row_idx}:")
            cells = row.find_all(['td', 'th'])
            print(f"  Number of cells: {len(cells)}")
            
            for cell_idx, cell in enumerate(cells):
                cell_classes = cell.get('class', [])
                cell_id = cell.get('id', '')
                cell_text = cell.get_text(strip=True)[:50]
                
                # Check for interesting classes
                if any(cls in ['navwkday', 'currentnavwkday', 'events', 'econoevents', 'tabspace'] for cls in cell_classes):
                    print(f"  Cell {cell_idx}: classes={cell_classes}, id={cell_id}, text='{cell_text}'")
                    
                    # If this is an events cell, check its children
                    if 'events' in cell_classes:
                        print(f"    Contains {len(cell.find_all('div', class_='econoevents'))} econoevents divs")
                        event_divs = cell.find_all('div', class_='econoevents')
                        for div_idx, div in enumerate(event_divs[:3]):
                            print(f"    Event {div_idx}: {div.get_text(strip=True)[:60]}")
        
        # If this table looks like the calendar, analyze it in detail
        if any('navwkday' in str(cell.get('class', [])) for row in rows for cell in row.find_all(['td', 'th'])):
            print("\n=== Detailed analysis of calendar table ===")
            for row_idx, row in enumerate(rows):
                print(f"\nRow {row_idx}:")
                cells = row.find_all(['td', 'th'])
                for cell_idx, cell in enumerate(cells):
                    cell_classes = cell.get('class', [])
                    if cell_classes or cell.get_text(strip=True):
                        cell_text = cell.get_text(strip=True)[:30]
                        print(f"  Cell {cell_idx}: classes={cell_classes}, text='{cell_text}'")
                        
                        # Count econoevents in this cell
                        econoevents = cell.find_all(class_=lambda x: x and 'econoevents' in x)
                        if econoevents:
                            print(f"    Contains {len(econoevents)} econoevents")
                            for ev_idx, ev in enumerate(econoevents[:2]):
                                print(f"      Event {ev_idx}: {ev.get_text(strip=True)[:40]}")

if __name__ == "__main__":
    debug_table_structure()