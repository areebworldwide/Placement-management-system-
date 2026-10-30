"""Job management screen (add / view / search / edit / delete job openings)."""
import utils
from widgets import AppButton, CrudPage, show_warning


class JobsPage(CrudPage):
    entity = "job"
    entity_plural = "jobs"
    columns = [
        ("id", "ID", 45, "center"),
        ("company", "Company", 130, "w"),
        ("role", "Job Role", 150, "w"),
        ("skills", "Required Skills", 190, "w"),
        ("min_cgpa", "Min CGPA", 70, "center"),
        ("package", "Package", 90, "center"),
        ("link", "Application Link", 200, "w"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app, "Jobs & Openings",
                         "Add job openings with their requirements. Minimum CGPA is set per job.")

    # ---- form ------------------------------------------------------------
    def build_form(self, form):
        form.add_combo("company", "Company", [])
        form.add_entry("role", "Job Role")
        form.add_entry("skills", "Required Skills (comma separated)")
        form.add_entry("min_cgpa", "Minimum CGPA (0 - 10)")
        form.add_entry("package", "Package (LPA)")
        form.add_entry("apply_link", "Application Link (https://...)")
        form.add_text("description", "Job Description", height=3)

    def on_refresh(self):
        names = [c["name"] for c in self.db.search_companies()]
        self.form.set_values("company", names)

    def read_form(self):
        f = self.form
        company = self.db.get_company_by_name(f.get("company"))
        if company is None:
            raise utils.ValidationError(
                "Please select a company. If the list is empty, add a company on the Companies page first.")
        return {
            "company_id": company["id"],
            "role": utils.clean_text(f.get("role"), "Job role", 2, 80),
            "required_skills": utils.parse_skills(f.get("skills"), required=False),
            "min_cgpa": utils.parse_cgpa(f.get("min_cgpa"), "Minimum CGPA"),
            "package": utils.parse_package(f.get("package")),
            "description": utils.clean_description(f.get("description")),
            "apply_link": utils.clean_url(f.get("apply_link"), "Application link"),
        }

    def record_to_form(self, record_id):
        job = self.db.get_job(record_id)
        if job is None:
            return
        f = self.form
        f.set("company", self.db.company_name(job["company_id"]))
        f.set("role", job["role"])
        f.set("skills", utils.skills_to_text(job["required_skills"]))
        f.set("min_cgpa", job["min_cgpa"])
        f.set("package", job["package"])
        f.set("apply_link", job["apply_link"])
        f.set("description", job["description"])

    # ---- table -----------------------------------------------------------
    def get_rows(self, query):
        return [
            (j["id"], [j["id"], j["company_name"], j["role"],
                       utils.skills_to_text(j["required_skills"]) or "-",
                       f"{j['min_cgpa']:.2f}", utils.format_package(j["package"]),
                       j["apply_link"] or "-"])
            for j in self.db.jobs_with_company(query)
        ]

    def build_extra_buttons(self, bar):
        AppButton(bar, text="Open Application Link", style="Ghost.TButton",
                   command=self.open_link).pack(side="left")

    def open_link(self):
        if self.selected_id is None:
            show_warning("Select a job from the table first.")
            return
        job = self.db.get_job(self.selected_id)
        if not job or not job["apply_link"]:
            show_warning("This job has no application link saved.")
            return
        if not utils.open_url(job["apply_link"]):
            show_warning("Could not open the default web browser.")

    # ---- database actions -----------------------------------------------
    def add_record(self, data):
        self.db.add_job(data)

    def update_record(self, record_id, data):
        self.db.update_job(record_id, data)

    def delete_prompt(self, record_id):
        job = self.db.get_job(record_id)
        count = self.db.count_job_applications(record_id)
        text = f"Delete the job {job['role']} at {self.db.company_name(job['company_id'])}?"
        if count:
            text += f"\n\nThis will also delete {count} application(s) for this job."
        return text

    def delete_record(self, record_id):
        removed = self.db.delete_job(record_id)
        return f"{removed} related application(s) were removed." if removed else ""
