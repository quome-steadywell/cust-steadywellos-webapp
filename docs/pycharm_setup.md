# PyCharm Setup Guide

This guide explains how to set up PyCharm to use the local `.venv` virtual environment for this project.

## Automatic Setup

The PyCharm configuration files in the `.idea` directory have been updated to use the local `.venv` virtual environment. When you open the project in PyCharm, it should automatically use the correct Python interpreter.

## Manual Setup

If you need to manually configure PyCharm to use the local `.venv`, follow these steps:

1. Open the project in PyCharm
2. Go to `File > Settings` (or `PyCharm > Preferences` on macOS)
3. Navigate to `Project: cust-steadywellos-webapp > Python Interpreter`
4. Click the gear icon and select `Add...`
5. Choose `Existing Environment`
6. Click the `...` button next to the interpreter path field
7. Navigate to the project's `.venv` directory and select the Python executable:
   - On macOS/Linux: `.venv/bin/python`
   - On Windows: `.venv\Scripts\python.exe`
8. Click `OK` to save the interpreter settings
9. Click `OK` to close the Settings dialog

## Verifying the Setup

To verify that PyCharm is using the correct Python interpreter:

1. Open any Python file in the project
2. Look at the bottom-right corner of the PyCharm window
3. You should see `Python 3.12 (cust-steadywellos-webapp)` or similar, indicating that PyCharm is using the local `.venv`

## Creating a New Virtual Environment

If you need to create a new virtual environment for the project:

1. Make sure you have Python 3.12 installed on your system
2. Open a terminal in the project root directory
3. Run: `python -m venv .venv`
4. Activate the virtual environment:
   - On macOS/Linux: `source .venv/bin/activate`
   - On Windows: `.venv\Scripts\activate`
5. Install the required packages: `pip install -r requirements.txt`
6. Follow the steps in the "Manual Setup" section to configure PyCharm to use the new virtual environment