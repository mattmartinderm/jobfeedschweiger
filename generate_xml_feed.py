import pandas as pd
import xml.etree.ElementTree as ET

def generate_xml_from_csv(csv_file, xml_file):
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # Root element
    root = ET.Element("jobs")

    for _, row in df.iterrows():
        job = ET.SubElement(root, "job")

        # Add job fields
        ET.SubElement(job, "jobid").text = str(row.get("Job ID", "N/A"))
        ET.SubElement(job, "title").text = str(row.get("Title", "N/A"))
        ET.SubElement(job, "location").text = str(row.get("Location", "N/A"))
        ET.SubElement(job, "time_type").text = str(row.get("Time Type", "N/A"))
        ET.SubElement(job, "posted_on").text = str(row.get("Posted On", "N/A"))
        ET.SubElement(job, "apply_link").text = str(row.get("Apply Link", "N/A"))
        ET.SubElement(job, "job_link").text = str(row.get("Job Link", "N/A"))

        # Description in CDATA to preserve HTML formatting
        desc = ET.SubElement(job, "description")
        description_html = str(row.get("Description", ""))
        desc.text = f"<![CDATA[{description_html}]]>"

    # Build the tree
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(xml_file, encoding="utf-8", xml_declaration=True)

    print(f"✅ XML feed created: {xml_file} with {len(df)} jobs.")


if __name__ == "__main__":
    generate_xml_from_csv("schweiger_jobs_formatted.csv", "schweiger_jobs.xml")
