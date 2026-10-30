"""JSON-backed storage and business rules for the placement application."""
import json
import math
import os
import tempfile
from datetime import date

import config
from utils import ValidationError, clean_date


class StorageError(RuntimeError):
    """Raised when application data cannot be read or safely persisted."""


class Collection:
    """A small JSON collection with atomic writes and corrupt-file recovery."""

    def __init__(self, path, warnings, required_fields):
        self.path = path
        self.warnings = warnings
        self.required_fields = required_fields
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            self.records = []
            self.save()
            return
        try:
            with open(path, "rb") as file:
                contents = file.read()
        except OSError as error:
            raise StorageError(f"Could not read {path}: {error}") from error
        if not contents.strip():
            self.records = []
            self.save()
            return
        try:
            data = json.loads(contents.decode("utf-8"))
            if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
                raise ValueError("the JSON root must be a list of records")
            collection_name = os.path.splitext(os.path.basename(path))[0]
            text_fields = {
                "students": ("name", "roll_no", "department", "email", "phone"),
                "companies": ("name", "industry", "location", "website", "contact_email"),
                "jobs": ("role", "description", "apply_link"),
                "applications": ("status", "application_date", "joining_date"),
            }[collection_name]
            for record in data:
                if not self.required_fields.issubset(record):
                    raise ValueError("a record is missing required fields")
                record_id = record["id"]
                if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id < 1:
                    raise ValueError("a record has an invalid ID")
                if any(not isinstance(record[field], str) for field in text_fields):
                    raise ValueError("a record has an invalid text field")
                if collection_name in ("students", "jobs"):
                    number_key = "cgpa" if collection_name == "students" else "min_cgpa"
                    number = record[number_key]
                    if (isinstance(number, bool) or not isinstance(number, (int, float))
                            or not math.isfinite(number) or not 0 <= number <= 10):
                        raise ValueError(f"a record has an invalid {number_key}")
                    if collection_name == "students":
                        skills = record["skills"]
                    else:
                        skills = record["required_skills"]
                    if not isinstance(skills, list) or any(not isinstance(skill, str) for skill in skills):
                        raise ValueError("a record has an invalid skills list")
                if collection_name == "jobs":
                    package = record["package"]
                    if (isinstance(package, bool) or not isinstance(package, (int, float))
                            or not math.isfinite(package) or package <= 0):
                        raise ValueError("a record has an invalid package")
                if collection_name in ("jobs", "applications"):
                    foreign_keys = ("company_id",) if collection_name == "jobs" else (
                        "student_id", "job_id")
                    if any(isinstance(record[key], bool) or not isinstance(record[key], int)
                           or record[key] < 1 for key in foreign_keys):
                        raise ValueError("a record has an invalid relationship ID")
                if collection_name == "applications":
                    if record["status"] not in config.STATUSES:
                        raise ValueError("an application has an invalid status")
                    clean_date(record["application_date"], "Application date")
                    if record["joining_date"]:
                        clean_date(record["joining_date"], "Joining date")
            ids = [record["id"] for record in data]
            if len(ids) != len(set(ids)):
                raise ValueError("record IDs must be unique")
            self.records = data
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            backup = path + ".corrupt"
            suffix = 1
            while os.path.exists(backup):
                backup = f"{path}.corrupt.{suffix}"
                suffix += 1
            try:
                os.replace(path, backup)
            except OSError as backup_error:
                raise StorageError(f"Could not preserve damaged data file {path}: {backup_error}") from backup_error
            self.records = []
            self.save()
            self.warnings.append(
                f"Invalid data in {os.path.basename(path)} was moved to "
                f"{os.path.basename(backup)}. A new empty file was created. ({error})")

    def save(self):
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=os.path.dirname(self.path),
                    prefix=".placement-", suffix=".tmp", delete=False) as file:
                temporary_path = file.name
                json.dump(self.records, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.path)
        except (OSError, TypeError, ValueError) as error:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass
            raise StorageError(f"Could not save {self.path}: {error}") from error


