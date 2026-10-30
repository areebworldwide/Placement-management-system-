"""Job applications screen: apply, history, filtering and placement status updates."""
import tkinter as tk
from tkinter import ttk

import config
import utils
from eligibility import offer_to_open_link, submit_application
from utils import ValidationError
from config import px
from widgets import (AppButton, AppEntry, Card, DataTable, ModalDialog, PageFrame, confirm,
                     show_info, show_warning)

TABLE_COLUMNS = [
    ("id", "App ID", 55, "center"),
    ("student", "Student", 140, "w"),
    ("roll_no", "Roll No", 90, "w"),
    ("company", "Company", 150, "w"),
    ("role", "Job Role", 140, "w"),
    ("package", "Package", 90, "center"),
    ("applied", "Applied On", 90, "center"),
    ("status", "Status", 90, "center"),
    ("joining", "Joining Date", 105, "center"),
]


def application_row(app):
    """Convert an application record into a table row (id, values, colour tag)."""
    return (app["id"], [
        app["id"], app["student_name"], app["roll_no"], app["company_name"], app["job_role"],
        utils.format_package(app["package"]), app["application_date"], app["status"],
        app["joining_date"] or "-",
    ], app["status"])


# ====================================================================== dialogs
class StatusDialog(ModalDialog):
    """Modal window to choose a new status (and joining date when Selected).
    After it closes, ``self.result`` is (status, joining_date) or None if cancelled."""

    def __init__(self, parent, application):
        super().__init__(parent, "Update Application Status")
        self.application = application
        frame = self.body
        ttk.Label(frame, text=f"{application['company_name']} - {application['job_role']}",
                  style="DialogTitle.TLabel").pack(anchor="w")
        ttk.Label(frame, text=f"Applied on {application['application_date']}",
                  style="CardMuted.TLabel").pack(anchor="w", pady=(0, px(16)))

        ttk.Label(frame, text="STATUS", style="Field.TLabel").pack(anchor="w", pady=(0, px(3)))
        self.status_combo = ttk.Combobox(frame, values=config.STATUSES, state="readonly", width=34)
        self.status_combo.set(application["status"])
        self.status_combo.pack(fill="x", pady=(0, px(12)))
        self.status_combo.bind("<<ComboboxSelected>>", lambda _e: self._toggle_date())

        ttk.Label(frame, text="JOINING DATE  (YYYY-MM-DD, required when Selected)",
                  style="Field.TLabel").pack(anchor="w", pady=(0, px(3)))
        self.date_entry = AppEntry(frame, width=34)
        self.date_entry.insert(0, application["joining_date"])
        self.date_entry.pack(fill="x", pady=(0, px(20)))
        self._toggle_date()

        buttons = ttk.Frame(frame, style="Card.TFrame")
        buttons.pack(fill="x")
        AppButton(buttons, text="Save Status", style="Primary.TButton",
                  command=self.on_save).pack(side="right")
        AppButton(buttons, text="Cancel", style="Ghost.TButton",
                  command=self.cancel).pack(side="right", padx=(0, px(10)))
        self.run()

    def _toggle_date(self):
        self.date_entry.config(state="normal" if self.status_combo.get() == "Selected" else "disabled")

    def on_save(self):
        status = self.status_combo.get()
        joining = ""
        try:
            if status == "Selected":
                joining = utils.clean_date(self.date_entry.get(), "Joining date")
                if joining < self.application["application_date"]:
                    raise ValidationError("Joining date cannot be before the application date.")
        except ValidationError as err:
            show_warning(str(err), parent=self)
            return
        self.finish((status, joining))


class HistoryWindow(tk.Toplevel):
    """Shows every application of one student."""

    def __init__(self, parent, student, rows):
        super().__init__(parent)
        self.title(f"Application History - {student['name']}")
        self.configure(bg=config.BG)
        self.geometry(f"{px(820)}x{px(420)}")
        box = ttk.Frame(self, padding=px(22))
        box.pack(fill="both", expand=True)
        ttk.Label(box, text=f"{student['name']} ({student['roll_no']})",
                  style="Title.TLabel", font=(config.FONT_SEMI, 16)).pack(anchor="w", pady=(0, px(12)))
        card = Card(box, padding=14)
        card.pack(fill="both", expand=True)
        table = DataTable(card.inner, [
            ("company", "Company", 130, "w"),
            ("role", "Job Role", 150, "w"),
            ("package", "Package", 90, "center"),
            ("applied", "Applied On", 90, "center"),
            ("status", "Status", 90, "center"),
            ("joining", "Joining Date", 90, "center"),
        ])
        table.pack(fill="both", expand=True)
        table.set_rows([
            (r["id"], [r["company_name"], r["job_role"], utils.format_package(r["package"]),
                       r["application_date"], r["status"], r["joining_date"] or "-"], r["status"])
            for r in rows
        ], "This student has not applied for any job yet.")


