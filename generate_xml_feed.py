import pandas as pd
from bs4 import BeautifulSoup
import re
import html

def format_text_description(raw_html):
    """Convert HTML to clean, structured plain text with readable spacing."""
    if not raw_html:
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # Replace anchor tags with plain text (keep visible text only)
    for a in soup.find_all("a"):
        link_text = a.get_text(" ", strip=True)
        href = a.get("href", "")
        if href:
            a.replace_with(f"{link_text} ({href})")
        else:
            a.replace_with(link_text)

    # Add bullets before <li> tags
    for li in soup.find_all("li"):
        li.insert_before("\n• ")
        li.insert_after("\n")

    # Add spacing around key tags
    for tag in soup.find_all(["p", "div", "ul", "br"]):
        tag.insert_before("\n")
        tag.insert_after("\n")

    text = soup.get_text(" ", strip=True)

    # Decode HTML entities
    text = html.unescape(text)

    # Normalize whitespace and fix spacing
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Add emphasis spacing for major headers
    headers = [
        "Job Summary:", "Schedule:", "Travel:", "Essential Functions:", 
        "Qualifications:", "Salary Range", "Hourly Pay Range"
    ]
    for header in headers:
        text = re.sub(fr"({header})", r"\n\n\1", text)

    # Ensure consistent paragraph breaks
    text = re.sub(r"(\S)\n(\S)", r"\1\n\n\2", text)

    return text.strip()


def generate_xml():
    print("🧩 Generating XML feed with professional formatting...")

    df = pd.read_csv("workday_jobs_full.csv")

    xml_output = ["<?xml version='1.0' encoding='utf-8'?>", "<jobs>"]

    for _, row in df.iterrows():
        jobid = row.get("jobid", "")
        title = row.get("title", "")
        location = row.get("location", "").replace("locations ", "").strip()
        time_type = row.get("time_type", "N/A")
        posted_on = str(row.get("posted_on", "")).replace("posted on", "").strip()
        job_link = row.get("job_link", "")
        description_raw = row.get("description", "")

        # Format the text nicely
        description_clean = format_text_description(description_raw)

        xml_output.append(f"  <job>")
        xml_output.append(f"    <jobid>{jobid}</jobid>")
        xml_output.append(f"    <title>{title}</title>")
        xml_output.append(f"    <location>{location}</location>")
        xml_output.append(f"    <time_type>{time_type}</time_type>")
        xml_output.append(f"    <posted_on>{posted_on}</posted_on>")
        xml_output.append(f"    <job_link>{job_link}</job_link>")
        xml_output.append(f"    <description><![CDATA[{description_clean}]]></description>")
        xml_output.append(f"  </job>")

    xml_output.append("</jobs>")

    with open("schweiger_jobs.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(xml_output))

    print(f"✅ XML feed created: schweiger_jobs.xml with {len(df)} jobs.")


if __name__ == "__main__":
    generate_xml()
