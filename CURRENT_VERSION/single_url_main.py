import os
import subprocess
from openpyxl import Workbook
from playwright.async_api import async_playwright
import asyncio
from checks.WCAG_1_3_1.test_blockquote_markup import test_blockquote_markup, write_blockquote_info_csv
from checks.WCAG_1_3_1.test_form_markup import test_form_markup, write_form_info_csv
from checks.WCAG_1_3_1.test_heading_markup import check_heading_markup, write_heading_info_csv
from checks.WCAG_1_3_1.test_landmark_markup import test_landmark_markup, write_landmark_info_csv
from checks.WCAG_1_3_1.test_list_markup import test_list_markup, write_list_info_csv
from checks.WCAG_1_3_1.test_structural_markup import test_structural_markup, write_structural_info_csv
from checks.WCAG_1_3_1.test_table_markup import test_table_markup, write_table_info_csv


def create_results_workbook():
    """Initialize an Excel workbook with the desired column format."""
    workbook = Workbook()
    summary_sheet = workbook.active
    summary_sheet.title = "Summary"
    # Column headers: URL, status, confidence score, and details for each WCAG test
    summary_sheet.append([
        "Tested URL",
        "Heading markup", "Heading Confidence", "Heading Details",
        "List markup", "List Confidence", "List Details",
        "Table markup", "Table Confidence", "Table Details",
        "Block-quote markup", "Block-quote Confidence", "Block-quote Details",
        "Landmarks", "Landmark Confidence", "Landmark Details",
        "Structural markup", "Structural Confidence", "Structural Details",
        "Forms", "Form Confidence", "Form Details",
    ])
    return workbook


async def fetch_html_content(url):
    """Fetch HTML content from the given URL."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            content = await page.content()
            await browser.close()
            return content
    except Exception as e:
        raise RuntimeError(f"Error fetching HTML content for {url}: {e}")


def process_url(url, workbook, results_dir):
    """Process a single URL and log detailed issues into Excel and CSV files for each test."""
    try:
        html_content = asyncio.run(fetch_html_content(url))
        if html_content is None:
            print(f"Failed to retrieve HTML content for {url}.")
            return

        # Tests and their respective functions
        tests_and_functions = {
            "heading_markup": (check_heading_markup, write_heading_info_csv),
            "list_markup": (test_list_markup, write_list_info_csv),
            "table_markup": (test_table_markup, write_table_info_csv),
            "blockquote_markup": (test_blockquote_markup, write_blockquote_info_csv),
            "landmark_markup": (test_landmark_markup, write_landmark_info_csv),
            "structural_markup": (test_structural_markup, write_structural_info_csv),
            "form_markup": (test_form_markup, write_form_info_csv),
        }

        # Prepare a row for the current URL
        row = [url]  # Initialize row with the URL

        for test_name, (test_function, write_function) in tests_and_functions.items():
            try:
                # Run the test function
                result = test_function(html_content)

                # Extract and append the test status
                test_status = result.get("status", "N/A")
                row.append(test_status)

                # Extract and append the overall confidence score
                overall_confidence = result.get("confidence", 100.0)
                row.append(f"{overall_confidence:.2f}%")

                # Extract and append formatted details
                details = result.get("details", [])
                issue_text = "\n".join(f"Line {d.get('Line Number', 'N/A')}: {d.get('Issue', 'N/A')}" for d in details) if details else "No issues found"
                row.append(issue_text)

                # Write CSV for this test
                if details:
                    csv_output_dir = os.path.join(results_dir, test_name)
                    os.makedirs(csv_output_dir, exist_ok=True)
                    csv_file_path = os.path.join(csv_output_dir, f"{test_name}_details.csv")

                    # Call the correct write function for this test
                    write_function(csv_file_path, details)
                    print(f"Saved CSV for {test_name} in {csv_file_path}")

            except Exception as test_error:
                print(f"Error during {test_name} for {url}: {test_error}")
                row.extend(["Error", "0.00%", "Error details unavailable"])

        # Append the row to the Excel summary sheet
        summary_sheet = workbook["Summary"]
        summary_sheet.append(row)

        # Save workbook after processing the URL
        results_file = os.path.join(results_dir, "wcag1.3.1_summary.xlsx")
        workbook.save(results_file)

        print(f"Completed processing {url}. Results saved in {results_file}.")
        return results_file

    except Exception as e:
        print(f"Unexpected error for {url}: {e}")


def open_results_file(file_path):
    """Open the results file in the default application."""
    try:
        if os.name == "nt":  # Windows
            os.startfile(file_path)
        elif os.name == "posix":  # macOS or Linux
            subprocess.run(["open" if "darwin" in os.uname().sysname.lower() else "xdg-open", file_path])
        else:
            print(f"Cannot determine how to open files on this platform.")
    except Exception as e:
        print(f"Failed to open the file {file_path}: {e}")


def main():
    # Prompt user for a single URL
    url = input("Enter the URL to test: ").strip()

    if not url:
        print("No URL provided. Exiting.")
        return

    # Generate the results folder structure
    base_results_dir = "output"
    os.makedirs(base_results_dir, exist_ok=True)

    # Create a subdirectory for the specific URL
    url_safe_name = url.replace("http://", "").replace("https://", "").replace("/", "_")
    url_results_dir = os.path.join(base_results_dir, url_safe_name)
    os.makedirs(url_results_dir, exist_ok=True)

    # Prepare Excel workbook
    workbook = create_results_workbook()

    # Process the single URL
    print(f"\nTesting URL: {url}")
    results_file = process_url(url, workbook, url_results_dir)

    if results_file:
        # Automatically open the results file
        open_results_file(results_file)

    print(f"\nTest completed. Results saved in {results_file}.")


if __name__ == "__main__":
    main()
