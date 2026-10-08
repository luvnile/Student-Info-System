"""Simple desktop interface for the Student Information System."""

import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from src.main import StudentInformationSystem
from src.utils.config import PROJECT_ROOT


class StudentInformationUI:
    """A small Tkinter interface backed by the student service."""

    FIELDS = (
        ("name", "Name"),
        ("email", "Email"),
        ("course", "Course"),
        ("year_level", "Year Level"),
    )

    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root or tk.Tk()
        self.system = StudentInformationSystem()
        self.service = self.system.student_service
        self.logger: logging.Logger = self.system.logger
        self.root.title("Student Information System")
        self.root.geometry("1120x720")
        self.root.minsize(900, 600)

        self.variables = {
            field: tk.StringVar()
            for field in (entry[0] for entry in self.FIELDS)
        }
        self.search_variable = tk.StringVar()
        self.selected_student_id: str | None = None
        self._resize_job: str | None = None
        self._background_photo: ImageTk.PhotoImage | None = None

        self._load_background()
        self._configure_styles()
        self._build_interface()
        self.root.bind("<Configure>", self._schedule_background_resize)
        self.refresh_students()

    def _load_background(self) -> None:
        """Load the requested project background, with a helpful missing-file error."""
        background_path = PROJECT_ROOT / "bg.jpg"
        if not background_path.is_file():
            raise FileNotFoundError(
                f"Background image not found: {background_path}"
            )
        with Image.open(background_path) as image:
            self._background_image = image.convert("RGB")

        self.background_label = tk.Label(self.root, borderwidth=0)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self._resize_background()

    def _schedule_background_resize(self, event: tk.Event) -> None:
        if event.widget is not self.root:
            return
        if self._resize_job is not None:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(100, self._resize_background)

    def _resize_background(self) -> None:
        self._resize_job = None
        width = max(self.root.winfo_width(), 1)
        height = max(self.root.winfo_height(), 1)
        image = ImageOps.fit(
            self._background_image,
            (width, height),
            method=Image.Resampling.LANCZOS,
        )
        self._background_photo = ImageTk.PhotoImage(image, master=self.root)
        self.background_label.configure(image=self._background_photo)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#25312b",
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#e5eee5",
            foreground="#263d31",
            font=("Segoe UI", 10, "bold"),
            padding=8,
        )
        style.map(
            "Treeview",
            background=[("selected", "#c7dfce")],
            foreground=[("selected", "#20382b")],
        )
        style.configure("TButton", padding=(10, 7), font=("Segoe UI", 9))
        style.configure("TEntry", padding=7)

    def _build_interface(self) -> None:
        page = tk.Frame(self.root, bg="#f5f7f2", padx=22, pady=18)
        page.pack(fill="both", expand=True, padx=22, pady=18)
        page.grid_columnconfigure(1, weight=1)
        page.grid_rowconfigure(2, weight=1)

        header = tk.Frame(page, bg="#f5f7f2")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        tk.Label(
            header,
            text="Student Information System",
            bg="#f5f7f2",
            fg="#263d31",
            font=("Segoe UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Manage student records",
            bg="#f5f7f2",
            fg="#607166",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(2, 0))

        form = tk.Frame(page, bg="#ffffff", padx=18, pady=16)
        form.grid(row=1, column=0, rowspan=2, sticky="nsw", padx=(0, 16))
        form.grid_columnconfigure(0, weight=1)
        tk.Label(
            form,
            text="Student Details",
            bg="#ffffff",
            fg="#263d31",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        for row, (field, label) in enumerate(self.FIELDS, start=1):
            tk.Label(
                form,
                text=label,
                bg="#ffffff",
                fg="#415248",
                font=("Segoe UI", 9, "bold"),
            ).grid(row=row * 2 - 1, column=0, sticky="w", pady=(7, 4))
            ttk.Entry(form, textvariable=self.variables[field], width=28).grid(
                row=row * 2, column=0, sticky="ew"
            )

        buttons = tk.Frame(form, bg="#ffffff")
        buttons.grid(row=10, column=0, sticky="ew", pady=(18, 0))
        ttk.Button(
            buttons, text="Add Student", command=self.add_student
        ).pack(fill="x", pady=3)
        ttk.Button(
            buttons, text="Save Changes", command=self.update_student
        ).pack(fill="x", pady=3)
        ttk.Button(
            buttons, text="Clear Form", command=self.clear_form
        ).pack(fill="x", pady=3)

        toolbar = tk.Frame(page, bg="#f5f7f2")
        toolbar.grid(row=1, column=1, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(0, weight=1)
        search_entry = ttk.Entry(toolbar, textvariable=self.search_variable)
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        search_entry.bind("<Return>", lambda _event: self.refresh_students())
        ttk.Button(
            toolbar, text="Search", command=self.refresh_students
        ).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(
            toolbar, text="Show All", command=self.show_all_students
        ).grid(row=0, column=2)

        records = tk.Frame(page, bg="#ffffff", padx=10, pady=10)
        records.grid(row=2, column=1, sticky="nsew")
        records.grid_columnconfigure(0, weight=1)
        records.grid_rowconfigure(0, weight=1)
        columns = ("student_id", "name", "email", "course", "year_level")
        self.table = ttk.Treeview(
            records, columns=columns, show="headings", selectmode="browse"
        )
        for column, heading, width in (
            ("student_id", "Student ID", 95),
            ("name", "Name", 150),
            ("email", "Email", 185),
            ("course", "Course", 150),
            ("year_level", "Year", 65),
        ):
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, minwidth=55, anchor="w")
        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            records, orient="vertical", command=self.table.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.bind("<<TreeviewSelect>>", self._select_student)

        actions = tk.Frame(page, bg="#f5f7f2")
        actions.grid(row=3, column=1, sticky="ew", pady=(10, 0))
        ttk.Button(
            actions, text="Delete Selected", command=self.delete_student
        ).pack(side="left")
        ttk.Button(
            actions, text="Export JSON", command=self.export_students
        ).pack(side="left", padx=(8, 0))
        self.status_variable = tk.StringVar(value="Ready")
        tk.Label(
            actions,
            textvariable=self.status_variable,
            bg="#f5f7f2",
            fg="#607166",
            font=("Segoe UI", 9),
        ).pack(side="right")

    def _selected_student_id(self) -> str | None:
        selection = self.table.selection()
        return selection[0] if selection else None

    def _select_student(self, event: tk.Event) -> None:
        if event.widget is not self.table:
            return
        student_id = self._selected_student_id()
        if student_id is None:
            return
        student = self.service.get_student(student_id)
        if student is None:
            self.refresh_students()
            return
        self.selected_student_id = student_id
        for field in self.variables:
            self.variables[field].set(student[field])
        self.status_variable.set(f"Selected {student_id}")

    def refresh_students(self) -> None:
        try:
            students = self.service.search_students(self.search_variable.get())
        except (ValueError, OSError) as error:
            self._show_error("Could not load students", error)
            return

        for item in self.table.get_children():
            self.table.delete(item)
        for student in students:
            values = tuple(
                student.get(field, "")
                for field in (
                    "student_id",
                    "name",
                    "email",
                    "course",
                    "year_level",
                )
            )
            self.table.insert("", "end", iid=student["student_id"], values=values)
        self.status_variable.set(f"{len(students)} student(s)")

    def show_all_students(self) -> None:
        self.search_variable.set("")
        self.refresh_students()

    def clear_form(self) -> None:
        self.selected_student_id = None
        for variable in self.variables.values():
            variable.set("")
        self.table.selection_remove(self.table.selection())
        self.status_variable.set("Ready")

    def _form_data(self) -> dict[str, str]:
        return {
            field: variable.get().strip()
            for field, variable in self.variables.items()
        }

    def add_student(self) -> None:
        try:
            student = self.service.add_student(self._form_data())
        except (ValueError, OSError) as error:
            self._show_error("Could not add student", error)
            return
        self.logger.info("Added student %s through desktop UI", student["student_id"])
        self.clear_form()
        self.refresh_students()
        self.status_variable.set(f"Added {student['student_id']}")

    def update_student(self) -> None:
        student_id = self.selected_student_id
        if student_id is None:
            messagebox.showinfo(
                "Select a student",
                "Select a student in the table before saving changes.",
                parent=self.root,
            )
            return
        try:
            updated = self.service.update_student(student_id, self._form_data())
        except (ValueError, OSError) as error:
            self._show_error("Could not update student", error)
            return
        if updated is None:
            messagebox.showerror(
                "Student not found",
                f"Student {student_id} no longer exists.",
                parent=self.root,
            )
            self.refresh_students()
            self.clear_form()
            return
        self.logger.info("Updated student %s through desktop UI", student_id)
        self.refresh_students()
        self.status_variable.set(f"Updated {student_id}")

    def delete_student(self) -> None:
        student_id = self._selected_student_id()
        if student_id is None:
            messagebox.showinfo(
                "Select a student",
                "Select a student in the table before deleting.",
                parent=self.root,
            )
            return
        if not messagebox.askyesno(
            "Delete student",
            f"Delete student {student_id}?",
            parent=self.root,
        ):
            return
        try:
            deleted = self.service.delete_student(student_id)
        except (ValueError, OSError) as error:
            self._show_error("Could not delete student", error)
            return
        if deleted:
            self.logger.info("Deleted student %s through desktop UI", student_id)
            self.clear_form()
            self.refresh_students()
            self.status_variable.set(f"Deleted {student_id}")

    def export_students(self) -> None:
        configured_output = self.system._project_path(
            self.system.config.get(
                "export", "output_file", "data/students_export.json"
            )
        )
        output_file = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export student records",
            initialdir=str(configured_output.parent),
            initialfile=configured_output.name,
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"),),
        )
        if not output_file:
            return
        try:
            exported_file = self.service.export_students(output_file)
        except (ValueError, OSError) as error:
            self._show_error("Could not export students", error)
            return
        self.logger.info("Exported students to %s through desktop UI", exported_file)
        self.status_variable.set(f"Exported to {exported_file}")
        messagebox.showinfo(
            "Export complete",
            f"Student records saved to:\n{exported_file}",
            parent=self.root,
        )

    def _show_error(self, title: str, error: Exception) -> None:
        self.logger.exception("%s: %s", title, error)
        messagebox.showerror(title, str(error), parent=self.root)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    """Start the desktop application."""
    StudentInformationUI().run()


if __name__ == "__main__":
    main()
