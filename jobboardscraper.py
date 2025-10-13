import time
import json
import re
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager


# ---------- Utility ----------
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


# ---------- WebDriver ----------
def setup_driver():
    log("🧩 Setting up Firefox WebDriver...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.log.level = "fatal"

    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)

    log("✅ WebDriver ready.")
    return driver


# ---------- Phase 1: Collect job list ----------
def collect_jobs():
    driver = setup_driver()
    url = "https://schweigerderm.wd12.myworkdayjobs.com/en-US/SchweigerCareers"
    log(f"🌐 Opening {url}")
    driver.get(url)

    # Wait for job count text
    job_count = None
    for i in range(1, 10):
        try:
            elem = driver.find_element(By.CSS_SELECTOR, "p[data-automation-id='jobFoundText']")
            txt = elem.text.strip()
            if "JOB" in txt:
                job_count = txt
                break
            log(f"⏳ Attempt {i}: jobFoundText = '{txt}'")
            time.sleep(1)
        except Exception:
            time.sleep(1)

    if not job_count:
        raise RuntimeError("❌ Could not locate job count text.")

    total_jobs = int(re.search(r"(\d+)", job_count).group(1))
    log(f"📊 Total jobs found: {total_jobs}")

    jobs = []
    wait = WebDriverWait(driver, 10)

    page = 1
    while True:
        log(f"📄 Scraping page {page}...")
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
        job_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-automation-id='compositeSubHeader']")

        log(f"   Found {len(job_cards)} job cards.")
        for card in job_cards:
            try:
                title_el = card.find_element(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
                job_title = title_el.text.strip()
                job_href = title_el.get_attribute("href")
                job_id_match = re.search(r"([A-Za-z0-9-]+)$", job_href)
                job_id = job_id_match.group(1) if job_id_match else "N/A"

                # new, robust location selector
                try:
                    loc_el = card.find_element(By.CSS_SELECTOR, "div[data-automation-id='locations'] span")
                    location = loc_el.text.strip()
                except Exception:
                    location = "N/A"

                jobs.append({
                    "Job ID": job_id,
                    "Title": job_title,
                    "Location": location,
                    "Job Link": job_href
                })
                log(f"   ▶️ {job_id} | {job_title} | {location}")
            except Exception as e:
                log(f"    ⚠️ Error parsing a job card: {e}")

        # Pagination
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, f"ul[role='list'] li[data-uxi-pagination-page='{page + 1}'] button")
            if not next_btn.is_enabled():
                break
            page += 1
            log(f"⏭️ Navigating to page {page}...")
            next_btn.click()
            time.sleep(2)
        except Exception:
            break

        if len(jobs) >= total_jobs:
            break

    driver.quit()
    log(f"📦 Done! Collected {len(jobs)} jobs total.")

    with open("workday_jobs_list.json", "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2)
    log("💾 Saved as 'workday_jobs_list.json'. ✅")
    return jobs


# ---------- Main ----------
if __name__ == "__main__":
    start = datetime.now()
    log(f"🚀 Job board scrape started at {start.strftime('%Y-%m-%d %H:%M:%S')}")

    # Phase 1
    jobs = collect_jobs()

    # Phase 2
    scrape_job_details(jobs)

    end = datetime.now()
    log(f"🏁 Finished in {(end - start).seconds}s total.")
