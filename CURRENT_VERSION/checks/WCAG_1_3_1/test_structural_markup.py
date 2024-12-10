import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

def write_structural_info(file_path, structural_info, format="csv"):
    """Writes structural information and issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing structural info to {file_path} in {format} format.")

    def write_csv():
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
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(structural_info, jsonfile, indent=4)

    def write_excel():
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

    format_dispatch = {
        "csv": write_csv,
        "json": write_json,
        "excel": write_excel
    }

    try:
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"Structural info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing structural info to {file_path}: {e}")
        return False

def validate_empty_structural(structural, content):
    """Checks if a structural element is empty or lacks meaningful content."""
    if not content and not structural.find_all(recursive=False):
        return "Structural element is empty or lacks meaningful content."
    return None

def validate_structural_purpose(tag, content):
    """Validates if the structural element's purpose is appropriate."""
    if tag == 'section' and len(content.split()) < 10:
        return "Section should contain a meaningful amount of content."
    if tag == 'article' and len(content.split()) < 50:
        return "Article should contain self-contained, detailed content."
    if tag == 'div' and len(content.split()) < 5:
        return "Div should not be used solely for structural purposes without meaningful content."
    return None

def validate_aria_role(structural):
    """Checks if structural elements like <div> and <section> use ARIA roles appropriately."""
    if structural.name in ['div', 'section'] and not structural.get('role'):
        return "Structural element is missing an ARIA role for accessibility."
    return None

def calculate_structural_confidence(issues, total_structures):
    """Calculates confidence for the structural markup test."""
    baseline_confidence = 100.0
    if total_structures > 0:
        confidence_penalty = (len(issues) / total_structures) * 50  # Max penalty: 50%
        baseline_confidence -= confidence_penalty
    return max(baseline_confidence, 0)

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
