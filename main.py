"""Entry point of the Student Placement Management System.

Run with:   python main.py
"""
import sys
import tkinter as tk
import traceback
from tkinter import messagebox, ttk

import config
import graphics
from applications import ApplicationsPage
from companies import CompaniesPage
from config import px
from dashboard import DashboardPage
from database import Database, StorageError
from eligibility import EligibilityPage
from jobs import JobsPage
from students import StudentsPage
from utils import ValidationError
from widgets import (AppButton, NavItem, PasswordDialog, apply_theme, show_error, show_info,
                     show_warning)


def enable_high_dpi():
    """Tell Windows the app handles high-DPI screens itself.
    Without this Windows stretches the window as a bitmap and everything looks blurry."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:  # never stop the program because of a cosmetic setting
        pass


class PlacementApp:
    """Main window: sidebar navigation on the left, one page visible on the right."""

    PAGES = [
        ("Dashboard", "dashboard", DashboardPage),
        ("Students", "students", StudentsPage),
        ("Companies", "companies", CompaniesPage),
        ("Jobs", "jobs", JobsPage),
        ("Eligibility Checker", "eligibility", EligibilityPage),
        ("Applications", "applications", ApplicationsPage),
    ]

    def __init__(self, db):
        self.db = db
        self.is_admin = False
        self.current_page = None

        self.root = tk.Tk()
        config.init_scale(self.root)
        self.root.title(config.APP_TITLE)
        self._set_geometry()
        self.root.report_callback_exception = self.handle_exception
        apply_theme(self.root)
        self.window_icon = graphics.make_logo(px(64), config.NAVY)
        self.root.iconphoto(True, self.window_icon)

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_pages()
        self.show_page("Dashboard")
        self.root.after(250, self._show_startup_warnings)

    def _set_geometry(self):
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width, height = min(px(1360), screen_w - 60), min(px(820), screen_h - 100)
        x, y = (screen_w - width) // 2, max(0, (screen_h - height) // 2 - 20)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(min(px(1120), width), min(px(700), height))

    # ---- layout ------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=px(262))
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.pack_propagate(False)

        brand = ttk.Frame(sidebar, style="Sidebar.TFrame")
        brand.pack(fill="x", padx=px(22), pady=(px(28), px(28)))
        self.logo = graphics.make_logo(px(42), config.NAVY)
        tk.Label(brand, image=self.logo, bg=config.NAVY, bd=0).pack(side="left")
        names = ttk.Frame(brand, style="Sidebar.TFrame")
        names.pack(side="left", padx=(px(12), 0))
        ttk.Label(names, text="Placement Cell", style="SidebarTitle.TLabel").pack(anchor="w")
        ttk.Label(names, text="Management System", style="SidebarMuted.TLabel").pack(anchor="w")

        ttk.Label(sidebar, text="MENU", style="SidebarMuted.TLabel").pack(
            anchor="w", padx=px(26), pady=(0, px(8)))
        self.nav_items = {}
        for name, icon, _page_class in self.PAGES:
            item = NavItem(sidebar, name, icon, command=lambda n=name: self.show_page(n))
            item.pack(fill="x", padx=px(14), pady=px(2))
            self.nav_items[name] = item

        footer = tk.Frame(sidebar, bg=config.NAVY_MID)
        footer.pack(side="bottom", fill="x", padx=px(14), pady=px(18))
        inner = tk.Frame(footer, bg=config.NAVY_MID)
        inner.pack(fill="x", padx=px(14), pady=px(14))
        tk.Label(inner, text="PLACEMENT OFFICER", bg=config.NAVY_MID, fg=config.SIDEBAR_TEXT,
                 font=(config.FONT, 8)).pack(anchor="w")
        self.admin_status = tk.Label(inner, text="", bg=config.NAVY_MID, fg=config.WHITE,
                                     font=(config.FONT_SEMI, 11))
        self.admin_status.pack(anchor="w", pady=(px(2), px(10)))
        self.admin_button = AppButton(inner, text="Admin Login", style="Primary.TButton",
                                      command=self.toggle_admin)
        self.admin_button.pack(fill="x")
        self._update_admin_widgets()

    def _build_pages(self):
        container = ttk.Frame(self.root)
        container.grid(row=0, column=1, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.pages = {}
        for name, _icon, page_class in self.PAGES:
            page = page_class(container, self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page

    # ---- navigation --------------------------------------------------------
    def show_page(self, name):
        page = self.pages[name]
        page.refresh()  # always show fresh data
        page.tkraise()
        self.current_page = name
        for item_name, item in self.nav_items.items():
            item.set_active(item_name == name)

    # ---- admin (placement officer) access ---------------------------------
    def require_admin(self):
        """Return True if admin is unlocked, asking for the password if needed."""
        if self.is_admin:
            return True
        dialog = PasswordDialog(self.root, check=lambda text: text == config.ADMIN_PASSWORD)
        if dialog.result:
            self._set_admin(True)
            return True
        return False

    def toggle_admin(self):
        if self.is_admin:
            self._set_admin(False)
            show_info("Admin locked. Status changes now require the password again.")
        else:
            self.require_admin()

    def _set_admin(self, value):
        self.is_admin = value
        self._update_admin_widgets()
        for page in self.pages.values():
            if hasattr(page, "on_admin_changed"):
                page.on_admin_changed()

    def _update_admin_widgets(self):
        if self.is_admin:
            self.admin_status.config(text="Unlocked", fg="#5FE0AE")
            self.admin_button.config(text="Admin Logout", style="DarkGhost.TButton")
        else:
            self.admin_status.config(text="Locked", fg="#F5C451")
            self.admin_button.config(text="Admin Login", style="Primary.TButton")

    # ---- errors ------------------------------------------------------------
    def _show_startup_warnings(self):
        if self.db.warnings:
            show_warning("\n\n".join(self.db.warnings))

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Called by Tkinter when a button handler fails: show a message, keep running."""
        if issubclass(exc_type, (ValidationError, StorageError)):
            show_error(str(exc_value))
        else:
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            show_error(f"An unexpected error occurred:\n\n{exc_value}")

    def run(self):
        self.root.mainloop()  # the only mainloop in the whole program


def main():
    enable_high_dpi()  # must happen before the first window is created
    try:
        db = Database()
    except StorageError as err:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Cannot start", str(err))
        root.destroy()
        return
    PlacementApp(db).run()


if __name__ == "__main__":
    main()
