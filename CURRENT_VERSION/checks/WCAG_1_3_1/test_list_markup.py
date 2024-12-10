import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def write_list_info(file_path, list_info, format="csv"):
    """Writes list information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing list info to {file_path} in {format} format.")

    def write_csv():
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
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(list_info, jsonfile, indent=4)

    def write_excel():
        df = pd.DataFrame(list_info)
        df.to_excel(file_path, index=False)

    format_dispatch = {
        "csv": write_csv,
        "json": write_json,
        "excel": write_excel
    }

    try:
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"List info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing list info to {file_path}: {e}")
        return False

# Validation Functions
def validate_list_element(lst):
    """Validates a list element for proper structure and semantics."""
    if lst.name not in ['ul', 'ol']:
        # Non-standard list elements must use ARIA roles
        if not lst.get('role') == 'list':
            return "Non-standard list element is missing role='list' for accessibility."
    if not lst.find_all('li'):
        return "List is malformed: no <li> elements found."
    return None

def validate_list_nesting(lst):
    """Checks for improper nesting of lists."""
    nested_lists = lst.find_all(['ul', 'ol'], recursive=True)
    for nested in nested_lists:
        if nested.find_parent(['ul', 'ol']) != lst:
            return "Nested list is not properly contained within a parent list item."
    return None

def validate_orphan_list_items(soup):
    """Checks for orphaned <li> elements outside a list container."""
    orphans = soup.find_all('li', recursive=False)
    if orphans:
        return "Orphaned <li> elements found outside <ul> or <ol> containers."
    return None

# Confidence Calculation
def calculate_list_confidence(issues, total_lists):
    """Calculates confidence for the list test."""
    baseline_confidence = 100.0
    weight_map = {
        "malformed": 20,
        "nested": 15,
        "orphaned": 10,
    }
    for issue in issues:
        for key, weight in weight_map.items():
            if key in issue['Issue'].lower():
                baseline_confidence -= weight
    return max(baseline_confidence - (len(issues) / total_lists) * 20, 0)

# Main Function
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

    # Check for orphaned <li> elements
    orphan_issue = validate_orphan_list_items(soup)
    if orphan_issue:
        issues.append({
            "List Index": "N/A",
            "List HTML": "N/A",
            "Issue": orphan_issue,
            "Issue Code": "1.3.1 (b)"
        })
        logging.warning(orphan_issue)

    # Validate each list element
    for index, lst in enumerate(lists):
        # Validate the list structure
        list_issue = validate_list_element(lst)
        if list_issue:
            issues.append({
                "List Index": index + 1,
                "List HTML": str(lst),
                "Issue": list_issue,
                "Issue Code": "1.3.1 (b)"
            })
            logging.warning(f"List {index + 1} issue: {list_issue}")

        # Validate nested lists
        nesting_issue = validate_list_nesting(lst)
        if nesting_issue:
            issues.append({
                "List Index": index + 1,
                "List HTML": str(lst),
                "Issue": nesting_issue,
                "Issue Code": "1.3.1 (b)"
            })
            logging.warning(f"List {index + 1} issue: {nesting_issue}")

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
