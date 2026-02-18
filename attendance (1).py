import sqlite3
import re
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime

# Main Window
root = Tk()
root.title("Department-wise Student Attendance Tracker")
root.geometry("1100x650")
root.configure(bg="#eaf2f8")

# Variables
name_var = StringVar()
date_var = StringVar()
dept_var = StringVar()
year_var = StringVar()
status_var = StringVar(value="Present")
search_var = StringVar()

present_count_var = StringVar(value="Present: 0")
absent_count_var = StringVar(value="Absent: 0")

departments = ["CSE", "ECE", "ME", "CE", "IT", "CS"]
tree = None

def ensure_table(dept):
    conn = sqlite3.connect(f"{dept.lower()}_attendance.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            present INTEGER DEFAULT 0,
            absent INTEGER DEFAULT 0,
            last_update TEXT
        )
    ''')
    conn.commit()
    conn.close()

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def submit():
    name = name_var.get().strip()
    date = date_var.get().strip()
    dept = dept_var.get()
    year = year_var.get()
    status = status_var.get()

    if not re.match(r"^[A-Za-z ]+$", name):
        messagebox.showerror("Validation Error", "Student name must contain only letters and spaces.")
        return
    if not is_valid_date(date):
        messagebox.showerror("Validation Error", "Date must be in YYYY-MM-DD format.")
        return
    if dept not in departments:
        messagebox.showerror("Validation Error", "Please select a valid department.")
        return
    if year not in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
        messagebox.showerror("Validation Error", "Please select a valid academic year.")
        return
    if status not in ["Present", "Absent"]:
        messagebox.showerror("Validation Error", "Select Present or Absent.")
        return

    present = 1 if status == "Present" else 0
    absent = 1 if status == "Absent" else 0
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ensure_table(dept)
    conn = sqlite3.connect(f"{dept.lower()}_attendance.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO attendance (student_name, attendance_date, department, year, present, absent, last_update)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, date, dept, year, present, absent, update_time))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", "Attendance recorded.")
    clear_fields()
    fetch_data(search_var.get().strip())
    calculate_totals(search_var.get().strip())

def clear_fields():
    name_var.set("")
    date_var.set("")
    year_var.set("")
    status_var.set("Present")

def fetch_data(name_filter=""):
    global tree
    for widget in display_frame.winfo_children():
        widget.destroy()

    selected_dept = dept_var.get()
    if not selected_dept:
        return

    ensure_table(selected_dept)
    conn = sqlite3.connect(f"{selected_dept.lower()}_attendance.db")
    cursor = conn.cursor()
    if name_filter:
        cursor.execute("SELECT * FROM attendance WHERE student_name LIKE ?", ('%' + name_filter + '%',))
    else:
        cursor.execute("SELECT * FROM attendance")
    rows = cursor.fetchall()
    conn.close()

    columns = ("ID", "Name", "Date", "Department", "Year", "Present", "Absent", "Last Update")

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
        background="#fdfefe",
        foreground="black",
        rowheight=30,
        fieldbackground="#fdfefe",
        font=("Segoe UI", 10)
    )
    style.map("Treeview",
        background=[("selected", "#5dade2")],
        foreground=[("selected", "white")]
    )
    style.configure("Treeview.Heading",
        font=("Segoe UI", 10, "bold"),
        background="#2e86c1",
        foreground="white"
    )

    tree = ttk.Treeview(display_frame, columns=columns, show="headings", style="Treeview")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=CENTER, width=130)

    tree.tag_configure("oddrow", background="#f2f2f2")
    tree.tag_configure("evenrow", background="#ffffff")

    for i, row in enumerate(rows):
        tag = "evenrow" if i % 2 == 0 else "oddrow"
        tree.insert("", END, values=row, tags=(tag,))

    tree.bind("<ButtonRelease-1>", select_item)
    tree.pack(fill=BOTH, expand=True)

    scrollbar = Scrollbar(display_frame, orient=VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=RIGHT, fill=Y)

def search():
    name_filter = search_var.get().strip()
    fetch_data(name_filter)
    calculate_totals(name_filter)

def calculate_totals(name_filter=""):
    selected_dept = dept_var.get()
    if not selected_dept:
        present_count_var.set("Present: 0")
        absent_count_var.set("Absent: 0")
        return

    ensure_table(selected_dept)
    conn = sqlite3.connect(f"{selected_dept.lower()}_attendance.db")
    cursor = conn.cursor()

    if name_filter:
        cursor.execute("SELECT SUM(present), SUM(absent) FROM attendance WHERE student_name LIKE ?", ('%' + name_filter + '%',))
    else:
        cursor.execute("SELECT SUM(present), SUM(absent) FROM attendance")

    result = cursor.fetchone()
    conn.close()

    total_present = result[0] if result[0] else 0
    total_absent = result[1] if result[1] else 0

    present_count_var.set(f"Present: {total_present}")
    absent_count_var.set(f"Absent: {total_absent}")

selected_id = None

def select_item(event):
    global selected_id
    item = tree.focus()
    if not item:
        return
    selected = tree.item(item, "values")
    selected_id = selected[0]
    name_var.set(selected[1])
    date_var.set(selected[2])
    dept_var.set(selected[3])
    year_var.set(selected[4])
    status_var.set("Present" if int(selected[5]) == 1 else "Absent")

def update_record():
    global selected_id
    if not selected_id:
        messagebox.showerror("Error", "Please select a record to update.")
        return

    dept = dept_var.get()
    ensure_table(dept)

    name = name_var.get().strip()
    date = date_var.get().strip()
    year = year_var.get()
    status = status_var.get()
    present = 1 if status == "Present" else 0
    absent = 1 if status == "Absent" else 0
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(f"{dept.lower()}_attendance.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE attendance
        SET student_name=?, attendance_date=?, year=?, present=?, absent=?, last_update=?
        WHERE id=?
    ''', (name, date, year, present, absent, update_time, selected_id))
    conn.commit()
    conn.close()

    messagebox.showinfo("Updated", "Record updated successfully.")
    clear_fields()
    fetch_data(search_var.get().strip())
    calculate_totals(search_var.get().strip())
    selected_id = None

