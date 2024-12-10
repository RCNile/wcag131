import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG)
def write_form_info(file_path, form_info, format="csv"):
    """Writes form issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing form info to {file_path} in {format} format.")
    try:
        # Prepare rows for writing
        rows = [
            {
                'Line Number': issue.get('Line Number', 'N/A'),
                'Input Type': issue.get('Input Type', 'N/A'),
                'Input HTML': issue.get('Input HTML', 'N/A'),
                'Issue': issue.get('Issue', 'N/A'),
                'Issue Code': issue.get('Issue Code', 'N/A'),
                'Count': issue.get('Count', 1),  # Include count if available
                'Confidence Percentage': form_info.get('confidence', 'N/A')  # Assuming confidence applies to all rows
            }
            for issue in form_info.get('details', [])
        ]

        # Write data based on format
        if format == "csv":
            fieldnames = ['Line Number', 'Input Type', 'Input HTML', 'Issue', 'Issue Code', 'Count', 'Confidence Percentage']
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        elif format == "json":
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(rows, jsonfile, indent=4)
        elif format == "excel":
            df = pd.DataFrame(rows)
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {format}")

        logging.info(f"Form info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing form info to {file_path}: {e}")
        return False


def group_issues(details):
    """
    Groups similar issues by their descriptions and counts occurrences.
    """
    grouped = defaultdict(list)
    for detail in details:
        issue_key = detail.get("issue", "N/A")
        grouped[issue_key].append(detail)
    return grouped

def validate_input_field(input_element):
    """Validates individual input elements for accessibility compliance."""
    exempt_types = {'image', 'submit', 'reset', 'button', 'hidden'}
    input_type = input_element.get('type', '').lower()

    # Skip exempt input types
    if input_type in exempt_types:
        return None

    match {
        "id_present": bool(input_element.get('id')),
        "wrapped_by_label": bool(input_element.find_parent('label')),
        "aria_present": bool(input_element.get('aria-label') or input_element.get('aria-labelledby'))
    }:
        case {"id_present": True}:
            form = input_element.find_parent('form')
            label = form.find('label', {'for': input_element['id']}) if form else None
            if label:
                return None
        case {"wrapped_by_label": True} | {"aria_present": True}:
            return None

    # Issue if no valid labeling is found
    return (
        f"Input element of type '{input_type}' is missing a proper label or an accessible alternative "
        f"(aria-label or aria-labelledby)."
    )

def validate_aria_attributes(form):
    """Checks ARIA attributes on forms for compliance."""
    if not form.get('aria-labelledby') and not form.get('aria-describedby'):
        return "Form is missing an aria-labelledby or aria-describedby attribute for accessibility."
    return None

def validate_form_grouping(form):
    """Checks for proper grouping of form fields."""
    if not form.find_all('fieldset') and not form.find_all('optgroup'):
        return "Form fields are not grouped (use <fieldset> or <optgroup> where appropriate)."
    return None

def calculate_confidence(issues, total_checks):
    """Calculates confidence for form accessibility."""
    baseline_confidence = 100.0
    weight_map = {
        "missing a label": 20,
        "missing a name": 15,
        "not grouped": 10,
        "missing an aria": 10,
    }
    for issue in issues:
        for key, weight in weight_map.items():
            if key in issue.get('issue', '').lower():
                baseline_confidence -= weight
    return max(baseline_confidence, 0)

def test_form_markup(html):
    """Tests for form accessibility compliance."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        forms = soup.find_all('form')
        logging.info(f"Found {len(forms)} forms.")

        issues = []

        for form_index, form in enumerate(forms):
            try:
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_index, input_element in enumerate(inputs):
                    if (input_issue := validate_input_field(input_element)):
                        issues.append({
                            "Line Number": getattr(input_element, "sourceline", "Unknown"),
                            "Input Type": input_element.get("type", "N/A"),
                            "Input HTML": str(input_element),
                            "Issue": input_issue,
                            "Issue Code": "1.3.1 (g)"
                        })

            except Exception as e:
                logging.error(f"Error processing form {form_index + 1}: {e}")

        confidence = calculate_confidence(issues, len(forms))
        return {
            "status": "Malformed" if issues else "Passed",
            "details": issues,
            "confidence": confidence,
            "issue_count": len(issues)
        }

    except Exception as e:
        logging.error(f"Error in form test: {e}")
        return {
            "status": "Error",
            "details": [{"Issue": "An unexpected error occurred.", "Issue Code": "1.3.1 (g)"}],
            "confidence": 50.0,
            "issue_count": 1
        }
