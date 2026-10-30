"""Student management screen."""
import config
import utils
from widgets import CrudPage


class StudentsPage(CrudPage):
    entity = "student"
    entity_plural = "students"
    columns = [
        ("id", "ID", 45, "center"),
        ("roll_no", "Roll No", 95, "w"),
        ("name", "Student", 145, "w"),
        ("department", "Department", 125, "w"),
        ("email", "Email", 170, "w"),
        ("phone", "Phone", 105, "w"),
        ("cgpa", "CGPA", 65, "center"),
        ("skills", "Skills", 180, "w"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app, "Students",
                         "Manage student profiles, academic details and skills.")

    def build_form(self, form):
        form.add_entry("name", "Full Name")
        form.add_entry("roll_no", "Roll Number")
        form.add_combo("department", "Department", config.DEPARTMENTS)
        form.add_entry("email", "Email")
        form.add_entry("phone", "Phone")
        form.add_entry("cgpa", "CGPA (0 - 10)")
        form.add_entry("skills", "Skills (comma separated)")

    def read_form(self):
        form = self.form
        return {
            "name": utils.clean_person_name(form.get("name")),
            "roll_no": utils.clean_text(form.get("roll_no"), "Roll number", 1, 40),
            "department": utils.clean_text(form.get("department"), "Department", 2, 60),
            "email": utils.clean_email(form.get("email")),
            "phone": utils.clean_phone(form.get("phone")),
            "cgpa": utils.parse_cgpa(form.get("cgpa")),
            "skills": utils.parse_skills(form.get("skills")),
        }

    def record_to_form(self, record_id):
        student = self.db.get_student(record_id)
        if student is None:
            return
        for key in ("name", "roll_no", "department", "email", "phone", "cgpa"):
            self.form.set(key, student[key])
        self.form.set("skills", utils.skills_to_text(student["skills"]))

    def get_rows(self, query):
        return [
            (student["id"], [
                student["id"], student["roll_no"], student["name"], student["department"],
                student["email"], student["phone"], f"{student['cgpa']:.2f}",
                utils.skills_to_text(student["skills"]) or "-",
            ])
            for student in self.db.search_students(query)
        ]

    def add_record(self, data):
        self.db.add_student(data)

    def update_record(self, record_id, data):
        self.db.update_student(record_id, data)

    def delete_prompt(self, record_id):
        student = self.db.get_student(record_id)
        count = self.db.count_student_applications(record_id)
        text = f"Delete {student['name']}?"
        if count:
            text += f"\n\nThis will also delete {count} application(s) linked to this student."
        return text

    def delete_record(self, record_id):
        removed = self.db.delete_student(record_id)
        return f"{removed} related application(s) were removed." if removed else ""
