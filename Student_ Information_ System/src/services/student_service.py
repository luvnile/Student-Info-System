"""Student CRUD operations and JSON persistence."""

import json
import os
import re
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from src.models.student import Student


class StudentService:
    """Manage student records stored in a JSON file."""

    REQUIRED_FIELDS = ("name", "email", "course", "year_level")
    EDITABLE_FIELDS = frozenset(REQUIRED_FIELDS)
    EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, data_file: str | Path = "data/students.json") -> None:
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self._save_students([])

    def _load_students(self) -> list[dict[str, Any]]:
        """Load records and reject malformed files instead of hiding corruption."""
        try:
            with self.data_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Student data file contains invalid JSON: {self.data_file}"
            ) from error
        except OSError as error:
            raise OSError(
                f"Unable to read student data from {self.data_file}: {error}"
            ) from error

        if not isinstance(data, list) or any(
            not isinstance(student, dict) for student in data
        ):
            raise ValueError(
                f"Student data must be a JSON list of objects: {self.data_file}"
            )
        return data

    def _save_students(self, students: list[dict[str, Any]]) -> None:
        """Atomically replace the JSON file so interrupted writes do not corrupt it."""
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.data_file.parent,
                delete=False,
                suffix=".tmp",
            ) as file:
                temporary_path = file.name
                json.dump(students, file, indent=4)
                file.write("\n")
            os.replace(temporary_path, self.data_file)
        except OSError as error:
            if temporary_path and os.path.exists(temporary_path):
                os.unlink(temporary_path)
            raise OSError(
                f"Unable to save student data to {self.data_file}: {error}"
            ) from error

    @classmethod
    def _normalize_student_data(
        cls, student_data: Mapping[str, Any]
    ) -> dict[str, str]:
        """Validate and normalize a complete set of editable student fields."""
        normalized: dict[str, str] = {}
        for field_name in cls.REQUIRED_FIELDS:
            value = student_data.get(field_name)
            if value is None:
                raise ValueError(f"{field_name.replace('_', ' ').title()} is required.")
            normalized[field_name] = str(value).strip()
            if not normalized[field_name]:
                raise ValueError(
                    f"{field_name.replace('_', ' ').title()} cannot be empty."
                )

        if not cls.EMAIL_PATTERN.fullmatch(normalized["email"]):
            raise ValueError("Invalid email address.")
        return normalized

    @staticmethod
    def _normalize_id(student_id: str) -> str:
        if not isinstance(student_id, str) or not student_id.strip():
            raise ValueError("Student ID cannot be empty.")
        return student_id.strip().upper()

    @staticmethod
    def _generate_student_id(students: list[dict[str, Any]]) -> str:
        numbers = []
        for student in students:
            current_id = str(student.get("student_id", ""))
            if current_id.startswith("STU") and current_id[3:].isdigit():
                numbers.append(int(current_id[3:]))
        return f"STU{max(numbers, default=0) + 1:03d}"

    def add_student(self, student_data: Mapping[str, Any]) -> dict[str, str]:
        """Validate and add a student, returning the saved record."""
        normalized = self._normalize_student_data(student_data)
        students = self._load_students()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        student = Student(
            student_id=self._generate_student_id(students),
            **normalized,
            created_at=now,
            updated_at=now,
        )
        record = student.to_dict()
        students.append(record)
        self._save_students(students)
        return record

    def get_all_students(self) -> list[dict[str, Any]]:
        """Return all student records."""
        return self._load_students()

    def get_student(self, student_id: str) -> dict[str, Any] | None:
        """Return one student by ID, or None when no matching record exists."""
        normalized_id = self._normalize_id(student_id)
        return next(
            (
                student
                for student in self._load_students()
                if student.get("student_id", "").upper() == normalized_id
            ),
            None,
        )

    def update_student(
        self, student_id: str, update_data: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        """Update supplied fields and return the updated record, if found."""
        unknown_fields = set(update_data) - self.EDITABLE_FIELDS
        if unknown_fields:
            raise ValueError(
                "Unsupported student field(s): " + ", ".join(sorted(unknown_fields))
            )

        normalized_id = self._normalize_id(student_id)
        students = self._load_students()
        for student in students:
            if student.get("student_id", "").upper() != normalized_id:
                continue

            updated_values = {
                field_name: student.get(field_name, "")
                for field_name in self.REQUIRED_FIELDS
            }
            updated_values.update(update_data)
            normalized = self._normalize_student_data(updated_values)
            student.update(normalized)
            student["updated_at"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            self._save_students(students)
            return student
        return None

    def delete_student(self, student_id: str) -> bool:
        """Delete a student by ID and report whether a record was removed."""
        normalized_id = self._normalize_id(student_id)
        students = self._load_students()
        remaining = [
            student
            for student in students
            if student.get("student_id", "").upper() != normalized_id
        ]
        if len(remaining) == len(students):
            return False
        self._save_students(remaining)
        return True

    def search_students(self, keyword: str) -> list[dict[str, Any]]:
        """Search student ID, name, email, course, and year level."""
        search_term = keyword.strip().casefold()
        students = self._load_students()
        if not search_term:
            return students
        return [
            student
            for student in students
            if any(
                search_term in str(student.get(field, "")).casefold()
                for field in (
                    "student_id",
                    "name",
                    "email",
                    "course",
                    "year_level",
                )
            )
        ]

    def export_students(
        self, output_file: str | Path = "data/students_export.json"
    ) -> str:
        """Export the current records as formatted JSON and return its path."""
        destination = Path(output_file)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("w", encoding="utf-8") as file:
                json.dump(self._load_students(), file, indent=4)
                file.write("\n")
        except OSError as error:
            raise OSError(
                f"Unable to export student data to {destination}: {error}"
            ) from error
        return str(destination)
