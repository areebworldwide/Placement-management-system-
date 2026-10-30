"""Dashboard screen: summary cards, status overview, shortcuts and recent applications."""
from tkinter import ttk

import config
from config import px
from widgets import AppButton, Card, DataTable, IconBadge, PageFrame, ProgressBar


class StatCard(Card):
    """Summary card: caption and icon on top, big number below, small note at the bottom."""

    def __init__(self, parent, caption, icon, accent):
        super().__init__(parent, padding=20)
        top = ttk.Frame(self.inner, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=caption, style="CardMuted.TLabel").pack(side="left", anchor="n")
        IconBadge(top, icon, accent, size=40).pack(side="right")
        self.value_label = ttk.Label(self.inner, text="0", style="StatValue.TLabel")
        self.value_label.pack(anchor="w", pady=(px(2), 0))
        self.note_label = ttk.Label(self.inner, text=" ", style="CardMuted.TLabel")
        self.note_label.pack(anchor="w")

    def set(self, value, note=" "):
        self.value_label.config(text=str(value))
        self.note_label.config(text=note)


class DashboardPage(PageFrame):
    CARD_SPECS = [
        ("students", "Registered Students", "students", config.NAVY_LIGHT),
        ("companies", "Companies", "companies", config.BLUE),
        ("applications", "Job Applications", "applications", config.AMBER),
        ("placed", "Placed Students", "eligibility", config.GREEN),
    ]
    SHORTCUTS = ["Students", "Companies", "Jobs", "Eligibility Checker", "Applications"]

    def __init__(self, parent, app):
        super().__init__(parent, app, "Dashboard", "A quick summary of placement activity.")
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(1, weight=1)
        self._build_cards()
        self._build_recent()
        self._build_side_panel()

    def _build_cards(self):
        row = ttk.Frame(self.body)
        row.grid(row=0, column=0, columnspan=2, sticky="ew")
        row.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        self.cards = {}
        gap = px(9)
        for column, (key, caption, icon, accent) in enumerate(self.CARD_SPECS):
            card = StatCard(row, caption, icon, accent)
            card.grid(row=0, column=column, sticky="ew",
                      padx=(0 if column == 0 else gap, 0 if column == 3 else gap))
            self.cards[key] = card

    def _build_recent(self):
        card = Card(self.body, padding=20)
        card.grid(row=1, column=0, sticky="nsew", pady=(px(20), 0), padx=(0, px(20)))
        ttk.Label(card.inner, text="Recent Applications", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, px(12)))
        self.recent_table = DataTable(card.inner, [
            ("student", "Student", 140, "w"),
            ("company", "Company", 150, "w"),
            ("role", "Job Role", 140, "w"),
            ("applied", "Applied On", 95, "center"),
            ("status", "Status", 95, "center"),
        ])
        self.recent_table.pack(fill="both", expand=True)

    def _build_side_panel(self):
        side = ttk.Frame(self.body, width=px(310))
        side.grid(row=1, column=1, sticky="ns", pady=(px(20), 0))

        status_card = Card(side, padding=20)
        status_card.pack(fill="x")
        ttk.Label(status_card.inner, text="Application Status", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, px(12)))
        self.status_labels, self.status_bars = {}, {}
        for status in config.STATUSES:
            block = ttk.Frame(status_card.inner, style="Card.TFrame")
            block.pack(fill="x", pady=px(5))
            line = ttk.Frame(block, style="Card.TFrame")
            line.pack(fill="x", pady=(0, px(5)))
            ttk.Label(line, text=status, style="Card.TLabel").pack(side="left")
            value = ttk.Label(line, text="0", style="CardTitle.TLabel")
            value.pack(side="right")
            bar = ProgressBar(block, config.STATUS_COLORS[status])
            bar.pack(fill="x")
            self.status_labels[status] = value
            self.status_bars[status] = bar

        nav_card = Card(side, padding=20)
        nav_card.pack(fill="x", pady=(px(20), 0))
        ttk.Label(nav_card.inner, text="Quick Navigation", style="CardTitle.TLabel").pack(
            anchor="w", pady=(0, px(10)))
        grid = ttk.Frame(nav_card.inner, style="Card.TFrame")
        grid.pack(fill="x")
        grid.columnconfigure((0, 1), weight=1, uniform="nav")
        for index, name in enumerate(self.SHORTCUTS):
            last = index == len(self.SHORTCUTS) - 1 and index % 2 == 0
            AppButton(grid, text=name, style="Ghost.TButton",
                      command=lambda n=name: self.app.show_page(n)).grid(
                row=index // 2, column=0 if last else index % 2, columnspan=2 if last else 1,
                sticky="ew", padx=px(3), pady=px(3))

    def refresh(self):
        stats = self.db.stats()
        self.cards["students"].set(stats["students"], "Registered in the system")
        self.cards["companies"].set(stats["companies"], f"{stats['jobs']} job opening(s)")
        self.cards["applications"].set(stats["applications"], "Across all companies")
        self.cards["placed"].set(stats["placed"], f"Placement rate: {stats['placement_rate']:.1f}%")
        total = stats["applications"] or 1
        for status, label in self.status_labels.items():
            count = stats["by_status"].get(status, 0)
            label.config(text=str(count))
            self.status_bars[status].set(count / total)

        recent = self.db.search_applications()[:8]
        self.recent_table.set_rows([
            (r["id"], [r["student_name"], r["company_name"], r["job_role"],
                       r["application_date"], r["status"]], r["status"])
            for r in recent
        ], "No applications yet.")
