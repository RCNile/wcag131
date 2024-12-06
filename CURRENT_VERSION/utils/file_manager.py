# utils/file_manager.py

import os
import logging
from datetime import datetime

def create_archive_folders(report_directory, page_name):
    # Create a timestamped folder to store archives
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_folder = os.path.join(report_directory, page_name, 'archive', timestamp)

    code_folder = os.path.join(archive_folder, 'code')
    image_folder = os.path.join(archive_folder, 'images')
    media_report_folder = os.path.join(archive_folder, 'media_reports')

    try:
        os.makedirs(code_folder, exist_ok=True)
        os.makedirs(image_folder, exist_ok=True)
        os.makedirs(media_report_folder, exist_ok=True)
        # Highlight: Added logging to verify folder creation
        logging.debug(f"Created folders: code - {code_folder}, images - {image_folder}, media reports - {media_report_folder}")
    except Exception as e:
        # Highlight: Added error handling for folder creation
        logging.error(f"Error creating archive folders: {e}")

    return code_folder, image_folder, media_report_folder

def list_sorted_archives(archive_path):
    if not os.path.exists(archive_path):
        return []

    # List all directories within the archive folder
    archives = [os.path.join(archive_path, d) for d in os.listdir(archive_path) if os.path.isdir(os.path.join(archive_path, d))]
    # Sort archives by creation time, newest first
    archives.sort(key=os.path.getctime, reverse=True)
    return archives
