"""
Fetches the latest films from a Letterboxd RSS feed and updates
the README.md between <!-- LETTERBOXD-START --> and <!-- LETTERBOXD-END --> markers.

Required env var: LETTERBOXD_USERNAME
"""

import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

LETTERBOXD_USERNAME = "paari01"
RSS_URL = f"https://letterboxd.com/paari01/rss/"
README_PATH = "README.md"
START_MARKER = "<!-- LETTERBOXD-START -->"
END_MARKER = "<!-- LETTERBOXD-END -->"
MAX_FILMS = 5

RATING_MAP = {
    "0.5": "½", "1.0": "★", "1.5": "★½", "2.0": "★★",
    "2.5": "★★½", "3.0": "★★★", "3.5": "★★★½", "4.0": "★★★★",
    "4.5": "★★★★½", "5.0": "★★★★★",
}


def fetch_rss(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()


def parse_films(xml_data: bytes) -> list[dict]:
    root = ET.fromstring(xml_data)
    ns = {
        "letterboxd": "https://a.lettersboxd.com/dtd/letterboxd-2.0.xsd",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    films = []
    for item in root.findall(".//item")[:MAX_FILMS]:
        title_el = item.find("letterboxd:filmTitle", ns)
        rating_el = item.find("letterboxd:memberRating", ns)
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")

        title = title_el.text if title_el is not None else item.findtext("title", "Unknown")
        link = link_el.text if link_el is not None else "#"
        rating_raw = rating_el.text if rating_el is not None else None
        rating = RATING_MAP.get(rating_raw, "—") if rating_raw else "—"

        # Parse and reformat date
        date_str = pub_date_el.text if pub_date_el is not None else ""
        try:
            dt = datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
            date = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            date = date_str[:10] if date_str else "—"

        films.append({"title": title, "link": link, "rating": rating, "date": date})

    return films


def build_table(films: list[dict]) -> str:
    rows = "\n".join(
        f"| [{f['title']}]({f['link']}) | {f['rating']} | {f['date']} |"
        for f in films
    )
    return f"| Film | Rating | Watched |\n|------|--------|---------|  \n{rows}"


def update_readme(table: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_section = f"{START_MARKER}\n{table}\n{END_MARKER}"
    updated = re.sub(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        new_section,
        content,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)


def main():
    if not LETTERBOXD_USERNAME:
        print("ERROR: LETTERBOXD_USERNAME is empty.")
        raise SystemExit(1)
    print(f"Using username: {LETTERBOXD_USERNAME}")

    print(f"Fetching RSS for user: {LETTERBOXD_USERNAME}")
    xml_data = fetch_rss(RSS_URL)
    films = parse_films(xml_data)

    if not films:
        print("No films found in RSS feed.")
        return

    print(f"Found {len(films)} film(s): {[f['title'] for f in films]}")
    table = build_table(films)
    update_readme(table)
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
