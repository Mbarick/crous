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
    for link in soup.find
