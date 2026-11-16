#!/usr/bin/env python3
"""Worldwide Covers Monitor, Python 3.9+, nur Standardbibliothek."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "items.json"
JS = ROOT / "data" / "items.js"
SOURCE_JS = ROOT / "data" / "sources.js"
STATE = ROOT / "data" / "state.json"
USER_AGENT = "WorldwideCoversMonitor/1.0 (philatelic RSS watcher; contact via site owner)"
MAX_ITEMS = 400
ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignore = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.ignore += 1
        if tag in ("p", "h1", "h2", "h3", "li", "br"):
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.ignore = max(0, self.ignore - 1)
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.ignore:
            self.parts.append(data)


def clean_html(raw):
    h = TextExtractor()
    h.feed(raw or "")
    return re.sub(r"\s+", " ", unescape("".join(h.parts))).strip()


def text(elem, path, default=""):
    target = elem.find(path)
    return "".join(target.itertext()).strip() if target is not None else default


def normalize_url(url):
    p = urllib.parse.urlsplit((url or "").strip())
    if p.scheme not in ("http", "https") or not p.netloc:
        return ""
    query = [(k,v) for k,v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm_") and k.lower() not in {"fbclid","gclid"}]
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urllib.parse.urlencode(query), ""))


def stable_id(source_id, url, title=""):
    key = normalize_url(url) or (source_id + "::" + title.casefold())
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def parse_feed(xml_data, source):
    root = ET.fromstring(xml_data)
    items = []
    if root.tag == ATOM + "feed":
        entries = root.findall(ATOM + "entry")
        for node in entries:
            title = text(node, ATOM + "title")
            links = node.findall(ATOM + "link")
            url = next((x.get("href", "") for x in links if x.get("rel", "alternate") == "alternate"), "")
            url = url or next((x.get("href", "") for x in links), "")
            summary = text(node, ATOM + "summary") or text(node, ATOM + "content")
            published = text(node, ATOM + "published") or text(node, ATOM + "updated")
            items.append(make_item(source, title, url, summary, published))
    else:
        entries = root.findall(".//item")
        for node in entries:
            title = text(node, "title")
            url = text(node, "link")
            summary = text(node, "description")
            published = text(node, "pubDate") or text(node, DC + "date")
            items.append(make_item(source, title, url, summary, published))
    return [i for i in items if i]


def make_item(source, title, url, summary="", published=""):
    title = clean_html(title)
    url = normalize_url(url)
    if not title or not url:
        return None
    return {
        "id": stable_id(source["id"], url, title),
        "title": title[:200],
        "url": url,
        "source": source["name"],
        "source_id": source["id"],
        "category": source.get("category", "Sonstiges"),
        "summary": clean_html(summary)[:160],
        "published": published[:70],
        "first_seen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "review_status": "ungeprüft",
        "priority": source.get("priority", "normal")
    }



class OfficialLinkScanner(HTMLParser):
    """Extrahiert anklickbare Originaldokumente samt kurzem vorherigem Kontext."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.recent = ""
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            self.current = {"href": href, "text": "", "context": self.recent[-360:]}

    def handle_data(self, data):
        fragment = re.sub(r"\s+", " ", data or " ")
        if self.current is not None:
            self.current["text"] += fragment
        else:
            self.recent = (self.recent + " " + fragment)[-1000:]

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.recent = (self.recent + " " + self.current["text"])[-1000:]
            self.current = None


def parse_official_bulletins(page, source):
    """Erfasst einzelne Bulletins/PDFs einer offiziellen Veröffentlichungsseite.

    Liest nur Linktitel und Umfeld, niemals den vollständigen PDF-Text.
    PDF-Fingerprinting kann separat im Live-Lauf aktiviert werden.
    """
    scanner = OfficialLinkScanner()
    scanner.feed(page)
    pattern = re.compile(source["title_pattern"], re.I)
    results = []
    seen = set()
    for link in scanner.links:
        url = normalize_url(urllib.parse.urljoin(source["url"], unescape(link["href"])))
        if not url or url in seen:
            continue
        if source.get("pdf_only") and not re.search(r"\.pdf(?:$|\?)", url, re.I):
            continue
        combined = link["context"] + " " + link["text"]
        matches = list(pattern.finditer(combined))
        if not matches:
            continue
        match = matches[-1]
        # Die Fundstelle direkt vor dem Link ist relevant; ein zufälliger Treffer
        # weiter oben in einer Navigation soll nicht falsch zugeordnet werden.
        if match.end() < len(combined) - 190:
            continue
        title = re.sub(r"\s+", " ", match.group(0)).strip()
        item = make_item(source, title, url, source.get("summary", "Offizielle Ausgabe; Details im Originaldokument prüfen."))
        if item:
            results.append(item)
            seen.add(url)
            if len(results) >= source.get("max_entries", 4):
                break
    if not results:
        raise ValueError("Keine passenden Dokumentlinks gefunden; Seitenstruktur oder Selektor prüfen")
    return results


