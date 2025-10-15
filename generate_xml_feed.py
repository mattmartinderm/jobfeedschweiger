import pandas as pd
import html
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# -------------------------------------------------------
# format text 
# -------------------------------------------------------
def format_text_description(raw_html):
    """Convert HTML to clean, readable plain text with proper bullet indentation and spacing."""
    import math
    if not raw_html or (isinstance(raw_html, float) and math.isnan(raw_html)):
        return ""

    raw_html = str(raw_html)
    soup = BeautifulSoup(raw_html, "html.parser")

    # Replace <a> tags with text + (URL)
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        a.replace_with(f"{text} ({href})" if href else text)

    # Add newlines around structural tags
    for tag in soup.find_all(["p", "div", "br", "ul", "ol", "h1", "h2", "h3"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    # Handle bullet points with indentation for nested lists
    for li in soup.find_all("li"):
        indent = ""
        parent = li.parent
        while parent and parent.name in ["ul", "ol"]:
            indent += "  "
            parent = parent.parent
        li.insert_before(f"\n{indent}• ")
        li.insert_after("\n")

    # Extract text and clean up
    text = soup.get_text(" ", strip=True)
    text = html.unescape(text)

    # Normalize spaces and punctuation
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(•\s*)+", "• ", text)  # Remove duplicate bullets
    text = re.sub(r"\s*•\s*", r"\n• ", text)  # Ensure bullet starts on new line
    text = re.sub(r"\n\s*•", r"\n•", text)  # Clean up spaces before bullets
    text = re.sub(r"\.\s+(?=[A-Z])", ".\n\n", text)  # Break paragraphs naturally
    text = re.sub(r":(?=\S)", ": ", text)

    # Add extra blank lines before section headers
    headers = [
        "Schweiger Dermatology Group's Ultimate Employee Experience",
        "Job Summary", "Schedule", "Travel", "Essential Functions",
        "Qualifications", "Hourly Pay Range", "Salary Range"
    ]
    for header in headers:
        text = re.sub(fr"\s*{header}\s*:", f"\n\n{header}:\n", text)

    # Fix double-bulleted or crammed lines
    text = re.sub(r"• ([^•]+) •", r"• \1\n• ", text)

    # Normalize blank lines
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
