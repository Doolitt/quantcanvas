#!/usr/bin/env python3
"""
Econoday Scrape & Store - Runs twice daily via cron

1. Scrapes current week's calendar (events, times, importance)
2. Fetches detail pages for all events with URLs (Prior/Consensus/Actual)
3. Saves to JSON files in data/ directory with timestamps
4. Maintains a latest.json symlink for the dashboard
"""

import requests
from bs4 import BeautifulSoup
import re, json, time, os
from datetime import datetime
from urllib.parse import urljoin
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict

BASE_URL = "https://us.econoday.com/"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# Importance mapping
IMP = {'djstar':5, 'star':4, 'speech':3, 'delayed':3, 'bullet':2}

# Category keywords
CATS = {
    'inflation':['cpi','inflation','pce','price'],
    'employment':['employment','jobless','payroll','nonfarm'],
    'housing':['housing','home','starts','permits','mortgage'],
    'manufacturing':['manufacturing','industrial','production','empire','philadelphia','ism'],
    'retail':['retail sales'],
    'confidence':['confidence','sentiment'],
    'speech':['speaks','speech','testimony','minutes'],
    'auction':['auction','bill','note','bond','treasury','tips'],
    'energy':['petroleum','oil','gas','eia','rig count'],
    'trade':['trade','import','export','international capital'],
    'gdp':['gdp','gross domestic'],
    'inventory':['inventory','inventories','durable goods'],
    'income':['personal income','outlays'],
}

def fix_url(u): return urljoin(BASE_URL, u) if u and not u.startswith('http') else u
def get_fid(u): m = re.search(r'fid=(\d+)', u or ''); return m.group(1) if m else ''
def get_imp(cls): return max((IMP.get(c,1) for c in cls), default=1)
def get_cat(name):
    nl = name.lower()
    for cat, kws in CATS.items():
        if any(k in nl for k in kws): return cat
    if any(w in nl for w in ['speaks','speech']): return 'speech'
    if any(w in nl for w in ['auction','bill','note','bond']): return 'auction'
    if 'settlement' in nl: return 'settlement'
    return 'other'

def parse_time(text):
    m = re.search(r'(\d{1,2}:\d{2}\s*[AP]M\s*ET)', text, re.I)
    if m: return text[:m.start()].strip(), m.group(1).strip()
    if 'settlement' in text.lower(): return text.strip(), 'All Day'
    return text.strip(), 'TBD'

def parse_date(text, year):
    text = text.replace('\xa0',' ')
    m = re.search(r'(\w+)\s+(\w+)\s+(\d+)', text)
    if not m: return None
    mo = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
    ms, ds = m.group(2), m.group(3)
    if ms in mo and ds.isdigit(): return f"{year:04d}-{mo[ms]:02d}-{int(ds):02d}"
    return None

