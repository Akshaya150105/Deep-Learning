import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Base URL
BASE_URL = "https://www.nhs.uk/conditions/"

# Output file
OUTPUT_FILE = "nhs_conditions_all.json"

# Log file
LOG_FILE = "scrape_log.txt"

# Headers for requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to log messages
def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{time.ctime()}: {message}\n")
    print(message)

# Function to scrape a single condition page
def scrape_condition_page(url, use_selenium=False):
    log_message(f"Scraping {url} (Selenium: {use_selenium})")
    try:
        if use_selenium:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
        else:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

        # Extract condition name
        title = soup.find("h1")
        condition_name = title.get_text(strip=True) if title else "Unknown"
        if condition_name.startswith("Overview-"):
            condition_name = condition_name.replace("Overview-", "").strip()
        log_message(f"Condition: {condition_name}")

        # Check for "Contents" menu and symptoms subpage
        symptoms_url = None
        contents = soup.find("nav", {"aria-label": "Contents"}) or soup.find("div", class_="nhsuk-contents-list")
        if contents:
            for link in contents.find_all("a", href=True):
                if "symptoms" in link.get_text(strip=True).lower():
                    symptoms_url = urljoin(url, link["href"])
                    break

        # Extract symptoms
        symptoms = []
        symptoms_section = None
        for tag in soup.find_all(["h2", "h3", "h4"]):
            tag_text = tag.get_text(strip=True).lower()
            if "symptoms" in tag_text or "signs" in tag_text:
                symptoms_section = tag
                break

        # Try symptoms subpage
        if symptoms_url and symptoms_url != url:
            log_message(f"Trying symptoms subpage: {symptoms_url}")
            try:
                sub_response = requests.get(symptoms_url, headers=HEADERS)
                sub_response.raise_for_status()
                sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                sub_content = sub_soup.find("main") or sub_soup.find("div", class_="nhsuk-grid-column-two-thirds")
                if sub_content:
                    for ul in sub_content.find_all("ul"):
                        symptoms.extend([li.get_text(strip=True) for li in ul.find_all("li") if li.get_text(strip=True)])
                    for p in sub_content.find_all("p"):
                        text = p.get_text(strip=True)
                        if text and any(k in text.lower() for k in ["include", "such as", ":"]) and not any(k in text.lower() for k in ["treatment", "relieve", "take ", "use ", "medicine", "paracetamol", "ibuprofen", "what is", "cause", "test", "support"]):
                            symptom_text = text.split(":", 1)[-1].strip() if ":" in text else text
                            symptom_list = [s.strip() for s in symptom_text.replace(" and ", ", ").split(",") if s.strip()]
                            symptoms.extend(symptom_list)
            except Exception as e:
                log_message(f"Error fetching symptoms subpage {symptoms_url}: {str(e)}")

        # Try main page symptoms section
        if symptoms_section and not symptoms:
            current_element = symptoms_section.find_next()
            while current_element and current_element.name not in ["h2", "h3", "h4"]:
                if current_element.name == "ul":
                    symptoms.extend([li.get_text(strip=True) for li in current_element.find_all("li") if li.get_text(strip=True)])
                elif current_element.name == "p":
                    text = current_element.get_text(strip=True)
                    if text and any(k in text.lower() for k in ["include", "such as", ":"]) and not any(k in text.lower() for k in ["treatment", "relieve", "take ", "use ", "medicine", "paracetamol", "ibuprofen", "what is", "cause", "test", "support"]):
                        symptom_text = text.split(":", 1)[-1].strip() if ":" in text else text
                        symptom_list = [s.strip() for s in symptom_text.replace(" and ", ", ").split(",") if s.strip()]
                        symptoms.extend(symptom_list)
                current_element = current_element.find_next()

        # Fallback: Check overview for symptoms (e.g., ADPKD)
        if not symptoms:
            overview_section = soup.find("h2", string=lambda x: x and "overview" in x.lower())
            if overview_section:
                current_element = overview_section.find_next()
                while current_element and current_element.name not in ["h2", "h3", "h4"]:
                    if current_element.name == "ul":
                        symptoms.extend([li.get_text(strip=True) for li in current_element.find_all("li") if li.get_text(strip=True)])
                    elif current_element.name == "p":
                        text = current_element.get_text(strip=True)
                        if text and any(k in text.lower() for k in ["include", "can cause", "problems"]) and not any(k in text.lower() for k in ["treatment", "relieve", "take ", "use ", "medicine", "paracetamol", "ibuprofen", "what is", "cause", "test", "support"]):
                            symptom_list = [s.strip() for s in text.replace(" and ", ", ").split(",") if s.strip()]
                            symptoms.extend([s for s in symptom_list if any(k in s.lower() for k in ["pain", "pressure", "blood", "infection", "stone", "swelling", "fever", "fatigue", "rash", "bleeding"])])
                    current_element = current_element.find_next()

        symptoms = list(dict.fromkeys([s for s in symptoms if s and len(s) > 3 and not any(k in s.lower() for k in ["what is", "causes", "treatment", "test", "support"])]))
        log_message(f"Symptoms: {len(symptoms)} found")

        # Extract overview
        overview = []
        main_content = soup.find("main") or soup.find("div", class_="nhsuk-grid-column-two-thirds")
        if main_content:
            overview_section = soup.find("h2", string=lambda x: x and "overview" in x.lower()) or main_content.find("h2")
            if overview_section:
                current_element = overview_section.find_next()
                while current_element and current_element.name not in ["h2", "h3", "h4"]:
                    if current_element.name == "p":
                        text = current_element.get_text(strip=True)
                        if text and len(text) > 10 and not any(k in text.lower() for k in ["javascript", "nhs", "cookie", "treatment", "relieve", "medicine", "paracetamol", "ibuprofen", "include", "such as"]):
                            overview.append(text)
                    current_element = current_element.find_next()
            else:
                # Fallback: First few paragraphs in main content
                for p in main_content.find_all("p")[:3]:
                    text = p.get_text(strip=True)
                    if text and len(text) > 10 and not any(k in text.lower() for k in ["javascript", "nhs", "cookie", "treatment", "relieve", "medicine", "paracetamol", "ibuprofen", "include", "such as"]):
                        overview.append(text)
        overview = " ".join(overview) if overview else ""
        log_message(f"Overview: {overview[:50]}..." if overview else "No overview")

        data = {
            "condition": condition_name,
            "symptoms": symptoms,
            "overview": overview,
            "url": url
        }
        return data

    except Exception as e:
        log_message(f"Error scraping {url}: {str(e)}")
        return None

