import csv
import re
import unicodedata
import os
import pandas as pd
from datetime import datetime
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class EnhancedQuizSorter:
    def __init__(self):
        self.students = []
        self.attendance_list = []
        self.quiz_data = []
        
    def _strip_diacritics(self, s: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

    # Accepts: "Last, Middle, First (Nick) #123"  OR  "Last, First (Nick) #123" (no middle)
    _ATT_RX = re.compile(
        r"""
        ^\s*
        (?P<last>[^,]+)\s*,\s*
        (?:
            (?P<middle>[^,()#]+?)\s*,\s*     # Middle present -> comma
            (?P<first>[^()#]+?)              # First
          |                                  # OR no explicit middle:
            (?P<first2>[^()#]+?)             # First when middle omitted
        )
        (?:\s*\((?P<nick>[^)]+)\))?          # optional (Nick)
        \s+(?P<id>\#\d+)\s*$
        """,
        re.VERBOSE,
    )

    def parse_attendance_entry_new(self, entry: str):
        m = self._ATT_RX.match(entry.strip().strip('"'))
        if not m:
            raise ValueError(f"Bad attendance line: {entry}")
        g = m.groupdict()
        first = (g["first"] or g["first2"] or "").strip()
        middle = (g["middle"] or "").strip()
        last = g["last"].strip()
        nick = (g["nick"] or "").strip()
        sid = g["id"].strip()

        # Clean keys for matching
        last_clean  = self._strip_diacritics(last).lower().replace("'", "'").strip()
        first_clean = self._strip_diacritics(first).lower().strip()
        nick_clean  = self._strip_diacritics(nick).lower().strip()
        return {
            "last": last, "middle": middle, "first": first, "nick": nick, "id": sid,
            "last_clean": last_clean, "first_clean": first_clean, "nick_clean": nick_clean,
            "last_initial": last_clean[:1]
        }

    def _format_canonical_last_middle_first(self, p):
        """Build 'Last, Middle, First (Nick) #ID' with commas only when middle exists."""
        if p["middle"]:
            base = f'{p["last"]}, {p["middle"]}, {p["first"]}'
        else:
            base = f'{p["last"]}, {p["first"]}'
        if p["nick"]:
            base += f' ({p["nick"]})'
        return f"{base} {p['id']}"

    def build_roster_index_new(self, attendance_lines):
        """Index keys for matching quiz 'First Last' / 'Nick Last' / 'First L.' / 'Nick L.'"""
        idx = {}
        for line in attendance_lines:
            if not line.strip():
                continue
            p = self.parse_attendance_entry_new(line)
            canonical = self._format_canonical_last_middle_first(p)

            # Keys - create multiple variations for matching
            keys = []
            
            # Standard format: "First Last"
            keys.append(f'{p["first_clean"]} {p["last_clean"]}')
            
            # Nickname format: "Nick Last"
            if p["nick_clean"]:
                keys.append(f'{p["nick_clean"]} {p["last_clean"]}')
            
            # Initial format: "First L."
            keys.append(f'{p["first_clean"]} {p["last_initial"]}.')
            
            # Nickname initial format: "Nick L."
            if p["nick_clean"]:
                keys.append(f'{p["nick_clean"]} {p["last_initial"]}.')
            
            # Just initial: "F. Last"
            keys.append(f'{p["first_clean"][:1]}. {p["last_clean"]}')
            
            # Nickname initial: "N. Last"
            if p["nick_clean"]:
                keys.append(f'{p["nick_clean"][:1]}. {p["last_clean"]}')
            
            # Add all keys to index
            for k in keys:
                if k and k.strip():
                    idx[k] = canonical
        
        return idx

    def normalize_quiz_name(self, raw: str) -> str:
        s = self._strip_diacritics(raw.strip().strip('"'))
        s = re.sub(r"\s+", " ", s)
        return s.lower()

    def lookup_canonical_new(self, raw_name: str, roster_index: dict):
        key = self.normalize_quiz_name(raw_name)
        
        # Direct match
        if key in roster_index:
            return roster_index[key]
        
        # Try removing dots (e.g., "N." -> "N")
        key2 = key.replace(".", "")
        if key2 in roster_index:
            return roster_index[key2]
        
        # Try fuzzy matching as fallback
        best_match = None
        best_score = 0
        for roster_key, canonical in roster_index.items():
            score = fuzz.ratio(key, roster_key)
            if score > best_score and score > 80:  # 80% similarity threshold
                best_score = score
                best_match = canonical
        
        return best_match

    def sort_key_by_last(self, canonical_name: str):
        last = canonical_name.split(",", 1)[0]
        return self._strip_diacritics(last).lower()
    
    def extract_period_from_path(self, path: str) -> str:
        """
        Infer the 'Period' name from a filename or parent folder.
        Examples:
          attendance/Period 1.csv -> 'Period 1'
          quiz_data/Period3_Mitosis.csv -> 'Period 3'
        Fallback: 'Period'
        """
        base = os.path.basename(path).lower()
        m = re.search(r'(period\s*\d+)', base)
        if m:
            return m.group(1).title().replace("  ", " ")
        # try parent folder
        parent = os.path.basename(os.path.dirname(path)).lower()
        m = re.search(r'(period\s*\d+)', parent)
        if m:
            return m.group(1).title().replace("  ", " ")
        return "Period"

    def is_weird_quiz_header(self, col: str) -> bool:
        """Headers like 'Quiz Values - Sheet1(1) (/10)', 'Values (2)', etc."""
        s = str(col).strip().lower()
        return (
            s.startswith("quiz values") or
            s.startswith("values") or
            "sheet" in s
        )

    def is_canonical_quiz(self, col: str) -> bool:
        """Canonical: 'Quiz N (/10)' exactly (case-insensitive, spaces flexible)."""
        return re.match(r'^\s*quiz\s+[1-9]\d*\s*\(/10\)\s*$', str(col), flags=re.IGNORECASE) is not None

    def detect_quiz_number(self, header: str) -> int | None:
        """
        Extract quiz number from a variety of headers.
        Priority:
          1) 'Quiz N'
          2) Any '(N)' or 'SheetN(N)' patterns
          3) Last standalone integer in the string
        """
        s = str(header)
        low = s.lower()

        m = re.search(r'\bquiz\s*0*([1-9]\d*)\b', low)
        if m:
            return int(m.group(1))

        # matches "(1)" or "Sheet1(1)" or "Sheet (2)" etc.
        m = re.search(r'(?:sheet\s*0*\d*\s*)?\(\s*0*([1-9]\d*)\s*\)', low)
        if m:
            return int(m.group(1))

        # generic last integer in the string (avoid #IDs because headers do not have '#')
        nums = re.findall(r'\b([1-9]\d*)\b', low)
        if nums:
            return int(nums[-1])

        return None

    def canonical_quiz_name(self, header: str) -> str:
        n = self.detect_quiz_number(header)
        if n is None:
            # default to 1 if we have a values/sheet style, otherwise return sanitized
            if self.is_weird_quiz_header(header) or str(header).strip().lower().startswith("quiz"):
                n = 1
                return f"Quiz {n} (/10)"
            return re.sub(r'\s+', ' ', str(header)).strip()
        return f"Quiz {n} (/10)"

    def fold_to_canonical(self, df: pd.DataFrame, use_curve: bool, curve_cap: int) -> pd.DataFrame:
        """
        Build a NEW dataframe that contains only:
          - 'Student'
          - ONE column per canonical quiz name 'Quiz N (/10)'
        All weird/duplicate headers are folded into their canonical target using retake_merge.
        """
        if "Student" not in df.columns:
            raise ValueError("DataFrame must contain a 'Student' column")

        # Identify quiz-like columns to process (exclude 'Student').
        quiz_like = [c for c in df.columns if c != "Student" and (
            self.is_canonical_quiz(c) or self.is_weird_quiz_header(str(c)) or "quiz" in str(c).lower() or "(/10)" in str(c)
        )]
        if not quiz_like:
            # Nothing to fold, return Student only
            return df[["Student"]].copy()

        # Group by canonical name
        groups: dict[str, list[str]] = {}
        for col in quiz_like:
            canon = self.canonical_quiz_name(col)
            groups.setdefault(canon, []).append(col)

        # Start with Student only
        out = pd.DataFrame({"Student": df["Student"]})

        # For each canonical group, merge all its source columns into one
        for canon_name, cols in groups.items():
            series = pd.Series(["X"] * len(df), index=df.index)
            for src in cols:
                vals = df[src].apply(self.normalize_score_cell)
                if use_curve:
                    vals = vals.apply(lambda x: self.apply_curve_cap(x, curve_cap))
                series = pd.Series([self.retake_merge(o, n) for o, n in zip(series, vals)], index=df.index)
            out[canon_name] = series

        # Order quiz columns by quiz number
        order = []
        for c in out.columns:
            if c == "Student":
                continue
            m = re.search(r'\bquiz\s*([1-9]\d*)\b', c.lower())
            n = int(m.group(1)) if m else 10_000
            order.append((n, c))
        order.sort()
        return out[["Student"] + [c for _, c in order]]

    def normalize_score_cell(self, v):
        """Return 'X' for NaN/blank; else clamp to int 0..100."""
        s = str(v).strip()
        if s == "" or s.lower() in {"nan", "none"}:
            return "X"
        try:
            return max(0, min(100, int(float(s))))  # clamp; curve comes later
        except Exception:
            return "X"

    def apply_curve_cap(self, v, cap):
        """Apply curve cap: min(score, cap). Treat X as X."""
        if isinstance(v, str):
            if v.strip().upper() == "X":
                return "X"
            try:
                v = int(float(v))
            except Exception:
                return "X"
        return min(int(v), int(cap))

    def apply_curve_cap9(self, v):
        """Curve rule: 10->9; 9->9; 8->8 ... Treat X as X."""
        return self.apply_curve_cap(v, 9)

    def retake_merge(self, existing, new_value):
        """
        existing/new_value may be 'X' or int-like.
        - If existing == 'X' and new is a number -> use new
        - If both numbers -> use higher
        - If new == 'X' -> keep existing
        """
        ex_is_x = (isinstance(existing, str) and existing.strip().upper() == "X")
        nv_is_x = (isinstance(new_value, str) and new_value.strip().upper() == "X")
        if ex_is_x and not nv_is_x:
            return int(new_value)
        if not ex_is_x and not nv_is_x:
            return max(int(existing), int(new_value))
        return existing

    def period_master_path(self, period: str) -> str:
        """Where we store the master CSV for a period (same directory as chosen output)."""
        safe = period.replace(" ", "_")
        return os.path.join(os.getcwd(), f"{safe}_MASTER.csv")
        
    def parse_student_name(self, full_name: str) -> Dict[str, str]:
        """
        Parse a student name in format: "Last, First Middle (Nickname) #ID"
        Returns a dictionary with parsed components
        """
        # Remove the ID number at the end
        name_part = re.sub(r' #\d+$', '', full_name)
        
        # Extract nickname if present
        nickname_match = re.search(r'\((.*?)\)', name_part)
        nickname = nickname_match.group(1) if nickname_match else ""
        
        # Remove nickname from name part
        name_without_nickname = re.sub(r'\(.*?\)', '', name_part).strip()
        
        # Split by comma to separate last name from first/middle
        parts = name_without_nickname.split(',')
        if len(parts) != 2:
            return {"last": "", "first": "", "middle": "", "nickname": nickname, "full": full_name}
        
        last_name = parts[0].strip()
        first_middle = parts[1].strip()
        
        # Split first and middle names
        first_middle_parts = first_middle.split()
        first_name = first_middle_parts[0] if first_middle_parts else ""
        middle_name = " ".join(first_middle_parts[1:]) if len(first_middle_parts) > 1 else ""
        
        return {
            "last": last_name,
            "first": first_name,
            "middle": middle_name,
            "nickname": nickname,
            "full": full_name
        }
    
    def load_quiz_data(self, csv_file: str) -> List[Dict]:
        """
        Load quiz data from CSV file
        """
        students = []
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                student_info = self.parse_student_name(row['Student'])
                student_info['scores'] = {k: v for k, v in row.items() if k != 'Student'}
                students.append(student_info)
        return students
    
    def load_attendance_list(self, attendance_file: str) -> List[Dict]:
        """
        Load full attendance list (expected format: CSV with full names)
        """
        attendance = []
        with open(attendance_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Assuming attendance file has a 'Name' column
                student_info = self.parse_student_name(row['Name'])
                attendance.append(student_info)
        return attendance
    
    def create_name_variations(self, student: Dict) -> List[str]:
        """
        Create various name variations for matching
        """
        variations = []
        
        # Full name variations
        if student['nickname']:
            variations.extend([
                f"{student['last']}, {student['first']} {student['middle']} ({student['nickname']})",
                f"{student['last']}, {student['first']} ({student['nickname']})",
                f"{student['last']}, {student['nickname']}"
            ])
        
        # Partial name variations
        variations.extend([
            f"{student['last']}, {student['first']}",
            f"{student['last']}, {student['first']} {student['middle']}",
            f"{student['last']}, {student['first'][0]}",  # First initial
            f"{student['last']}, {student['first'][0]}. {student['middle']}",  # First initial with middle
        ])
        
        # Nickname variations
        if student['nickname']:
            variations.extend([
                f"{student['last']}, {student['nickname']}",
                f"{student['nickname']} {student['last']}",
                f"{student['last']}, {student['nickname'][0]}"  # Nickname initial
            ])
        
        return variations
    
    def enhanced_fuzzy_match(self, partial_name: str, full_names: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        Enhanced fuzzy matching with multiple strategies
        """
        best_match = None
        best_score = 0
        
        for full_name in full_names:
            # Create all possible variations
            variations = self.create_name_variations(full_name)
            
            for variation in variations:
                # Try different matching strategies
                scores = [
                    fuzz.ratio(partial_name.lower(), variation.lower()),
                    fuzz.partial_ratio(partial_name.lower(), variation.lower()),
                    fuzz.token_sort_ratio(partial_name.lower(), variation.lower()),
                    fuzz.token_set_ratio(partial_name.lower(), variation.lower())
                ]
                
                max_score = max(scores)
                if max_score > best_score and max_score > 70:  # Higher threshold
                    best_score = max_score
                    best_match = full_name
        
        return best_match, best_score
    
    def find_missing_students(self, quiz_students: List[Dict], attendance_list: List[Dict]) -> List[Dict]:
        """
        Find students who are in attendance but not in quiz data
        """
        quiz_names = {(s['last'], s['first']) for s in quiz_students}
        missing = []
        
        for attendance_student in attendance_list:
            if (attendance_student['last'], attendance_student['first']) not in quiz_names:
                missing.append(attendance_student)
        
        return missing
    
    def process_with_attendance(self, quiz_file: str, attendance_file: str) -> List[Dict]:
        """
        Process quiz data with attendance list to identify missing students
        """
        # Load data
        quiz_students = self.load_quiz_data(quiz_file)
        attendance_list = self.load_attendance_list(attendance_file)
        
        # Find missing students
        missing_students = self.find_missing_students(quiz_students, attendance_list)
        
        # Get quiz columns for missing entries
        quiz_columns = list(quiz_students[0]['scores'].keys()) if quiz_students else []
        
        # Add missing students with X marks
        for missing_student in missing_students:
            missing_student['scores'] = {col: 'X' for col in quiz_columns}
            missing_student['absent'] = True
            quiz_students.append(missing_student)
        
        # Sort by last name, then middle name, then first name, then nickname
        quiz_students.sort(key=lambda x: (x['last'], x['middle'], x['first'], x['nickname']))
        
        return quiz_students
    
    def export_with_attendance(self, students: List[Dict], output_file: str):
        """
        Export data with X marks for absent students (no status column)
        """
        if not students:
            return
        
        # Get all quiz columns
        quiz_columns = list(students[0]['scores'].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['Student'] + quiz_columns
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for student in students:
                row = {
                    'Student': student['full']
                }
                row.update(student['scores'])
                writer.writerow(row)
    
    def export_sorted_data(self, students: List[Dict], output_file: str):
        """
        Export sorted quiz data without attendance processing
        """
        if not students:
            return
        
        # Get all quiz columns
        quiz_columns = list(students[0]['scores'].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['Student'] + quiz_columns
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            for student in students:
                row = {
                    'Student': student['full']
                }
                row.update(student['scores'])
                writer.writerow(row)
    
    def process_with_canonical_names(self, quiz_file: str, attendance_file: str, output_file: str):
        """
        Process quiz data with canonical name replacement and proper sorting
        """
        # 1) Read attendance lines (single column, header optional)
        att_lines = []
        with open(attendance_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            # If the first line looks like a header, skip it; else include
            if first_line.strip().lower() in {"student", "period 1 attendance", '"student"'}:
                att_lines = [line.strip() for line in f if line.strip()]
            else:
                att_lines = [first_line.strip()] + [line.strip() for line in f if line.strip()]

        roster_index = self.build_roster_index_new(att_lines)

        # 2) Load quiz CSV (names typed by students)
        quiz_rows = []
        with open(quiz_file, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            if "Student" not in r.fieldnames:
                raise ValueError("Quiz CSV must have a 'Student' column.")
            for row in r:
                quiz_rows.append(row)

        # 3) Replace 'Student' with canonical 'Last, Middle, First (Nick) #ID'
        canonical_rows, unmatched = [], []
        for row in quiz_rows:
            raw = row["Student"]
            canon = self.lookup_canonical_new(raw, roster_index)
            if not canon:
                unmatched.append(raw)
                # Optional: skip unmatched entirely instead of keeping them
                # continue
                canon = f"[UNMATCHED] {raw}"
            row["Student"] = canon
            canonical_rows.append(row)

        # 4) Sort by last name
        canonical_rows.sort(key=lambda r: self.sort_key_by_last(r["Student"]))

        # 5) Write CSV
        if canonical_rows:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = canonical_rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(canonical_rows)
        
        return canonical_rows, unmatched
    
    def process_with_canonical_names_full_roster(self, quiz_file: str, attendance_file: str, output_file: str):
        """
        Process quiz data with canonical name replacement, full roster inclusion, and X for missing scores
        """
        # 1) Read attendance lines (single column, header optional)
        att_lines = []
        with open(attendance_file, "r", encoding="utf-8") as f:
            first_line = f.readline()
            # If the first line looks like a header, skip it; else include
            if first_line.strip().lower() in {"student", "period 1 attendance", '"student"'}:
                att_lines = [line.strip() for line in f if line.strip()]
            else:
                att_lines = [first_line.strip()] + [line.strip() for line in f if line.strip()]

        roster_index = self.build_roster_index_new(att_lines)

        # 2) Load quiz CSV (names typed by students)
        quiz_rows = []
        with open(quiz_file, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            if "Student" not in r.fieldnames:
                raise ValueError("Quiz CSV must have a 'Student' column.")
            for row in r:
                quiz_rows.append(row)

        # ---- columns present in the quiz CSV ----
        quiz_columns = [c for c in quiz_rows[0].keys() if c != "Student"]

        # ---- map quiz names -> canonical ----
        canonical_rows = {}
        unmatched = []
        for row in quiz_rows:
            raw = row["Student"]
            canon = self.lookup_canonical_new(raw, roster_index)
            if not canon:
                unmatched.append(raw)
                # Skip unmatched entirely; they are not in attendance
                continue
            # Normalize all blanks/None to "X" (we'll also coerce NaN later)
            fixed = {"Student": canon}
            for c in quiz_columns:
                v = row.get(c, "")
                fixed[c] = "X" if (v is None or str(v).strip() == "" or str(v).lower() == "nan") else v
            canonical_rows[canon] = fixed  # last write wins if duplicates

        # ---- add missing students from attendance with full X row ----
        for att_line in att_lines:
            p = self.parse_attendance_entry_new(att_line)
            canon = self._format_canonical_last_middle_first(p)
            if canon not in canonical_rows:
                canonical_rows[canon] = {"Student": canon, **{c: "X" for c in quiz_columns}}

        # ---- turn dict -> list and sort by last name ----
        rows_out = list(canonical_rows.values())
        rows_out.sort(key=lambda r: self.sort_key_by_last(r["Student"]))

        # ---- write CSV (ensure X, not NaN) ----
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Student"] + quiz_columns)
            w.writeheader()
            for r in rows_out:
                # Safety: convert any lingering NaN to "X"
                for c in quiz_columns:
                    v = r.get(c, "")
                    if v is None or str(v).strip() == "" or str(v).lower() == "nan":
                        r[c] = "X"
                w.writerow(r)
        
        return rows_out, unmatched
    
    def make_attendance_line(self, last, first, middle, nick, sid):
        """Helper to create attendance line in canonical format"""
        if middle:
            base = f"{last}, {middle}, {first}"
        else:
            base = f"{last}, {first}"
        if nick:
            base += f" ({nick})"
        return f"{base} #{sid}"
    
    def create_sample_attendance(self, quiz_file: str, output_file: str):
        """
        Create a sample attendance file based on quiz data with additional absent students
        """
        quiz_students = self.load_quiz_data(quiz_file)
        
        # Additional students who will be "absent" (not in quiz data)
        absent_students = [
            self.make_attendance_line("Brown", "Sarah", "Elizabeth", "Sadie", "1000000020"),
            self.make_attendance_line("Taylor", "Michael", "James", "Mike", "1000000021"),
            self.make_attendance_line("White", "Jennifer", "Anne", "Jenny", "1000000022"),
            self.make_attendance_line("Harris", "David", "Robert", "Dave", "1000000023"),
            self.make_attendance_line("Martin", "Lisa", "Marie", "Liz", "1000000024"),
            self.make_attendance_line("Thompson", "Christopher", "Lee", "Chris", "1000000025"),
            self.make_attendance_line("Garcia", "Maria", "Sofia", "Mari", "1000000026"),
            self.make_attendance_line("Anderson", "Kevin", "Patrick", "Kev", "1000000027"),
            self.make_attendance_line("Lewis", "Amanda", "Grace", "Mandy", "1000000028"),
            self.make_attendance_line("Walker", "Daniel", "Thomas", "Dan", "1000000029")
        ]
        
        # Combine all students
        all_students = [student['full'] for student in quiz_students] + absent_students
        
        # Sort alphabetically by last name, middle name, first name, nickname
        # Parse names for proper sorting
        parsed_students = []
        for student in all_students:
            parsed = self.parse_student_name(student)
            parsed_students.append((parsed, student))
        
        parsed_students.sort(key=lambda x: (x[0]['last'], x[0]['middle'], x[0]['first'], x[0]['nickname']))
        all_students = [student for _, student in parsed_students]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Expected_Status'])
            
            for student in all_students:
                # Mark if student is expected to be present (in quiz data) or absent
                status = "Present" if student in [s['full'] for s in quiz_students] else "Absent"
                writer.writerow([student, status])
        
        print(f"Created attendance file: {output_file}")
        print(f"Total students: {len(all_students)}")
        print(f"Expected present: {len(quiz_students)}")
        print(f"Expected absent: {len(absent_students)}")

def main():
    sorter = EnhancedQuizSorter()
    
    # Example usage
    quiz_file = "test_quiz_data.csv"
    attendance_file = "full_attendance_list.csv"
    output_file = "enhanced_sorted_data.csv"
    
    try:
        print("=== Enhanced Quiz Sorter Demo ===\n")
        
        # Create attendance file with absent students for testing
        sorter.create_sample_attendance(quiz_file, attendance_file)
        print()
        
        # Process with attendance
        students = sorter.process_with_attendance(quiz_file, attendance_file)
        sorter.export_with_attendance(students, output_file)
        
        print(f"✅ Successfully processed {len(students)} students")
        print(f"💾 Output saved to {output_file}")
        
        # Show statistics
        present_count = sum(1 for s in students if not s.get('absent', False))
        absent_count = sum(1 for s in students if s.get('absent', False))
        print(f"📊 Present: {present_count}, Absent: {absent_count}")
        
        # Show sample of results
        print(f"\n📋 Sample of processed data:")
        print("Present students:")
        present_examples = [s for s in students if not s.get('absent', False)][:2]
        for student in present_examples:
            print(f"  ✅ {student['last']}, {student['first']} - {student['scores']}")
        
        print("\nAbsent students:")
        absent_examples = [s for s in students if s.get('absent', False)][:2]
        for student in absent_examples:
            print(f"  ❌ {student['last']}, {student['first']} - {student['scores']}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find file - {e}")
    except Exception as e:
        print(f"❌ Error processing data: {e}")

if __name__ == "__main__":
    main()
