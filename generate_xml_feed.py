import pandas as pd
import html
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# -------------------------------------------------------
# Clean & format the job description text
# -------------------------------------------------------
def format_text_description(raw_html):
    """Convert HTML to clean, structured plain text with readable formatting."""
    import math
    if not raw_html or (isinstance(raw_html, float) and math.isnan(raw_html)):
        return ""

    raw_html = str(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")

    # Replace anchor tags with plain text (keep URL in parentheses)
    for a in soup.find_all("a"):
        link_text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        if href:
            a.replace_with(f"{link_text} ({href})")
        else:
            a.replace_with(link_text)

    # Add bullets and indentation for <li> tags (nested list support)
    for li in soup.find_all("li"):
        depth = 0
        parent = li.parent
        while parent and parent.name == "ul":
            depth += 1
            parent = parent.parent
        indent = "  " * (depth - 1) if depth > 1 else ""
        li.insert_before(f"\n{indent}• ")
        li.insert_after("\n")

    # Add spacing before/after paragraphs and lists
    for tag in soup.find_all(["p", "div", "ul", "br"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text(" ", strip=True)
    text = html.unescape(text)

    # Clean up spacing inside parentheses
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)

    # Bold key section headers
    headers = [
        "Schweiger Dermatology Group's Ultimate Employee Experience",
        "Job Summary:", "Schedule:", "Travel:", "Essential Functions:",
        "Qualifications:", "Hourly Pay Range", "Salary Range"
    ]
    for header in headers:
        text = re.sub(fr"\s*{header}", f"\n\n**{header}**", text)

    # Add spacing before bullets for clear separation
    text = re.sub(r"(\S)\s*•", r"\1\n•", text)

    # Normalize multiple newlines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Clean stray spaces at line starts
    text = re.sub(r"\n\s+", "\n", text)

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
