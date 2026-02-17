#!/usr/bin/env python3
"""
Econoday Economic Calendar Scraper - Version 3

Updated with correct table structure parsing:
- Dates and events are in the SAME row
- Date cells at indices 49-53, event cells at indices 54-58 (5-cell offset)
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
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
    time: str = ""  # Format: "08:30 AM ET"
    date: str = ""  # Format: "2026-02-17"
    country: str = "US"
    importance: int = 1  # 1-5 scale
    category: str = ""  # e.g., "inflation", "employment", "housing", "speech"
    forecast: str = ""
    actual: str = ""
    previous: str = ""
    unit: str = ""
    # Fields from detail page
    event_url: str = ""
    description: str = ""
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

class EconodayScraperV3:
    """Updated scraper for Econoday's actual table structure"""
    
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
        'djstar': 5,  # Dow Jones star - highest importance
        'star': 4,    # Regular star - high importance
        'speech': 3,  # Fed speeches - medium-high importance
        'delayed': 3, # Delayed data releases
        'bullet': 2,  # Regular events with bullet
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
        'auction': ['auction', 'bill', 'note', 'bond', 'treasury', 'tips'],
        'energy': ['petroleum', 'oil', 'gas', 'energy', 'eia'],
        'trade': ['trade', 'import', 'export', 'balance', 'international'],
        'gdp': ['gdp', 'gross domestic product'],
        'leading': ['leading', 'indicators'],
        'inventory': ['inventory', 'inventories'],
        'settlement': ['settlement'],
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
        """Parse main Econoday page using correct table structure"""
        soup = BeautifulSoup(html, 'html.parser')
        events = []
        
        # Find the main calendar table (table with class 'tablewrapper')
        calendar_table = soup.find('table', class_='tablewrapper')
        if not calendar_table:
            # Fallback: look for any table with date cells
            logger.warning("Could not find table with class 'tablewrapper'")
            tables = soup.find_all('table')
            for table in tables:
                if table.find(['td', 'th'], class_=lambda x: x and 'navwkday' in x):
                    calendar_table = table
                    break
        
        if not calendar_table:
            logger.error("Could not find calendar table")
            return self.fallback_parse(soup)
        
        # Find all rows in the table
        rows = calendar_table.find_all('tr')
        logger.info(f"Found {len(rows)} rows in calendar table")
        
        # Look for the row that contains both dates and events
        date_event_row = None
        for row in rows:
            # Check if this row has date cells
            date_cells = row.find_all(['td', 'th'], class_=lambda x: x and ('navwkday' in x or 'currentnavwkday' in x))
            if date_cells:
                # Also check if this row has event cells
                event_cells = row.find_all(['td', 'th'], class_=lambda x: x and 'events' in x)
                if event_cells:
                    date_event_row = row
                    logger.info(f"Found row with {len(date_cells)} date cells and {len(event_cells)} event cells")
                    break
        
        if not date_event_row:
            logger.error("Could not find row with both dates and events")
            return self.fallback_parse(soup)
        
        # Extract all cells from this row
        cells = date_event_row.find_all(['td', 'th'])
        logger.info(f"Row has {len(cells)} total cells")
        
        # Find date cells and map them to their indices
        date_indices = {}
        for idx, cell in enumerate(cells):
            cell_classes = cell.get('class', [])
            if 'navwkday' in cell_classes or 'currentnavwkday' in cell_classes:
                date_text = cell.get_text(strip=True)
                parsed_date = self.parse_date_text(date_text)
                if parsed_date:
                    date_indices[idx] = {
                        'date': parsed_date,
                        'original_text': date_text,
                        'is_today': 'currentnavwkday' in cell_classes
                    }
        
        if not date_indices:
            logger.error("Could not find any date cells")
            return self.fallback_parse(soup)
        
        logger.info(f"Found {len(date_indices)} date cells at indices: {list(date_indices.keys())}")
        
        # Find event cells and map them to dates
        # Based on analysis: events are 5 cells after dates in the same row
        for date_idx, date_info in date_indices.items():
            event_cell_idx = date_idx + 5  # Events are 5 cells after dates
            
            if event_cell_idx < len(cells):
                event_cell = cells[event_cell_idx]
                if 'events' in event_cell.get('class', []):
                    events_for_date = self.extract_events_from_cell(event_cell, date_info['date'])
                    events.extend(events_for_date)
                    logger.info(f"Found {len(events_for_date)} events for {date_info['date']}")
                else:
                    logger.warning(f"Cell at index {event_cell_idx} is not an events cell (classes: {event_cell.get('class', [])})")
            else:
                logger.warning(f"Event cell index {event_cell_idx} out of range for {date_info['date']}")
        
        logger.info(f"Parsed {len(events)} events from main page")
        return events
    
    def parse_date_text(self, date_text: str) -> Optional[str]:
        """Parse date text like 'Monday Feb 16' to '2026-02-16'"""
        # Clean up non-breaking spaces
        date_text = date_text.replace('\xa0', ' ')
        
        # Pattern: "Monday Feb 16" or "Tuesday Feb 17"
        pattern = r'(\w+)\s+(\w+)\s+(\d+)'
        match = re.search(pattern, date_text)
        
        if match:
            day_of_week, month_str, day_str = match.groups()
            
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            
            if month_str in month_map and day_str.isdigit():
                month = month_map[month_str]
                day = int(day_str)
                
                # Determine year (assume current year for now)
                # TODO: Handle year boundaries (December/January transition)
                year = self.current_year
                
                # Quick sanity check: if month is December and we're in January, adjust year
                current_month = datetime.now().month
                if month == 12 and current_month == 1:
                    year -= 1
                elif month == 1 and current_month == 12:
                    year += 1
                
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        return None
    
    def extract_events_from_cell(self, cell, date_str: str) -> List[EconomicEvent]:
        """Extract all events from an events cell"""
        events = []
        
        # Find all econoevents divs in this cell
        event_divs = cell.find_all('div', class_=lambda x: x and 'econoevents' in x)
        
        for div in event_divs:
            event = self.parse_event_div(div, date_str)
            if event:
                events.append(event)
        
        return events
    
    def parse_event_div(self, div, date_str: str) -> Optional[EconomicEvent]:
        """Parse a single econoevents div"""
        try:
            # Extract event text
            event_text = div.get_text(strip=True)
            if not event_text:
                return None
            
            # Parse event name and time
            event_name, event_time = self.parse_event_text(event_text)
            if not event_name:
                return None
            
            # Create event ID
            event_id = f"econoday_{date_str}_{event_name.replace(' ', '_').lower()[:50]}"
            
            # Determine importance from CSS classes
            element_classes = div.get('class', [])
            importance = self.determine_importance(element_classes)
            
            # Determine category
            category = self.determine_category(event_name)
            
            # Extract event URL if available
            event_url = ""
            link = div.find('a')
            if link and link.get('href'):
                href = link.get('href')
                if href.startswith('/'):
                    event_url = self.BASE_URL.rstrip('/') + href
                else:
                    event_url = href
            
            # Create event object
            event = EconomicEvent(
                event_id=event_id,
                name=event_name,
                time=event_time,
                date=date_str,
                importance=importance,
                category=category,
                event_url=event_url,
            )
            
            logger.debug(f"Parsed event: {event_name} at {event_time} (importance: {importance})")
            return event
            
        except Exception as e:
            logger.error(f"Error parsing event div: {e}")
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
        
        # If no time found, check for settlement events
        if not event_time:
            if 'settlement' in text.lower():
                event_time = "All Day"
            else:
                event_time = "Time TBD"
        
        # Clean up event name
        event_name = re.sub(r'\s+', ' ', event_name).strip()
        
        # If event_name is empty after removing time, use original text
        if not event_name:
            event_name = text
        
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
        
        # Default based on event type
        if any(word in event_name_lower for word in ['speaks', 'speech', 'testimony']):
            return 'speech'
        elif any(word in event_name_lower for word in ['auction', 'bill', 'note', 'bond', 'tips']):
            return 'auction'
        elif any(word in event_name_lower for word in ['settlement']):
            return 'settlement'
        
        return 'other'
    
    def fallback_parse(self, soup) -> List[EconomicEvent]:
        """Fallback parsing method if table structure not found"""
        events = []
        
        # Find all econoevents divs directly
        event_divs = soup.find_all('div', class_=lambda x: x and 'econoevents' in x)
        logger.info(f"Fallback: Found {len(event_divs)} econoevents divs")
        
        # Use today's date as default
        today = datetime.now().strftime("%Y-%m-%d")
        
        for div in event_divs:
            event = self.parse_event_div(div, today)
            if event:
                events.append(event)
        
        return events
    
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
            
            # Look for forecast, actual, previous values
            # This needs to be customized based on actual detail page structure
            
            # Look for description
            description_div = soup.find('div', class_='eventdescription')
            if description_div:
                event.description = description_div.get_text(strip=True)[:500]
            
            # Look for data in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
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
        logger.info("Starting Econoday scraper V3")
        
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
                    time.sleep(1)
                
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
        print(f"\n=== Econoday Scraper V3 Summary ===")
        print(f"Total events: {len(self.events)}")
        
        if self.events:
            print(f"\nSample events:")
            for i, event in enumerate(self.events[:10]):
                print(f"{i+1}. {event.date} {event.time} - {event.name} (Importance: {event.importance}, Category: {event.category})")
            
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
            
            # Count by date
            date_counts = {}
            for event in self.events:
                date_counts[event.date] = date_counts.get(event.date, 0) + 1
            
            print(f"\nEvents by date:")
            for date in sorted(date_counts.keys()):
                count = date_counts[date]
                print(f"  {date}: {count} events")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape economic events from Econoday (V3)")
    parser.add_argument("--fetch-details", action="store_true", help="Fetch detailed event information")
    parser.add_argument("--output-json", type=str, help="Output JSON file path")
    parser.add_argument("--output-csv", type=str, help="Output CSV file path")
    parser.add_argument("--print-summary", action="store_true", help="Print summary to console")
    
    args = parser.parse_args()
    
    # Create and run scraper
    scraper = EconodayScraperV3()
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