def scrape_week():
    """Scrape current week's calendar"""
    print(f"[{datetime.now().isoformat()}] Scraping current week...")
    r = requests.get(BASE_URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    table = soup.find('table', class_='tablewrapper')
    if not table:
        for t in soup.find_all('table'):
            if t.find('td', class_=lambda x: x and 'navwkday' in x):
                table = t; break
    if not table: return []
    
    # Find row with dates+events
    for row in table.find_all('tr'):
        dcs = row.find_all('td', class_=lambda x: x and ('navwkday' in x or 'currentnavwkday' in x))
        ecs = row.find_all('td', class_=lambda x: x and 'events' in x)
        if dcs and ecs: break
    else: return []
    
    cells = row.find_all('td')
    year = datetime.now().year
    
    # Map dates
    dates = {}
    for i, c in enumerate(cells):
        cl = c.get('class',[])
        if 'navwkday' in cl or 'currentnavwkday' in cl:
            d = parse_date(c.get_text(strip=True), year)
            if d: dates[i] = d
    
    # Extract events
    events = []
    for di, ds in dates.items():
        ei = di + 5
        if ei >= len(cells): continue
        ec = cells[ei]
        if 'events' not in ec.get('class',[]): continue
        
        for div in ec.find_all('div', class_=lambda x: x and 'econoevents' in x):
            txt = div.get_text(strip=True)
            if not txt: continue
            name, etime = parse_time(txt)
            if not name: continue
            
            link = div.find('a')
            raw_url = link.get('href','') if link else ''
            
            events.append({
                'name': name, 'time': etime, 'date': ds,
                'importance': get_imp(div.get('class',[])),
                'category': get_cat(name),
                'fid': get_fid(raw_url),
                'event_url': fix_url(raw_url),
            })
    
    print(f"  Found {len(events)} events across {len(dates)} days")
    return events

def fetch_detail(event):
    """Fetch Prior/Consensus/Actual from detail page"""
    url = event.get('event_url','')
    if not url: return event
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200: return event
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Data table
        dt = soup.find('table', class_=lambda x: x and 'event_values' in x)
        if dt:
            hr = dt.find('tr', class_='actual_consensus_toprow')
            if hr:
                cols = [td.get_text(strip=True).lower() for td in hr.find_all('td')]
                metrics = []
                for row in dt.find_all('tr'):
                    if 'actual_consensus_toprow' in row.get('class',[]): continue
                    tds = row.find_all('td')
                    if len(tds) < 2: continue
                    m = {'metric': tds[0].get_text(strip=True)}
                    for j, td in enumerate(tds[1:], 1):
                        v = td.get_text(strip=True).replace('\xa0',' ')
                        if j < len(cols):
                            h = cols[j]
                            if 'prior' in h and 'revised' not in h: m['prior'] = v
                            elif 'revised' in h: m['prior_revised'] = v
                            elif 'consensus' in h and 'range' not in h: m['consensus'] = v
                            elif 'range' in h: m['consensus_range'] = v
                            elif 'actual' in h: m['actual'] = v
                    metrics.append(m)
                event['metrics'] = metrics
                event['has_actual'] = any(m.get('actual') for m in metrics)
        
        # RPI
        rpi = soup.find('table', class_=lambda x: x and 'rpi_compact' in x)
        if rpi:
            vals = rpi.find_all('span', attrs={'data-rpi': True})
            rpis = [v.get('data-rpi','') for v in vals if 'noval' not in v.get('class',[])]
            if len(rpis) >= 1: event['rpi_prior'] = rpis[0]
            if len(rpis) >= 2: event['rpi_current'] = rpis[1]
        
        # Text sections
        for sec in soup.find_all('div', class_='econo-section'):
            t = sec.get_text(strip=True)
            if t.startswith('Definition'): event['definition'] = t[10:].strip()[:300]
            elif t.startswith(('Consensus Outlook','Why Investors Care')): event['analysis'] = t[:300]
        
    except Exception as e:
        event['error'] = str(e)
    
    return event

def run_scrape():
    """Full scrape: calendar + details"""
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Step 1: Scrape calendar
    events = scrape_week()
    
    # Step 2: Fetch details for events with URLs
    has_url = [e for e in events if e.get('event_url')]
    print(f"  Fetching details for {len(has_url)} events...")
    for i, e in enumerate(has_url):
        fetch_detail(e)
        if (i+1) % 10 == 0: print(f"    {i+1}/{len(has_url)} done")
        time.sleep(0.4)
    
    # Step 3: Build summary
    with_metrics = [e for e in events if e.get('metrics')]
    with_actual = [e for e in events if e.get('has_actual')]
    
    result = {
        'scraped_at': datetime.now().isoformat(),
        'total_events': len(events),
        'events_with_data': len(with_metrics),
        'events_with_actual': len(with_actual),
        'events': events,
    }
    
    # Step 4: Save
    filepath = os.path.join(DATA_DIR, f'econoday_{ts}.json')
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    # Update latest.json symlink
    latest = os.path.join(DATA_DIR, 'latest.json')
    if os.path.islink(latest) or os.path.exists(latest):
        os.remove(latest)
    os.symlink(filepath, latest)
    
    print(f"\n{'='*50}")
    print(f"SCRAPE COMPLETE")
    print(f"{'='*50}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Events: {len(events)}")
    print(f"With metrics: {len(with_metrics)}")
    print(f"With actual: {len(with_actual)}")
    print(f"Saved: {filepath}")
    print(f"Latest: {latest}")
    
    # Date breakdown
    dates = {}
    for e in events: dates[e['date']] = dates.get(e['date'],0)+1
    for d in sorted(dates): print(f"  {d}: {dates[d]} events")
    
    return result

if __name__ == '__main__':
    run_scrape()
