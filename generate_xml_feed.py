import pandas as pd
from bs4 import BeautifulSoup
import html
import re
import os

def format_html_description(raw_html):
    """Clean and simplify HTML for JBoard rendering."""
    if not isinstance(raw_html, str) or not raw_html.strip():
        return ""

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove unnecessary tags
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Ensure line breaks render properly
    for br in soup.find_all("br"):
        br.replace_with("<br/>")

    # Clean up nested tags and normalize structure
    for tag in soup.find_all(["div", "span", "section"]):
        tag.unwrap()

    # Ensure paragraphs wrap text properly
    for p in soup.find_all("p"):
        p.attrs = {}

    # Clean list formatting
    for ul in soup.find_all("ul"):
        ul.attrs = {"style": "margin-left:15px;"}
    for li in soup.find_all("li"):
        li.attrs = {}

    # Convert <b>, <strong>, <i>, etc. to clean equivalents
    for tag in soup.find_all(["b", "strong"]):
        tag.name = "strong"
    for tag in soup.find_all(["i", "em"]):
        tag.name = "em"

    # Clean up whitespace
    html_output = str(soup)
    html_output = re.sub(r"\s*\n\s*", " ", html_output)
    html_output = re.sub(r"\s{2,}", " ", html_output).strip()

    # Wrap in <p> if plain text only
    if not any(tag in html_output for tag in ["<p", "<ul", "<li", "<br"]):
        html_output = f"<p>{html.escape(html_output)}</p>"

    return html_output


def generate_xml():
    print("🧩 Generating XML feed with clean HTML formatting...")

    csv_path = "workday_jobs_full.csv"
    output_path = "schweiger_jobs.xml"

    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write("<jobs>\n")

        for _, row in df.iterrows():
            jobid = html.escape(str(row.get("jobid", "")).strip())
            title = html.escape(str(row.get("title", "")).strip())
            location = html.escape(str(row.get("location", "")).replace("locations ", "").strip())
            time_type = html.escape(str(row.get("time_type", "")).strip())
            posted_on = html.escape(str(row.get("posted_on", "")).replace("posted on ", "").strip())
            job_link = html.escape(str(row.get("job_link", "")).strip())
            description_raw = row.get("description", "")

            description_clean = format_html_description(description_raw)

            f.write("  <job>\n")
            f.write(f"    <jobid>{jobid}</jobid>\n")
            f.write(f"    <title>{title}</title>\n")
            f.write(f"    <location>{location}</location>\n")
            f.write(f"    <time_type>{time_type}</time_type>\n")
            f.write(f"    <posted_on>{posted_on}</posted_on>\n")
            f.write(f"    <job_link>{job_link}</job_link>\n")
            f.write(f"    <description><![CDATA[{description_clean}]]></description>\n")
            f.write("  </job>\n")

        f.write("</jobs>\n")

    print(f"✅ XML feed created: {output_path} with {len(df)} jobs.")


if __name__ == "__main__":
    generate_xml()
