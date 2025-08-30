import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import os
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from enhanced_quiz_sorter import EnhancedQuizSorter

class QuizSorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Sorter for TAs")
        self.root.geometry("700x600")
        
        # Set a modern color scheme
        self.bg_color = "#f5f5f5"  # Light gray background
        self.accent_color = "#2E7D32"  # Dark green accent
        self.text_color = "#212121"  # Very dark gray text
        self.highlight_color = "#1565C0"  # Dark blue highlight
        self.button_bg = "#0D47A1"  # Very dark blue for buttons
        self.button_fg = "#FFFFFF"  # Pure white text
        
        self.root.configure(bg=self.bg_color)
        
        # Set up ttk styles for consistent theming
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme which allows color overrides
        
        # Configure custom button styles
        self.style.configure('Blue.TButton',
                           background='#000080',
                           foreground='white',
                           borderwidth=2,
                           focuscolor='none',
                           font=('Arial', 11, 'bold'))
        
        # --- ttk style fixes (text always visible on macOS clam theme) ---
        self.style.layout('Green.TButton', [
            ('Button.padding', {'sticky': 'nswe', 'children': [
                ('Button.label', {'sticky': 'nswe'})
            ]})
        ])
        self.style.configure('Green.TButton',
            relief='flat',
            font=('Arial', 18, 'bold'),
            padding=(50, 20),
            background='#006400',
            foreground='white'
        )
        # Force text color in all states
        self.style.map('Green.TButton',
            foreground=[
                ('disabled', '#F2F2F2'),
                ('pressed',  'white'),
                ('active',   'white'),
                ('focus',    'white'),
                ('!disabled','white'),
            ],
            background=[
                ('disabled', '#5a8f5a'),
                ('pressed',  '#055c05'),
                ('active',   '#0b7a0b'),
                ('focus',    '#0b7a0b'),
                ('!disabled','#006400'),
            ]
        )
        
        # Configure custom checkbox style
        self.style.configure('Custom.TCheckbutton',
                           background=self.bg_color,
                           foreground=self.text_color,
                           selectcolor='#1976D2',
                           font=('Arial', 10))
        
        self.sorter = EnhancedQuizSorter()
        self.quiz_file = ""
        self.attendance_file = ""
        
        self.create_widgets()
        
    def apply_button_colors(self):
        """This method is no longer needed with ttk styles"""
        pass
        
    def create_pdf_file(self, csv_file_path, pdf_title="Quiz Results - Grading Sheet"):
        """Create a PDF file from the CSV and open it automatically"""
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file_path)
            
            # Create PDF file path with timestamp to make it unique
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(csv_file_path)[0]
            pdf_file_path = f"{base_name}_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_file_path, pagesize=landscape(letter))
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            title_style.alignment = 1  # Center alignment
            title = Paragraph(pdf_title, title_style)
            elements.append(title)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))
            
            # Convert DataFrame to list and coerce NaN -> "X"
            df = df.fillna("X")  # replaces pandas NaN
            for col in df.columns:
                df.loc[df[col].astype(str).str.strip().isin(["", "nan", "NaN", "None"]), col] = "X"

            data = [df.columns.tolist()] + df.values.tolist()

            # Create table
            table = Table(data)

            # Style: header + grid; center/bold X marks
            style = TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('ALIGN',      (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, 0), 12),

                # Body
                ('GRID',       (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN',     (0, 1), (-1, -1), 'MIDDLE'),
                ('ALIGN',      (1, 1), (-1, -1), 'CENTER'),  # center scores/X
                ('FONTSIZE',   (1, 1), (-1, -1), 10),
            ])

            # Make "X" bold so it fills the box
            # (Apply to all body cells that contain "X")
            for r in range(1, len(data)):
                for c in range(1, len(data[0])):  # score cols only
                    if str(data[r][c]).strip().upper() == "X":
                        style.add('FONTNAME', (c, r), (c, r), 'Helvetica-Bold')
            
            table.setStyle(style)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            # Open the PDF file automatically
            import subprocess
            import platform
            
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', pdf_file_path])
            elif platform.system() == 'Windows':
                os.startfile(pdf_file_path)
            else:  # Linux
                subprocess.run(['xdg-open', pdf_file_path])
                
            return pdf_file_path
            
        except Exception as e:
            messagebox.showerror("PDF Export Error", f"Could not create PDF file: {str(e)}")
            return None
        
    def create_widgets(self):
        # Title
        title_label = tk.Label(self.root, text="Quiz Sorter for TAs", 
                              font=("Arial", 20, "bold"), 
                              bg=self.bg_color, fg=self.text_color)
        title_label.pack(pady=15)
        
        # Subtitle
        subtitle_label = tk.Label(self.root, text="Organize Wayground quiz data with attendance tracking", 
                                 font=("Arial", 10), 
                                 bg=self.bg_color, fg="#666666")
        subtitle_label.pack(pady=(0, 15))
        
        # File selection frame
        file_frame = tk.LabelFrame(self.root, text="📁 File Selection", 
                                  font=("Arial", 12, "bold"),
                                  bg=self.bg_color, fg=self.text_color,
                                  padx=15, pady=15)
        file_frame.pack(fill="x", padx=25, pady=10)
        
        # Quiz file selection
        tk.Label(file_frame, text="Quiz Data File (CSV):", 
                font=("Arial", 10, "bold"),
                bg=self.bg_color, fg=self.text_color).grid(row=0, column=0, sticky="w", pady=8)
        self.quiz_label = tk.Label(file_frame, text="No file selected", 
                                  fg="#999999", bg=self.bg_color,
                                  font=("Arial", 9))
        self.quiz_label.grid(row=0, column=1, sticky="w", padx=15, pady=8)
        self.browse_quiz_btn = ttk.Button(file_frame, text="📁 Browse Files", 
                                        command=self.select_quiz_file,
                                        style='Blue.TButton',
                                        padding=(25, 8))
        self.browse_quiz_btn.grid(row=0, column=2, padx=10, pady=8)
        
        # Attendance file selection
        tk.Label(file_frame, text="Attendance List (CSV):", 
                font=("Arial", 10, "bold"),
                bg=self.bg_color, fg=self.text_color).grid(row=1, column=0, sticky="w", pady=8)
        self.attendance_label = tk.Label(file_frame, text="No file selected (optional)", 
                                        fg="#999999", bg=self.bg_color,
                                        font=("Arial", 9))
        self.attendance_label.grid(row=1, column=1, sticky="w", padx=15, pady=8)
        self.browse_attendance_btn = ttk.Button(file_frame, text="📁 Browse Files", 
                                              command=self.select_attendance_file,
                                              style='Blue.TButton',
                                              padding=(25, 8))
        self.browse_attendance_btn.grid(row=1, column=2, padx=10, pady=8)
        
        # Options frame
        options_frame = tk.LabelFrame(self.root, text="⚙️ Options", 
                                     font=("Arial", 12, "bold"),
                                     bg=self.bg_color, fg=self.text_color,
                                     padx=15, pady=15)
        options_frame.pack(fill="x", padx=25, pady=10)
        
        # Checkboxes for options
        self.add_absent_students = tk.BooleanVar(value=True)
        self.checkbox1 = ttk.Checkbutton(options_frame, text="Add absent students with X marks", 
                                       variable=self.add_absent_students,
                                       style='Custom.TCheckbutton')
        self.checkbox1.pack(anchor="w", pady=3)
        
        self.sort_alphabetically = tk.BooleanVar(value=True)
        self.checkbox2 = ttk.Checkbutton(options_frame, text="Sort alphabetically by last name", 
                                       variable=self.sort_alphabetically,
                                       style='Custom.TCheckbutton')
        self.checkbox2.pack(anchor="w", pady=3)
        
        # --- Curve cap controls ---
        self.curve_enabled = tk.BooleanVar(value=True)
        self.curve_cap_var = tk.IntVar(value=9)

        curve_row = ttk.Frame(options_frame)
        curve_row.pack(anchor="w", pady=3, fill="x")

        ttk.Checkbutton(curve_row,
            text="Apply curve cap",
            variable=self.curve_enabled,
            style='Custom.TCheckbutton'
        ).pack(side="left")

        ttk.Label(curve_row, text="Max points:", background=self.bg_color, foreground=self.text_color).pack(side="left", padx=(12,4))

        # Use tk.Spinbox for numeric input (0..20; adjust bounds as you like)
        self.curve_cap_spin = tk.Spinbox(curve_row, from_=0, to=20, width=4, textvariable=self.curve_cap_var)
        self.curve_cap_spin.pack(side="left")

        # Enable/disable spinbox tied to checkbox state
        def _toggle_curve_spin(*_):
            state = 'normal' if self.curve_enabled.get() else 'disabled'
            self.curve_cap_spin.configure(state=state)

        self.curve_enabled.trace_add('write', _toggle_curve_spin)
        _toggle_curve_spin()
        
        # Output frame
        output_frame = tk.LabelFrame(self.root, text="💾 Output", 
                                    font=("Arial", 12, "bold"),
                                    bg=self.bg_color, fg=self.text_color,
                                    padx=15, pady=15)
        output_frame.pack(fill="x", padx=25, pady=10)
        
        tk.Label(output_frame, text="Output File:", 
                font=("Arial", 10, "bold"),
                bg=self.bg_color, fg=self.text_color).grid(row=0, column=0, sticky="w", pady=8)
        self.output_label = tk.Label(output_frame, text="sorted_quiz_data.csv", 
                                    fg=self.highlight_color, bg=self.bg_color,
                                    font=("Arial", 9, "bold"))
        self.output_label.grid(row=0, column=1, sticky="w", padx=15, pady=8)
        self.choose_output_btn = ttk.Button(output_frame, text="📁 Choose Location", 
                                          command=self.select_output_file,
                                          style='Blue.TButton',
                                          padding=(25, 8))
        self.choose_output_btn.grid(row=0, column=2, padx=10, pady=8)
        
        # Process button
        self.process_text = tk.StringVar(value="🚀 Process Quiz Data")
        self.process_button = ttk.Button(
            self.root,
            textvariable=self.process_text,
            style='Green.TButton',
            command=self.process_data
        )
        self.process_button.pack(pady=25)
        
        # Status and results
        self.status_label = tk.Label(self.root, text="Ready to process", 
                                    fg=self.highlight_color, bg=self.bg_color,
                                    font=("Arial", 10, "bold"))
        self.status_label.pack(pady=5)
        
        # Results text area
        results_frame = tk.LabelFrame(self.root, text="📊 Results", 
                                     font=("Arial", 12, "bold"),
                                     bg=self.bg_color, fg=self.text_color,
                                     padx=15, pady=15)
        results_frame.pack(fill="both", expand=True, padx=25, pady=10)
        
        self.results_text = tk.Text(results_frame, height=10, wrap="word",
                                   font=("Arial", 9),
                                   bg="white", fg=self.text_color)
        scrollbar = tk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def select_quiz_file(self):
        # Set default directory to input folder
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
            
        filename = filedialog.askopenfilename(
            title="Select Quiz Data File",
            initialdir=default_dir,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.quiz_file = filename
            self.quiz_label.config(text=os.path.basename(filename), fg="black")
            
    def select_attendance_file(self):
        # Set default directory to attendance folder
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
            
        filename = filedialog.askopenfilename(
            title="Select Attendance List",
            initialdir=default_dir,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.attendance_file = filename
            self.attendance_label.config(text=os.path.basename(filename), fg="black")
            
    def select_output_file(self):
        # Set default directory to output folder
        default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        if not os.path.exists(default_dir):
            default_dir = os.getcwd()
            
        filename = filedialog.asksaveasfilename(
            title="Save Output File",
            initialdir=default_dir,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_label.config(text=os.path.basename(filename), fg="blue")
            
    def process_data(self):
        if not self.quiz_file:
            messagebox.showerror("Error", "Please select a quiz data file first!")
            return
            
        try:
            # Update status and disable button during processing
            self.status_label.config(text="Processing...", fg="orange")
            self.process_button.state(['disabled'])
            self.process_text.set("🔄 Processing…")
            self.root.update_idletasks()
            
            # Process the data based on user selections
            if self.attendance_file:
                # Use new canonical name processing with full roster inclusion
                canonical_rows, unmatched = self.sorter.process_with_canonical_names_full_roster(
                    self.quiz_file, self.attendance_file, self.output_label.cget("text")
                )
                
                # ---- START MULTI-COLUMN MERGE REPLACEMENT ----
                # Convert canonical_rows (list[dict]) to DataFrame
                df_new = pd.DataFrame(canonical_rows)

                # Normalize Student dupes and ensure a single row per student for this import
                df_new = df_new.groupby("Student", as_index=False).first()

                # Apply folding to deduplicate headers BEFORE merging into the MASTER
                use_curve = bool(self.curve_enabled.get()) if hasattr(self, "curve_enabled") else True
                curve_cap = int(self.curve_cap_var.get()) if hasattr(self, "curve_cap_var") else 9
                df_new = self.sorter.fold_to_canonical(df_new, use_curve=use_curve, curve_cap=curve_cap)

                # Identify quiz columns present in this import (after folding)
                quiz_columns = [c for c in df_new.columns if c != "Student" and self.sorter.is_canonical_quiz(c)]
                if not quiz_columns:
                    raise ValueError("No quiz columns detected in the quiz CSV. Expected headers like 'Quiz 1 (/10)'.")

                # Load or create the MASTER for this period
                period = self.sorter.extract_period_from_path(self.attendance_file)
                master_path = self.sorter.period_master_path(period)

                if os.path.exists(master_path):
                    df_master = pd.read_csv(master_path)
                else:
                    # Build master from full attendance (canonical lines) so ALL students exist
                    # Read attendance lines for canonical names
                    att_lines = []
                    with open(self.attendance_file, "r", encoding="utf-8") as f:
                        first_line = f.readline()
                        if first_line.strip().lower() in {"student", "period 1 attendance", '"student"'}:
                            att_lines = [line.strip() for line in f if line.strip()]
                        else:
                            att_lines = [first_line.strip()] + [line.strip() for line in f if line.strip()]
                    
                    # Convert attendance lines to canonical format
                    canonical_attendance = []
                    for line in att_lines:
                        p = self.sorter.parse_attendance_entry_new(line)
                        canon = self.sorter._format_canonical_last_middle_first(p)
                        canonical_attendance.append(canon)
                    
                    df_master = pd.DataFrame({"Student": canonical_attendance})

                # Deduplicate students
                df_master = df_master.drop_duplicates(subset=["Student"]).reset_index(drop=True)
                
                # Clean master CSV to keep only canonical quiz columns
                df_master = self.sorter.fold_to_canonical(df_master, use_curve=False, curve_cap=curve_cap)  # fold legacy weird headers without altering numeric values

                # Ensure every quiz column from this import exists in master (default to X)
                for qc in quiz_columns:
                    if qc not in df_master.columns:
                        df_master[qc] = "X"

                # Retake-merge each quiz column independently
                for qc in quiz_columns:
                    merged = df_master.merge(df_new[["Student", qc]], on="Student", how="left", suffixes=("", "_NEW"))

                    def _resolve_row(row):
                        ex = row[qc]
                        nv = row.get(f"{qc}_NEW", "X")
                        # df_new already normalized/curved, but normalize again defensively
                        nv = self.sorter.normalize_score_cell(nv)
                        return self.sorter.retake_merge(ex, nv)

                    merged[qc] = merged.apply(_resolve_row, axis=1)
                    df_master = merged.drop(columns=[c for c in merged.columns if c.endswith("_NEW")])

                # Sort by last name from canonical "Last, Middle, First (Nick) #ID"
                df_master["__sortkey__"] = df_master["Student"].apply(lambda s: s.split(",", 1)[0].strip().lower())
                df_master = df_master.sort_values("__sortkey__").drop(columns="__sortkey__").reset_index(drop=True)

                # Save MASTER and user-selected output CSV (same data)
                df_master.to_csv(master_path, index=False)
                out_csv = self.output_label.cget("text")
                df_master.to_csv(out_csv, index=False)

                # Build PDF with a clear title (uses your updated create_pdf_file signature)
                pdf_title = f"{period} – Quiz Results (updated)"
                pdf_file = self.create_pdf_file(out_csv, pdf_title=pdf_title)
                # ---- END MULTI-COLUMN MERGE REPLACEMENT ----
                
                # Convert to student format for statistics
                students = []
                for _, row in merged.iterrows():
                    student_info = self.sorter.parse_student_name(row['Student'])
                    student_info['scores'] = {k: v for k, v in row.items() if k != 'Student'}
                    student_info['absent'] = any('X' in str(v) for v in student_info['scores'].values())
                    students.append(student_info)
                
                # Show unmatched names in results
                if unmatched:
                    self.results_text.insert(tk.END, f"\n⚠️ Unmatched names:\n")
                    for name in unmatched:
                        self.results_text.insert(tk.END, f"   • {name}\n")
            else:
                # Process without attendance (just sort)
                students = self.sorter.load_quiz_data(self.quiz_file)
                if self.sort_alphabetically.get():
                    students.sort(key=lambda x: (x['last'], x['middle'], x['first'], x['nickname']))
                self.sorter.export_sorted_data(students, self.output_label.cget("text"))
            
            # Calculate statistics
            present_count = sum(1 for s in students if not s.get('absent', False))
            absent_count = sum(1 for s in students if s.get('absent', False))
            
            # Show results
            results = f"✅ Processing Complete!\n\n"
            results += f"📊 Statistics:\n"
            results += f"   • Total students: {len(students)}\n"
            results += f"   • Present: {present_count}\n"
            results += f"   • Absent: {absent_count}\n"
            results += f"   • Output file: {self.output_label.cget('text')}\n\n"
            
            results += f"📋 Sample of processed data:\n"
            for i, student in enumerate(students[:5]):
                status_icon = "❌" if student.get('absent', False) else "✅"
                results += f"   {i+1}. {status_icon} {student['last']}, {student['first']}\n"
            
            if len(students) > 5:
                results += f"   ... and {len(students) - 5} more students\n"
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, results)
            
            # Update status and re-enable button
            self.status_label.config(text="✅ Processing complete!", fg="green")
            self.process_button.state(['!disabled'])
            self.process_text.set("🚀 Process Quiz Data")
            self.root.update_idletasks()
            
            # Create and open PDF file
            pdf_file = self.create_pdf_file(self.output_label.cget("text"))
            
            # Show success message
            if self.attendance_file:
                period = self.sorter.extract_period_from_path(self.attendance_file)
                master_path = self.sorter.period_master_path(period)
                if pdf_file:
                    messagebox.showinfo("Success", 
                                      f"Data processed successfully!\n\n"
                                      f"📁 CSV saved to: {self.output_label.cget('text')}\n"
                                      f"📊 Master CSV: {os.path.basename(master_path)}\n"
                                      f"📄 PDF opened: {os.path.basename(pdf_file)}\n"
                                      f"👥 Total students: {len(students)}\n"
                                      f"✅ Present: {present_count}\n"
                                      f"❌ Absent: {absent_count}")
                else:
                    messagebox.showinfo("Success", 
                                      f"Data processed successfully!\n\n"
                                      f"📁 Output saved to: {self.output_label.cget('text')}\n"
                                      f"📊 Master CSV: {os.path.basename(master_path)}\n"
                                      f"👥 Total students: {len(students)}\n"
                                      f"✅ Present: {present_count}\n"
                                      f"❌ Absent: {absent_count}")
            else:
                if pdf_file:
                    messagebox.showinfo("Success", 
                                      f"Data processed successfully!\n\n"
                                      f"📁 CSV saved to: {self.output_label.cget('text')}\n"
                                      f"📄 PDF opened: {os.path.basename(pdf_file)}\n"
                                      f"👥 Total students: {len(students)}\n"
                                      f"✅ Present: {present_count}\n"
                                      f"❌ Absent: {absent_count}")
                else:
                    messagebox.showinfo("Success", 
                                      f"Data processed successfully!\n\n"
                                      f"📁 Output saved to: {self.output_label.cget('text')}\n"
                                      f"👥 Total students: {len(students)}\n"
                                      f"✅ Present: {present_count}\n"
                                      f"❌ Absent: {absent_count}")
            
        except FileNotFoundError as e:
            self.status_label.config(text="❌ File not found", fg="red")
            self.process_button.state(['!disabled'])
            self.process_text.set("🚀 Process Quiz Data")
            self.root.update_idletasks()
            messagebox.showerror("File Error", f"Could not find the specified file:\n{str(e)}")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, f"❌ File Error: {str(e)}")
            
        except Exception as e:
            self.status_label.config(text="❌ Error occurred", fg="red")
            self.process_button.state(['!disabled'])
            self.process_text.set("🚀 Process Quiz Data")
            self.root.update_idletasks()
            messagebox.showerror("Processing Error", f"An error occurred during processing:\n{str(e)}")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, f"❌ Error: {str(e)}")

def main():
    root = tk.Tk()
    app = QuizSorterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