# ====================================================================== page
class ApplicationsPage(PageFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Job Applications",
                         "Apply for jobs, review application history and update placement status.")
        self.student_ids = {}
        self.job_ids = {}
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)
        self._build_apply_card()
        self._build_table_card()

    # ---- layout ------------------------------------------------------------
    def _build_apply_card(self):
        card = Card(self.body)
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        box = card.inner
        box.columnconfigure((0, 1), weight=1, uniform="apply")
        ttk.Label(box, text="New Application", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8))
        ttk.Label(box, text="STUDENT", style="Field.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Label(box, text="JOB", style="Field.TLabel").grid(row=1, column=1, sticky="w")
        self.student_combo = ttk.Combobox(box, state="readonly")
        self.student_combo.grid(row=2, column=0, sticky="ew", padx=(0, 12), pady=(2, 0))
        self.job_combo = ttk.Combobox(box, state="readonly")
        self.job_combo.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=(2, 0))
        AppButton(box, text="Apply", style="Primary.TButton", command=self.on_apply).grid(
            row=2, column=2, padx=(0, 8))
        AppButton(box, text="Open Job Link", style="Ghost.TButton", command=self.on_open_job_link).grid(
            row=2, column=3)

    def _build_table_card(self):
        card = Card(self.body)
        card.grid(row=1, column=0, sticky="nsew")
        box = card.inner

        top = ttk.Frame(box, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="SEARCH", style="Field.TLabel").pack(side="left", padx=(0, px(10)))
        self.search_var = tk.StringVar()
        AppEntry(top, textvariable=self.search_var, width=28).pack(side="left")
        ttk.Label(top, text="STATUS", style="Field.TLabel").pack(side="left", padx=(px(18), px(10)))
        self.status_filter = ttk.Combobox(top, values=["All"] + config.STATUSES,
                                          state="readonly", width=14)
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=(0, px(10)))
        AppButton(top, text="Clear", style="Ghost.TButton", command=self.clear_filters).pack(side="left")
        self.count_label = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="right")
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        self.status_filter.bind("<<ComboboxSelected>>", lambda _e: self.refresh_table())

        self.table = DataTable(box, TABLE_COLUMNS)
        self.table.pack(fill="both", expand=True)

        actions = ttk.Frame(box, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        AppButton(actions, text="Update Status", style="Primary.TButton",
                   command=self.on_update_status).pack(side="left", padx=(0, 8))
        AppButton(actions, text="Delete Application", style="Danger.TButton",
                   command=self.on_delete).pack(side="left", padx=(0, 8))
        AppButton(actions, text="Open Application Link", style="Ghost.TButton",
                   command=self.on_open_selected_link).pack(side="left", padx=(0, 8))
        AppButton(actions, text="Student History", style="Ghost.TButton",
                   command=self.on_history).pack(side="left")
        self.admin_label = ttk.Label(actions, text="", style="CardMuted.TLabel")
        self.admin_label.pack(side="right")

    # ---- data --------------------------------------------------------------
    def refresh(self):
        for combo, mapping, choices in (
            (self.student_combo, self.student_ids, self.db.student_choices()),
            (self.job_combo, self.job_ids, self.db.job_choices()),
        ):
            current = combo.get()
            mapping.clear()
            mapping.update(dict(choices))
            combo["values"] = [label for label, _ in choices]
            if current not in mapping:
                combo.set("")
        self.refresh_table()
        self.on_admin_changed()

    def refresh_table(self):
        query = self.search_var.get().strip()
        status = self.status_filter.get() or "All"
        rows = self.db.search_applications(query, status)
        if query or status != "All":
            message = "No applications match your search or filter."
        else:
            message = "No applications yet.\nChoose a student and a job above, then click Apply."
        self.table.set_rows([application_row(r) for r in rows], message)
        self.count_label.config(text=f"{len(rows)} application(s)")

    def clear_filters(self):
        self.search_var.set("")
        self.status_filter.set("All")
        self.refresh_table()

    def on_admin_changed(self):
        if self.app.is_admin:
            self.admin_label.config(text="Admin unlocked: status changes allowed")
        else:
            self.admin_label.config(text="Status changes need admin login (sidebar)")

    # ---- actions -----------------------------------------------------------
    def on_apply(self):
        student_id = self.student_ids.get(self.student_combo.get())
        job_id = self.job_ids.get(self.job_combo.get())
        if student_id is None or job_id is None:
            show_warning("Please select both a student and a job.")
            return
        try:
            application = submit_application(self.db, student_id, job_id)
        except ValidationError as err:
            show_warning(str(err))
            return
        self.refresh_table()
        show_info(f"Application submitted for {application['job_role']} at "
                  f"{application['company_name']}.\nStatus: {application['status']}")
        offer_to_open_link(self.db, job_id)

    def on_open_job_link(self):
        job_id = self.job_ids.get(self.job_combo.get())
        if job_id is None:
            show_warning("Please select a job first.")
            return
        self._open_link(self.db.get_job(job_id))

    def on_open_selected_link(self):
        application = self._selected_application()
        if application is not None:
            self._open_link(self.db.get_job(application["job_id"]))

    @staticmethod
    def _open_link(job):
        if not job or not job["apply_link"]:
            show_warning("This job has no application link saved.")
        elif not utils.open_url(job["apply_link"]):
            show_warning("Could not open the default web browser.")

    def _selected_application(self):
        application_id = self.table.selected_id()
        if application_id is None:
            show_warning("Select an application from the table first.")
            return None
        return self.db.get_application(application_id)

    def on_update_status(self):
        application = self._selected_application()
        if application is None or not self.app.require_admin():
            return
        dialog = StatusDialog(self, application)
        if dialog.result is None:
            return
        status, joining = dialog.result
        try:
            self.db.set_application_status(application["id"], status, joining)
        except ValidationError as err:
            show_warning(str(err))
            return
        self.refresh_table()
        show_info(f"Status updated to {status}.")

    def on_delete(self):
        application = self._selected_application()
        if application is None or not self.app.require_admin():
            return
        if not confirm(f"Delete the application for {application['job_role']} at "
                       f"{application['company_name']}?", yes_text="Delete", no_text="Cancel",
                       danger=True):
            return
        self.db.delete_application(application["id"])
        self.refresh_table()
        show_info("Application deleted.")

    def on_history(self):
        application = self._selected_application()
        if application is None:
            return
        student = self.db.get_student(application["student_id"])
        HistoryWindow(self, student, self.db.student_applications(student["id"]))
