import pandas as pd
import html
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# -------------------------------------------------------
def format_text_description(raw_html):
    """Convert HTML to readable plain text with line breaks and bullet points."""
    import math
    if not raw_html or (isinstance(raw_html, float) and math.isnan(raw_html)):
        return ""

    raw_html = str(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")

    # Replace <a> with text + (URL)
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        a.replace_with(f"{text} ({href})" if href else text)

    # Convert <li> into line-bulleted items
    for li in soup.find_all("li"):
        li.insert_before("\n• ")
        li.insert_after("\n")

    # Add blank lines between paragraphs, headers, and sections
    for tag in soup.find_all(["p", "div", "ul", "ol", "br", "h1", "h2", "h3"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    # Get raw text and clean up
    text = soup.get_text(separator=" ", strip=True)
    text = html.unescape(text)

    # Replace multiple spaces and punctuation issues
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\S)\s*•", r"\1\n•", text)  # Start bullets on new lines
    text = re.sub(r"(\.)([A-Z])", r"\1\n\n\2", text)  # Paragraph spacing
    text = re.sub(r"\n{3,}", "\n\n", text)  # Limit blank lines
    text = re.sub(r"\n\s+", "\n", text)  # Trim line starts

    # Add line breaks before key section headers
    headers = [
        "Schweiger Dermatology Group's Ultimate Employee Experience",
        "Job Summary:", "Schedule:", "Travel:", "Essential Functions:",
        "Qualifications:", "Hourly Pay Range", "Salary Range"
    ]
    for header in headers:
        text = re.sub(fr"\s*{header}", f"\n\n{header}\n", text)

    return text.strip()


# -------------------------------------------------------
# Generate XML feed
# -------------------------------------------------------
def generate_xml():
    print("🧩 Generating XML feed with professional formatting...")

    # Load CSV
    df = pd.read_csv("workday_jobs_full.csv")

    root = ET.Element("jobs")

    for _, row in df.iterrows():
        job = ET.SubElement(root, "job")

        # Match CSV headers exactly
        ET.SubElement(job, "jobid").text = str(row.get("jobid", "")).strip()
        ET.SubElement(job, "title").text = str(row.get("title", "")).strip()
        ET.SubElement(job, "location").text = str(row.get("location", "")).replace("locations", "").strip()
        ET.SubElement(job, "time_type").text = str(row.get("time_type", "N/A")).strip()

        # Remove "posted" from the posted_on field
        posted_clean = str(row.get("posted_on", "")).replace("posted on", "").replace("Posted", "").strip()
        ET.SubElement(job, "posted_on").text = posted_clean

        ET.SubElement(job, "job_link").text = str(row.get("job_link", "")).strip()

        # Clean and format description
        description_raw = row.get("description", "")
        description_clean = format_text_description(description_raw)

        desc_element = ET.SubElement(job, "description")
        desc_element.text = f"<![CDATA[{description_clean}]]>"

    # Write final XML
    tree = ET.ElementTree(root)
    tree.write("schweiger_jobs.xml", encoding="utf-8", xml_declaration=True)
    print("✅ XML feed generated successfully as 'schweiger_jobs.xml'")

# -------------------------------------------------------
# Run
# -------------------------------------------------------
if __name__ == "__main__":
    generate_xml()