def delete_record():
    global selected_id
    if not selected_id:
        messagebox.showerror("Error", "Please select a record to delete.")
        return

    dept = dept_var.get()
    conn = sqlite3.connect(f"{dept.lower()}_attendance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM attendance WHERE id=?", (selected_id,))
    conn.commit()
    conn.close()

    messagebox.showinfo("Deleted", "Record deleted successfully.")
    clear_fields()
    fetch_data(search_var.get().strip())
    calculate_totals(search_var.get().strip())
    selected_id = None

# GUI
Label(root, text="Student Name", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=0, column=0, padx=10, pady=5, sticky=E)
Entry(root, textvariable=name_var, width=30, font=("Segoe UI", 10)).grid(row=0, column=1, padx=10)

Label(root, text="Date (YYYY-MM-DD)", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=1, column=0, padx=10, pady=5, sticky=E)
Entry(root, textvariable=date_var, width=30, font=("Segoe UI", 10)).grid(row=1, column=1)

Label(root, text="Department", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=2, column=0, padx=10, pady=5, sticky=E)
dept_combo = ttk.Combobox(root, textvariable=dept_var, values=departments, width=28, state="readonly", font=("Segoe UI", 10))
dept_combo.grid(row=2, column=1)
dept_combo.bind("<<ComboboxSelected>>", lambda e: fetch_data())

Label(root, text="Year", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=3, column=0, padx=10, pady=5, sticky=E)
ttk.Combobox(root, textvariable=year_var, values=["1st Year", "2nd Year", "3rd Year", "4th Year"],
             width=28, state="readonly", font=("Segoe UI", 10)).grid(row=3, column=1)

Label(root, text="Status", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=4, column=0, padx=10, pady=5, sticky=E)
Radiobutton(root, text="Present", variable=status_var, value="Present", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=4, column=1, sticky=W)
Radiobutton(root, text="Absent", variable=status_var, value="Absent", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=4, column=1, sticky=E)

Button(root, text="Submit Attendance", command=submit, bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"),
       width=20).grid(row=5, column=0, pady=10, padx=10)

Button(root, text="Update", command=update_record, bg="#ffc107", fg="black", font=("Segoe UI", 10, "bold"),
       width=10).grid(row=5, column=1, sticky=W)

Button(root, text="Delete", command=delete_record, bg="#dc3545", fg="white", font=("Segoe UI", 10, "bold"),
       width=10).grid(row=5, column=1, sticky=E)

Label(root, text="Search Name", bg="#eaf2f8", font=("Segoe UI", 10)).grid(row=5, column=2, sticky=W, padx=10)
Entry(root, textvariable=search_var, width=20, font=("Segoe UI", 10)).grid(row=5, column=2, padx=100)
Button(root, text="Search", command=search, bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"),
       width=10).grid(row=5, column=3)

display_frame = Frame(root, bg="#eaf2f8")
display_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

Label(root, textvariable=present_count_var, font=("Segoe UI", 10, "bold"), bg="#eaf2f8", fg="green").grid(row=7, column=0, sticky=W, padx=10)
Label(root, textvariable=absent_count_var, font=("Segoe UI", 10, "bold"), bg="#eaf2f8", fg="red").grid(row=7, column=1, sticky=W)

root.grid_rowconfigure(6, weight=1)
root.grid_columnconfigure(2, weight=1)

root.mainloop()