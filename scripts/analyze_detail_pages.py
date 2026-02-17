#!/usr/bin/env python3
"""
Analyze Econoday detail page structure to find forecast/actual data
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin

BASE_URL = "https://us.econoday.com/"

def fix_url(url: str) -> str:
    """Convert relative URL to absolute"""
    if not url:
        return ""
    
    if url.startswith('http://') or url.startswith('https://'):
        return url
    
    if url.startswith('/'):
        return urljoin(BASE_URL, url)
    
    # Handle byevent, byshoweventarticle, etc.
    return urljoin(BASE_URL, url)

def fetch_and_analyze(url: str, event_name: str):
    """Fetch detail page and analyze its structure"""
    if not url:
        print(f"No URL for {event_name}")
        return
    
    url = fix_url(url)
    print(f"\n{'='*60}")
    print(f"Analyzing: {event_name}")
    print(f"URL: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Failed to fetch: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save HTML for manual inspection
        filename = f"/tmp/econoday_{event_name.replace(' ', '_').replace('/', '_')[:50]}.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print(f"HTML saved to: {filename}")
        
        # Look for specific structures
        
        print("\n1. Looking for eventdescription div:")
        desc_div = soup.find('div', class_='eventdescription')
        if desc_div:
            text = desc_div.get_text(strip=True)[:200]
            print(f"   Found: {text}")
        else:
            print("   Not found")
        
        print("\n2. Looking for tables:")
        tables = soup.find_all('table')
        print(f"   Found {len(tables)} tables")
        
        for i, table in enumerate(tables[:3]):  # Analyze first 3 tables
            rows = table.find_all('tr')
            print(f"   Table {i+1}: {len(rows)} rows")
            
            # Look for forecast/actual/previous in table cells
            for row_idx, row in enumerate(rows[:5]):  # First 5 rows
                cells = row.find_all(['td', 'th'])
                if cells:
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    # Check if any cell contains forecast/actual keywords
                    for cell_text in cell_texts:
                        if any(keyword in cell_text.lower() for keyword in ['forecast', 'actual', 'previous', 'consensus', 'prior', 'revised']):
                            print(f"     Row {row_idx}: {cell_texts}")
                            break
        
        print("\n3. Looking for specific classes with 'data', 'value', 'forecast', etc.:")
        interesting_classes = ['data', 'value', 'forecast', 'actual', 'previous', 'consensus', 'prior']
        for cls in interesting_classes:
            elements = soup.find_all(class_=lambda x: x and cls in str(x).lower())
            if elements:
                print(f"   Class '{cls}': Found {len(elements)} elements")
                for elem in elements[:2]:  # First 2
                    parent_text = elem.parent.get_text(strip=True)[:100] if elem.parent else ""
                    print(f"     Element: {elem.get_text(strip=True)[:50]} | Parent: {parent_text}")
        
        print("\n4. Looking for divs with event data:")
        # Common Econoday patterns
        event_divs = soup.find_all('div', class_=lambda x: x and any(
            word in str(x).lower() for word in ['event', 'detail', 'data', 'release', 'schedule']
        ))
        print(f"   Found {len(event_divs)} event-related divs")
        for div in event_divs[:3]:
            div_text = div.get_text(strip=True)[:150]
            print(f"     Div: {div_text}")
        
        print("\n5. Looking for meta/og tags with data:")
        meta_tags = soup.find_all(['meta', 'og:title', 'og:description'])
        for tag in meta_tags:
            content = tag.get('content', '') or tag.get('property', '') or ''
            if any(keyword in content.lower() for keyword in ['forecast', 'actual', 'consensus']):
                print(f"   Meta: {content[:100]}")
        
        print("\n6. Full page text analysis (keywords):")
        full_text = soup.get_text()
        keywords = ['forecast', 'actual', 'previous', 'consensus', 'survey', 'estimate', 'expected']
        for keyword in keywords:
            count = full_text.lower().count(keyword)
            if count > 0:
                # Find context around keyword
                matches = re.finditer(rf'.{{0,50}}{keyword}.{{0,50}}', full_text, re.IGNORECASE)
                for match in list(matches)[:2]:  # First 2 matches
                    print(f"   '{keyword}': {match.group()}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Analyze different types of event detail pages"""
    
    # Load scraped events
    try:
        with open('econoday_events.json', 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        print("econoday_events.json not found. Run scraper first.")
        return
    
    print(f"Loaded {len(events)} events")
    
    # Select sample events of different types
    sample_events = []
    
    # Look for different event types
    event_types = {
        'retail': 'Retail Sales',
        'speech': 'Speaks',  
        'auction': 'Auction',
        'settlement': 'Settlement',
        'manufacturing': 'Manufacturing',
        'housing': 'Housing'
    }
    
    for event in events:
        event_name = event.get('name', '').lower()
        event_url = event.get('event_url', '')
        
        # Categorize and collect samples
        if not event_url:
            continue
            
        for etype, keyword in event_types.items():
            if keyword.lower() in event_name and etype not in [s[0] for s in sample_events]:
                sample_events.append((etype, event['name'], event_url))
                break
        
        # Also get first few events for general analysis
        if len(sample_events) < 3:
            sample_events.append(('general', event['name'], event_url))
    
    print(f"\nSelected {len(sample_events)} sample events for analysis:")
    for etype, name, url in sample_events:
        print(f"  {etype}: {name}")
    
    # Analyze each sample
    for etype, name, url in sample_events:
        fetch_and_analyze(url, f"{etype}_{name}")
        time.sleep(2)  # Be polite

if __name__ == "__main__":
    main()