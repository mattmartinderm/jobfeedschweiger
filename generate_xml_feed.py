import pandas as pd
import html
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# -------------------------------------------------------
# format text 
# -------------------------------------------------------
def format_html_description(raw_html):
    """Clean HTML but preserve structure for jBoard rendering."""
    import math
    if not raw_html or (isinstance(raw_html, float) and math.isnan(raw_html)):
        return ""

    soup = BeautifulSoup(str(raw_html), "html.parser")

    # Remove unwanted containers, scripts, or styling
    for tag in soup(["script", "style", "meta", "iframe"]):
        tag.decompose()

    # Fix <a> links to show text + clickable URL
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        if href:
            a.replace_with(BeautifulSoup(f'<a href="{href}" target="_blank">{text}</a>', "html.parser"))
        else:
            a.replace_with(text)

    # Normalize <div> and <span> as <p> when they contain text
    for div in soup.find_all("div"):
        if div.get_text(strip=True):
            div.name = "p"
    for span in soup.find_all("span"):
        if span.get_text(strip=True):
            span.unwrap()

    # Replace <br> and empty <p> with real line breaks
    for br in soup.find_all("br"):
        br.replace_with(BeautifulSoup("<br/>", "html.parser"))

    # Simplify list formatting (ensure <ul> and <li> are well-structured)
    for ul in soup.find_all("ul"):
        ul.attrs = {}
    for li in soup.find_all("li"):
        li.attrs = {}

    # Keep only the safe tags
    allowed_tags = {"p", "br", "ul", "ol", "li", "strong", "em", "b", "i", "a"}
    for tag in soup.find_all(True):
        if tag.name not in allowed_tags:
            tag.unwrap()

    # Convert to clean HTML
    cleaned_html = str(soup)
    cleaned_html = cleaned_html.replace("\n", "").strip()

    return cleaned_html


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
