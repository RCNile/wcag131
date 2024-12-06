import logging
import csv
import json
import pandas as pd
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Function to write landmark issues to a file
def write_landmark_info(file_path, landmark_info, format="csv"):
    """Writes landmark information to a file in CSV, JSON, or Excel format."""
    logging.debug(f"Writing landmark info to {file_path} in {format} format.")
    try:
        if format == "csv":
            fieldnames = ['Landmark Index', 'Landmark Tag', 'Landmark HTML', 'Issue', 'Issue Code', 'Confidence Percentage']
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for landmark in landmark_info:
                    for issue in landmark['issues']:
                        writer.writerow({
                            'Landmark Index': landmark['landmark_index'],
                            'Landmark Tag': landmark['landmark_tag'],
                            'Landmark HTML': landmark['landmark_html'],
                            'Issue': issue,
                            'Issue Code': "1.3.1 (e)",
                            'Confidence Percentage': landmark.get('confidence_percentage', 'N/A')
                        })
        elif format == "json":
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(landmark_info, jsonfile, indent=4)
        elif format == "excel":
            rows = []
            for landmark in landmark_info:
                for issue in landmark['issues']:
                    rows.append({
                        'Landmark Index': landmark['landmark_index'],
                        'Landmark Tag': landmark['landmark_tag'],
                        'Landmark HTML': landmark['landmark_html'],
                        'Issue': issue,
                        'Issue Code': "1.3.1 (e)",
                        'Confidence Percentage': landmark.get('confidence_percentage', 'N/A')
                    })
            df = pd.DataFrame(rows)
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported file format: {format}")
        logging.info(f"Landmark info successfully written to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error writing landmark info to {file_path}: {e}")
        return False

# Landmark testing function
def test_landmark_markup(html):
    """Tests for proper usage of landmark elements in the HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    landmarks = soup.find_all(['header', 'nav', 'main', 'footer', 'section', 'aside', 'article', 'form', 'hgroup'])
    logging.info(f"Found {len(landmarks)} landmark elements.")

    if not landmarks:
        logging.warning("No landmark elements found. Markup not applicable.")
        return {"status": "Not Applicable", "details": [], "confidence": 100.0}

    issues = []
    for index, landmark in enumerate(landmarks):
        landmark_content = landmark.get_text(strip=True)
        landmark_html = str(landmark)

        # Check for issues with the landmark
        empty_check = check_empty_landmark(landmark_content)
        content_check = check_landmark_content(landmark)

        # Aggregate issues for the current landmark
        landmark_issues = [check for check in [empty_check, content_check] if check]
        confidence_percentage = calculate_landmark_confidence(landmark_issues, len(landmarks))

        if landmark_issues:
            issues.append({
                "landmark_index": index + 1,
                "landmark_tag": landmark.name,
                "landmark_html": landmark_html,
                "issues": landmark_issues,
                "confidence_percentage": confidence_percentage
            })

    # Calculate overall confidence
    overall_confidence = (
        sum(landmark.get("confidence_percentage", 0) for landmark in issues) / len(issues)
        if issues else 100.0
    )

    return {
        "status": "Malformed" if issues else "Passed",
        "details": issues,
        "confidence": overall_confidence
    }

# Check if the landmark element is empty
def check_empty_landmark(landmark_content):
    """Checks if the landmark element is empty or lacks meaningful content."""
    if not landmark_content.strip():
        return "Landmark element is empty or has no meaningful content."
    return None

# Check if the content matches the purpose of the landmark
def check_landmark_content(landmark):
    """Validates the content of a landmark element using match-case."""
    tag = landmark.name
    content = landmark.get_text(strip=True)
    element_html = str(landmark)

    match tag:
        case 'nav' if 'href' not in element_html:
            return "Landmark <nav> should contain navigation links."
        case 'main' if len(content.split()) < 20:
            return "Landmark <main> should contain the primary content of the page."
        case 'header' if 'h1' not in element_html:
            return "Landmark <header> should include an <h1> element."
        case 'footer' if len(content.split()) < 5:
            return "Landmark <footer> should contain footer information."
        case 'aside' if len(content.split()) < 10:
            return "Landmark <aside> should have meaningful content."
        case 'section' if len(content.split()) < 10:
            return "Landmark <section> should have a meaningful amount of content."
        case 'article' if len(content.split()) < 50:
            return "Landmark <article> should contain self-contained detailed content."
        case 'form' if not landmark.find(['input', 'textarea', 'select']):
            return "Landmark <form> should include input elements."
        case 'form' if not landmark.find_all('label') and not any(
            inp.get('aria-label') for inp in landmark.find_all(['input', 'textarea', 'select'])
        ):
            return "Landmark <form> should have labeled inputs using <label> elements or aria-label attributes."
        case _:
            return None

# Calculate confidence for landmarks
def calculate_landmark_confidence(landmark_issues, total_landmarks):
    """Calculates confidence for landmark compliance."""
    baseline_confidence = 95.0
    for issue in landmark_issues:
        if "empty" in issue.lower():
            baseline_confidence -= 20
        elif "should contain" in issue.lower():
            baseline_confidence -= 10
    if total_landmarks > 0:
        baseline_confidence *= (1 - len(landmark_issues) / total_landmarks)
    return max(baseline_confidence, 0)

