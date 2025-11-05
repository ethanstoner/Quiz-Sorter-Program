# Quiz Sorter for TAs

A professional tool for organizing Wayground quiz data with attendance tracking, designed specifically for Teaching Assistants.

## Overview

This application streamlines the quiz grading workflow by automatically processing quiz data, matching student names, integrating attendance records, and generating professional PDF output. It supports multiple quizzes, retakes, configurable grading curves, and maintains separate master files for each class period.

## Key Features

- **Canonical Name Formatting** - Output uses standardized format: `Last, Middle, First (Nick) #ID` based on attendance records
- **Sorted Output** - CSV and PDF files are automatically sorted by last name
- **Complete Roster** - All students appear in output; missing scores render as **X** (bold in PDF)
- **Configurable Curve Cap** - Toggle on/off and set maximum points (e.g., 10, 9, 8). Scores are capped at `min(score, cap)`
- **Retake Support** - Importing a quiz again only raises a student's score (or replaces **X**); other students' scores remain intact
- **Multi-Quiz Merge** - Import files with multiple quiz columns (e.g., Quiz 1–5). All columns are merged into the period MASTER without overwriting others
- **Period Management** - Each period maintains a separate MASTER CSV that accumulates all quizzes

## Folder Structure

```
Quiz Sorter Program/
├── input/           # Place your quiz data CSV files here
├── attendance/      # Place your attendance list CSV files here  
├── output/          # Processed files (CSV + PDF) are saved here
├── quiz_sorter_gui.py      # Main GUI application
├── enhanced_quiz_sorter.py # Core processing logic
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Quick Start

1. **Install Dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Run the Program:**
   ```bash
   python3 quiz_sorter_gui.py
   ```

3. **Use the GUI:**
   - Select your quiz data file from the `input/` folder
   - Select your attendance list from the `attendance/` folder (optional)
   - Choose output location (recommended: `output/` folder)
   - Click "Process Quiz Data"
   - PDF will open automatically!

## Typical Workflow

1. Export quiz results from Google Sheets as CSV (tabular with `Student` and quiz columns like `Quiz 1 (/10)`).
2. Choose the **Attendance CSV** and the **Quiz Data CSV** in the app.
3. (Optional) Enable **Apply curve cap** and set **Max points**.
4. Click **Process Quiz Data**.
5. The app will:
   - Map `Student` to attendance canonical names
   - Merge scores into the **{Period}_MASTER.csv**
   - Fill missing cells with **X**
   - Sort by last name
   - Save your selected output CSV
   - Generate a print-ready PDF

## Retake Processing

To process retakes, import a CSV with the same quiz column name (e.g., `Quiz 3 (/10)`).

**Retake Rules:**
- If the existing score is **X**, the new score replaces it
- If both are numbers, the higher value is preserved
- Other students' scores remain unaffected

### Header De-duplication

Some Google Sheets exports include extra headers such as `Quiz Values - Sheet(1) (/10)` in addition to standard headers like `Quiz 1 (/10)`. The importer normalizes headers to canonical names (e.g., `Quiz 1 (/10)`) and consolidates duplicates into a single column.

**When consolidating multiple columns representing the same quiz:**
- If the existing value is X and the new value is a number, the number is used
- If both are numbers, the higher number is preserved
- If the new value is X, the existing value remains unchanged

## Features

- **Smart Name Matching** - Handles partial names (e.g., "Bob V" → "Bob Vance")
- **Attendance Integration** - Automatically adds absent students with X marks
- **Alphabetical Sorting** - Sorts by last name, then first name
- **Professional PDF Output** - Print-ready format with highlighting for absent students
- **Auto-Open PDF** - Automatically opens PDF after processing completes
- **Smart Retakes** - Preserves higher scores when importing retakes
- **Multi-Column Support** - Handles quiz files with multiple quiz columns simultaneously
- **Configurable Grading** - Apply curve caps and normalize scores
- **Period Management** - Separate master files for different class periods

## Use Cases

- Teaching Assistants across all subjects
- Wayground quiz data processing
- Attendance tracking and integration
- Professional grade sheet creation
- Print-ready output for manual grading
- Managing multiple quiz attempts and retakes

## File Formats

### Quiz Data CSV Format:
```
Student Name,Quiz 1 (/10),Quiz 2 (/10),Quiz 3 (/10)
Bob Vance,8,7,9
Allison Ion,10,9,8
```

### Attendance List CSV Format:
```
Name
Vance, Bob Michael (Bobby) #1000000001
Ion, Allison Grace (Allie) #1000000002
Smith, John David (Johnny) #1000000003
```

## Testing Retakes

1. Run a first import with normal scores.
2. Create a copy of that quiz CSV and bump a few students' scores in `Quiz 2 (/10)`.
3. Import the copy. Verify the MASTER shows the higher values for those students, and unchanged values for the rest.

## Testing Different Period Formats

The app tries to infer the **Period** from either the file name or the folder:
- Examples: `Period 1.csv`, `period_2_attendance.csv`, `Period3_Mitosis.csv`
- If no period is found, it falls back to `Period`.

The MASTER will be saved as `{Period}_MASTER.csv` in the working directory.

## Testing Guide

### Quick Manual Test Plan

1. **UI Verification** - Launch the application and confirm the button displays "Process Quiz Data" in all states
2. **Multi-Column Import** - Import a quiz with columns `Quiz 1 (/10)` through `Quiz 5 (/10)` and verify MASTER adds all 5 columns
3. **Curve Cap** - Toggle curve cap to 8 and re-import the same quiz; confirm no value exceeds 8
4. **Retakes** - Create a retake CSV where 3 students have higher scores in `Quiz 3 (/10)`. Import and verify only those 3 scores increase
5. **Period Management** - Rename the attendance file to include a period string like `period_7`, import a quiz, and confirm a new `Period_7_MASTER.csv` is created
6. **PDF Output** - Open the generated PDF and verify names are in canonical format, sorted by last name, and X cells render bold and centered

## Troubleshooting

**Common Issues and Solutions:**

- **PDF won't open** - Ensure you have a PDF viewer installed on your system
- **Import errors** - Run `pip3 install -r requirements.txt` to install all required dependencies
- **File not found** - Verify that files are placed in the correct folders (`input/` for quiz data, `attendance/` for attendance lists)
- **Button text visibility on macOS** - The application uses enhanced styling to ensure button text is visible
- **Multi-column imports** - Ensure quiz columns are named following the format: `Quiz 1 (/10)`, `Quiz 2 (/10)`, etc.

## Support

This tool was designed specifically for Teaching Assistant workflow optimization. For questions, issues, or feature requests, please open an issue on the GitHub repository.

---

**Designed for efficiency. Built for educators.**
