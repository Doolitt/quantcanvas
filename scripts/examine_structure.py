#!/usr/bin/env python3
"""
Examine the DOM structure around econoevents elements
"""

import requests
from bs4 import BeautifulSoup

def examine_structure():
    url = "https://us.econoday.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print("Fetching page...")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all econoevents elements
    econoevents = soup.find_all(class_=lambda x: x and 'econoevents' in x)
    print(f"Found {len(econoevents)} econoevents elements")
    
    # Examine first few in detail
    for i in range(min(5, len(econoevents))):
        event = econoevents[i]
        print(f"\n=== Event {i+1} ===")
        print(f"Text: {event.get_text(strip=True)}")
        print(f"Classes: {event.get('class', [])}")
        
        # Print parent hierarchy
        parent = event.parent
        level = 0
        while parent and level < 5:
            print(f"Parent level {level}: {parent.name} class={parent.get('class', [])} id={parent.get('id', '')}")
            parent = parent.parent
            level += 1
        
        # Print siblings
        print("Siblings (before and after):")
        parent = event.parent
        if parent:
            children = list(parent.children)
            try:
                idx = children.index(event)
                # Show 2 siblings before and after
                for j in range(max(0, idx-2), min(len(children), idx+3)):
                    if j == idx:
                        prefix = "-> "
                    else:
                        prefix = "   "
                    sibling = children[j]
                    if hasattr(sibling, 'name'):
                        text = sibling.get_text(strip=True)[:50]
                        print(f"{prefix}{j}: {sibling.name} class={sibling.get('class', [])} - {text}")
            except (ValueError, AttributeError):
                pass
    
    # Look for date headers near events
    print("\n=== Looking for date pattern ===")
    # Search for elements that might be dates
    all_elements = soup.find_all(['span', 'div', 'td', 'th'])
    date_patterns = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Monday', 'Tuesday', 'Wednesday']
    
    date_elements = []
    for elem in all_elements:
        text = elem.get_text(strip=True)
        if any(pattern in text for pattern in date_patterns):
            date_elements.append((elem, text))
    
    print(f"Found {len(date_elements)} date-like elements")
    for elem, text in date_elements[:10]:
        print(f"Date: {text}")
        print(f"  Tag: {elem.name}, class: {elem.get('class', [])}, id: {elem.get('id', '')}")
        
        # Show children
        children = elem.find_all(class_=lambda x: x and 'econoevents' in x)
        if children:
            print(f"  Has {len(children)} econoevents children")
            for child in children[:3]:
                print(f"    - {child.get_text(strip=True)[:50]}")

if __name__ == "__main__":
    examine_structure()