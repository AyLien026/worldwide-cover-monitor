#!/usr/bin/env python3
"""Conservative monthly source watcher: NEVER automatically changes postal prices.
Matching a price token is only a weak signal, not verification of tariff class.
"""
from __future__ import annotations
import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

DB = Path(__file__).with_name('rates.json')
USER_AGENT = 'Mozilla/5.0 (compatible; WorldwideCoversPostageWatcher/1.0; +https://www.worldwidecovers.com/)'

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'):
            self.skip += 1
        if tag in ('td','th','p','li','div'):
            self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript'):
            self.skip = max(0,self.skip-1)
        self.parts.append(' ')
    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

def get_text(url):
    if not url.startswith(('https://','http://')):
        raise ValueError('Invalid source URL')
    req=Request(url,headers={'User-Agent':USER_AGENT,'Accept-Language':'en,fr;q=.8,pt;q=.7'})
    with urlopen(req,timeout=18) as response:
        body=response.read(4_000_000)
        content_type=response.headers.get('Content-Type','').lower()
    if body.startswith(b'%PDF') or 'application/pdf' in content_type:
        raise ValueError('PDF source requires a separate parser')
    parser=PlainText()
    parser.feed(body.decode('utf-8',errors='replace'))
    return re.sub(r'\s+',' ',' '.join(parser.parts))

def token_present(page, token):
    return bool(re.search(r'(?<![\d.,])'+re.escape(token)+r'(?![\d.,])',page,re.I))

def check_record(item,today):
    if not item.get('source_url') or not item.get('watch_token'):
        return
    try:
        found=token_present(get_text(item['source_url']),item['watch_token'])
        state='seen' if found else 'review'
        detail=('Listed number found on official page (not full tariff confirmation).' if found
                else 'Expected number not found: manual tariff review needed.')
    except Exception as err:
        state='unavailable'
        detail='Source could not be read ('+type(err).__name__+'); review manually.'
    item['check']={'state':state,'checked_at':today,'detail':detail}
    print(item['country']+': '+state)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    data=json.loads(DB.read_text(encoding='utf-8'))
    today=datetime.now(timezone.utc).date().isoformat()
    for item in data['rates']:
        check_record(item,today)
    data['last_scan_at']=today
    if not args.dry_run:
        DB.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    alerts=[x for x in data['rates'] if x.get('check',{}).get('state') in ('review','unavailable')]
    print(f"{len(data['rates'])} entries; {len(alerts)} source-check alerts. No prices changed.")

if __name__=='__main__':
    main()
