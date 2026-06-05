#!/usr/bin/env python3
"""
Multi-University Directory Scraper
===================================
Scrapes publicly available contact info from university directories.

NOTE: Most student directories require authentication. This scraper
only accesses publicly available faculty/staff information.

USAGE:
    python3 university_scraper.py
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# University directory configurations
UNIVERSITIES = {
    "uw": {
        "name": "University of Washington",
        "url": "https://directory.uw.edu/",
        "search_field": "input[name='query']",
        "submit": "keys",  # Press Enter
        "email_domain": "@uw.edu",
    },
    "ufl": {
        "name": "University of Florida",
        "url": "https://directory.ufl.edu/directory/SearchPerson",
        "search_field": "input[type='text']",
        "submit": "keys",
        "email_domain": "@ufl.edu",
    },
    "osu": {
        "name": "Ohio State University",
        "url": "https://www.osu.edu/search",
        "search_field": "input[type='search'], input[type='text']",
        "submit": "keys",
        "email_domain": "@osu.edu",
    },
    "auburn": {
        "name": "Auburn University",
        "url": "https://peoplefinder.auburn.edu/peoplefinder/",
        "search_field": "input[type='text'], input[name='search']",
        "submit": "keys",
        "email_domain": "@auburn.edu",
    },
    "psu": {
        "name": "Penn State University",
        "url": "https://directory.psu.edu/",
        "search_field": "input[type='text']",
        "submit": "keys",
        "email_domain": "@psu.edu",
    },
    "asu": {
        "name": "Arizona State University",
        "url": "https://search.asu.edu/",
        "search_field": "input[type='text'], input[type='search']",
        "submit": "keys",
        "email_domain": "@asu.edu",
    },
}


class UniversityScraper:
    def __init__(self):
        self.driver = None
        self.contacts = []

    def setup_browser(self):
        print("Starting Chrome browser...")
        options = Options()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def close_browser(self):
        if self.driver:
            self.driver.quit()

    def search_directory(self, uni_key, search_term):
        """Search a university directory"""
        if uni_key not in UNIVERSITIES:
            print(f"Unknown university: {uni_key}")
            return []

        uni = UNIVERSITIES[uni_key]
        print(f"\n{'='*60}")
        print(f"Searching {uni['name']} for '{search_term}'")
        print(f"URL: {uni['url']}")
        print(f"{'='*60}")

        try:
            self.driver.get(uni['url'])
            time.sleep(3)

            # Find search field
            search_field = None
            for selector in uni['search_field'].split(', '):
                try:
                    search_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if not search_field:
                print(f"  Could not find search field")
                return []

            # Enter search term
            search_field.clear()
            search_field.send_keys(search_term)
            time.sleep(0.5)

            # Submit
            if uni['submit'] == 'keys':
                search_field.send_keys(Keys.RETURN)
            else:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, uni['submit'])
                    submit_btn.click()
                except:
                    search_field.send_keys(Keys.RETURN)

            time.sleep(4)

            # Extract results
            contacts = self.extract_contacts(uni['email_domain'], uni['name'])
            print(f"  Found {len(contacts)} contacts")
            return contacts

        except Exception as e:
            print(f"  Error: {e}")
            return []

    def extract_contacts(self, email_domain, university):
        """Extract contacts from current page"""
        contacts = []
        page_source = self.driver.page_source
        body_text = self.driver.find_element(By.TAG_NAME, "body").text

        # Find all email addresses matching the domain
        domain_pattern = email_domain.replace('.', r'\.')
        email_pattern = rf'([a-zA-Z0-9._%+-]+{domain_pattern})'
        emails = list(set(re.findall(email_pattern, page_source, re.IGNORECASE)))

        # Try to extract from table rows
        rows = self.driver.find_elements(By.CSS_SELECTOR, "table tr, .result, .person, [class*='result']")

        for row in rows:
            try:
                text = row.text.strip()
                if not text or len(text) < 5:
                    continue

                contact = {
                    "name": "",
                    "email": "",
                    "phone": "",
                    "title": "",
                    "department": "",
                    "university": university,
                    "scraped_at": datetime.now().isoformat()
                }

                # Get name from links
                try:
                    links = row.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        link_text = link.text.strip()
                        if "mailto:" in href:
                            contact["email"] = href.replace("mailto:", "").split("?")[0]
                        elif link_text and "@" not in link_text and len(link_text) > 2 and len(link_text) < 50:
                            if re.match(r'^[A-Za-z]', link_text):
                                contact["name"] = link_text
                except:
                    pass

                # Fallback email
                if not contact["email"]:
                    match = re.search(email_pattern, text, re.IGNORECASE)
                    if match:
                        contact["email"] = match.group(1)

                # Phone
                phone_match = re.search(r'\+?1?\s*[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}', text)
                if phone_match:
                    contact["phone"] = phone_match.group(0)

                # Name from first line if not found
                if not contact["name"]:
                    lines = text.split('\n')
                    if lines:
                        first_line = lines[0].strip()
                        if re.match(r'^[A-Z][a-z]+', first_line) and "@" not in first_line:
                            contact["name"] = first_line

                if contact["name"] or contact["email"]:
                    # Avoid duplicates
                    is_dup = any(c["email"] == contact["email"] and c["name"] == contact["name"] for c in contacts if contact["email"])
                    if not is_dup:
                        contacts.append(contact)

            except:
                continue

        # Fallback: just extract emails
        if not contacts and emails:
            for email in emails[:50]:  # Limit
                contacts.append({
                    "name": "",
                    "email": email,
                    "phone": "",
                    "title": "",
                    "department": "",
                    "university": university,
                    "scraped_at": datetime.now().isoformat()
                })

        return contacts

    def save_contacts(self, filename_base):
        """Save contacts to CSV and JSON"""
        if not self.contacts:
            print("No contacts to save")
            return

        csv_file = f"{filename_base}.csv"
        json_file = f"{filename_base}.json"

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["name", "email", "phone", "title", "department", "university", "scraped_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.contacts)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.contacts, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(self.contacts)} contacts to {csv_file}")

    def scrape_multiple(self, universities, search_term):
        """Scrape multiple universities"""
        self.setup_browser()

        for uni_key in universities:
            try:
                contacts = self.search_directory(uni_key, search_term)
                self.contacts.extend(contacts)
            except Exception as e:
                print(f"Error with {uni_key}: {e}")
                continue

        self.close_browser()
        return self.contacts


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║     Multi-University Directory Scraper                   ║
║     Scrapes publicly available directory info            ║
╚══════════════════════════════════════════════════════════╝

Available universities:
  uw     - University of Washington
  ufl    - University of Florida
  osu    - Ohio State University
  auburn - Auburn University
  psu    - Penn State University
  asu    - Arizona State University

NOTE: Student directories usually require login.
      This scrapes publicly available faculty/staff data.
    """)

    # Get search term
    search_term = input("Enter search term (e.g., 'ang', 'smith'): ").strip()
    if not search_term:
        search_term = "ang"

    print("\nSelect universities (comma-separated, or 'all'):")
    print("Example: uw,ufl,osu")
    uni_input = input("Universities: ").strip().lower()

    if uni_input == 'all':
        universities = list(UNIVERSITIES.keys())
    else:
        universities = [u.strip() for u in uni_input.split(',') if u.strip() in UNIVERSITIES]

    if not universities:
        universities = ['uw']

    print(f"\nWill search: {', '.join(universities)}")
    print(f"Search term: '{search_term}'")
    print("Starting in 3 seconds...\n")
    time.sleep(3)

    scraper = UniversityScraper()

    try:
        scraper.scrape_multiple(universities, search_term)
        scraper.save_contacts(f"university_contacts_{search_term}")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        scraper.save_contacts(f"university_contacts_{search_term}")
        scraper.close_browser()

    print(f"\nTotal contacts collected: {len(scraper.contacts)}")


if __name__ == "__main__":
    main()
