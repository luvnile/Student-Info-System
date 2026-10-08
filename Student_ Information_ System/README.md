# Student Information System

A simple student information system featuring both a desktop user interface and a command-line interface. Student records are securely managed and saved locally in a JSON format.

## Features

- CRUD Operations: Add, view, update, and delete student records.
- Advanced Search: Filter students by ID, name, email, course, or academic year.
- Data Export: Save student information to JSON and export datasets seamlessly.
- Validation: Check that required fields are complete and email addresses are valid.
- Logging: Maintain a comprehensive application activity log.
- CI/CD Testing: Automated unit testing locally and via GitHub Actions workflow.

## Project Structure

```text
student-info-system/
├── .github/workflows/   # GitHub Actions test workflow
├── bg.jpg               # Background image for the desktop app
├── config/              # Application configuration settings
├── data/                # Local JSON database directory (Git ignored)
├── logs/                # Application activity logs (Git ignored)
├── src/
│   ├── models/          # Student data models
│   ├── services/        # Student record business logic
│   ├── utils/           # Configuration and logging utilities
│   ├── main.py          # Command-line interface entry point
│   └── ui.py            # Desktop GUI application
├── tests/               # Unit test suite
├── main.py              # Desktop GUI application entry point
└── requirements.txt     # Python dependencies
```

## Prerequisites

- Python 3.10 or newer
- Git

## Installation & Setup

1. Clone the repository and navigate to the project root.
2. Install the required Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Running the Desktop App
```powershell
python main.py
```
*Note: Ensure `bg.jpg` remains in the root directory to load the GUI background properly.*

### Running the Command-Line Version
```powershell
python -m src.main
```

## Running Tests

Execute the local unit test suite with the following command:

```powershell
python -m unittest discover -s tests -v
```
*Note: GitHub Actions automatically triggers these tests on Python versions 3.10 through 3.13 upon every push or pull request.*
