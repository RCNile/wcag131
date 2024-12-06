import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

"""
WCAG 1.3.1 (c) Test for proper usage of table markup (table, th, tr, td) in the HTML.
"""

logging.basicConfig(level=logging.DEBUG)

# Function to write table issues to a file
def write_table_info(file_path, table_info, format="csv"):
    """Writes table information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing table info to {file_path} in {format} format.")

    def write_csv():
        """Writes table information to a CSV file."""
        fieldnames = ['Table Index', 'Table HTML', 'Issue', 'Confidence Percentage']
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for table in table_info:
                writer.writerow({
                    'Table Index': table.get('Table Index', 'N/A'),
                    'Table HTML': table.get('Table HTML', 'N/A'),
                    'Issue': table.get('Issue', 'N/A'),
                    'Confidence Percentage': table.get('Confidence Percentage', 'N/A')
                })

    def write_json():
        """Writes table information to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(table_info, jsonfile, indent=4)

    def write_excel():
        """Writes table information to an Excel file."""
        rows = [
            {
                'Table Index': table.get('Table Index', 'N/A'),
                'Table HTML': table.get('Table HTML', 'N/A'),
                'Issue': table.get('Issue', 'N/A'),
                'Confidence Percentage': table.get('Confidence Percentage', 'N/A')
            }
            for table in table_info
        ]
        df = pd.DataFrame(rows)
        df.to_excel(file_path, index=False)

    # Dispatch table for format handling
    format_dispatch = {
        "csv": write_csv,
        "json": write_json,
        "excel": write_excel
    }

    try:
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"Table info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing table info to {file_path}: {e}")
        return False

# Helper functions for validation
validate_headers = lambda table: (
    "Table is missing headers (th elements)."
    if not table.find_all('th') else
    None
)

validate_rows = lambda table: (
    "Table is missing rows (tr elements)."
    if not table.find_all('tr') else
    None
)

validate_aria_role = lambda table: (
    "Table is missing an ARIA role for accessibility."
    if not table.get('role') and table.get('summary') is None else
    None
)

# Confidence calculation function
def calculate_table_confidence(num_issues, num_checks):
    """Calculates confidence for the table test."""
    baseline_confidence = 95.0
    confidence_penalty = (num_issues / num_checks) * 50  # Max penalty: 50%
    return max(baseline_confidence - confidence_penalty, 0)

# Main table markup test function
def test_table_markup(html):
    """Tests for proper usage of table markup (table, th, tr, td) in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    logging.info(f"Found {len(tables)} table elements.")

    if not tables:
        logging.warning("No tables found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []
    total_tables = len(tables)

    for index, table in enumerate(tables):
        table_issues = [
            validation_issue
            for validation_issue in [
                validate_headers(table),
                validate_rows(table),
                validate_aria_role(table)
            ]
            if validation_issue is not None
        ]

        if table_issues:
            issues.append({
                "Table Index": index + 1,
                "Table HTML": str(table),
                "Issue": " ".join(table_issues),
                "Confidence Percentage": calculate_table_confidence(len(table_issues), 3)
            })
            for issue in table_issues:
                logging.warning(f"Table {index + 1} issue: {issue}")

    # Calculate overall confidence
    overall_confidence = calculate_table_confidence(len(issues), total_tables)

    return {
        "status": "Malformed" if issues else "Passed",
        "details": issues,
        "confidence": overall_confidence
    }
