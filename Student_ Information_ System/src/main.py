"""Command-line interface for the Student Information System."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.services.student_service import StudentService
from src.utils.config import Config, PROJECT_ROOT
from src.utils.logger import setup_logger


class StudentInformationSystem:
    """Coordinate the interactive menu and student service."""

    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config = Config(config_file)
        data_file = self._project_path(
            self.config.get("data", "students_file", "data/students.json")
        )
        log_file = self._project_path(
            self.config.get("logging", "log_file", "logs/app.log")
        )
        self.student_service = StudentService(data_file=data_file)
        self.logger = setup_logger(log_file=log_file)

    @staticmethod
    def _project_path(value: str | Path) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else PROJECT_ROOT / path

    @staticmethod
    def _display_student(student: dict[str, Any]) -> None:
        print("-" * 50)
        for label, key in (
            ("ID", "student_id"),
            ("Name", "name"),
            ("Email", "email"),
            ("Course", "course"),
            ("Year Level", "year_level"),
        ):
            print(f"{label}: {student[key]}")
        print("-" * 50)

    def _perform(self, action_name: str, action: Callable[[], None]) -> None:
        try:
            action()
        except (ValueError, OSError) as error:
            self.logger.exception("%s failed", action_name)
            print(f"Error: {error}")

    def add_student(self) -> None:
        print("\n--- Add New Student ---")
        data = {
            "name": input("Name: ").strip(),
            "email": input("Email: ").strip(),
            "course": input("Course: ").strip(),
            "year_level": input("Year Level: ").strip(),
        }
        student = self.student_service.add_student(data)
        self.logger.info("Added student %s", student["student_id"])
        print(f"Student added successfully. ID: {student['student_id']}")

    def view_all_students(self) -> None:
        students = self.student_service.get_all_students()
        if not students:
            print("No students found.")
            return
        for student in students:
            self._display_student(student)

    def view_student_by_id(self) -> None:
        student = self.student_service.get_student(input("Enter Student ID: "))
        if student is None:
            print("Student not found.")
        else:
            self._display_student(student)

    def update_student(self) -> None:
        student_id = input("Enter Student ID: ").strip()
        student = self.student_service.get_student(student_id)
        if student is None:
            print("Student not found.")
            return

        print("Press Enter to keep the current value.")
        update_data = {}
        for field, label in (
            ("name", "Name"),
            ("email", "Email"),
            ("course", "Course"),
            ("year_level", "Year Level"),
        ):
            value = input(f"{label} [{student[field]}]: ").strip()
            if value:
                update_data[field] = value
        if not update_data:
            print("No changes were made.")
            return

        updated = self.student_service.update_student(student_id, update_data)
        if updated is None:
            print("Student not found.")
            return
        self.logger.info("Updated student %s", student_id)
        print("Student updated successfully.")

    def delete_student(self) -> None:
        student_id = input("Enter Student ID: ").strip()
        student = self.student_service.get_student(student_id)
        if student is None:
            print("Student not found.")
            return
        if input(f"Delete {student['name']}? (y/n): ").strip().casefold() != "y":
            print("Delete operation cancelled.")
            return
        if self.student_service.delete_student(student_id):
            self.logger.info("Deleted student %s", student_id)
            print("Student deleted successfully.")

    def search_students(self) -> None:
        results = self.student_service.search_students(
            input("Enter search keyword: ")
        )
        if not results:
            print("No matching students found.")
            return
        for student in results:
            self._display_student(student)

    def export_students(self) -> None:
        output_file = self._project_path(
            self.config.get("export", "output_file", "data/students_export.json")
        )
        exported_file = self.student_service.export_students(output_file)
        self.logger.info("Exported students to %s", exported_file)
        print(f"Students exported to {exported_file}")

    def display_menu(self) -> None:
        print(
            "\n"
            "=== STUDENT INFORMATION SYSTEM ===\n"
            "1. Add Student\n"
            "2. View All Students\n"
            "3. View Student by ID\n"
            "4. Update Student\n"
            "5. Delete Student\n"
            "6. Search Students\n"
            "7. Export Students\n"
            "8. Exit"
        )

    def run(self) -> None:
        actions: dict[str, tuple[str, Callable[[], None]]] = {
            "1": ("Add student", self.add_student),
            "2": ("View students", self.view_all_students),
            "3": ("Find student", self.view_student_by_id),
            "4": ("Update student", self.update_student),
            "5": ("Delete student", self.delete_student),
            "6": ("Search students", self.search_students),
            "7": ("Export students", self.export_students),
        }
        self.logger.info("Student Information System started")
        try:
            while True:
                self.display_menu()
                choice = input("Enter your choice (1-8): ").strip()
                if choice == "8":
                    print("Goodbye!")
                    break
                selected_action = actions.get(choice)
                if selected_action is None:
                    print("Invalid choice. Please enter a number from 1-8.")
                    continue
                action_name, action = selected_action
                self._perform(action_name, action)
        except KeyboardInterrupt:
            print("\nApplication interrupted.")
            self.logger.warning("Application interrupted by user")
        finally:
            self.logger.info("Student Information System stopped")


def main() -> None:
    """Start the command-line application."""
    StudentInformationSystem().run()


if __name__ == "__main__":
    main()