class Database:
    """Owns the four JSON collections and enforces their relationships."""

    COLLECTION_FIELDS = {
        "students": {"id", "name", "roll_no", "department", "email", "phone", "cgpa", "skills"},
        "companies": {"id", "name", "industry", "location", "website", "contact_email"},
        "jobs": {"id", "company_id", "role", "required_skills", "min_cgpa", "package",
                 "description", "apply_link"},
        "applications": {"id", "student_id", "job_id", "application_date", "status",
                         "joining_date"},
    }

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or config.DATA_DIR
        self.warnings = []
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            self._collections = {
                name: Collection(
                    os.path.join(self.data_dir, f"{name}.json"), self.warnings, required_fields)
                for name, required_fields in self.COLLECTION_FIELDS.items()
            }
        except OSError as error:
            raise StorageError(f"Could not open the data folder {self.data_dir}: {error}") from error

    def _records(self, name):
        return self._collections[name].records

    def _save(self, *names):
        for name in names:
            self._collections[name].save()

    def _next_id(self, name):
        return max((int(row.get("id", 0)) for row in self._records(name)), default=0) + 1

    @staticmethod
    def _ensure_unique(records, key, value, label, exclude_id=None):
        normalized = str(value).strip().casefold()
        if any(str(row.get(key, "")).strip().casefold() == normalized
               and row.get("id") != exclude_id
               for row in records):
            raise ValidationError(f"A {label} with that value already exists.")

    @staticmethod
    def _find(records, record_id):
        return next((row for row in records if row.get("id") == record_id), None)

    # Students
    def add_student(self, data):
        self._ensure_unique(self._records("students"), "roll_no", data["roll_no"],
                            "student with this roll number")
        student = {"id": self._next_id("students"), **data}
        self._records("students").append(student)
        self._save("students")
        return student

    def update_student(self, record_id, data):
        student = self.get_student(record_id)
        if student is None:
            raise ValidationError("This student no longer exists.")
        self._ensure_unique(self._records("students"), "roll_no", data["roll_no"],
                            "student with this roll number", record_id)
        student.update(data)
        self._save("students")
        return student

    def get_student(self, record_id):
        return self._find(self._records("students"), record_id)

    def search_students(self, query=""):
        needle = query.casefold().strip()
        return [row for row in self._records("students")
                if not needle or any(needle in str(row.get(key, "")).casefold()
                                     for key in ("name", "roll_no", "department", "email",
                                                 "phone", "skills"))]

    def student_choices(self):
        return [(f"{row['name']} ({row['roll_no']})", row["id"])
                for row in self.search_students()]

    def count_student_applications(self, student_id):
        return sum(row["student_id"] == student_id for row in self._records("applications"))

    def student_applications(self, student_id):
        return [row for row in self.search_applications() if row["student_id"] == student_id]

    def delete_student(self, student_id):
        if self.get_student(student_id) is None:
            raise ValidationError("This student no longer exists.")
        applications = self._records("applications")
        retained = [row for row in applications if row["student_id"] != student_id]
        removed = len(applications) - len(retained)
        self._collections["students"].records.remove(self.get_student(student_id))
        self._collections["applications"].records = retained
        self._save("students", "applications")
        return removed

    # Companies
    def add_company(self, data):
        self._ensure_unique(self._records("companies"), "name", data["name"], "company")
        company = {"id": self._next_id("companies"), **data}
        self._records("companies").append(company)
        self._save("companies")
        return company

    def update_company(self, record_id, data):
        company = self.get_company(record_id)
        if company is None:
            raise ValidationError("This company no longer exists.")
        self._ensure_unique(self._records("companies"), "name", data["name"], "company", record_id)
        company.update(data)
        self._save("companies")
        return company

    def get_company(self, record_id):
        return self._find(self._records("companies"), record_id)

    def get_company_by_name(self, name):
        normalized = name.strip().casefold()
        return next((row for row in self._records("companies")
                     if row["name"].casefold() == normalized), None)

    def company_name(self, company_id):
        company = self.get_company(company_id)
        return company["name"] if company else "Unknown company"

    def search_companies(self, query=""):
        needle = query.casefold().strip()
        return [row for row in self._records("companies")
                if not needle or any(needle in str(row.get(key, "")).casefold()
                                     for key in ("name", "industry", "location", "website",
                                                 "contact_email"))]

    def count_company_jobs(self, company_id):
        return sum(row["company_id"] == company_id for row in self._records("jobs"))

    def company_dependents(self, company_id):
        job_ids = {row["id"] for row in self._records("jobs") if row["company_id"] == company_id}
        return len(job_ids), sum(row["job_id"] in job_ids for row in self._records("applications"))

    def delete_company(self, company_id):
        company = self.get_company(company_id)
        if company is None:
            raise ValidationError("This company no longer exists.")
        jobs, applications = self.company_dependents(company_id)
        job_ids = {row["id"] for row in self._records("jobs") if row["company_id"] == company_id}
        self._collections["companies"].records.remove(company)
        self._collections["jobs"].records = [
            row for row in self._records("jobs") if row["company_id"] != company_id]
        self._collections["applications"].records = [
            row for row in self._records("applications") if row["job_id"] not in job_ids]
        self._save("companies", "jobs", "applications")
        return jobs, applications

    # Jobs
    def add_job(self, data):
        if self.get_company(data["company_id"]) is None:
            raise ValidationError("Please select a valid company.")
        self._ensure_unique(
            [row for row in self._records("jobs") if row["company_id"] == data["company_id"]],
            "role", data["role"], "job role at this company")
        job = {"id": self._next_id("jobs"), **data}
        self._records("jobs").append(job)
        self._save("jobs")
        return job

    def update_job(self, record_id, data):
        job = self.get_job(record_id)
        if job is None:
            raise ValidationError("This job no longer exists.")
        if self.get_company(data["company_id"]) is None:
            raise ValidationError("Please select a valid company.")
        siblings = [row for row in self._records("jobs")
                    if row["company_id"] == data["company_id"] and row["id"] != record_id]
        self._ensure_unique(siblings, "role", data["role"], "job role at this company")
        job.update(data)
        self._save("jobs")
        return job

    def get_job(self, record_id):
        return self._find(self._records("jobs"), record_id)

    def job_choices(self):
        return [(f"{self.company_name(job['company_id'])} - {job['role']}", job["id"])
                for job in self.jobs_with_company()]

    def jobs_with_company(self, query=""):
        needle = query.casefold().strip()
        result = []
        for job in self._records("jobs"):
            company = self.get_company(job["company_id"])
            if company is None:
                continue
            if needle and not any(needle in str(value).casefold()
                                  for value in (company["name"], job["role"],
                                                job["required_skills"], job["description"])):
                continue
            result.append({**job, "company_name": company["name"]})
        return result

    def count_job_applications(self, job_id):
        return sum(row["job_id"] == job_id for row in self._records("applications"))

    def delete_job(self, job_id):
        job = self.get_job(job_id)
        if job is None:
            raise ValidationError("This job no longer exists.")
        self._collections["jobs"].records.remove(job)
        applications = self._records("applications")
        retained = [row for row in applications if row["job_id"] != job_id]
        removed = len(applications) - len(retained)
        self._collections["applications"].records = retained
        self._save("jobs", "applications")
        return removed

    # Applications
    def add_application(self, student_id, job_id):
        student, job = self.get_student(student_id), self.get_job(job_id)
        if student is None or job is None:
            raise ValidationError("Please choose a valid student and job.")
        if any(row["student_id"] == student_id and row["job_id"] == job_id
               for row in self._records("applications")):
            raise ValidationError("This student has already applied for this job.")
        application = {
            "id": self._next_id("applications"),
            "student_id": student_id,
            "job_id": job_id,
            "application_date": date.today().strftime(config.DATE_FORMAT),
            "status": config.DEFAULT_STATUS,
            "joining_date": "",
        }
        self._records("applications").append(application)
        self._save("applications")
        return self.get_application(application["id"])

    def _application_view(self, application):
        student, job = self.get_student(application["student_id"]), self.get_job(application["job_id"])
        if student is None or job is None:
            return None
        company = self.get_company(job["company_id"])
        return {
            **application,
            "student_name": student["name"],
            "roll_no": student["roll_no"],
            "company_name": company["name"] if company else "Unknown company",
            "job_role": job["role"],
            "package": job["package"],
        }

    def get_application(self, application_id):
        application = self._find(self._records("applications"), application_id)
        return self._application_view(application) if application else None

    def search_applications(self, query="", status="All"):
        needle = query.casefold().strip()
        results = []
        for application in self._records("applications"):
            if status != "All" and application["status"] != status:
                continue
            row = self._application_view(application)
            if row is None:
                continue
            if needle and not any(needle in str(row.get(key, "")).casefold()
                                  for key in ("student_name", "roll_no", "company_name", "job_role",
                                              "status", "application_date")):
                continue
            results.append(row)
        return sorted(results, key=lambda row: (row["application_date"], row["id"]), reverse=True)

    def set_application_status(self, application_id, status, joining_date=""):
        application = self._find(self._records("applications"), application_id)
        if application is None:
            raise ValidationError("This application no longer exists.")
        if status not in config.STATUSES:
            raise ValidationError("Please choose a valid application status.")
        if status == "Selected":
            joining_date = clean_date(joining_date, "Joining date")
            if joining_date < application["application_date"]:
                raise ValidationError("Joining date cannot be before the application date.")
        else:
            joining_date = ""
        application.update(status=status, joining_date=joining_date)
        self._save("applications")
        return self.get_application(application_id)

    def delete_application(self, application_id):
        application = self._find(self._records("applications"), application_id)
        if application is None:
            raise ValidationError("This application no longer exists.")
        self._records("applications").remove(application)
        self._save("applications")

    def stats(self):
        applications = self.search_applications()
        selected_students = {row["student_id"] for row in applications
                             if row["status"] == "Selected"}
        students = self._records("students")
        by_status = {status: 0 for status in config.STATUSES}
        for application in applications:
            by_status[application["status"]] = by_status.get(application["status"], 0) + 1
        return {
            "students": len(students),
            "companies": len(self._records("companies")),
            "jobs": len(self._records("jobs")),
            "applications": len(applications),
            "placed": len(selected_students),
            "placement_rate": 100 * len(selected_students) / len(students) if students else 0.0,
            "by_status": by_status,
        }
