import pandas as pd
import html
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# -------------------------------------------------------
# format text 
# -------------------------------------------------------
def format_text_description(raw_html):
    """Convert HTML to well-structured plain text with natural line breaks and clean bullet spacing."""
    import math
    if not raw_html or (isinstance(raw_html, float) and math.isnan(raw_html)):
        return ""

    raw_html = str(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")

    # Replace <a> tags with "text (url)"
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        a.replace_with(f"{text} ({href})" if href else text)

    # Add bullet markers and newlines for lists
    for li in soup.find_all("li"):
        li.insert_before("\n• ")
        li.insert_after("\n")

    # Add spacing before and after paragraphs and lists
    for tag in soup.find_all(["p", "div", "ul", "ol", "br", "h1", "h2", "h3"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text(separator=" ", strip=True)
    text = html.unescape(text)

    # Collapse extra spaces
    text = re.sub(r"\s+", " ", text)

    # Ensure single bullet per line
    text = re.sub(r"(•\s*)+", "• ", text)

    # Add newlines before bullets
    text = re.sub(r"(\S)\s*•", r"\1\n•", text)

    # Add double newlines after sentences ending in a period followed by uppercase
    text = re.sub(r"\.\s+(?=[A-Z])", ".\n\n", text)

    # Ensure space after colons
    text = re.sub(r":(?=\S)", ": ", text)

    # Add blank lines before section headers
    headers = [
        "Schweiger Dermatology Group's Ultimate Employee Experience",
        "Job Summary", "Schedule", "Travel", "Essential Functions",
        "Qualifications", "Hourly Pay Range", "Salary Range"
    ]
    for header in headers:
        text = re.sub(fr"\s*{header}\s*:", f"\n\n{header}:\n", text)

    # Normalize extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text

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
