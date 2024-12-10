import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

"""
1.3.1 (a) Heading markup is used appropriately
"""
# Configure logging
logging.basicConfig(level=logging.DEBUG)

def check_heading_markup(html):
    """
    Validates heading markup for WCAG compliance.
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span'])
        logging.info(f"Found {len(headings)} elements potentially acting as headings.")

        if not headings:
            return {
                "status": "Not Applicable",
                "details": [],
                "confidence": 100.0,
                "issue_count": 0
            }

        issues = []

        # Helper to add an issue
        def add_issue(line, tag, text, issue, code):
            issues.append({
                "Line Number": line,
                "Heading Tag": tag,
                "Text Content": text.strip(),
                "Issue": issue,
                "Issue Code": code
            })

        # Track hierarchy levels
        prev_level = 0
        seen_texts = set()  # To detect repetition
        for heading in headings:
            line_number = getattr(heading, "sourceline", "Unknown")
            heading_tag = heading.name
            heading_text = heading.get_text(strip=True)
            role = heading.get('role', '')
            aria_level = heading.get('aria-level', '')

            # Check if the element is intended to act as a heading
            is_aria_heading = role == 'heading'

            # Skip elements that are neither semantic headings nor ARIA headings
            if heading_tag not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and not is_aria_heading:
                continue

            # Determine the current heading level
            current_level = None
            if is_aria_heading:
                try:
                    current_level = int(aria_level)
                except ValueError:
                    current_level = None
            else:
                current_level = int(heading_tag[1])

            # Use match-case to handle heading issues
            match {
                "is_repetitive": heading_text in seen_texts,
                "is_aria_heading": is_aria_heading,
                "missing_aria_level": is_aria_heading and not aria_level,
                "invalid_aria_level": is_aria_heading and (not aria_level.isdigit() or not (1 <= int(aria_level) <= 6)),
                "is_empty": not heading_text.strip(),
                "hierarchy_skip": prev_level and current_level and current_level > prev_level + 1,
                "first_heading_invalid": prev_level == 0 and current_level != 1
            }:
                case {"is_repetitive": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        "Repetitive heading detected.",
                        "1.3.1 (a)"
                    )
                case {"is_aria_heading": True, "missing_aria_level": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        "Missing aria-level on role='heading'.",
                        "ARIA12"
                    )
                case {"is_aria_heading": True, "invalid_aria_level": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        f"Invalid aria-level '{aria_level}'. Must be between 1 and 6.",
                        "ARIA12"
                    )
                case {"is_aria_heading": True, "is_empty": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        "Heading with role='heading' is empty or not descriptive.",
                        "2.4.6"
                    )
                case {"hierarchy_skip": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        f"Skipped heading levels from <h{prev_level}> to <h{current_level}>.",
                        "1.3.1 (a)"
                    )
                case {"first_heading_invalid": True}:
                    add_issue(
                        line_number,
                        heading_tag,
                        heading_text,
                        "The first heading should be <h1> or aria-level='1'.",
                        "1.3.1 (a)"
                    )

            # Update previous level for hierarchy tracking
            if current_level:
                prev_level = current_level

            # Mark this text as seen
            seen_texts.add(heading_text)

        # Calculate confidence score
        confidence = calculate_heading_confidence(issues, len(headings))

        return {
            "status": "Malformed" if issues else "Passed",
            "details": issues,
            "confidence": confidence,
            "issue_count": len(issues)
        }

    except Exception as e:
        logging.error(f"Error while checking heading markup: {e}")
        return {
            "status": "Error",
            "details": [{"Issue": "An unexpected error occurred.", "Issue Code": "1.3.1 (a)"}],
            "confidence": 50.0,
            "issue_count": 1
        }

def calculate_heading_confidence(issues, total_headings):
    """
    Calculates confidence score for heading compliance.
    """
    baseline_confidence = 95.0
    for issue in issues:
        if "multiple <h1>" in issue.get('Issue', '').lower():
            baseline_confidence -= 15
        elif "missing aria-level" in issue.get('Issue', '').lower():
            baseline_confidence -= 10
        elif "skipped heading levels" in issue.get('Issue', '').lower():
            baseline_confidence -= 5
    if total_headings > 0:
        baseline_confidence *= (1 - len(issues) / total_headings)
    return max(baseline_confidence, 0)


def calculate_heading_confidence(issues, total_headings):
    """
    Calculates confidence score for heading compliance.
    """
    baseline_confidence = 95.0
    for issue in issues:
        if "multiple <h1>" in issue.get('Issue', '').lower():
            baseline_confidence -= 15
        elif "missing aria-level" in issue.get('Issue', '').lower():
            baseline_confidence -= 10
        elif "skipped heading levels" in issue.get('Issue', '').lower():
            baseline_confidence -= 5
    if total_headings > 0:
        baseline_confidence *= (1 - len(issues) / total_headings)
    return max(baseline_confidence, 0)

def write_heading_info(file_path, heading_info, format="csv"):
    """
    Writes heading issues into a CSV, JSON, or Excel file.
    """
    logging.debug(f"Writing heading info to {file_path} in {format} format.")
    try:
        if format == "csv":
            fieldnames = ['Line Number', 'Heading Tag', 'Text Content', 'Issue', 'Issue Code']
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(heading_info)
        elif format == "json":
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(heading_info, jsonfile, indent=4)
        elif format == "excel":
            df = pd.DataFrame(heading_info)
            df.to_excel(file_path, index=False)
        else:
            raise ValueError("Unsupported file format.")
        logging.info(f"Heading info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing heading info: {e}")
        return False
