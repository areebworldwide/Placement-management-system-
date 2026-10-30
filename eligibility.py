"""Eligibility rules and the Eligibility Checker screen.

Rules (both must be true):
  1. student CGPA >= the job's minimum CGPA
  2. the student has EVERY skill the job requires (case-insensitive)
"""
from tkinter import ttk

import config
import utils
from utils import ValidationError
from config import px
from widgets import (AppButton, Card, DataTable, PageFrame, ResultBadge, confirm, show_info,
                     show_warning)


# ====================================================================== logic
def check_eligibility(student, job):
    """Compare a student with a job. Returns a dictionary:

    eligible, cgpa_ok, skills_ok, matched, missing, details (list of sentences),
    summary (one short sentence for tables).
    """
    cgpa_ok = student["cgpa"] >= job["min_cgpa"]
    owned = {skill.lower() for skill in student["skills"]}
    matched = [s for s in job["required_skills"] if s.lower() in owned]
    missing = [s for s in job["required_skills"] if s.lower() not in owned]
    skills_ok = not missing

    details, short = [], []
    if cgpa_ok:
        details.append(f"CGPA OK: student has {student['cgpa']:.2f}, job needs at least {job['min_cgpa']:.2f}.")
    else:
        details.append(f"CGPA too low: student has {student['cgpa']:.2f}, job needs at least {job['min_cgpa']:.2f}.")
        short.append(f"CGPA {student['cgpa']:.2f} < {job['min_cgpa']:.2f}")

    if not job["required_skills"]:
        details.append("Skills OK: this job does not list any required skills.")
    elif skills_ok:
        details.append(f"Skills OK: student has all required skills ({', '.join(matched)}).")
    else:
        details.append(f"Missing skills: {', '.join(missing)}.")
        if matched:
            details.append(f"Matched skills: {', '.join(matched)}.")
        short.append("Missing: " + ", ".join(missing))

    eligible = cgpa_ok and skills_ok
    return {
        "eligible": eligible,
        "cgpa_ok": cgpa_ok,
        "skills_ok": skills_ok,
        "matched": matched,
        "missing": missing,
        "details": details,
        "summary": "Meets all requirements" if eligible else "; ".join(short),
    }


def submit_application(db, student_id, job_id):
    """Create an application after checking eligibility and duplicates.
    Raises ValidationError with a readable reason if the student cannot apply."""
    student = db.get_student(student_id)
    job = db.get_job(job_id)
    if student is None or job is None:
        raise ValidationError("Please choose a valid student and job.")
    result = check_eligibility(student, job)
    if not result["eligible"]:
        raise ValidationError(
            f"{student['name']} is not eligible for this job.\n\n" + "\n".join(result["details"]))
    return db.add_application(student_id, job_id)


def offer_to_open_link(db, job_id, parent=None):
    """After applying, offer to open the company's application page in the browser."""
    job = db.get_job(job_id)
    if job and job["apply_link"]:
        if confirm("Do you want to open the company's application page in your browser now?",
                   parent=parent, yes_text="Open Page", no_text="Not now"):
            if not utils.open_url(job["apply_link"]):
                show_warning("Could not open the default web browser.", parent=parent)


