import csv
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

# Input and output file names
INPUT_CSV = "workday_jobs_full.csv"
OUTPUT_XML = "schweiger_jobs.xml"

def clean_html_keep_text(html):
    """Removes all HTML tags and keeps readable text only."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text

def clean_posted_on(raw):
    """Removes any version of 'posted', 'Posted on', etc."""
    if not raw:
        return ""
    text = raw.strip()
    # Remove any case-insensitive 'posted' words and 'on'
    text = text.replace("\n", " ")
    words = text.split()
    cleaned = " ".join([w for w in words if w.lower() not in {"posted", "on"}])
    return cleaned.strip()

def main():
    jobs = []

    # Read the CSV file
    with open(INPUT_CSV, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            jobs.append({
                "jobid": row.get("jobid", "").strip(),
                "title": row.get("title", "").strip(),
                "location": row.get("location", "").replace("locations ", "").strip(),
                "time_type": row.get("time_type", "").strip(),
                "posted_on": clean_posted_on(row.get("posted_on", "")),
                "job_link": row.get("job_link", "").strip(),
                "description": clean_html_keep_text(row.get("description", "")),
            })

    # Create XML structure
    root = ET.Element("jobs")

    for job in jobs:
        job_elem = ET.SubElement(root, "job")

        ET.SubElement(job_elem, "jobid").text = job["jobid"]
        ET.SubElement(job_elem, "title").text = job["title"]
        ET.SubElement(job_elem, "location").text = job["location"]
        ET.SubElement(job_elem, "time_type").text = job["time_type"]
        ET.SubElement(job_elem, "posted_on").text = job["posted_on"]
        ET.SubElement(job_elem, "job_link").text = job["job_link"]

        # Add description wrapped in CDATA
        desc_elem = ET.SubElement(job_elem, "description")
        desc_elem.text = f"<![CDATA[{job['description']}]]>"

    # Write the XML file
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_XML, encoding="utf-8", xml_declaration=True)

    print(f"✅ XML feed created: {OUTPUT_XML} with {len(jobs)} jobs.")

if __name__ == "__main__":
    main()
