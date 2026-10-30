"""Company management screen (add / view / search / edit / delete companies)."""
import utils
from widgets import AppButton, CrudPage, show_warning


class CompaniesPage(CrudPage):
    entity = "company"
    entity_plural = "companies"
    columns = [
        ("id", "ID", 45, "center"),
        ("name", "Company", 160, "w"),
        ("industry", "Industry", 130, "w"),
        ("location", "Location", 120, "w"),
        ("website", "Website", 190, "w"),
        ("email", "HR Email", 180, "w"),
        ("jobs", "Jobs", 55, "center"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, app, "Companies",
                         "Keep a list of recruiting companies. Add their job openings on the Jobs page.")

    # ---- form ------------------------------------------------------------
    def build_form(self, form):
        form.add_entry("name", "Company Name")
        form.add_entry("industry", "Industry")
        form.add_entry("location", "Location")
        form.add_entry("website", "Website (https://...)")
        form.add_entry("contact_email", "HR Contact Email (optional)")

    def read_form(self):
        f = self.form
        return {
            "name": utils.clean_text(f.get("name"), "Company name", 2, 80),
            "industry": utils.clean_text(f.get("industry"), "Industry", 2, 60),
            "location": utils.clean_text(f.get("location"), "Location", 2, 60),
            "website": utils.clean_url(f.get("website"), "Website"),
            "contact_email": utils.clean_email(f.get("contact_email"), required=False),
        }

    def record_to_form(self, record_id):
        company = self.db.get_company(record_id)
        if company is None:
            return
        for key in ("name", "industry", "location", "website", "contact_email"):
            self.form.set(key, company[key])

    # ---- table -----------------------------------------------------------
    def get_rows(self, query):
        return [
            (c["id"], [c["id"], c["name"], c["industry"], c["location"], c["website"] or "-",
                       c["contact_email"] or "-", self.db.count_company_jobs(c["id"])])
            for c in self.db.search_companies(query)
        ]

    def build_extra_buttons(self, bar):
        AppButton(bar, text="Open Company Website", style="Ghost.TButton",
                   command=self.open_website).pack(side="left")

    def open_website(self):
        if self.selected_id is None:
            show_warning("Select a company from the table first.")
            return
        company = self.db.get_company(self.selected_id)
        if not company or not company["website"]:
            show_warning("This company has no website saved.")
            return
        if not utils.open_url(company["website"]):
            show_warning("Could not open the default web browser.")

    # ---- database actions -----------------------------------------------
    def add_record(self, data):
        self.db.add_company(data)

    def update_record(self, record_id, data):
        self.db.update_company(record_id, data)

    def delete_prompt(self, record_id):
        company = self.db.get_company(record_id)
        jobs, apps = self.db.company_dependents(record_id)
        text = f"Delete {company['name']}?"
        if jobs or apps:
            text += (f"\n\nThis will also delete {jobs} job(s) and "
                     f"{apps} application(s) linked to this company.")
        return text

    def delete_record(self, record_id):
        jobs, apps = self.db.delete_company(record_id)
        if jobs or apps:
            return f"{jobs} job(s) and {apps} application(s) were removed."
        return ""
