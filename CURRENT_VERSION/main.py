import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import asyncio
from openpyxl import Workbook
from playwright.async_api import async_playwright
from datetime import datetime
from checks.WCAG_1_3_1.test_blockquote_markup import test_blockquote_markup
from checks.WCAG_1_3_1.test_form_markup import test_form_markup
from checks.WCAG_1_3_1.test_heading_markup import check_heading_markup
from checks.WCAG_1_3_1.test_landmark_markup import test_landmark_markup
from checks.WCAG_1_3_1.test_list_markup import test_list_markup
from checks.WCAG_1_3_1.test_structural_markup import test_structural_markup
from checks.WCAG_1_3_1.test_table_markup import test_table_markup


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


def process_url(url, workbook, results_file):
    """Process a single URL and log detailed issues into Excel."""
    try:
        html_content = asyncio.run(fetch_html_content(url))
        if html_content is None:
            print(f"Failed to retrieve HTML content for {url}.")
            return

        # Tests and their respective functions
        tests_and_functions = {
            "heading_markup": check_heading_markup,
            "list_markup": test_list_markup,
            "table_markup": test_table_markup,
            "blockquote_markup": test_blockquote_markup,
            "landmark_markup": test_landmark_markup,
            "structural_markup": test_structural_markup,
            "form_markup": test_form_markup,
        }

        # Mapping for formatting details based on test name
        format_details = {
            "table_markup": lambda details: "\n".join(
                f"Table Index: {detail.get('Table Index', 'N/A')}, "
                f"Issue: {detail.get('Issue', 'N/A')}, "
                f"Code: {detail.get('Issue Code', 'N/A')}, "
                f"Confidence: {detail.get('Confidence Percentage', 'N/A')}%, "
                f"HTML: {detail.get('Table HTML', 'N/A')}"
                for detail in details
            ),
            # Other formatters for different tests go here
        }

        # Prepare a row for the current URL
        row = [url]  # Initialize row with the URL

        for test_name, test_function in tests_and_functions.items():
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
                if details:
                    issue_text = format_details.get(test_name, lambda x: "No formatter available")(details)
                else:
                    issue_text = "No issues found"
                row.append(issue_text)

            except Exception as test_error:
                print(f"Error during {test_name} for {url}: {test_error}")
                row.extend(["Error", "0.00%", "Error details unavailable"])

        # Append the row to the Excel summary sheet
        summary_sheet = workbook["Summary"]
        summary_sheet.append(row)

        # Save workbook after processing each URL
        workbook.save(results_file)

        print(f"Completed processing {url}. Results saved in Excel.")

    except Exception as e:
        print(f"Unexpected error for {url}: {e}")


def main():
    # File containing the list of URLs
    script_dir = os.path.dirname(os.path.abspath(__file__))
    urls_file = os.path.join(script_dir, "urls.txt")

    # Timeout duration in seconds
    timeout_duration = 120

    # Verify if urls.txt exists
    if not os.path.exists(urls_file):
        print(f"File {urls_file} not found.")
        return

    # Read URLs from the file
    with open(urls_file, "r") as file:
        urls = [url.strip() for url in file.readlines() if url.strip()]

    if not urls:
        print("No URLs found in the file. Exiting.")
        return

    # Prepare Excel workbook
    workbook = create_results_workbook()

    # Define the results file location at the start
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(script_dir, f"WCAG1.3.1_{timestamp}.xlsx")
    workbook.save(results_file)  # Save the initial workbook structure

    # Process each URL with a timeout
    for i, url in enumerate(urls, start=1):
        print(f"\nTesting URL {i}/{len(urls)}: {url}")

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process_url, url, workbook, results_file)

            try:
                # Run the URL processing with a timeout
                future.result(timeout=timeout_duration)
            except TimeoutError:
                print(f"Timeout: Test for {url} took too long and was skipped.")
                future.cancel()
            except Exception as e:
                print(f"Unexpected error for {url}: {e}")

    print(f"\nBatch test completed. Final results saved to {results_file}.")


if __name__ == "__main__":
    main()
