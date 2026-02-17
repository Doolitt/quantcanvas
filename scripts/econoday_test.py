#!/usr/bin/env python3
"""
Test script to examine Econoday HTML structure
"""

import requests
from bs4 import BeautifulSoup
import json

def fetch_econoday_page():
    """Fetch the main Econoday page"""
    url = "https://us.econoday.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        return None
    
    return response.text

def analyze_html_structure(html):
    """Analyze HTML structure to find economic events"""
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n=== Analyzing HTML Structure ===\n")
    
    # Find all links that might be events
    event_links = soup.find_all('a', href=lambda x: x and 'byevent' in x)
    print(f"Found {len(event_links)} links with 'byevent'")
    
    # Print first few links
    for i, link in enumerate(event_links[:10]):
        print(f"{i+1}. {link.get_text(strip=True)[:50]}... -> {link.get('href')}")
    
    # Look for event tables or containers
    print("\n=== Looking for event containers ===\n")
    
    # Check for specific divs or sections
    for div in soup.find_all(['div', 'section', 'table']):
        class_attr = div.get('class', [])
        id_attr = div.get('id', '')
        if any(keyword in str(class_attr) + str(id_attr) for keyword in ['event', 'calendar', 'economic', 'schedule']):
            print(f"Found container: class={class_attr}, id={id_attr}")
            # Print a sample of content
            text_sample = div.get_text(strip=True)[:100]
            print(f"  Sample: {text_sample}...")
    
    # Look for date headers
    print("\n=== Looking for date headers ===\n")
    date_headers = soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
    for header in date_headers:
        text = header.get_text(strip=True)
        if any(date_word in text.lower() for date_word in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'feb', 'jan', 'mar']):
            print(f"Date header: {text}")
    
    # Save sample HTML for manual inspection
    with open('/tmp/econoday_sample.html', 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()[:5000]))
    print("\nSample HTML saved to /tmp/econoday_sample.html")
    
    return soup

def main():
    """Main function"""
    html = fetch_econoday_page()
    if html:
        analyze_html_structure(html)

if __name__ == "__main__":
    main()