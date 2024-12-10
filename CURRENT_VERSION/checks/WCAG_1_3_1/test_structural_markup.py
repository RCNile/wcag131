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

def validate_structural_element(tag, content, structural):
    """Validates structural elements for empty content, ARIA roles, and proper usage."""
    issues = []

    # Check if structural element is empty
    if not content and not structural.find_all(recursive=False):
        issues.append("Structural element is empty or lacks meaningful content.")

    # Check for purpose-specific validation
    match tag:
        case 'section' if len(content.split()) < 10:
            issues.append("Section should contain a meaningful amount of content.")
        case 'article' if len(content.split()) < 50:
            issues.append("Article should contain self-contained, detailed content.")
        case 'div' if len(content.split()) < 5:
            issues.append("Div should not be used solely for structural purposes without meaningful content.")

    # Check for ARIA roles in structural elements
    if tag in ['div', 'section'] and not structural.get('role'):
        issues.append("Structural element is missing an ARIA role for accessibility.")

    return issues

def validate_missing_regions(soup):
    """Checks for missing important page regions."""
    missing_regions = []
    required_regions = {'header': 'Header', 'nav': 'Navigation', 'main': 'Main Content', 'footer': 'Footer', 'aside': 'Aside'}

    for tag, region_name in required_regions.items():
        if not soup.find(tag):
            missing_regions.append(f"Missing {region_name} region (<{tag}> tag).")

    return missing_regions

def validate_missing_landmarks(soup):
    """Checks for missing ARIA landmarks."""
    required_landmarks = {'banner': 'Banner', 'navigation': 'Navigation', 'main': 'Main Content', 'contentinfo': 'Content Info'}
    missing_landmarks = []

    for role, landmark_name in required_landmarks.items():
        if not soup.find(attrs={'role': role}):
            missing_landmarks.append(f"Missing {landmark_name} landmark (role='{role}').")

    return missing_landmarks

def calculate_structural_confidence(issues, total_structures):
    """Calculates confidence for the structural markup test."""
    baseline_confidence = 100.0
    severity_map = {
        "empty or lacks meaningful content": 15,
        "missing an aria role": 10,
        "should contain meaningful content": 20,
        "missing region": 15,
        "missing landmark": 10
    }

    for issue in issues:
        # Extract the issue text if it's a dictionary
        issue_text = issue if isinstance(issue, str) else issue.get("Issue", "")
        for key, weight in severity_map.items():
            if key in issue_text.lower():
                baseline_confidence -= weight

    if total_structures > 0:
        confidence_penalty = (len(issues) / total_structures) * 30  # Additional penalty for proportion of issues
        baseline_confidence -= confidence_penalty

    return max(baseline_confidence, 0)


def test_structural_markup(html):
    """Tests for proper usage of structural elements in the HTML."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        structural_elements = soup.find_all(['article', 'section', 'div'])
        logging.info(f"Found {len(structural_elements)} structural elements.")

        issues = []

        for index, element in enumerate(structural_elements):
            try:
                tag = element.name
                content = element.get_text(strip=True)
                html_snippet = str(element)[:100]
                line_number = getattr(element, "sourceline", "Unknown")

                # Check for issues
                element_issues = validate_structural_element(tag, content, element)

                if element_issues:
                    for issue in element_issues:
                        issues.append({
                            "Line Number": line_number,
                            "Structural Tag": tag,
                            "HTML Snippet": html_snippet,
                            "Issue": issue,
                            "Issue Code": "1.3.1 (f)"
                        })

            except Exception as e:
                logging.error(f"Error processing structural element at index {index}: {e}")

        # Additional validations for regions and landmarks
        for validation_func, tag_name in [
            (validate_missing_regions, "Region"),
            (validate_missing_landmarks, "Landmark")
        ]:
            try:
                missing_issues = validation_func(soup)
                for issue in missing_issues:
                    issues.append({
                        "Line Number": "N/A",
                        "Structural Tag": tag_name,
                        "HTML Snippet": "N/A",
                        "Issue": issue,
                        "Issue Code": "1.3.1 (f)"
                    })
            except Exception as e:
                logging.error(f"Error validating {tag_name}: {e}")

        logging.debug(f"Collected issues: {issues}")
        confidence = calculate_structural_confidence(issues, len(structural_elements))
        result = {
            "status": "Malformed" if issues else "Passed",
            "details": issues,
            "confidence": confidence,
            "issue_count": len(issues)
        }
        logging.debug(f"Test Result for Structural Markup: {result}")
        return result

    except Exception as e:
        logging.error(f"Error in structural test: {e}")
        return {
            "status": "Error",
            "details": [{"Issue": "An unexpected error occurred.", "Issue Code": "1.3.1 (f)"}],
            "confidence": 50.0,
            "issue_count": 1
        }

