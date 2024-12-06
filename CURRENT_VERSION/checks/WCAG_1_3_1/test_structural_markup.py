import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup
import os
from datetime import datetime

"""
WCAG 1.3.1 (f) Other structural markup is used appropriately
"""

logging.basicConfig(level=logging.DEBUG)

# Function to write structural element issues to a file
def write_structural_info(file_path, structural_info, format="csv"):
    """Writes structural information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing structural info to {file_path} in {format} format.")

    def write_csv():
        """Writes structural information to a CSV file."""
        fieldnames = ['Structural Index', 'Structural Tag', 'Structural HTML', 'Issue', 'Confidence Percentage']
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for structural in structural_info:
                for issue in structural['issues']:
                    writer.writerow({
                        'Structural Index': structural.get('structural_index', 'N/A'),
                        'Structural Tag': structural.get('structural_tag', 'N/A'),
                        'Structural HTML': structural.get('structural_html', 'N/A'),
                        'Issue': issue,
                        'Confidence Percentage': structural.get('confidence_percentage', 'N/A')
                    })

    def write_json():
        """Writes structural information to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(structural_info, jsonfile, indent=4)

    def write_excel():
        """Writes structural information to an Excel file."""
        rows = [
            {
                'Structural Index': structural.get('structural_index', 'N/A'),
                'Structural Tag': structural.get('structural_tag', 'N/A'),
                'Structural HTML': structural.get('structural_html', 'N/A'),
                'Issue': issue,
                'Confidence Percentage': structural.get('confidence_percentage', 'N/A')
            }
            for structural in structural_info
            for issue in structural['issues']
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
        # Execute the appropriate write function based on the format
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"Structural info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing structural info to {file_path}: {e}")
        return False

# Helper functions for validation checks
validate_empty_structural = lambda structural, content: (
    "Structural element is empty or lacks meaningful content."
    if not content and not structural.find_all(recursive=False) else
    None
)

validate_structural_purpose = lambda tag, content: (
    "Section should contain a meaningful amount of content."
    if tag == 'section' and len(content.split()) < 10 else
    "Article should contain detailed content."
    if tag == 'article' and len(content.split()) < 50 else
    "Div should not be used solely for structural purposes without meaningful content."
    if tag == 'div' and len(content.split()) < 5 else
    None
)

validate_aria_role = lambda structural: (
    "Structural element is missing an ARIA role for accessibility."
    if structural.name in ['div', 'section'] and not structural.get('role') else
    None
)

# Confidence calculation function
def calculate_structural_confidence(issues, total_structures):
    """Calculates confidence for the structural markup test."""
    baseline_confidence = 95.0
    if total_structures > 0:
        confidence_penalty = (len(issues) / total_structures) * 50  # Max penalty: 50%
        baseline_confidence -= confidence_penalty
    return max(baseline_confidence, 0)

# Main structural elements test function
def test_structural_markup(html):
    """Tests for proper usage of structural elements (article, section, div) in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    structural_elements = soup.find_all(['article', 'section', 'div'])
    logging.info(f"Found {len(structural_elements)} structural elements.")

    if not structural_elements:
        logging.warning("No structural elements found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []

    for index, structural in enumerate(structural_elements):
        structural_content = structural.get_text(strip=True)
        structural_html = str(structural)

        # Validate structural element
        structural_issues = [
            validation_issue
            for validation_issue in [
                validate_empty_structural(structural, structural_content),
                validate_structural_purpose(structural.name, structural_content),
                validate_aria_role(structural)
            ]
            if validation_issue is not None
        ]

        if structural_issues:
            issues.append({
                "structural_index": index + 1,
                "structural_tag": structural.name,
                "structural_html": structural_html,
                "issues": structural_issues,
                "confidence_percentage": 0  # Placeholder, updated later
            })

    # Calculate overall confidence
    confidence = calculate_structural_confidence(issues, len(structural_elements))

    # Attach confidence to each issue
    for issue in issues:
        issue["confidence_percentage"] = confidence

    # Return structured results
    return {
        "status": "Malformed" if issues else "Passed",
        "details": issues,
        "confidence": confidence
    }
