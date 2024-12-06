import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to write list issues to a file
def write_list_info(file_path, list_info, format="csv"):
    """Writes list information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing list info to {file_path} in {format} format.")

    def write_csv():
        """Writes list information to a CSV file."""
        fieldnames = ['List Index', 'List HTML', 'Issue', 'Issue Code', 'Confidence Percentage']
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for lst in list_info:
                writer.writerow({
                    'List Index': lst.get('List Index', 'N/A'),
                    'List HTML': lst.get('List HTML', 'N/A'),
                    'Issue': lst.get('Issue', 'N/A'),
                    'Issue Code': lst.get('Issue Code', 'N/A'),
                    'Confidence Percentage': lst.get('Confidence Percentage', 'N/A')
                })

    def write_json():
        """Writes list information to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(list_info, jsonfile, indent=4)

    def write_excel():
        """Writes list information to an Excel file."""
        df = pd.DataFrame(list_info)
        df.to_excel(file_path, index=False)

    # Dispatch table for format handling
    format_dispatch = {
        "csv": write_csv,
        "json": write_json,
        "excel": write_excel
    }

    try:
        # Execute the appropriate write function based on the format
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"List info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing list info to {file_path}: {e}")
        return False

# Helper functions for validation checks
validate_list = lambda lst: (
    "List is malformed. No <li> elements found."
    if not lst.find_all('li') else
    "List is missing proper ARIA roles for accessibility."
    if lst.name not in ['ul', 'ol'] and not lst.get('role') else
    None
)

# Confidence calculation function
def calculate_list_confidence(list_issues, total_lists):
    """Calculates confidence for the list test."""
    baseline_confidence = 95.0
    malformed_lists = len(list_issues)

    # Adjust confidence based on the proportion of malformed lists
    confidence_penalty = (malformed_lists / total_lists) * 50  # Max penalty: 50%
    return max(baseline_confidence - confidence_penalty, 0)

# Main list markup test function
def test_list_markup(html):
    """Tests for proper usage of list markup (ul, ol, li) in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    lists = soup.find_all(['ul', 'ol', 'div', 'section'])
    logging.info(f"Found {len(lists)} potential list elements.")

    if not lists:
        logging.warning("No lists found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []
    total_lists = len(lists)

    for index, lst in enumerate(lists):
        # Validate the list element
        validation_issue = validate_list(lst)
        if validation_issue:
            issues.append({
                "List Index": index + 1,
                "List HTML": str(lst),
                "Issue": validation_issue,
                "Issue Code": "1.3.1 (b)"
            })
            logging.warning(f"List {index + 1} issue: {validation_issue}")

    # Calculate overall confidence
    confidence = calculate_list_confidence(issues, total_lists)

    # Attach confidence to each issue
    for issue in issues:
        issue["Confidence Percentage"] = confidence

    # Return structured results
    return {
        "status": "Malformed" if issues else "Passed",
        "details": issues,
        "confidence": confidence
    }