# Function to get condition URLs from A-Z page
def get_condition_urls():
    log_message("Fetching condition URLs from A-Z...")
    try:
        condition_urls = []
        response = requests.get(BASE_URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find lists containing condition links
        lists = soup.find_all("ul")
        for ul in lists:
            links = ul.find_all("a", href=True)
            for link in links:
                href = link["href"]
                text = link.get_text(strip=True)
                if "/conditions/" in href and not href.endswith("/conditions/") and not text.lower().startswith(("see ", "back to")):
                    full_url = urljoin(BASE_URL, href)
                    condition_urls.append(full_url)

        if not condition_urls:
            log_message("No links found with requests; trying Selenium")
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(BASE_URL)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "ul")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            driver.quit()
            lists = soup.find_all("ul")
            for ul in lists:
                links = ul.find_all("a", href=True)
                for link in links:
                    href = link["href"]
                    text = link.get_text(strip=True)
                    if "/conditions/" in href and not href.endswith("/conditions/") and not text.lower().startswith(("see ", "back to")):
                        full_url = urljoin(BASE_URL, href)
                        condition_urls.append(full_url)

        unique_urls = list(set(condition_urls))
        log_message(f"Found {len(unique_urls)} unique URLs")
        return unique_urls

    except Exception as e:
        log_message(f"Error fetching A-Z page: {str(e)}")
        return []

# Function to save data
def save_data(data):
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        log_message(f"Saved {len(data)} entries to {OUTPUT_FILE}")
    except Exception as e:
        log_message(f"Error saving {OUTPUT_FILE}: {str(e)}")

# Function to load existing data
def load_existing_data():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            log_message(f"Loaded {len(data)} entries from {OUTPUT_FILE}")
            return data
        except json.JSONDecodeError:
            log_message("Error reading existing JSON; starting fresh")
    return []

# Main function
def main():
    # Initialize data
    structured_data = load_existing_data()
    scraped_urls = {item["url"] for item in structured_data}

    # Get condition URLs
    condition_urls = get_condition_urls()
    if not condition_urls:
        log_message("No URLs found; saving empty JSON")
        save_data(structured_data)
        return

    # Filter out scraped URLs
    condition_urls = [url for url in condition_urls if url not in scraped_urls]
    log_message(f"Remaining to scrape: {len(condition_urls)}")

    # Scrape all URLs
    for i, url in enumerate(condition_urls, 1):
        log_message(f"Scraping {i}/{len(condition_urls)}: {url}")
        for attempt in range(2):
            condition_data = scrape_condition_page(url, use_selenium=(attempt == 1))
            if condition_data and (condition_data["symptoms"] or condition_data["overview"]):
                structured_data.append(condition_data)
                save_data(structured_data)
                break
            log_message(f"Attempt {attempt + 1} failed for {url}")
        else:
            log_message(f"Failed to scrape {url} after retries")
        time.sleep(2)

    log_message("Scraping complete")

if __name__ == "__main__":
    main()