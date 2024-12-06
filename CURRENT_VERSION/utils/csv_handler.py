import csv
import shutil

# Function to read from a CSV file and return the rows
def read_csv(file_path):
    """Reads a CSV file and returns a list of rows as dictionaries."""
    with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    return rows

# Function to write to a CSV file
def write_csv(file_path, rows, fieldnames):
    """Writes a list of dictionaries (rows) to a CSV file."""
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# Function to append to a CSV file
def append_csv(file_path, rows, fieldnames):
    """Appends rows to an existing CSV file."""
    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if csvfile.tell() == 0:  # If the file is empty, write the header
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

# Function to create a backup of a CSV file
def backup_csv(original_file, backup_file):
    """Backs up the original CSV file to a backup location."""
    shutil.copy(original_file, backup_file)
