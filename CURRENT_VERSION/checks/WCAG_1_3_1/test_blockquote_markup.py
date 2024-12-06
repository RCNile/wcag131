import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to write blockquote issues to a file
def write_blockquote_info(file_path, blockquote_info, format="csv"):
    """Writes blockquote issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing blockquote info to {file_path} in {format} format.")
    try:
        if format == "csv":
            fieldnames = ['Blockquote Index', 'Blockquote HTML', 'Issue', 'Issue Code', 'Confidence Percentage']
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for blockquote in blockquote_info:
                    for issue in blockquote['issues']:
                        writer.writerow({
                            'Blockquote Index': blockquote.get('blockquote_index', 'N/A'),
                            'Blockquote HTML': blockquote.get('blockquote_html', 'N/A'),
                            'Issue': issue.get('issue', 'N/A'),
                            'Issue Code': "1.3.1 (f)",  # Adjust WCAG code as needed
                            'Confidence Percentage': blockquote.get('confidence_percentage', 'N/A')
                        })
        elif format == "json":
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(blockquote_info, jsonfile, indent=4)
        elif format == "excel":
            rows = []
            for blockquote in blockquote_info:
                for issue in blockquote['issues']:
                    rows.append({
                        'Blockquote Index': blockquote.get('blockquote_index', 'N/A'),
                        'Blockquote HTML': blockquote.get('blockquote_html', 'N/A'),
                        'Issue': issue.get('issue', 'N/A'),
                        'Issue Code': "1.3.1 (f)",  # Adjust WCAG code as needed
                        'Confidence Percentage': blockquote.get('confidence_percentage', 'N/A')
                    })
            df = pd.DataFrame(rows)
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {format}")
        logging.info(f"Blockquote info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing blockquote info to {file_path}: {e}")
        return False

# Helper functions for validation
validate_blockquote = lambda element: (
    "Blockquote is missing a cite attribute or <footer> for source attribution."
    if not element.get('cite') and not element.find('footer') else
    None
)

validate_aria = lambda element: (
    "Blockquote is missing an aria-labelledby or aria-describedby for better accessibility."
    if not element.get('aria-labelledby') and not element.get('aria-describedby') else
    None
)

# Confidence calculation function
def calculate_confidence(blockquote_issues, total_checks):
    """Calculates confidence for blockquote accessibility compliance."""
    baseline_confidence = 95.0
    for issue in blockquote_issues:
        match issue.get('issue', '').lower():
            case issue if "missing a cite" in issue:
                baseline_confidence -= 20
            case issue if "missing an aria" in issue:
                baseline_confidence -= 15
    return max(baseline_confidence, 0)

# Main blockquote markup test function
def test_blockquote_markup(html):
    """Tests for proper usage of blockquote elements in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    blockquotes = soup.find_all('blockquote')
    logging.info(f"Found {len(blockquotes)} blockquote elements.")

    if not blockquotes:
        logging.warning("No blockquote elements found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []

    for blockquote_index, blockquote in enumerate(blockquotes):
        blockquote_html = str(blockquote)

        # Validate blockquote for source attribution and ARIA tags
        blockquote_issues = [
            validation_issue
            for validation_issue in [
                validate_blockquote(blockquote),
                validate_aria(blockquote)
            ]
            if validation_issue is not None
        ]

        # Calculate confidence for the current blockquote
        confidence_percentage = calculate_confidence(blockquote_issues, len(blockquote_issues))

        if blockquote_issues:
            issues.append({
                "blockquote_index": blockquote_index + 1,
                "blockquote_html": blockquote_html,
                "issues": [{"issue": issue} for issue in blockquote_issues],
                "confidence_percentage": confidence_percentage
            })

            for issue in blockquote_issues:
                logging.warning(f"Blockquote {blockquote_index + 1}: {issue}")

    # Calculate overall confidence
    overall_confidence = (
        sum(blockquote.get("confidence_percentage", 0) for blockquote in issues) / len(issues)
        if issues else 100.0
    )

    return {"status": "Malformed" if issues else "Passed", "details": issues, "confidence": overall_confidence}
