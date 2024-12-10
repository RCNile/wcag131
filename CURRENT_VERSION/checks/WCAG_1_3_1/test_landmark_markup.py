import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

def write_landmark_info(file_path, landmark_info, format="csv"):
    """Writes landmark information to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing landmark info to {file_path} in {format} format.")
    try:
        details = landmark_info.get("details", [])  # Extract details directly
        rows = [
            {
                'Landmark Index': idx + 1,
                'Landmark Tag': detail.get('Landmark Tag', 'N/A'),
                'Landmark HTML': detail.get('HTML Snippet', 'N/A'),
                'Issue': detail.get('Issue', 'N/A'),
                'Suggestion': generate_suggestion(detail.get('Issue', ''), detail.get('Landmark Tag', 'N/A')),
                'Confidence Percentage': landmark_info.get('confidence', 'N/A')
            }
            for idx, detail in enumerate(details)
        ]

        # Write data to the specified format
        if format == "csv":
            fieldnames = ['Landmark Index', 'Landmark Tag', 'Landmark HTML', 'Issue', 'Suggestion', 'Confidence Percentage']
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

        logging.info(f"Landmark info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing landmark info to {file_path}: {e}")
        return False



def check_empty_landmark(landmark_content):
    """Checks if the landmark element is empty or lacks meaningful content."""
    if not landmark_content.strip():
        return "Landmark element is empty or has no meaningful content."
    return None

def check_landmark_content(landmark):
    """Validates the content of a landmark element based on its type."""
    tag = landmark.name
    content = landmark.get_text(strip=True)

    match tag:
        case 'nav' if not landmark.find_all('a', href=True):
            return "Landmark <nav> should contain navigation links."
        case 'main' if len(content.split()) < 20:
            return "Landmark <main> should contain the primary content of the page."
        case 'header' if not landmark.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            return "Landmark <header> should include a heading element (e.g., <h1>)."
        case 'footer' if len(content.split()) < 5:
            return "Landmark <footer> should contain footer information."
        case 'aside' if len(content.split()) < 10:
            return "Landmark <aside> should have meaningful content."
        case 'section' if len(content.split()) < 10:
            return "Landmark <section> should have a meaningful amount of content."
        case 'article' if len(content.split()) < 50:
            return "Landmark <article> should contain self-contained, detailed content."
        case 'form' if not landmark.find(['input', 'textarea', 'select']):
            return "Landmark <form> should include input elements."
        case 'form' if not landmark.find_all('label') and not any(
            inp.get('aria-label') for inp in landmark.find_all(['input', 'textarea', 'select'])
        ):
            return "Landmark <form> should have labeled inputs using <label> elements or aria-label attributes."
        case _:
            return None

def calculate_landmark_confidence(landmark_issues, total_landmarks):
    """Calculates confidence for landmark compliance."""
    baseline_confidence = 100.0
    weight_map = {
        "empty": 20,
        "should contain": 10,
    }

    for issue in landmark_issues:
        # Extract the issue text if it's a dictionary
        issue_text = issue if isinstance(issue, str) else issue.get("Issue", "")
        for key, weight in weight_map.items():
            if key in issue_text.lower():
                baseline_confidence -= weight

    # Adjust confidence by issue density
    if total_landmarks > 0:
        confidence_penalty = (len(landmark_issues) / total_landmarks) * 10  # Proportional penalty
        baseline_confidence -= confidence_penalty

    return max(baseline_confidence, 0)


def generate_suggestion(issue, tag):
    """Generates a suggestion based on the identified issue."""
    if "empty" in issue.lower():
        return f"Ensure the <{tag}> element contains meaningful content."
    if "should contain" in issue.lower():
        return f"Ensure the <{tag}> element fulfills its intended purpose with adequate content."
    if "navigation links" in issue.lower():
        return "Add <a> elements with href attributes to the <nav> landmark for navigation."
    if "heading element" in issue.lower():
        return f"Include a heading element (e.g., <h1>) within the <{tag}> landmark."
    return "Review and correct the landmark element."


def test_landmark_markup(html):
    """Tests for proper usage of landmark elements in the HTML."""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        landmarks = soup.find_all(['header', 'nav', 'main', 'footer', 'section', 'aside', 'article', 'form', 'hgroup'])
        logging.info(f"Found {len(landmarks)} landmark elements.")

        if not landmarks:
            logging.warning("No landmark elements detected in the document.")
            return {
                "status": "Not Applicable",
                "details": [{"Issue": "No landmark elements found in the document.", "Issue Code": "1.3.1 (e)"}],
                "confidence": 100.0,
                "issue_count": 1
            }

        issues = []

        for index, landmark in enumerate(landmarks):
            try:
                content = landmark.get_text(strip=True)
                html_snippet = str(landmark)[:100]
                line_number = getattr(landmark, "sourceline", "Unknown")

                # Check for issues
                landmark_issues = []
                if (empty_issue := check_empty_landmark(content)):
                    landmark_issues.append({"Issue": empty_issue})
                if (content_issue := check_landmark_content(landmark)):
                    landmark_issues.append({"Issue": content_issue})

                for issue in landmark_issues:
                    issues.append({
                        "Line Number": line_number,
                        "Landmark Tag": landmark.name if landmark.name else "Unknown",
                        "HTML Snippet": html_snippet,
                        "Issue": issue["Issue"],
                        "Issue Code": "1.3.1 (e)"
                    })

            except Exception as e:
                logging.error(f"Error processing landmark at index {index}: {e}")
                issues.append({
                    "Line Number": "Unknown",
                    "Landmark Tag": "Unknown",
                    "HTML Snippet": str(landmark)[:100],
                    "Issue": f"Error processing landmark: {str(e)}",
                    "Issue Code": "1.3.1 (e)"
                })

        if not issues:
            logging.info("No issues detected for landmark markup.")
            return {
                "status": "Passed",
                "details": [{"Issue": "All landmark elements are valid.", "Issue Code": "1.3.1 (e)"}],
                "confidence": 100.0,
                "issue_count": 0
            }

        confidence = calculate_landmark_confidence(issues, len(landmarks))
        result = {
            "status": "Malformed",
            "details": issues,
            "confidence": confidence,
            "issue_count": len(issues)
        }
        logging.debug(f"Landmark test result: {result}")
        return result

    except Exception as e:
        logging.error(f"Unexpected error in landmark test: {e}")
        return {
            "status": "Error",
            "details": [{"Issue": f"Unexpected error occurred: {e}", "Issue Code": "1.3.1 (e)"}],
            "confidence": 50.0,
            "issue_count": 1
        }
