#!/usr/bin/env python3
"""
Econoday Economic Calendar Scraper - Final Version

Features:
- Correct table structure parsing (70-cell row, 5-cell offset)
- Fixed URL handling (relative → absolute)
- Detail page parsing with Prior/Consensus/Actual extraction
- RPI (Relative Performance Index) extraction
- Definition and analysis text extraction
- Multiple week scraping support
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import json
import csv
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field
from urllib.parse import urljoin
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://us.econoday.com/"

@dataclass
class EventMetric:
    """A single metric row from the detail page (e.g., CPI - M/M)"""
    metric_name: str = ""
    prior: str = ""
    consensus: str = ""
    consensus_range: str = ""
    actual: str = ""

@dataclass 
class EconomicEvent:
    """Full economic event with detail data"""
    source: str = "econoday"
    event_id: str = ""
    fid: str = ""           # Econoday's internal event type ID
    name: str = ""
    time: str = ""
    date: str = ""
    country: str = "US"
    importance: int = 1
    category: str = ""
    event_url: str = ""
    # Detail page data
    metrics: List[Dict] = field(default_factory=list)  # List of {metric_name, prior, consensus, consensus_range, actual}
    rpi_prior: str = ""     # Relative Performance Index - prior event
    rpi_current: str = ""   # RPI - current event
    definition: str = ""
    analysis: str = ""      # "Consensus Outlook" or "Why Investors Care"
    has_actual: bool = False # Whether actual data is available
    
    def to_dict(self):
        return asdict(self)

# Importance mapping from CSS classes
IMPORTANCE_MAP = {
    'djstar': 5, 'star': 4, 'speech': 3,
    'delayed': 3, 'bullet': 2, 'default': 1,
}

# Category keywords
CATEGORY_KEYWORDS = {
    'inflation': ['cpi', 'inflation', 'pce', 'price'],
    'employment': ['employment', 'jobless', 'payroll', 'unemployment', 'nonfarm'],
    'housing': ['housing', 'home', 'starts', 'permits', 'mortgage'],
    'manufacturing': ['manufacturing', 'industrial', 'production', 'factory', 'empire', 'philadelphia', 'ism'],
    'retail': ['retail sales'],
    'confidence': ['confidence', 'sentiment', 'survey'],
    'speech': ['speaks', 'speech', 'testimony', 'minutes'],
    'auction': ['auction', 'bill', 'note', 'bond', 'treasury', 'tips'],
    'energy': ['petroleum', 'oil', 'gas', 'energy', 'eia', 'rig count'],
    'trade': ['trade', 'import', 'export', 'international capital'],
    'gdp': ['gdp', 'gross domestic'],
    'leading': ['leading', 'indicators'],
    'inventory': ['inventory', 'inventories', 'durable goods'],
    'settlement': ['settlement'],
    'income': ['personal income', 'outlays', 'pce'],
}

def fix_url(url: str) -> str:
    """Convert any URL to absolute"""
    if not url:
        return ""
    if url.startswith('http'):
        return url
    return urljoin(BASE_URL, url)

def extract_fid(url: str) -> str:
    """Extract fid parameter from URL"""
    match = re.search(r'fid=(\d+)', url)
    return match.group(1) if match else ""

def determine_importance(classes: List[str]) -> int:
    for cls in classes:
        if cls in IMPORTANCE_MAP:
            return IMPORTANCE_MAP[cls]
    return 1

def determine_category(name: str) -> str:
    name_lower = name.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name_lower:
                return category
    if any(w in name_lower for w in ['speaks', 'speech', 'testimony']):
        return 'speech'
    if any(w in name_lower for w in ['auction', 'bill', 'note', 'bond']):
        return 'auction'
    if 'settlement' in name_lower:
        return 'settlement'
    return 'other'

def parse_event_text(text: str) -> Tuple[str, str]:
    """Extract name and time from event text"""
    time_pattern = r'(\d{1,2}:\d{2}\s*[AP]M\s*ET)'
    match = re.search(time_pattern, text, re.IGNORECASE)
    if match:
        return text[:match.start()].strip(), match.group(1).strip()
    if 'settlement' in text.lower():
        return text.strip(), "All Day"
    return text.strip(), "Time TBD"

def parse_date_text(text: str, year: int) -> Optional[str]:
    """Parse 'Monday Feb 16' → '2026-02-16'"""
    text = text.replace('\xa0', ' ')
    match = re.search(r'(\w+)\s+(\w+)\s+(\d+)', text)
    if not match:
        return None
    _, month_str, day_str = match.groups()
    month_map = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                 'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    if month_str in month_map and day_str.isdigit():
        return f"{year:04d}-{month_map[month_str]:02d}-{int(day_str):02d}"
    return None

class EconodayScraper:
    """Production Econoday scraper"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        })
        self.events: List[EconomicEvent] = []
        self.year = datetime.now().year
    
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        try:
            r = self.session.get(url, timeout=15)
            r.raise_for_status()
            return BeautifulSoup(r.text, 'html.parser')
        except Exception as e:
            logger.error(f"Fetch failed {url}: {e}")
            return None
    
    def scrape_week(self, day: int = None, month: int = None, year: int = None) -> List[EconomicEvent]:
        """Scrape one week of events"""
        if day and month and year:
            url = f"{BASE_URL}byweek?day={day}&month={month}&year={year}&lid=0"
        else:
            url = BASE_URL
        
        logger.info(f"Scraping week: {url}")
        soup = self.fetch(url)
        if not soup:
            return []
        
        # Find calendar table
        table = soup.find('table', class_='tablewrapper')
        if not table:
            for t in soup.find_all('table'):
                if t.find(['td','th'], class_=lambda x: x and 'navwkday' in x):
                    table = t
                    break
        
        if not table:
            logger.error("No calendar table found")
            return []
        
        # Find the row with dates AND events
        target_row = None
        for row in table.find_all('tr'):
            dates = row.find_all(['td','th'], class_=lambda x: x and ('navwkday' in x or 'currentnavwkday' in x))
            events = row.find_all(['td','th'], class_=lambda x: x and 'events' in x)
            if dates and events:
                target_row = row
                break
        
        if not target_row:
            logger.error("No date+event row found")
            return []
        
        cells = target_row.find_all(['td','th'])
        
        # Map dates to their cell indices
        date_indices = {}
        for idx, cell in enumerate(cells):
            cls = cell.get('class', [])
            if 'navwkday' in cls or 'currentnavwkday' in cls:
                parsed = parse_date_text(cell.get_text(strip=True), year or self.year)
                if parsed:
                    date_indices[idx] = parsed
        
        logger.info(f"Found dates: {list(date_indices.values())}")
        
        # Extract events (5-cell offset from dates)
        week_events = []
        for date_idx, date_str in date_indices.items():
            event_idx = date_idx + 5
            if event_idx >= len(cells):
                continue
            
            event_cell = cells[event_idx]
            if 'events' not in event_cell.get('class', []):
                continue
            
            for div in event_cell.find_all('div', class_=lambda x: x and 'econoevents' in x):
                text = div.get_text(strip=True)
                if not text:
                    continue
                
                name, evt_time = parse_event_text(text)
                if not name:
                    continue
                
                # Extract URL and fid
                link = div.find('a')
                raw_url = link.get('href', '') if link else ''
                event_url = fix_url(raw_url)
                fid = extract_fid(raw_url)
                
                evt = EconomicEvent(
                    event_id=f"econoday_{date_str}_{name.replace(' ','_').lower()[:50]}",
                    fid=fid,
                    name=name,
                    time=evt_time,
                    date=date_str,
                    importance=determine_importance(div.get('class', [])),
                    category=determine_category(name),
                    event_url=event_url,
                )
                week_events.append(evt)
        
        logger.info(f"Scraped {len(week_events)} events for week")
        return week_events
    
    def fetch_details(self, event: EconomicEvent) -> EconomicEvent:
        """Fetch detail page and extract Prior/Consensus/Actual + RPI + text"""
        if not event.event_url:
            return event
        
        soup = self.fetch(event.event_url)
        if not soup:
            return event
        
        # === 1. Parse data table (Prior / Consensus / Consensus Range / Actual) ===
        data_table = soup.find('table', class_=lambda x: x and 'event_values' in x)
        if data_table:
            header_row = data_table.find('tr', class_='actual_consensus_toprow')
            if header_row:
                headers = [td.get_text(strip=True).lower() for td in header_row.find_all('td')]
                
                for row in data_table.find_all('tr'):
                    if 'actual_consensus_toprow' in row.get('class', []):
                        continue
                    
                    tds = row.find_all('td')
                    if len(tds) < 2:
                        continue
                    
                    metric = {'metric_name': tds[0].get_text(strip=True)}
                    
                    for i, td in enumerate(tds[1:], 1):
                        val = td.get_text(strip=True)
                        if i < len(headers):
                            h = headers[i]
                            if 'prior' in h:
                                metric['prior'] = val
                            elif 'consensus' in h and 'range' not in h:
                                metric['consensus'] = val
                            elif 'range' in h:
                                metric['consensus_range'] = val
                            elif 'actual' in h:
                                metric['actual'] = val
                                event.has_actual = True
                        else:
                            # Fallback: assign by position
                            if i == 1: metric['prior'] = val
                            elif i == 2: metric['consensus'] = val
                            elif i == 3: metric['consensus_range'] = val
                            elif i == 4: metric['actual'] = val; event.has_actual = True
                    
                    if metric.get('metric_name'):
                        event.metrics.append(metric)
        
        # === 2. Parse RPI table ===
        rpi_table = soup.find('table', class_=lambda x: x and 'rpi_compact' in x)
        if rpi_table:
            rpi_values = rpi_table.find_all('span', class_='rpi-value')
            for rv in rpi_values:
                data_rpi = rv.get('data-rpi', '')
                if data_rpi and 'noval' not in rv.get('class', []):
                    if not event.rpi_prior:
                        event.rpi_prior = data_rpi
                    elif not event.rpi_current:
                        event.rpi_current = data_rpi
        
        # === 3. Parse text sections ===
        sections = soup.find_all('div', class_='econo-section')
        for section in sections:
            text = section.get_text(strip=True)
            if text.startswith('Definition'):
                event.definition = text[len('Definition'):].strip()[:500]
            elif text.startswith('Consensus Outlook') or text.startswith('Why Investors Care'):
                event.analysis = text[:500]
        
        return event
    
    def scrape(self, weeks: int = 1, fetch_details: bool = False, 
               start_day: int = None, start_month: int = None, start_year: int = None) -> List[EconomicEvent]:
        """Main entry point"""
        logger.info(f"Starting scrape: {weeks} week(s), details={fetch_details}")
        
        all_events = []
        
        if weeks == 1 and not start_day:
            # Current week
            all_events = self.scrape_week()
        else:
            # Multiple weeks or specific start
            if start_day and start_month and start_year:
                base = datetime(start_year, start_month, start_day)
            else:
                base = datetime.now()
            
            for w in range(weeks):
                d = base + timedelta(weeks=w)
                events = self.scrape_week(d.day, d.month, d.year)
                all_events.extend(events)
                if w < weeks - 1:
                    time.sleep(1)
        
        # Deduplicate by event_id
        seen = set()
        unique = []
        for e in all_events:
            if e.event_id not in seen:
                seen.add(e.event_id)
                unique.append(e)
        all_events = unique
        
        logger.info(f"Total unique events: {len(all_events)}")
        
        # Fetch details
        if fetch_details:
            has_url = [e for e in all_events if e.event_url]
            logger.info(f"Fetching details for {len(has_url)} events with URLs...")
            for i, event in enumerate(has_url):
                self.fetch_details(event)
                if (i + 1) % 5 == 0:
                    logger.info(f"  Details fetched: {i+1}/{len(has_url)}")
                time.sleep(0.5)  # Be polite
        
        self.events = all_events
        return all_events
    
    def save_json(self, path: str = "econoday_events.json"):
        with open(path, 'w') as f:
            json.dump([e.to_dict() for e in self.events], f, indent=2, default=str)
        logger.info(f"Saved {len(self.events)} events to {path}")
    
    def save_csv(self, path: str = "econoday_events.csv"):
        if not self.events:
            return
        
        # Flatten metrics for CSV — use consistent columns
        flat_fields = ['source','event_id','fid','name','time','date','country',
                       'importance','category','event_url','primary_metric',
                       'prior','consensus','consensus_range','actual',
                       'rpi_prior','rpi_current','has_actual','definition','analysis']
        
        rows = []
        for e in self.events:
            row = {
                'source': e.source, 'event_id': e.event_id, 'fid': e.fid,
                'name': e.name, 'time': e.time, 'date': e.date,
                'country': e.country, 'importance': e.importance,
                'category': e.category, 'event_url': e.event_url,
                'rpi_prior': e.rpi_prior, 'rpi_current': e.rpi_current,
                'has_actual': e.has_actual,
                'definition': e.definition[:200] if e.definition else '',
                'analysis': e.analysis[:200] if e.analysis else '',
                'primary_metric': '', 'prior': '', 'consensus': '',
                'consensus_range': '', 'actual': '',
            }
            if e.metrics:
                m = e.metrics[0]
                row['primary_metric'] = m.get('metric_name', '')
                row['prior'] = m.get('prior', '')
                row['consensus'] = m.get('consensus', '')
                row['consensus_range'] = m.get('consensus_range', '')
                row['actual'] = m.get('actual', '')
            rows.append(row)
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flat_fields)
            writer.writeheader()
            writer.writerows(rows)
        logger.info(f"Saved {len(rows)} events to {path}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"ECONODAY SCRAPER - FINAL VERSION")
        print(f"{'='*60}")
        print(f"Total events: {len(self.events)}")
        
        with_details = [e for e in self.events if e.metrics]
        with_actual = [e for e in self.events if e.has_actual]
        print(f"Events with detail data: {len(with_details)}")
        print(f"Events with actual values: {len(with_actual)}")
        
        # By date
        dates = {}
        for e in self.events:
            dates[e.date] = dates.get(e.date, 0) + 1
        print(f"\nBy date:")
        for d in sorted(dates):
            print(f"  {d}: {dates[d]} events")
        
        # By importance
        imp = {}
        for e in self.events:
            imp[e.importance] = imp.get(e.importance, 0) + 1
        print(f"\nBy importance:")
        for i in sorted(imp):
            print(f"  Level {i}: {imp[i]} events")
        
        # By category
        cats = {}
        for e in self.events:
            cats[e.category] = cats.get(e.category, 0) + 1
        print(f"\nBy category:")
        for c in sorted(cats):
            print(f"  {c}: {cats[c]} events")
        
        # Show events with actual data
        if with_actual:
            print(f"\nEvents with actual data:")
            for e in with_actual[:10]:
                m = e.metrics[0] if e.metrics else {}
                print(f"  {e.date} {e.name}")
                print(f"    Prior: {m.get('prior','')} | Consensus: {m.get('consensus','')} | Actual: {m.get('actual','')}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Econoday Scraper (Final)")
    parser.add_argument("--weeks", type=int, default=1, help="Number of weeks to scrape")
    parser.add_argument("--details", action="store_true", help="Fetch detail pages")
    parser.add_argument("--start-day", type=int, help="Start day")
    parser.add_argument("--start-month", type=int, help="Start month")
    parser.add_argument("--start-year", type=int, help="Start year")
    parser.add_argument("--output", type=str, default="econoday_events", help="Output filename prefix")
    args = parser.parse_args()
    
    scraper = EconodayScraper()
    scraper.scrape(
        weeks=args.weeks,
        fetch_details=args.details,
        start_day=args.start_day,
        start_month=args.start_month,
        start_year=args.start_year,
    )
    scraper.save_json(f"{args.output}.json")
    scraper.save_csv(f"{args.output}.csv")
    scraper.print_summary()

if __name__ == "__main__":
    main()
