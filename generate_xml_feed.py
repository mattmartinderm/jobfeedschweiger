import pandas as pd
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def generate_xml_from_csv(csv_file, xml_file):
    """Convert the Schweiger job CSV to an XML feed."""
    if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
        print(f"⚠️  CSV file '{csv_file}' is missing or empty. Skipping XML generation.")
        return

    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        print(f"⚠️  CSV file '{csv_file}' is empty or unreadable.")
        return

    if df.empty:
        print(f"⚠️  CSV file '{csv_file}' has no rows.")
        return

    root = Element("jobs")

    for _, row in df.iterrows():
        job_el = SubElement(root, "job")

        SubElement(job_el, "title").text = str(row.get("Job Title", ""))
        SubElement(job_el, "timeType").text = str(row.get("Time Type", ""))
        SubElement(job_el, "locations").text = str(row.get("Location(s)", ""))
        SubElement(job_el, "datePosted").text = str(row.get("Date Posted", ""))
        SubElement(job_el, "url").text = str(row.get("Job URL", ""))
        SubElement(job_el, "applyUrl").text = str(row.get("Apply URL", ""))

        desc_html = str(row.get("Description (HTML)", ""))
        desc_el = SubElement(job_el, "description")
        desc_el.text = f"<![CDATA[{desc_html}]]>"

    xml_str = minidom.parseString(tostring(root, "utf-8")).toprettyxml(indent="  ")
    with open(xml_file, "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"✅ XML feed created: {xml_file} with {len(df)} jobs.")


if __name__ == "__main__":
    generate_xml_from_csv("schweiger_jobs_formatted.csv", "schweiger_jobs.xml")
