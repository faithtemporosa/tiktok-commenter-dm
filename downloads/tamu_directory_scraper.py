#!/usr/bin/env python3
"""
UW Directory Scraper (Interactive Mode)
========================================
Opens UW directory, lets you search manually, then scrapes results.

SETUP:
    pip3 install selenium webdriver-manager --break-system-packages

USAGE:
    python3 tamu_directory_scraper.py
"""

import time
import json
import csv
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False
    print("Install: pip3 install webdriver-manager --break-system-packages")

# Configuration
UW_DIRECTORY_URL = "https://directory.uw.edu/"
OUTPUT_CSV = "uw_contacts.csv"
OUTPUT_JSON = "uw_contacts.json"


class UWDirectoryScraper:
    def __init__(self):
        self.driver = None
        self.contacts = []

    def setup_browser(self):
        """Set up Chrome browser"""
        options = Options()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        print("Starting Chrome browser...")

        if HAS_WEBDRIVER_MANAGER:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        else:
            self.driver = webdriver.Chrome(options=options)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Navigating to {UW_DIRECTORY_URL}...")
        self.driver.get(UW_DIRECTORY_URL)
        time.sleep(2)
        print(f"✓ Browser opened: {self.driver.current_url}")

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            print("✓ Browser closed")

    def scrape_current_page(self):
        """Scrape all contacts from current search results page"""
        contacts = []

        try:
            # Wait for results to load
            time.sleep(2)

            page_source = self.driver.page_source
            page_text = self.driver.find_element(By.TAG_NAME, "body").text

            print(f"\nScraping results...")

            # Try to find result rows - UW directory typically uses tables or divs
            result_selectors = [
                "table.results tr",
                "table tr",
                ".person",
                ".result",
                "[class*='result']",
                ".directory-listing tr",
                "div.person-info",
            ]

            result_elements = []
            for selector in result_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 1:  # Skip if only header row
                        result_elements = elements
                        print(f"  Found {len(elements)} elements with selector: {selector}")
                        break
                except:
                    continue

            # Extract from each result element
            for elem in result_elements:
                try:
                    text = elem.text.strip()
                    if not text or len(text) < 5:
                        continue

                    # Skip header rows
                    if text.startswith("Name") or "Department" in text and "Email" in text:
                        continue

                    contact = self.extract_contact_from_element(elem, text)
                    if contact.get("name") or contact.get("email"):
                        contacts.append(contact)
                        print(f"  ✓ {contact.get('name', 'Unknown')} | {contact.get('email', 'No email')} | {contact.get('phone', '')}")

                except Exception as e:
                    continue

            # Fallback: extract all emails from page
            if not contacts:
                print("  Trying fallback extraction...")
                emails = set(re.findall(r'([a-zA-Z0-9._%+-]+@(?:uw|u\.washington)\.edu)', page_source))
                for email in emails:
                    contacts.append({
                        "name": "",
                        "email": email,
                        "phone": "",
                        "title": "",
                        "department": "",
                        "scraped_at": datetime.now().isoformat()
                    })
                    print(f"  ✓ {email}")

            print(f"\n  Total contacts found: {len(contacts)}")

        except Exception as e:
            print(f"  Error scraping: {e}")

        return contacts

    def extract_contact_from_element(self, elem, text):
        """Extract contact info from a result element"""
        contact = {
            "name": "",
            "email": "",
            "phone": "",
            "title": "",
            "department": "",
            "scraped_at": datetime.now().isoformat()
        }

        # Try to find specific fields within the element
        try:
            # Look for links (often names or emails)
            links = elem.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href") or ""
                link_text = link.text.strip()

                if "mailto:" in href:
                    contact["email"] = href.replace("mailto:", "").split("?")[0]
                elif link_text and not contact["name"]:
                    # First link text is usually the name
                    if re.match(r'^[A-Za-z]', link_text) and "@" not in link_text:
                        contact["name"] = link_text
        except:
            pass

        # Extract from text
        lines = text.split('\n')

        # Name (usually first line)
        if not contact["name"] and lines:
            first_line = lines[0].strip()
            if first_line and len(first_line) > 2 and len(first_line) < 100:
                if re.match(r'^[A-Za-z]', first_line) and "@" not in first_line:
                    contact["name"] = first_line

        # Email
        if not contact["email"]:
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@(?:uw|u\.washington)\.edu)', text)
            if email_match:
                contact["email"] = email_match.group(1)

        # Phone
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            contact["phone"] = phone_match.group(0)

        # Department - look for common patterns
        for line in lines:
            line = line.strip()
            dept_keywords = ['Department', 'College', 'School', 'Medicine', 'Engineering', 'Arts', 'Sciences', 'Library', 'Hospital']
            if any(kw in line for kw in dept_keywords):
                contact["department"] = line
                break

        # Title
        title_keywords = ['Professor', 'Director', 'Manager', 'Coordinator', 'Assistant', 'Associate', 'Dean', 'Chair', 'Specialist', 'Analyst', 'Administrator', 'Student', 'Staff']
        for line in lines:
            line = line.strip()
            if any(kw in line for kw in title_keywords):
                contact["title"] = line
                break

        return contact

    def save_contacts(self):
        """Save contacts to files"""
        if not self.contacts:
            print("No contacts to save.")
            return

        # CSV
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["name", "email", "phone", "title", "department", "scraped_at"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.contacts)
        print(f"✓ Saved to {OUTPUT_CSV}")

        # JSON
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(self.contacts, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved to {OUTPUT_JSON}")

    def run_interactive(self):
        """Run in interactive mode"""
        print("""
╔══════════════════════════════════════════════════════════╗
║     UW Directory Scraper (Interactive Mode)              ║
║     https://directory.uw.edu/                            ║
╚══════════════════════════════════════════════════════════╝
        """)

        self.setup_browser()

        print("\n" + "="*60)
        print("Browser is open. Do your search on the page.")
        print("="*60)

        while True:
            print("\nOptions:")
            print("  [Enter] Scrape current page results")
            print("  [q]     Quit and save")

            try:
                choice = input("\nPress Enter to scrape, or 'q' to quit: ").strip().lower()
            except EOFError:
                choice = ""

            if choice == 'q':
                break

            # Scrape current page
            new_contacts = self.scrape_current_page()
            self.contacts.extend(new_contacts)

            print(f"\nTotal contacts collected: {len(self.contacts)}")

        # Save and close
        self.save_contacts()
        self.close_browser()

        print(f"\n{'='*60}")
        print(f"DONE! Collected {len(self.contacts)} contacts.")
        print(f"{'='*60}")


def main():
    scraper = UWDirectoryScraper()
    try:
        scraper.run_interactive()
    except KeyboardInterrupt:
        print("\n\n⏹ Stopped by user")
        scraper.save_contacts()
        scraper.close_browser()


if __name__ == "__main__":
    main()
