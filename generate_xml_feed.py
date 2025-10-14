import csv
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

# ---------------------------------------------------------------------------
# Helper function to clean and format descriptions
# ---------------------------------------------------------------------------
def clean_description(html_content):
    """Convert HTML into readable plain text while keeping structure."""
    soup = BeautifulSoup(html_content or "", "html.parser")

    # Replace <br> tags with newlines
    for br in soup.find_all("br"):
        br.replace_with("\n")

    # Add bullets for <li> elements
    for li in soup.find_all("li"):
        li.insert_before("• ")
        li.append("\n")

    # Add line breaks after <p> elements
    for p in soup.find_all("p"):
        p.insert_after("\n")

    # Extract readable text
    text = soup.get_text(separator=" ", strip=True)

    # Collapse extra spaces/newlines
    text = re.sub(r'\n\s*\n+', '\n\n', text).strip()

    # Wrap in CDATA so XML remains valid
    return f"<![CDATA[{text}]]>"

# ---------------------------------------------------------------------------
# Main XML feed generator
# ---------------------------------------------------------------------------
def generate_xml_feed(input_csv="workday_jobs_full.csv", output_xml="schweiger_jobs.xml"):
    jobs = []

    # Read from CSV
    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            jobs.append(row)

    # Create XML root
    root = ET.Element("jobs")

    # Iterate through jobs and create elements
    for job in jobs:
        job_elem = ET.SubElement(root, "job")

        ET.SubElement(job_elem, "jobid").text = job.get("jobid", "")
        ET.SubElement(job_elem, "title").text = job.get("title", "")
        ET.SubElement(job_elem, "location").text = job.get("location", "")
        ET.SubElement(job_elem, "time_type").text = job.get("time_type", "")
        ET.SubElement(job_elem, "posted_on").text = job.get("posted_on", "")
        ET.SubElement(job_elem, "job_link").text = job.get("job_link", "")

        # Clean and add job description
        html_description = job.get("description", "")
        description_text = clean_description(html_description)
        ET.SubElement(job_elem, "description").text = description_text

    # Write XML file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_xml, encoding="utf-8", xml_declaration=True)

    print(f"✅ XML feed created: {output_xml} with {len(jobs)} jobs.")

# ---------------------------------------------------------------------------
# Run the script
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    generate_xml_feed()