# ====================================================================== page
class EligibilityPage(PageFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Eligibility Checker",
                         "Check whether a student meets a job's CGPA and skill requirements.")
        self.student_ids = {}
        self.job_ids = {}
        self._build_picker()
        self._build_result()
        self._build_table()

    # ---- layout ------------------------------------------------------------
    def _build_picker(self):
        card = Card(self.body)
        card.pack(fill="x")
        box = card.inner
        box.columnconfigure((0, 1), weight=1, uniform="pick")
        ttk.Label(box, text="STUDENT", style="Field.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(box, text="JOB", style="Field.TLabel").grid(row=0, column=1, sticky="w")
        self.student_combo = ttk.Combobox(box, state="readonly")
        self.student_combo.grid(row=1, column=0, sticky="ew", padx=(0, px(14)), pady=(px(2), px(14)))
        self.job_combo = ttk.Combobox(box, state="readonly")
        self.job_combo.grid(row=1, column=1, sticky="ew", pady=(px(2), px(14)))
        buttons = ttk.Frame(box, style="Card.TFrame")
        buttons.grid(row=2, column=0, columnspan=2, sticky="w")
        AppButton(buttons, text="Check Eligibility", style="Primary.TButton",
                   command=self.on_check).pack(side="left", padx=(0, 8))
        AppButton(buttons, text="Check All Jobs for Student", style="Secondary.TButton",
                   command=self.on_check_all).pack(side="left")

    def _build_result(self):
        card = Card(self.body)
        card.pack(fill="x", pady=px(16))
        box = card.inner
        self.badge = ResultBadge(box)
        self.badge.pack(side="left", anchor="n", padx=(0, px(20)))
        right = ttk.Frame(box, style="Card.TFrame")
        right.pack(side="left", fill="x", expand=True)
        self.result_title = ttk.Label(right, text="No check performed yet", style="DialogTitle.TLabel")
        self.result_title.pack(anchor="w")
        self.result_text = ttk.Label(right, text="Choose a student and a job, then click Check Eligibility.",
                                     style="Card.TLabel", justify="left", wraplength=px(820))
        self.result_text.pack(anchor="w", pady=(px(4), px(12)))
        buttons = ttk.Frame(right, style="Card.TFrame")
        buttons.pack(anchor="w")
        AppButton(buttons, text="Apply for this Job", style="Primary.TButton",
                  command=self.on_apply).pack(side="left", padx=(0, px(10)))
        AppButton(buttons, text="Open Application Link", style="Ghost.TButton",
                  command=self.on_open_link).pack(side="left")

    def _build_table(self):
        card = Card(self.body)
        card.pack(fill="both", expand=True)
        ttk.Label(card.inner, text="Eligibility for all jobs", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, px(12)))
        self.table = DataTable(card.inner, [
            ("company", "Company", 130, "w"),
            ("role", "Job Role", 150, "w"),
            ("min_cgpa", "Min CGPA", 75, "center"),
            ("skills", "Required Skills", 190, "w"),
            ("result", "Result", 100, "center"),
            ("reason", "Reason", 260, "w"),
        ], height=6)
        self.table.pack(fill="both", expand=True)
        self.table.set_rows([], "Select a student and click 'Check All Jobs for Student'.")

    # ---- data --------------------------------------------------------------
    def refresh(self):
        self._load_combo(self.student_combo, self.student_ids, self.db.student_choices())
        self._load_combo(self.job_combo, self.job_ids, self.db.job_choices())

    @staticmethod
    def _load_combo(combo, mapping, choices):
        current = combo.get()
        mapping.clear()
        mapping.update(dict(choices))
        combo["values"] = [label for label, _ in choices]
        if current not in mapping:
            combo.set("")

    def _selected_student(self):
        student_id = self.student_ids.get(self.student_combo.get())
        if student_id is None:
            show_warning("Please select a student first.")
            return None
        return self.db.get_student(student_id)

    def _selected_job(self):
        job_id = self.job_ids.get(self.job_combo.get())
        if job_id is None:
            show_warning("Please select a job first.")
            return None
        return self.db.get_job(job_id)

    # ---- actions -----------------------------------------------------------
    def on_check(self):
        student = self._selected_student()
        if student is None:
            return
        job = self._selected_job()
        if job is None:
            return
        result = check_eligibility(student, job)
        company = self.db.company_name(job["company_id"])
        if result["eligible"]:
            self.result_title.config(text="ELIGIBLE", foreground=config.GREEN)
            self.badge.show("ok")
        else:
            self.result_title.config(text="NOT ELIGIBLE", foreground=config.RED)
            self.badge.show("bad")
        header = f"{student['name']} ({student['roll_no']})  ->  {job['role']} at {company}\n"
        self.result_text.config(text=header + "\n".join(result["details"]))

    def on_check_all(self):
        student = self._selected_student()
        if student is None:
            return
        rows = []
        for job in self.db.jobs_with_company():
            result = check_eligibility(student, job)
            rows.append((job["id"], [
                job["company_name"], job["role"], f"{job['min_cgpa']:.2f}",
                utils.skills_to_text(job["required_skills"]) or "-",
                "Eligible" if result["eligible"] else "Not eligible", result["summary"],
            ], "ok" if result["eligible"] else "bad"))
        self.table.set_rows(rows, "No jobs have been added yet. Add jobs on the Jobs page.")

    def on_apply(self):
        student = self._selected_student()
        if student is None:
            return
        job = self._selected_job()
        if job is None:
            return
        try:
            submit_application(self.db, student["id"], job["id"])
        except ValidationError as err:
            show_warning(str(err))
            return
        show_info(f"Application submitted for {job['role']} at "
                  f"{self.db.company_name(job['company_id'])}.\nStatus: {config.DEFAULT_STATUS}")
        offer_to_open_link(self.db, job["id"])

    def on_open_link(self):
        job = self._selected_job()
        if job is None:
            return
        if not job["apply_link"]:
            show_warning("This job has no application link saved.")
        elif not utils.open_url(job["apply_link"]):
            show_warning("Could not open the default web browser.")
