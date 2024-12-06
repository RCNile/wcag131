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
        """Writes form information to a CSV file."""
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
        """Writes form information to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(form_info, jsonfile, indent=4)

    def write_excel():
        """Writes form information to an Excel file."""
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
            logging.info(f"Form info successfully written to {file_path}.")
            return True
        else:
            raise ValueError(f"Unsupported file format: {format}")
    except Exception as e:
        logging.error(f"Error writing form info to {file_path}: {e}")
        return False

# Helper functions for validation checks
validate_input_field = lambda inp: (
    "Input element is missing a label or aria-label."
    if not (inp.find_parent('label') or inp.get('aria-label')) else
    "Input element is missing a name or id attribute."
    if not inp.get('name', '').strip() and not inp.get('id', '').strip() else
    None
)

validate_aria = lambda form: (
    "Form is missing an aria-labelledby or aria-describedby attribute for accessibility."
    if not form.get('aria-labelledby') and not form.get('aria-describedby') else
    None
)

validate_form_grouping = lambda form: (
    "Form fields are not grouped (use <fieldset> or <optgroup> where appropriate)."
    if not form.find_all('fieldset') and not form.find_all('optgroup') else
    None
)

# Confidence calculation function
def calculate_confidence(form_issues, total_checks):
    """Calculates confidence for a form's correctness assessment."""
    baseline_confidence = 95.0
    for issue in form_issues:
        match issue.get('issue', '').lower():
            case issue if "missing a label" in issue:
                baseline_confidence -= 20
            case issue if "not grouped" in issue:
                baseline_confidence -= 15
            case issue if "missing an aria" in issue:
                baseline_confidence -= 10
    return max(baseline_confidence, 0)

# Main form markup test function
def test_form_markup(html):
    """Tests for proper labeling of form elements and correct grouping in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    forms = soup.find_all('form')
    logging.info(f"Found {len(forms)} form elements")

    if not forms:
        logging.warning("No forms found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []

    for form_index, form in enumerate(forms):
        inputs = form.find_all(['input', 'textarea', 'select'])
        logging.info(f"Found {len(inputs)} input elements in form {form_index + 1}")

        # Validate ARIA attributes
        aria_issue = validate_aria(form)

        # Validate form grouping
        grouping_issue = validate_form_grouping(form)

        # Validate each input field
        form_issues = [
            {
                "form_index": form_index + 1,
                "input_index": input_index + 1,
                "input_html": str(inp),
                "issue": validation_issue,
            }
            for input_index, inp in enumerate(inputs)
            if (validation_issue := validate_input_field(inp)) is not None
        ]

        # Add ARIA and grouping issues if applicable
        if aria_issue:
            form_issues.append({
                "form_index": form_index + 1,
                "input_index": "N/A",
                "input_html": "N/A",
                "issue": aria_issue,
            })

        if grouping_issue:
            form_issues.append({
                "form_index": form_index + 1,
                "input_index": "N/A",
                "input_html": "N/A",
                "issue": grouping_issue,
            })

        # Calculate confidence for the current form
        confidence_percentage = calculate_confidence(form_issues, len(inputs) + (1 if grouping_issue else 0) + (1 if aria_issue else 0))

        if form_issues:
            issues.append({
                "form_index": form_index + 1,
                "issues": form_issues,
                "confidence_percentage": confidence_percentage
            })

            for issue in form_issues:
                logging.warning(f"Form {form_index + 1}: {issue}")

    # Calculate overall confidence
    overall_confidence = (
        sum(form.get("confidence_percentage", 0) for form in issues) / len(issues)
        if issues else 100.0
    )

    return {"status": "Malformed" if issues else "Passed", "details": issues, "confidence": overall_confidence}
