#!/usr/bin/env python3
"""
Script to traverse the project folder structure, concatenate all text files,
and save them to a single text file.
"""

import os
import sys
import datetime
import shutil
from pathlib import Path

# Directories to exclude from traversal
EXCLUDED_DIRS = [
    ".github",
    ".venv",
    "legacy",
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "venv",
    "env",
    ".idea",
    "gemini-archive",
    ".vscode",
    ".DS_Store",
]

# File patterns to exclude (using basename)
EXCLUDED_FILE_PATTERNS = [
    "gemini-",
    ".pyc",
    ".pyo",
    ".so",
    ".o",
    ".a",
    ".lib",
    ".dll",
    ".exe",
    ".bin",
    ".lock",
    ".DS_Store",
]

# Binary file extensions to exclude
BINARY_EXTENSIONS = [
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".otf",
    ".pyc",
    ".pyo",
    ".so",
    ".o",
    ".a",
    ".lib",
    ".dll",
    ".exe",
    ".bin",
    ".db",
    ".sqlite",
    ".pickle",
    ".pkl",
    ".npy",
    ".npz",
    ".excalidraw",
    ".xml",
]

# Maximum file size to process (in bytes) - 100KB to keep output small
MAX_FILE_SIZE = 100 * 1024

# Large text files to specifically exclude
EXCLUDED_FILES = [
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "uv.lock",
    "tags",
]


def should_include_dir(dir_path):
    """Check if directory should be included in traversal."""
    dir_name = os.path.basename(dir_path)
    return dir_name not in EXCLUDED_DIRS


def should_include_file(file_path):
    """Check if file should be included in output."""
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(file_path)

    # Check if file is in excluded files list
    if filename in EXCLUDED_FILES:
        print(f"Skipping excluded file: {filename}")
        return False

    # Check if file matches any excluded pattern
    for pattern in EXCLUDED_FILE_PATTERNS:
        if pattern in filename:
            return False

    # Check if it's a known binary extension
    if ext.lower() in BINARY_EXTENSIONS:
        return False

    # Check if file is too large
    try:
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            print(f"Skipping large file: {file_path} ({file_size / 1024:.1f} KB)")
            return False
    except OSError:
        # If we can't get the file size, skip it
        return False

    # Include all files that aren't explicitly excluded
    return True


def main():
    # Get the project root directory (assuming script is in scripts/ directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Create archive directory if it doesn't exist
    archive_dir = os.path.join(script_dir, "gemini-archive")
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"Created archive directory: {archive_dir}")

    # Move existing gemini output files to archive
    for filename in os.listdir(script_dir):
        if filename.startswith("gemini-") and filename.endswith(".txt"):
            old_path = os.path.join(script_dir, filename)
            new_path = os.path.join(archive_dir, filename)
            try:
                shutil.move(old_path, new_path)
                print(f"Moved {filename} to archive")
            except Exception as e:
                print(f"Error moving {filename} to archive: {e}")

    # Generate timestamp for output filename
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"gemini-{timestamp}.txt"

    # Output file path
    output_file = os.path.join(script_dir, output_filename)

    print(f"Traversing project directory: {project_root}")
    print(f"Output will be saved to: {output_file}")

    # Collect all files to include
    files_to_process = []

    for root, dirs, files in os.walk(project_root):
        # Modify dirs in-place to exclude unwanted directories
        dirs[:] = [d for d in dirs if should_include_dir(os.path.join(root, d))]

        for file in files:
            file_path = os.path.join(root, file)
            if should_include_file(file_path):
                # Get relative path from project root
                rel_path = os.path.relpath(file_path, project_root)
                files_to_process.append((rel_path, file_path))

    # Sort files by path for consistent output
    files_to_process.sort()

    # Process files and write to output
    total_files = len(files_to_process)
    processed_files = 0
    skipped_files = 0

    print(f"Found {total_files} files to process")

    with open(output_file, "w", encoding="utf-8") as out_file:
        for rel_path, abs_path in files_to_process:
            try:
                # Try to detect if file is binary
                is_binary = False
                try:
                    with open(abs_path, "r", encoding="utf-8") as test_file:
                        test_file.read(1024)  # Try to read a small chunk
                except UnicodeDecodeError:
                    is_binary = True

                if is_binary:
                    print(f"Skipping binary file: {rel_path}")
                    skipped_files += 1
                    continue

                with open(abs_path, "r", encoding="utf-8") as in_file:
                    content = in_file.read()

                # Write file separator with relative path
                out_file.write(f"File: --- /{rel_path}\n")

                # Write file content
                out_file.write(content)

                # Add newlines for separation
                if not content.endswith("\n"):
                    out_file.write("\n")
                out_file.write("\n")

                processed_files += 1
                if processed_files % 10 == 0:
                    print(f"Progress: {processed_files}/{total_files} files processed")

            except Exception as e:
                print(f"Error processing {rel_path}: {e}")
                skipped_files += 1

    print(f"Completed! Processed {processed_files} files, skipped {skipped_files} files")
    print(f"Output saved to {output_file} with timestamp {timestamp}")

    # Show output file size
    output_size = os.path.getsize(output_file)
    print(f"Output file size: {output_size / (1024 * 1024):.2f} MB")

    if output_size > 100 * 1024 * 1024:
        print(f"⚠️  WARNING: Output file exceeds 100 MB limit for Gemini!")
        print(f"Consider reducing MAX_FILE_SIZE or excluding more files.")


if __name__ == "__main__":
    main()
