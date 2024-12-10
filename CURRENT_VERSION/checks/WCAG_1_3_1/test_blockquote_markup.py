import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def write_blockquote_info(file_path, blockquote_info, format="csv"):
    """Writes blockquote issues to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing blockquote info to {file_path} in {format} format.")
    try:
        rows = []
        for blockquote in blockquote_info:
            for issue in blockquote['issues']:
                rows.append({
                    'Blockquote Index': blockquote.get('blockquote_index', 'N/A'),
                    'Blockquote HTML': blockquote.get('blockquote_html', 'N/A'),
                    'Issue': issue.get('issue', 'N/A'),
                    'Issue Code': "1.3.1 (d)",  # Adjust WCAG code as needed
                    'Confidence Percentage': blockquote.get('confidence_percentage', 'N/A')
                })

        if format == "csv":
            fieldnames = ['Blockquote Index', 'Blockquote HTML', 'Issue', 'Issue Code', 'Confidence Percentage']
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

        logging.info(f"Blockquote info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing blockquote info to {file_path}: {e}")
        return False

def validate_blockquote(blockquote):
    """Validates a blockquote for source attribution and accessibility."""
    match {
        "missing_cite": not blockquote.get('cite') and not blockquote.find('footer'),
        "missing_aria": not blockquote.get('aria-labelledby') and not blockquote.get('aria-describedby')
    }:
        case {"missing_cite": True}:
            return "Blockquote is missing a cite attribute or <footer> for source attribution."
        case {"missing_aria": True}:
            return "Blockquote is missing an aria-labelledby or aria-describedby for better accessibility."
    return None

def calculate_confidence(blockquote_issues, total_checks):
    """Calculates confidence for blockquote accessibility compliance."""
    baseline_confidence = 95.0
    for issue in blockquote_issues:
        match issue.get('issue', '').lower():
            case issue if "missing a cite" in issue:
                baseline_confidence -= 20
            case issue if "missing an aria" in issue:
                baseline_confidence -= 15
    return max(baseline_confidence - (len(blockquote_issues) / total_checks) * 5, 0)

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

        # Validate blockquote for issues
        blockquote_issues = []
        issue = validate_blockquote(blockquote)
        if issue:
            blockquote_issues.append({"issue": issue})

        # Calculate confidence for the current blockquote
        confidence_percentage = calculate_confidence(blockquote_issues, 1)

        if blockquote_issues:
            issues.append({
                "blockquote_index": blockquote_index + 1,
                "blockquote_html": blockquote_html,
                "issues": blockquote_issues,
                "confidence_percentage": confidence_percentage
            })

            for issue_detail in blockquote_issues:
                logging.warning(f"Blockquote {blockquote_index + 1}: {issue_detail['issue']}")

    # Calculate overall confidence
    overall_confidence = (
        sum(blockquote.get("confidence_percentage", 0) for blockquote in issues) / len(issues)
        if issues else 100.0
    )

    return {"status": "Malformed" if issues else "Passed", "details": issues, "confidence": overall_confidence}
