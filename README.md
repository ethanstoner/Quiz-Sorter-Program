# Quiz Sorter for TAs 📊

A professional tool for organizing Wayground quiz data with attendance tracking, designed specifically for Teaching Assistants.

## What's New

- **Canonical names everywhere**: Output uses `Last, Middle, First (Nick) #ID` based on attendance.
- **Sorted output**: CSV and PDF are sorted by last name.
- **Full roster**: All students appear in the output. Missing scores render as **X** (bold in PDF).
- **Configurable curve cap**: Toggle on/off and set the cap (e.g., 10, 9, 8). Scores are capped at `min(score, cap)`.
- **Retakes support**: Importing a quiz again only **raises** a student's score (or replaces **X**); other students' scores remain intact.
- **Multi-quiz merge**: Import files with multiple quiz columns (e.g., Quiz 1–5). All columns are merged into the period MASTER without overwriting others.
- **Period MASTER files**: Each period keeps a MASTER CSV that accumulates all quizzes.

## 📁 Folder Structure

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

## 🚀 Quick Start

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

## Retakes

To process retakes, import a CSV with the same quiz column name (e.g., `Quiz 3 (/10)`).
For each student:
- If the existing score is **X**, the new score replaces it.
- If both are numbers, the higher value wins.
- Other students are unaffected.

### Header de-duplication

Some Google Sheets exports include extra headers such as `Quiz Values - Sheet(1) (/10)` in addition
to standard headers like `Quiz 1 (/10)`. The importer now normalizes headers to canonical names
(e.g., `Quiz 1 (/10)`) and folds duplicates into a single column. When folding multiple columns that
represent the same quiz, the app merges each cell using the retake rule:
- If the existing value is X and the new value is a number, the number wins.
- If both are numbers, the higher number wins.
- If the new value is X, the existing value remains.

## 📋 Features

- ✅ **Smart Name Matching**: Handles partial names (e.g., "Bob V" → "Bob Vance")
- ✅ **Attendance Integration**: Adds absent students with X marks
- ✅ **Alphabetical Sorting**: Sorts by last name, first name
- ✅ **Professional PDF**: Print-ready with highlighting for absent students
- ✅ **Auto-Open**: PDF opens automatically after processing
- ✅ **Smart Retakes**: Preserve higher scores when importing retakes
- ✅ **Multi-Column Support**: Handle quiz files with multiple quiz columns
- ✅ **Configurable Grading**: Apply curve caps and normalize scores
- ✅ **Period Management**: Separate master files for different class periods

## 🎯 Perfect for:
- Marine Biology TAs (and other subjects!)
- Wayground quiz data processing
- Attendance tracking
- Grade sheet creation
- Print-ready output for manual grading
- Managing multiple quiz attempts and retakes

## 📝 File Formats

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

## Quick Manual Test Plan

1) **UI**: Launch the app. Confirm the green button shows "🚀 Process Quiz Data" in all states.
2) **Multi-Column**: Import a quiz with columns `Quiz 1 (/10)` to `Quiz 5 (/10)` and verify MASTER adds all 5.
3) **Curve Cap**: Toggle curve cap to 8; re-import the same quiz. Confirm no value exceeds 8.
4) **Retakes**: Create a retake CSV where 3 students have higher scores in `Quiz 3 (/10)`. Import it. Confirm only those 3 increase.
5) **Periods**: Rename the attendance to include a new period string like `period 7`, import a quiz, and confirm a new `Period_7_MASTER.csv` is created.
6) **PDF**: Open the PDF and verify names are canonical, sorted by last, and X cells render bold-centered.

## 🔧 Troubleshooting

- **PDF won't open**: Make sure you have a PDF viewer installed
- **Import errors**: Run `pip3 install -r requirements.txt`
- **File not found**: Check that files are in the correct folders
- **Button text issues on macOS**: The app now uses enhanced styling to ensure visibility
- **Multi-column imports**: Ensure quiz columns are named like `Quiz 1 (/10)`, `Quiz 2 (/10)`, etc.

## 📞 Support

This tool was designed specifically for TA workflow optimization. Enjoy your organized grading! 🎓
