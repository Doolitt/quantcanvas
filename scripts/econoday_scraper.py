#!/usr/bin/env python3
"""
Econoday Economic Calendar Scraper

This script scrapes economic events from https://us.econoday.com/
and stores them in a structured format for the QuantCanvas platform.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json
import csv
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class EconomicEvent:
    """Economic event data structure matching our database schema"""
    source: str = "econoday"
    event_id: str = ""  # Unique identifier from Econoday
    name: str = ""
    time: str = ""  # Format: "08:30 ET"
    date: str = ""  # Format: "2026-02-17"
    country: str = "US"
    importance: int = 1  # 1-5 scale
    category: str = ""  # e.g., "inflation", "employment", "housing", "speech"
    forecast: str = ""
    actual: str = ""
    previous: str = ""
    unit: str = ""
    # Fields to be populated from detail page
    event_url: str = ""
    description: str = ""
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class EconodayScraper:
    """Main scraper class for Econoday economic calendar"""
    
    BASE_URL = "https://us.econoday.com/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Map CSS classes to importance levels
    IMPORTANCE_MAP = {
        'djstar': 5,  # Highest importance (Dow Jones star)
        'star': 4,    # High importance
        'speech': 3,  # Fed speeches
        'delayed': 3, # Delayed data (often important)
        'bullet': 2,  # Regular events
        'default': 1, # Basic events
    }
    
    # Map keywords to categories
    CATEGORY_KEYWORDS = {
        'inflation': ['cpi', 'inflation', 'pce', 'price'],
        'employment': ['employment', 'jobless', 'payroll', 'unemployment', 'wage'],
        'housing': ['housing', 'home', 'starts', 'permits', 'sales', 'mortgage'],
        'manufacturing': ['manufacturing', 'industrial', 'production', 'factory', 'empire', 'philadelphia'],
        'retail': ['retail', 'sales', 'consumer'],
        'confidence': ['confidence', 'sentiment', 'consumer', 'survey'],
        'speech': ['speaks', 'speech', 'testimony', 'testifies'],
        'auction': ['auction', 'bill', 'note', 'bond', 'treasury'],
        'energy': ['petroleum', 'oil', 'gas', 'energy', 'eia'],
        'trade': ['trade', 'import', 'export', 'balance'],
        'gdp': ['gdp', 'gross domestic product'],
        'leading': ['leading', 'indicators'],
        'inventory': ['inventory', 'inventories'],
    }
    
    def __init__(self, base_url=None):
        self.base_url = base_url or self.BASE_URL
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.events: List[EconomicEvent] = []
        self.current_year = datetime.now().year
        
    def fetch_page(self, url: str = None) -> Optional[str]:
        """Fetch HTML content from URL"""
        url = url or self.base_url
        try:
            logger.info(f"Fetching {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def parse_main_page(self, html: str) -> List[EconomicEvent]:
        """Parse main Econoday page to extract events"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Find the events table
        events_table = soup.find('div', class_='eventstable')
        if not events_table:
            logger.error("Could not find events table")
            return events
        
        # Extract current dates from the page
        date_spans = events_table.find_all('span', class_='dateheader')
        current_dates = {}
        
        # We'll track which date we're currently parsing
        current_date = None
        date_pattern = re.compile(r'(\w+)\s+(\w+)\s+(\d+)')
        
        # Parse all rows/containers
        for element in events_table.find_all(['div', 'span']):
            # Check if this is a date header
            element_classes = element.get('class', [])
            element_text = element.get_text(strip=True)
            
            # Look for date headers
            if 'dateheader' in element_classes:
                match = date_pattern.search(element_text)
                if match:
                    day_name, month_name, day_num = match.groups()
                    # Convert to proper date (we'll need to handle year)
                    # For now, use current year and approximate month
                    month_map = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    if month_name in month_map:
                        current_date = f"{self.current_year}-{month_map[month_name]:02d}-{int(day_num):02d}"
                        logger.info(f"Parsing events for {current_date} ({day_name})")
            
            # Check if this is an event container
            if 'econoevents' in element_classes:
                if not current_date:
                    logger.warning("Found event but no current date set")
                    continue
                    
                event = self.parse_event_element(element, current_date)
                if event:
                    events.append(event)
        
        logger.info(f"Parsed {len(events)} events from main page")
        return events
    
    def parse_event_element(self, element, event_date: str) -> Optional[EconomicEvent]:
        """Parse a single event element"""
        try:
            # Extract event text
            event_text = element.get_text(strip=True)
            if not event_text:
                return None
            
            # Parse event name and time
            event_name, event_time = self.parse_event_text(event_text)
            if not event_name:
                return None
            
            # Create event ID from name and date
            event_id = f"{event_date}_{event_name.replace(' ', '_').lower()}"
            
            # Determine importance from CSS classes
            element_classes = element.get('class', [])
            importance = self.determine_importance(element_classes)
            
            # Determine category from event name
            category = self.determine_category(event_name)
            
            # Check if this is a speech
            is_speech = 'speech' in element_classes
            
            # Extract event URL if available
            event_url = ""
            link = element.find('a')
            if link and link.get('href'):
                event_url = self.BASE_URL.rstrip('/') + '/' + link.get('href')
            
            # Create event object
            event = EconomicEvent(
                event_id=event_id,
                name=event_name,
                time=event_time,
                date=event_date,
                importance=importance,
                category=category,
                event_url=event_url,
            )
            
            logger.debug(f"Parsed event: {event_name} at {event_time} (importance: {importance})")
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event element: {e}")
            return None
    
    def parse_event_text(self, text: str) -> Tuple[str, str]:
        """Parse event text to extract name and time"""
        # Common time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*[AP]M\s*ET)',  # 8:30 AM ET
            r'(\d{1,2}:\d{2}\s*[AP]M)',       # 8:30 AM
            r'(\d{1,2}\s*[AP]M\s*ET)',        # 8 AM ET
        ]
        
        event_time = ""
        event_name = text
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                event_time = match.group(1).strip()
                # Remove time from event name
                event_name = text[:match.start()].strip()
                break
        
        # If no time found, check for all day events
        if not event_time:
            # Check for settlement events (no specific time)
            if 'settlement' in text.lower():
                event_time = "All Day"
            else:
                event_time = "Time TBD"
        
        # Clean up event name
        event_name = re.sub(r'\s+', ' ', event_name).strip()
        
        return event_name, event_time
    
    def determine_importance(self, classes: List[str]) -> int:
        """Determine importance level from CSS classes"""
        for cls in classes:
            if cls in self.IMPORTANCE_MAP:
                return self.IMPORTANCE_MAP[cls]
        return self.IMPORTANCE_MAP['default']
    
    def determine_category(self, event_name: str) -> str:
        """Determine category from event name keywords"""
        event_name_lower = event_name.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in event_name_lower:
                    return category
        
        # Default categories based on event type
        if any(word in event_name_lower for word in ['speaks', 'speech', 'testimony']):
            return 'speech'
        elif any(word in event_name_lower for word in ['auction', 'bill', 'note', 'bond']):
            return 'auction'
        elif any(word in event_name_lower for word in ['settlement']):
            return 'settlement'
        
        return 'other'
    
    def fetch_event_details(self, event: EconomicEvent) -> EconomicEvent:
        """Fetch detailed information from event page"""
        if not event.event_url:
            return event
        
        try:
            logger.info(f"Fetching details for {event.name}")
            html = self.fetch_page(event.event_url)
            if not html:
                return event
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try to find forecast, actual, previous values
            # This will need to be customized based on actual page structure
            # For now, we'll just extract some basic info
            
            # Look for description
            description_div = soup.find('div', class_='eventdescription')
            if description_div:
                event.description = description_div.get_text(strip=True)[:500]
            
            # Look for data tables
            tables = soup.find_all('table')
            for table in tables:
                # Simple parsing - can be enhanced based on actual structure
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        header = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)
                        
                        if 'forecast' in header:
                            event.forecast = value
                        elif 'actual' in header:
                            event.actual = value
                        elif 'previous' in header:
                            event.previous = value
                        elif 'unit' in header or 'measure' in header:
                            event.unit = value
            
            logger.debug(f"Fetched details for {event.name}")
            
        except Exception as e:
            logger.error(f"Error fetching event details: {e}")
        
        return event
    
    def scrape(self, fetch_details: bool = False) -> List[EconomicEvent]:
        """Main scraping method"""
        logger.info("Starting Econoday scraper")
        
        # Fetch main page
        html = self.fetch_page()
        if not html:
            logger.error("Failed to fetch main page")
            return []
        
        # Parse main page
        self.events = self.parse_main_page(html)
        
        # Fetch details if requested
        if fetch_details and self.events:
            logger.info(f"Fetching details for {len(self.events)} events")
            detailed_events = []
            for i, event in enumerate(self.events):
                detailed_event = self.fetch_event_details(event)
                detailed_events.append(detailed_event)
                
                # Be polite - delay between requests
                if i < len(self.events) - 1:
                    time.sleep(1)  # 1 second delay
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Fetched details for {i + 1}/{len(self.events)} events")
            
            self.events = detailed_events
        
        logger.info(f"Scraping complete. Found {len(self.events)} events.")
        return self.events
    
    def save_to_json(self, filepath: str = "econoday_events.json"):
        """Save events to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump([event.to_dict() for event in self.events], f, indent=2, default=str)
        logger.info(f"Saved {len(self.events)} events to {filepath}")
    
    def save_to_csv(self, filepath: str = "econoday_events.csv"):
        """Save events to CSV file"""
        if not self.events:
            logger.warning("No events to save")
            return
        
        fieldnames = list(self.events[0].to_dict().keys())
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for event in self.events:
                writer.writerow(event.to_dict())
        logger.info(f"Saved {len(self.events)} events to {filepath}")
    
    def print_summary(self):
        """Print summary of scraped events"""
        print(f"\n=== Econoday Scraper Summary ===")
        print(f"Total events: {len(self.events)}")
        
        if self.events:
            print(f"\nSample events:")
            for i, event in enumerate(self.events[:5]):
                print(f"{i+1}. {event.date} {event.time} - {event.name} (Importance: {event.importance})")
            
            # Count by importance
            importance_counts = {}
            for event in self.events:
                importance_counts[event.importance] = importance_counts.get(event.importance, 0) + 1
            
            print(f"\nEvents by importance:")
            for importance in sorted(importance_counts.keys()):
                count = importance_counts[importance]
                print(f"  Level {importance}: {count} events")
            
            # Count by category
            category_counts = {}
            for event in self.events:
                category_counts[event.category] = category_counts.get(event.category, 0) + 1
            
            print(f"\nEvents by category:")
            for category in sorted(category_counts.keys()):
                count = category_counts[category]
                print(f"  {category}: {count} events")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape economic events from Econoday")
    parser.add_argument("--fetch-details", action="store_true", help="Fetch detailed event information")
    parser.add_argument("--output-json", type=str, help="Output JSON file path")
    parser.add_argument("--output-csv", type=str, help="Output CSV file path")
    parser.add_argument("--print-summary", action="store_true", help="Print summary to console")
    
    args = parser.parse_args()
    
    # Create and run scraper
    scraper = EconodayScraper()
    events = scraper.scrape(fetch_details=args.fetch_details)
    
    # Save outputs
    if args.output_json:
        scraper.save_to_json(args.output_json)
    elif args.output_csv:
        scraper.save_to_csv(args.output_csv)
    else:
        # Default output
        scraper.save_to_json("econoday_events.json")
        scraper.save_to_csv("econoday_events.csv")
    
    # Print summary
    if args.print_summary or not (args.output_json or args.output_csv):
        scraper.print_summary()

if __name__ == "__main__":
    main()