def pdf_digest(url, max_bytes=25_000_000):
    """PDF-Prüfsumme erkennt auch Änderungen unter einer konstanten Dokument-URL."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"})
    with urllib.request.urlopen(req, timeout=24) as response:
        digest = hashlib.sha256()
        total = 0
        first = True
        while True:
            chunk = response.read(256 * 1024)
            if not chunk:
                break
            if first:
                if not chunk.lstrip().startswith(b"%PDF-"):
                    raise ValueError("Erwartetes PDF fehlt (keine PDF-Signatur)")
                first = False
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("PDF zu groß (Limit 25 MB)")
            digest.update(chunk)
    return digest.hexdigest()[:20]


def check_usps_issues(source):
    """Prüft fortlaufende USPS-Ausgaben über ihre offiziellen PDF-URLs.

    Das ist ein URL-Verfügbarkeitscheck, KEINE Auswertung einzelner Sonderstempel.
    """
    result = []
    start = int(source.get("start_issue", 22713))
    max_checks = int(source.get("max_probes", 8))
    for num in range(start, start + max_checks):
        year = int(source.get("year", datetime.now(timezone.utc).year))
        url = f"https://about.usps.com/postal-bulletin/{year}/pb{num}/pb{num}.pdf"
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status != 200:
                    break
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if "html" in content_type:
                    break
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                break
            raise
        item = make_item(source, f"USPS Postal Bulletin {num} ({year})", url,
                         "Offizielle Ausgabe: Kapitel 'Pictorial Postmarks' und Ersttagsstempel prüfen. Einzeltermine nicht automatisch extrahiert.")
        if item:
            result.append(item)
    if not result:
        raise ValueError("Keine USPS-Ausgabe erreichbar; URL-Prüfung möglicherweise blockiert")
    return result

def parse_deutschepost_page(page, source):
    plain = clean_html(page)
    # Beispiele: 'Ausgabe 24-2026| 04. November 2026' / 'Ausgabe 24–2026'
    match = re.search(r"Ausgabe\s+(\d{1,2})\s*[-–]\s*(20\d{2})", plain, re.I)
    if not match:
        raise ValueError("Keine Ausgabennummer gefunden; HTML möglicherweise geändert")
    issue = f"{match.group(1)}-{match.group(2)}"
    title = f"Neue Ausgabe 'Stempel und Informationen': {issue}"
    item = make_item(source, title, source["url"] + "?ausgabe=" + issue,
                     "Offizielle Deutsche-Post-Übersicht. Konkrete Stempeltermine bitte im verlinkten Heft prüfen.")
    # Datensatz enthält einen Abruflink zur offiziellen Übersichtsseite, keine erfundenen PDFs.
    item["url"] = source["url"]
    item["id"] = stable_id(source["id"], source["url"] + "?ausgabe=" + issue)
    item["published"] = "Ausgabe " + issue
    return [item]


def is_relevant(item, source, keywords):
    if source["kind"] in ("edition_page", "official_bulletins", "usps_issues"):
        return True
    haystack = (item["title"] + " " + item["summary"]).casefold()
    return any(word.casefold() in haystack for word in keywords)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/html;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=18) as resp:
        content = resp.read(2_000_000 + 1)
        if len(content) > 2_000_000:
            raise ValueError("Quelle zu groß (>2 MB)")
        return content


def load_json(path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def atomic_json(path, obj):
    path.parent.mkdir(exist_ok=True, parents=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def write_js(items):
    # JSON is safe inside an external JS file; escape to avoid accidental HTML tag parsing in other contexts.
    JS.write_text("window.WCM_DATA = " + json.dumps(items, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + ";\n", encoding="utf-8")


def write_sources_js(sources):
    catalog = [{k: s.get(k) for k in ("id", "name", "category", "url", "enabled", "note") if k in s} for s in sources]
    SOURCE_JS.write_text("window.WCM_SOURCES = " + json.dumps(catalog, ensure_ascii=False).replace("\u2028", "\\u2028").replace("\u2029", "\\u2029") + ";\n", encoding="utf-8")


def notify_zulip(items):
    if not items:
        return
    vars = ["ZULIP_SITE", "ZULIP_BOT_EMAIL", "ZULIP_API_KEY", "ZULIP_CHANNEL"]
    if not all(os.environ.get(x) for x in vars):
        return
    base = os.environ["ZULIP_SITE"].rstrip("/")
    if not base.startswith("https://"):
        raise ValueError("ZULIP_SITE muss mit https:// beginnen")
    import base64
    credentials = f"{os.environ['ZULIP_BOT_EMAIL']}:{os.environ['ZULIP_API_KEY']}".encode()
    headers = {"Authorization": "Basic " + base64.b64encode(credentials).decode(), "User-Agent": USER_AGENT}
    for item in items[:15]:
        content = f"**{item['title']}**\n\nQuelle: [{item['source']}]({item['url']})\n\nStatus: automatisch gefunden – noch nicht redaktionell geprüft."
        fields = urllib.parse.urlencode({"type": "stream", "to": os.environ["ZULIP_CHANNEL"], "topic": os.environ.get("ZULIP_TOPIC", "Neue Fundstücke"), "content": content}).encode()
        req = urllib.request.Request(base + "/api/v1/messages", data=fields, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status not in (200, 201):
                raise RuntimeError(f"Zulip HTTP {r.status}")


def run(config_path, offline_fixture=None):
    config = load_json(config_path, {})
    write_sources_js(config.get("sources", []))
    sources = [s for s in config.get("sources", []) if s.get("enabled")]
    keywords = config.get("filters", {}).get("keywords", [])
    existing = load_json(DATA, [])
    existing_ids = {x["id"] for x in existing}
    new = []
    errors = {}
    for s in sources:
        try:
            if s["kind"] == "usps_issues":
                parsed = check_usps_issues(s)
            else:
                raw = Path(offline_fixture).read_bytes() if offline_fixture and s["kind"] == "rss" else fetch(s["url"])
                if s["kind"] == "rss":
                    parsed = parse_feed(raw, s)
                elif s["kind"] == "official_bulletins":
                    parsed = parse_official_bulletins(raw.decode("utf-8", "replace"), s)
                    if s.get("track_pdf_changes"):
                        # Ein neues PDF unter derselben URL bekommt eine neue ID.
                        # Das verhindert übersehene Änderungen an Jahresübersichten.
                        for entry in parsed:
                            if entry["url"].lower().split("?")[0].endswith(".pdf"):
                                digest = pdf_digest(entry["url"])
                                entry["id"] = stable_id(s["id"], entry["url"] + "#sha256=" + digest)
                                entry["summary"] = "Offizielles PDF neu oder inhaltlich geändert; einzelne Termine und Einsendefristen im Dokument prüfen."
                else:
                    parsed = parse_deutschepost_page(raw.decode("utf-8", "replace"), s)
            useful = [x for x in parsed if is_relevant(x, s, keywords)]
            for i in useful:
                if i["id"] not in existing_ids:
                    existing_ids.add(i["id"])
                    new.append(i)
            print(f"OK {s['name']}: {len(parsed)} Einträge, {len(useful)} passend, {len([x for x in useful if x in new])} neu")
        except Exception as e:
            errors[s["id"]] = str(e)
            print(f"WARNUNG {s['name']}: {e}", file=sys.stderr)
    first_run = not load_json(STATE, {}).get("last_attempt")
    result = sorted(new + existing, key=lambda r: r.get("first_seen", ""), reverse=True)[:MAX_ITEMS]
    atomic_json(DATA, result)
    write_js(result)
    atomic_json(STATE, {"last_attempt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "active_sources": len(sources), "new_items": len(new), "source_errors": errors})
    # Kein Benachrichtigungssturm bei der allerersten Bestandsaufnahme.
    if not first_run:
        try:
            notify_zulip(new)
        except Exception as e:
            print(f"WARNUNG Zulip: {e}", file=sys.stderr)
    print(f"Fertig: {len(result)} Archivmeldungen, {len(new)} neue Einträge, {len(errors)} Quellenfehler")
    return 0 if len(errors) < len(sources) else 2


def main():
    p = argparse.ArgumentParser(description="Worldwide Covers Monitor")
    p.add_argument("--config", type=Path, default=ROOT / "sources.json")
    p.add_argument("--offline-fixture", type=str, help="RSS-Beispiel lokal statt Internet abrufen (Test)")
    args = p.parse_args()
    return run(args.config, args.offline_fixture)


if __name__ == "__main__":
    sys.exit(main())
