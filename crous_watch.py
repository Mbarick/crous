import json
import os
import re
import smtplib
import time
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

BASE_HOST = "https://trouverunlogement.lescrous.fr"
SEARCH_URL = os.environ["SEARCH_URL"]
STATE_FILE = Path("seen_listings.json")
MAX_PAGES = int(os.environ.get("MAX_PAGES", "15"))

NTFY_TOPIC = os.environ.get("NTFY_TOPIC")
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
NOTIFY_EMAIL_TO = os.environ.get("NOTIFY_EMAIL_TO")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
}

ACCOMMODATION_RE = re.compile(r"/tools/\d+/accommodations/(\d+)")


def url_with_page(url, page):
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    query["page"] = [str(page)]
    new_query = urlencode(query, doseq=True)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def get_total_pages(soup):
    last_page_link = soup.find("a", string=re.compile("Derniere page"))
    if last_page_link and last_page_link.get("href"):
        match = re.search(r"page=(\d+)", last_page_link["href"])
        if match:
            return int(match.group(1))
    return 1


def parse_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    listings = {}
    for link in soup.find_all("a", href=ACCOMMODATION_RE):
        match = ACCOMMODATION_RE.search(link["href"])
        if not match:
            continue
        acc_id = match.group(1)
        name = link.get_text(strip=True)
        if not name:
            continue
        href = link["href"]
        full_url = BASE_HOST + href if href.startswith("/") else href
        address = ""
        try:
            container = link.find_parent(["div", "li", "article"])
            if container:
                text_after = container.get_text(" ", strip=True)
                address = text_after.replace(name, "", 1).strip(" -")[:120]
        except Exception:
            pass
        listings[acc_id] = {"name": name, "url": full_url, "address": address}
    return listings, soup


def fetch_all_listings(start_url):
    resp = requests.get(start_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    listings, soup = parse_listings(resp.text)
    total_pages = min(get_total_pages(soup), MAX_PAGES)
    print(f"{total_pages} page(s) a parcourir.")
    for page in range(2, total_pages + 1):
        time.sleep(1)
        page_url = url_with_page(start_url, page)
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Erreur page {page}: {e}")
            continue
        page_listings, _ = parse_listings(resp.text)
        listings.update(page_listings)
    return listings


def load_seen():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_seen(listings):
    STATE_FILE.write_text(json.dumps(listings, ensure_ascii=False, indent=2), encoding="utf-8")


def format_listing(item):
    line = item["name"]
    if item.get("address"):
        line += " - " + item["address"]
    line += "\n" + item["url"]
    return line


def notify_ntfy(new_items):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC non defini, notification ntfy ignoree.")
        return
    body = "\n\n".join(format_listing(item) for item in new_items.values())
    first_url = next(iter(new_items.values()))["url"]
    payload = {
        "topic": NTFY_TOPIC,
        "title": str(len(new_items)) + " nouveau(x) logement(s) Crous",
        "message": body[:4000],
        "priority": 5,
        "tags": ["house"],
        "click": first_url,
    }
    try:
        resp = requests.post("https://ntfy.sh/", json=payload, timeout=10)
        print("ntfy status: " + str(resp.status_code) + " - " + resp.text[:200])
    except Exception as e:
        print("Erreur envoi ntfy: " + str(e))


def notify_email(new_items):
    if not (GMAIL_ADDRESS and GMAIL_APP_PASSWORD and NOTIFY_EMAIL_TO):
        return
    body = "Nouveaux logements Crous disponibles :\n\n"
    body += "\n\n".join(format_listing(item) for item in new_items.values())
    body += "\n\nRecherche surveillee : " + SEARCH_URL
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "Nouveau(x) logement(s) Crous (" + str(len(new_items)) + ")"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_EMAIL_TO
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_ADDRESS, [NOTIFY_EMAIL_TO], msg.as_string())
        print("Email envoye.")
    except Exception as e:
        print("Erreur envoi email: " + str(e))


def main():
    current = fetch_all_listings(SEARCH_URL)
    print(str(len(current)) + " logement(s) trouve(s) au total sur la recherche.")
    seen = load_seen()
    new_ids = set(current) - set(seen)
    if not new_ids:
        print("Aucun nouveau logement depuis la derniere verification.")
        save_seen(current)
        return
    new_items = {acc_id: current[acc_id] for acc_id in new_ids}
    print(str(len(new_items)) + " nouveau(x) logement(s) repere(s) :")
    for item in new_items.values():
        print(" - " + item["name"] + " (" + item["url"] + ")")
    notify_ntfy(new_items)
    notify_email(new_items)
    save_seen(current)


if __name__ == "__main__":
    main()
