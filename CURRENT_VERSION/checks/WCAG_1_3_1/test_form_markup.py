import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to write form issues to a file
def write_form_info(file_path, form_info, format="csv"):
    """Writes form issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing form info to {file_path} in {format} format.")

    def write_csv():
        fieldnames = ['Form Index', 'Input Index', 'Input HTML', 'Issue', 'Issue Code', 'Confidence Percentage']
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for form in form_info:
                for issue in form['issues']:
                    writer.writerow({
                        'Form Index': form.get('form_index', 'N/A'),
                        'Input Index': issue.get('input_index', 'N/A'),
                        'Input HTML': issue.get('input_html', 'N/A'),
                        'Issue': issue.get('issue', 'N/A'),
                        'Issue Code': "1.3.1 (g)",
                        'Confidence Percentage': form.get('confidence_percentage', 'N/A')
                    })

    def write_json():
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(form_info, jsonfile, indent=4)

    def write_excel():
        rows = [
            {
                'Form Index': form.get('form_index', 'N/A'),
                'Input Index': issue.get('input_index', 'N/A'),
                'Input HTML': issue.get('input_html', 'N/A'),
                'Issue': issue.get('issue', 'N/A'),
                'Issue Code': "1.3.1 (g)",
                'Confidence Percentage': form.get('confidence_percentage', 'N/A')
            }
            for form in form_info
            for issue in form['issues']
        ]
        df = pd.DataFrame(rows)
        df.to_excel(file_path, index=False)

    format_dispatch = {"csv": write_csv, "json": write_json, "excel": write_excel}

    try:
        if format in format_dispatch:
            format_dispatch[format]()
            logging.info(f"Form info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing form info to {file_path}: {e}")
        return False

# Validation checks
def validate_input_field(input_element):
    """Validates individual input elements for accessibility compliance based on WAVE's forms assessment."""
    exempt_types = {'image', 'submit', 'reset', 'button', 'hidden'}
    input_type = input_element.get('type', '').lower()

    # Skip validation for exempt input types
    if input_type in exempt_types:
        return None

    # Check for associated <label> element
    input_id = input_element.get('id')
    if input_id and input_element.find_parent('form'):
        # Check if a <label> is associated with the `id`
        label = input_element.find_parent('form').find('label', {'for': input_id})
        if label:
            return None

    # Check for direct wrapping by a <label> element
    if input_element.find_parent('label'):
        return None

    # Check for ARIA attributes as a fallback
    if input_element.get('aria-label') or input_element.get('aria-labelledby'):
        return None

    # If none of the above conditions are met, return an issue
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

# Confidence calculation function
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

# Main form markup test function
def test_form_markup(html):
    """Tests form elements for WAVE-aligned accessibility compliance."""
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    logging.info(f"Found {len(forms)} form elements")

    if not forms:
        logging.warning("No forms found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    form_results = []

    for form_index, form in enumerate(forms):
        inputs = form.find_all(['input', 'textarea', 'select'])
        logging.info(f"Form {form_index + 1} contains {len(inputs)} input elements.")

        form_issues = []

        # Validate ARIA attributes
        if (aria_issue := validate_aria_attributes(form)):
            form_issues.append({
                "form_index": form_index + 1,
                "input_index": "N/A",
                "input_html": str(form),
                "issue": aria_issue
            })

        # Validate form grouping
        if (grouping_issue := validate_form_grouping(form)):
            form_issues.append({
                "form_index": form_index + 1,
                "input_index": "N/A",
                "input_html": str(form),
                "issue": grouping_issue
            })

        # Validate each input field
        for input_index, input_element in enumerate(inputs):
            if (input_issue := validate_input_field(input_element)):
                form_issues.append({
                    "form_index": form_index + 1,
                    "input_index": input_index + 1,
                    "input_html": str(input_element),
                    "issue": input_issue
                })

        # Calculate confidence
        confidence = calculate_confidence(form_issues, len(inputs))
        if form_issues:
            form_results.append({"form_index": form_index + 1, "issues": form_issues, "confidence_percentage": confidence})

    overall_confidence = sum(f["confidence_percentage"] for f in form_results) / len(form_results) if form_results else 100.0
    return {"status": "Malformed" if form_results else "Passed", "details": form_results, "confidence": overall_confidence}
