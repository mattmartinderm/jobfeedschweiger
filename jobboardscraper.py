import json
import re
import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from xml.etree.ElementTree import Element, SubElement, ElementTree


def ts():
    return datetime.now().strftime("%H:%M:%S")


def setup_driver():
    print(f"[{ts()}] 🧩 Setting up Chrome WebDriver...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    print(f"[{ts()}] ✅ WebDriver ready.")
    return driver


# ────────────────────────────────────────────────
# ✅ PHASE 1 – Collect job listings from Workday
# ────────────────────────────────────────────────
def collect_jobs():
    url = "https://schweigerderm.wd12.myworkdayjobs.com/en-US/SchweigerCareers"
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)

    print(f"[{ts()}] 🌐 Opening {url}")
    driver.get(url)

    # Wait for job count
    job_count_text = ""
    for attempt in range(10):
        try:
            elem = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "p[data-automation-id='jobFoundText']"))
            )
            job_count_text = elem.text.strip()
            if re.search(r"\d+", job_count_text):
                print(f"[{ts()}] 🔍 Attempt {attempt+1}: jobFoundText = '{job_count_text}'")
                break
            else:
                print(f"[{ts()}] ⏳ Attempt {attempt+1}: jobFoundText = '{job_count_text}'")
            time.sleep(1)
        except Exception as e:
            print(f"[{ts()}] ⚠️ Attempt {attempt+1} failed: {e}")
            time.sleep(1)

    total_jobs = int(re.search(r"(\d+)", job_count_text).group(1)) if re.search(r"\d+", job_count_text) else 0
    print(f"[{ts()}] 📊 Total jobs found: {total_jobs}")

    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
    time.sleep(1)

    all_jobs = []
    seen_job_ids = set()
    page = 1

    def scrape_page():
        links = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
        print(f"[{ts()}] 📄 Scraping page {page} — found {len(links)} jobs.")
        for i, link in enumerate(links, start=1):
            try:
                title = link.text.strip()
                href = link.get_attribute("href")
                job_id_match = re.search(r"(\d{3,5}-\d+|R-\d+)", href)
                job_id = job_id_match.group(1) if job_id_match else "N/A"

                container = link.find_element(By.XPATH, "./ancestor::li[1]")

                def safe(selector):
                    try:
                        return container.find_element(By.CSS_SELECTOR, selector).text.strip()
                    except:
                        return "N/A"

                location = safe("div[data-automation-id='locations']")
                time_type = safe("div[data-automation-id='timeType']")
                posted_on = safe("div[data-automation-id='postedOn']")

                job_data = {
                    "jobid": job_id,
                    "title": title,
                    "location": location,
                    "time_type": time_type,
                    "posted_on": posted_on,
                    "job_link": href,
                }
                all_jobs.append(job_data)
                seen_job_ids.add(job_id)
                print(f"   ▶️ {job_id} | {title} | {location}")
            except Exception as e:
                print(f"   ⚠️ Error scraping job {i}: {e}")

    scrape_page()

    # Pagination
    try:
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uxi-widget-type='paginationPageButton']")
        total_pages = len(page_buttons)
        print(f"[{ts()}] 🧭 Detected {total_pages} pages total.")

        for p in range(2, total_pages + 1):
            try:
                print(f"[{ts()}] ⏭️ Navigating to page {p}...")
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[aria-label='page {p}']"))
                )
                last_seen = list(seen_job_ids)
                driver.execute_script("arguments[0].click();", button)
                print(f"[{ts()}]    🔄 Clicked page {p}, waiting for new jobs...")

                WebDriverWait(driver, 10).until(lambda d: any(
                    (re.search(r"(\d{3,5}-\d+|R-\d+)", a.get_attribute("href")) and
                     re.search(r"(\d{3,5}-\d+|R-\d+)", a.get_attribute("href")).group(1)) not in last_seen
                    for a in d.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
                ))

                time.sleep(1)
                page = p
                scrape_page()
            except Exception as e:
                print(f"[{ts()}] ⚠️ Pagination failed on page {p}: {e}")
                break
    except Exception as e:
        print(f"[{ts()}] ⚠️ Pagination setup failed: {e}")

    driver.quit()
    print(f"[{ts()}] 📦 Done! Collected {len(all_jobs)} jobs total.")

    with open("workday_jobs_list.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)
    print(f"[{ts()}] 💾 Saved as 'workday_jobs_list.json'. ✅")

    return all_jobs


# ────────────────────────────────────────────────
# ✅ PHASE 2 – Scrape full job descriptions + create XML
# ────────────────────────────────────────────────
def scrape_job_descriptions(jobs):
    driver = setup_driver()
    wait = WebDriverWait(driver, 20)
    results = []

    for i, job in enumerate(jobs, start=1):
        link = job["job_link"]
        print(f"[{ts()}] 🌐 ({i}/{len(jobs)}) Opening {link}")
        try:
            driver.get(link)
            desc_elem = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']"))
            )
            description_html = desc_elem.get_attribute("outerHTML")
            job["description"] = description_html
            results.append(job)
            print(f"   ✅ Scraped {job['jobid']} — {job['title']}")
        except Exception as e:
            print(f"   ⚠️ Failed to scrape {link}: {e}")
            job["description"] = ""
            results.append(job)

    driver.quit()
    print(f"[{ts()}] 📦 Done scraping {len(results)} job descriptions.")

    # CSV
    csv_file = "workday_jobs_full.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["jobid", "title", "location", "time_type", "posted_on", "job_link", "description"])
        for j in results:
            writer.writerow([
                j.get("jobid", ""),
                j.get("title", ""),
                j.get("location", ""),
                j.get("time_type", ""),
                j.get("posted_on", ""),
                j.get("job_link", ""),
                j.get("description", ""),
            ])
    print(f"[{ts()}] 💾 CSV saved as '{csv_file}'")

    # XML (clean for JBoard)
    root = Element("jobs")

    for j in results:
        job_el = SubElement(root, "job")
        SubElement(job_el, "jobid").text = j.get("jobid", "")
        SubElement(job_el, "title").text = j.get("title", "")
        SubElement(job_el, "location").text = j.get("location", "")
        SubElement(job_el, "time_type").text = j.get("time_type", "")
        SubElement(job_el, "posted_on").text = j.get("posted_on", "")
        SubElement(job_el, "job_link").text = j.get("job_link", "")

        raw_html = j.get("description", "")
        soup = BeautifulSoup(raw_html, "html.parser")
        main_div = soup.find("div", {"data-automation-id": "jobPostingDescription"})
        if main_div:
            cleaned_html = ''.join(str(child) for child in main_div.contents)
        else:
            cleaned_html = raw_html

        # Remove style + class attributes
        for tag in soup.find_all(True):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in ["href", "target", "rel"]}

        desc_el = SubElement(job_el, "description")
        desc_el.text = f"<![CDATA[{cleaned_html.strip()}]]>"

    xml_file = "workday_jobs_full.xml"
    ElementTree(root).write(xml_file, encoding="utf-8", xml_declaration=True)
    print(f"[{ts()}] 💾 XML saved as '{xml_file}' ✅")


# ────────────────────────────────────────────────
# ✅ MAIN EXECUTION
# ────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[{ts()}] 🚀 Job board scrape started at {datetime.now()}")
    jobs = collect_jobs()
    scrape_job_descriptions(jobs)
    print(f"[{ts()}] 🏁 All done!")
