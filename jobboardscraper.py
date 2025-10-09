import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def setup_driver():
    """Set up a headless Firefox driver."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)

def scrape_workday_jobs():
    """Scrapes Schweiger Dermatology Workday job listings and saves to CSV."""
    base_url = "https://schweigerderm.wd12.myworkdayjobs.com/en-US/SchweigerCareers"
    driver = setup_driver()
    driver.get(base_url)
    wait = WebDriverWait(driver, 45)

    print("🌐 Opening Schweiger Dermatology Careers page...")

    # Wait for job count text
    try:
        job_count_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-automation-id='jobCount']")))
        job_count_text = job_count_el.text.strip()
        print(f"🔎 Job count text: {job_count_text}")
    except Exception:
        print("⚠️  Could not find job count text.")
        job_count_text = "Unknown"

    # Wait for job titles
    print("⏳ Waiting for job titles to appear...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))

    all_jobs = []
    total_jobs_scraped = 0
    page_num = 1

    while True:
        print(f"📄 Scraping page {page_num}...")
        time.sleep(2)

        job_links = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
        print(f"   Found {len(job_links)} jobs on this page.")

        for index, job_link in enumerate(job_links, start=1):
            try:
                title = job_link.text.strip()
                job_url = job_link.get_attribute("href")

                # ✅ Extract Job ID (e.g., R-195)
                job_id_match = re.search(r"(R-\d+)", job_url)
                job_id = job_id_match.group(1) if job_id_match else "N/A"

                driver.execute_script("arguments[0].scrollIntoView(true);", job_link)
                job_link.click()

                # Wait for description page to load
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")))
                time.sleep(1)

                # Extract fields
                try:
                    location_elems = driver.find_elements(By.CSS_SELECTOR, "div[data-automation-id='locations'] dd.css-129m7dg")
                    locations = [el.text.strip() for el in location_elems]
                    location_text = ", ".join(locations) if locations else "N/A"
                except:
                    location_text = "N/A"

                try:
                    time_type_el = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='time'] dd.css-129m7dg")
                    time_type = time_type_el.text.strip()
                except:
                    time_type = "N/A"

                try:
                    posted_on_el = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='postedOn'] dd.css-129m7dg")
                    posted_on = posted_on_el.text.strip()
                except:
                    posted_on = "N/A"

                try:
                    description_el = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")
                    description_html = description_el.get_attribute("innerHTML").strip()
                except:
                    description_html = "N/A"

                try:
                    apply_link_el = driver.find_element(By.CSS_SELECTOR, "a[data-automation-id='adventureButton']")
                    apply_link = apply_link_el.get_attribute("href")
                except:
                    apply_link = job_url

                # ✅ Store job data
                job_data = {
                    "Job ID": job_id,
                    "Title": title,
                    "Location": location_text,
                    "Time Type": time_type,
                    "Posted On": posted_on,
                    "Description": description_html,
                    "Apply Link": apply_link,
                    "Job Link": job_url
                }
                all_jobs.append(job_data)
                total_jobs_scraped += 1

                print(f"   ✅ Scraped job {total_jobs_scraped}: {title}...")

                driver.back()
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
                time.sleep(1)

            except Exception as e:
                print(f"⚠️  Error scraping job {index}: {e}")
                driver.back()
                time.sleep(2)
                continue

        # Pagination
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
            if next_button.is_enabled():
                driver.execute_script("arguments[0].click();", next_button)
                page_num += 1
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
                time.sleep(2)
            else:
                print("⏹️ Reached last page or could not find next button.")
                break
        except:
            print("⏹️ Reached last page or could not find next button.")
            break

    driver.quit()

    df = pd.DataFrame(all_jobs)
    df.to_csv("schweiger_jobs_formatted.csv", index=False, encoding="utf-8-sig")
    print(f"📦 Done! Scraped {total_jobs_scraped} jobs out of expected {job_count_text}.")
    print("💡 File saved as 'schweiger_jobs_formatted.csv' with full HTML formatting in descriptions.")

if __name__ == "__main__":
    scrape_workday_jobs()
