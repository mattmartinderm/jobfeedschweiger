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
    """Set up Firefox WebDriver."""
    options = Options()
    options.add_argument("--width=1400")
    options.add_argument("--height=900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
    return driver


def clean_html(raw_html: str) -> str:
    """Trim unwanted text but preserve basic HTML structure."""
    # Remove script/style if any, but keep p/li/b/i/u tags
    raw_html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", raw_html)
    raw_html = re.sub(r"\s+", " ", raw_html)
    raw_html = raw_html.replace("Apply Now", "").strip()
    return raw_html


def scrape_workday_jobs():
    """Scrape Schweiger Dermatology jobs with formatted descriptions."""
    url = "https://schweigerderm.wd12.myworkdayjobs.com/SchweigerCareers"
    driver = setup_driver()
    wait = WebDriverWait(driver, 45)
    driver.get(url)
    print("🌐 Opening Schweiger Dermatology Careers page...")

    # Wait for job count text to show number
    count_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p[data-automation-id='jobFoundText']")))
    for _ in range(60):
        text = count_elem.text.strip()
        if text and text[0].isdigit():
            break
        time.sleep(0.5)
    total_jobs_text = count_elem.text.strip()
    print(f"🔎 Job count text: {total_jobs_text}")

    total_jobs = 0
    for token in total_jobs_text.split():
        if token.isdigit():
            total_jobs = int(token)
            break

    print("⏳ Waiting for job titles to appear...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
    time.sleep(2)

    all_jobs = []
    page = 1

    while True:
        print(f"\n📄 Scraping page {page}...")
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
        print(f"   Found {len(job_links)} jobs on this page.")

        for i in range(len(job_links)):
            try:
                job_links = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
                if i >= len(job_links):
                    break

                title_elem = job_links[i]
                title = title_elem.text.strip()
                job_href = title_elem.get_attribute("href")

                driver.execute_script("arguments[0].scrollIntoView(true);", title_elem)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", title_elem)

                # Wait for job details
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")))
                time.sleep(1)

                # Description with HTML formatting preserved
                desc_elem = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")
                description_html = clean_html(desc_elem.get_attribute("innerHTML"))

                # Extract Locations (may have multiple)
                try:
                    loc_container = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='locations']")
                    location_elems = loc_container.find_elements(By.CSS_SELECTOR, "dd.css-129m7dg")
                    locations = " | ".join([loc.text.strip() for loc in location_elems if loc.text.strip()])
                except:
                    locations = "N/A"

                # Extract Time Type
                try:
                    time_type_elem = driver.find_element(By.XPATH, "//dt[normalize-space(text())='time type']/following-sibling::dd")
                    time_type = time_type_elem.text.strip()
                except:
                    time_type = "N/A"

                # Extract Posted On
                try:
                    posted_elem = driver.find_element(By.XPATH, "//dt[normalize-space(text())='posted on']/following-sibling::dd")
                    posted_on = posted_elem.text.strip()
                except:
                    posted_on = "N/A"

                # Extract Apply Link
                try:
                    apply_elem = driver.find_element(By.CSS_SELECTOR, "a[data-automation-id='adventureButton']")
                    apply_link = apply_elem.get_attribute("href")
                except:
                    apply_link = job_href

                all_jobs.append({
                    "Job Title": title,
                    "Time Type": time_type,
                    "Location(s)": locations,
                    "Date Posted": posted_on,
                    "Job URL": job_href,
                    "Apply URL": apply_link,
                    "Description (HTML)": description_html
                })
                print(f"   ✅ Scraped job {len(all_jobs)}: {title[:60]}...")

                driver.back()
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
                time.sleep(1)

            except Exception as e:
                print(f"⚠️  Error scraping job {i + 1}: {e}")
                try:
                    driver.back()
                    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
                except:
                    pass
                continue

        # Move to next page
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button[data-uxi-element-id='next']")
            if "disabled" in next_button.get_attribute("class"):
                print("⏹️ No more pages.")
                break
            driver.execute_script("arguments[0].click();", next_button)
            page += 1
            time.sleep(4)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
        except Exception:
            print("⏹️ Reached last page or could not find next button.")
            break

    driver.quit()

    df = pd.DataFrame(all_jobs)
    csv_name = "schweiger_jobs_formatted.csv"
    df.to_csv(csv_name, index=False)
    print(f"\n📦 Done! Scraped {len(df)} jobs out of expected {total_jobs}.")
    print(f"💡 File saved as '{csv_name}' with full HTML formatting in descriptions.")


if __name__ == "__main__":
    scrape_workday_jobs()
