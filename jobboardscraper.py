import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager


def setup_driver():
    """Set up headless Firefox WebDriver for GitHub Actions."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=options)


def scrape_workday_jobs():
    """Scrape all job listings from Schweiger Dermatology's Workday site."""
    driver = setup_driver()
    wait = WebDriverWait(driver, 45)
    url = "https://schweigerderm.wd12.myworkdayjobs.com/en-US/SchweigerCareers"
    driver.get(url)

    print("🌐 Opening Schweiger Dermatology Careers page...")

    # Wait for total job count
    job_count_text = None
    for _ in range(5):
        try:
            count_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2[data-automation-id='jobCount']")))
            job_count_text = count_elem.text.strip()
            if job_count_text:
                print(f"🔎 Job count text: {job_count_text}")
                break
        except:
            time.sleep(3)

    if not job_count_text:
        print("⚠️ Could not find job count text. Continuing anyway.")

    # Wait for job list
    print("⏳ Waiting for job titles to appear...")
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")))
    time.sleep(2)

    jobs = []
    page_num = 1

    # Helper function to scrape all job cards on the current page
    def scrape_page(page_number):
        job_cards = driver.find_elements(By.CSS_SELECTOR, "li[data-automation-id='compositeJobPosting']")
        print(f"📄 Scraping page {page_number}...")
        print(f"   Found {len(job_cards)} jobs on this page.")

        for i, card in enumerate(job_cards, start=1):
            try:
                title_elem = card.find_element(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")
                title = title_elem.text.strip()
                job_link = title_elem.get_attribute("href")

                # Extract job ID (e.g. R-12345)
                job_id_match = re.search(r"(R-\d+)", job_link)
                job_id = job_id_match.group(1) if job_id_match else "N/A"

                # Extract location, time type, and posting date
                location_elem = card.find_element(By.CSS_SELECTOR, "div[data-automation-id='locations']")
                location = location_elem.text.strip() if location_elem else "N/A"

                time_type_elem = card.find_element(By.CSS_SELECTOR, "div[data-automation-id='timeType']")
                time_type = time_type_elem.text.strip() if time_type_elem else "N/A"

                posted_elem = card.find_element(By.CSS_SELECTOR, "div[data-automation-id='postedOn']")
                posted_on = posted_elem.text.strip() if posted_elem else "N/A"

                # Open detail page in a new tab
                driver.execute_script("window.open(arguments[0]);", job_link)
                driver.switch_to.window(driver.window_handles[-1])
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")))

                desc_elem = driver.find_element(By.CSS_SELECTOR, "div[data-automation-id='jobPostingDescription']")
                description_html = desc_elem.get_attribute("outerHTML")

                apply_link_elem = driver.find_element(By.CSS_SELECTOR, "a[data-automation-id='applyButton']")
                apply_link = apply_link_elem.get_attribute("href")

                jobs.append({
                    "Job ID": job_id,
                    "Title": title,
                    "Location": location,
                    "Time Type": time_type,
                    "Posted On": posted_on,
                    "Apply Link": apply_link,
                    "Job Link": job_link,
                    "Description": description_html
                })

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                print(f"   ✅ Scraped job {i}: {title}...")

            except Exception as e:
                print(f"   ⚠️ Error scraping job {i} on page {page_number}: {e}")
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

    # Scrape first page
    scrape_page(page_num)

    # Pagination via numbered buttons
    try:
        time.sleep(2)
        wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "button[data-uxi-widget-type='paginationPageButton']")
        ))
        page_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-uxi-widget-type='paginationPageButton']")
        total_pages = len(page_buttons)
        print(f"🧭 Detected {total_pages} pages of results.")

        for p in range(2, total_pages + 1):
            try:
                page_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f"button[aria-label='page {p}']")))
                first_title_before = driver.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")[0].text.strip()

                driver.execute_script("arguments[0].click();", page_button)
                print(f"⏭️ Navigating to page {p}... Waiting for jobs to refresh...")

                wait.until(lambda d: (
                    d.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']") and
                    d.find_elements(By.CSS_SELECTOR, "a[data-automation-id='jobTitle']")[0].text.strip() != first_title_before
                ))
                time.sleep(2)

                scrape_page(p)

            except Exception as e:
                print(f"⚠️ Pagination failed at page {p}: {e}")
                break

    except Exception as e:
        print(f"⏹️ Pagination setup failed: {e}")

    driver.quit()

    # Save CSV
    df = pd.DataFrame(jobs)
    csv_name = "schweiger_jobs_formatted.csv"
    df.to_csv(csv_name, index=False, encoding="utf-8-sig")
    print(f"📦 Done! Scraped {len(df)} jobs out of expected {job_count_text or 'Unknown'}.")
    print(f"💡 File saved as '{csv_name}' with full HTML formatting in descriptions.")


if __name__ == "__main__":
    scrape_workday_jobs()
