import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

def write_table_info(file_path, table_info, format="csv"):
    """Writes table information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing table info to {file_path} in {format} format.")

    def write_csv():
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
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(table_info, jsonfile, indent=4)

    def write_excel():
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

# Validation Functions
def validate_headers(table):
    """Ensures the table has <th> headers and appropriate attributes."""
    headers = table.find_all('th')
    if not headers:
        return "Table is missing <th> header cells."
    for header in headers:
        if not header.get('scope') and not header.get('id'):
            return "Header cell is missing 'scope' or 'id' for association."
    return None

def validate_rows(table):
    """Checks if the table contains rows (<tr>)."""
    if not table.find_all('tr'):
        return "Table is missing <tr> row elements."
    return None

def validate_aria_role(table):
    """Validates the presence of ARIA roles or summary for accessibility."""
    if not table.get('role') and not table.get('summary'):
        return "Table is missing an ARIA role or a summary attribute."
    return None

def validate_layout_table(table):
    """Detects if the table is improperly used for layout purposes."""
    if not table.find_all('th') and len(table.find_all('tr')) <= 2:
        return "Table appears to be used for layout purposes."
    return None

def calculate_table_confidence(num_issues, num_checks):
    """Calculates confidence for the table test."""
    baseline_confidence = 95.0
    confidence_penalty = (num_issues / num_checks) * 50  # Max penalty: 50%
    return max(baseline_confidence - confidence_penalty, 0)

# Main Function
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
                validate_aria_role(table),
                validate_layout_table(table)
            ]
            if validation_issue is not None
        ]

        if table_issues:
            issues.append({
                "Table Index": index + 1,
                "Table HTML": str(table),
                "Issue": " ".join(table_issues),
                "Confidence Percentage": calculate_table_confidence(len(table_issues), 4)
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
