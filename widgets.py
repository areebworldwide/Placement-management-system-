"""Reusable Tkinter building blocks with a polished, modern look.

* apply_theme        - colours, fonts and ttk styles for the whole application
* AppButton / NavItem / AppEntry - custom-drawn controls (rounded, hover effects)
* MessageDialog / PasswordDialog / ModalDialog - themed pop-up windows
* show_* / confirm   - convenience functions that open a MessageDialog
* Card, PageFrame, Form, DataTable, CrudPage - layout building blocks
"""
import tkinter as tk
from datetime import datetime
from tkinter import font as tkfont
from tkinter import ttk

import config
import graphics
from config import px
from utils import ValidationError


def widget_bg(widget):
    """Background colour of any (tk or ttk) widget, so shapes blend in perfectly."""
    try:
        return graphics.to_hex(widget.cget("background"))
    except tk.TclError:
        style = ttk.Style(widget)
        name = str(widget.cget("style")) or widget.winfo_class()
        return graphics.to_hex(style.lookup(name, "background") or config.BG)


# ====================================================================== theme
def apply_theme(root):
    """Create every ttk style used by the application."""
    style = ttk.Style(root)
    style.theme_use("clam")
    F, FS = config.FONT, config.FONT_SEMI
    root.configure(bg=config.BG)
    root.option_add("*TCombobox*Listbox.font", (F, 10))
    root.option_add("*TCombobox*Listbox.background", config.WHITE)
    root.option_add("*TCombobox*Listbox.foreground", config.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", config.ROW_SELECT)
    root.option_add("*TCombobox*Listbox.selectForeground", config.NAVY)

    style.configure(".", font=(F, 10), background=config.BG, foreground=config.TEXT)
    style.configure("TFrame", background=config.BG)
    style.configure("Card.TFrame", background=config.WHITE)
    style.configure("Sidebar.TFrame", background=config.NAVY)

    # ---- labels
    style.configure("TLabel", background=config.BG, foreground=config.TEXT)
    style.configure("Title.TLabel", font=(FS, 22), foreground=config.NAVY)
    style.configure("Subtitle.TLabel", foreground=config.MUTED)
    style.configure("Date.TLabel", foreground=config.MUTED, font=(F, 10))
    style.configure("Card.TLabel", background=config.WHITE)
    style.configure("Field.TLabel", background=config.WHITE, foreground=config.LABEL, font=(FS, 9))
    style.configure("CardTitle.TLabel", background=config.WHITE, foreground=config.NAVY,
                    font=(FS, 12))
    style.configure("DialogTitle.TLabel", background=config.WHITE, foreground=config.NAVY,
                    font=(FS, 14))
    style.configure("CardMuted.TLabel", background=config.WHITE, foreground=config.MUTED)
    style.configure("Error.TLabel", background=config.WHITE, foreground=config.RED_DARK,
                    font=(F, 9))
    style.configure("Empty.TLabel", background=config.WHITE, foreground=config.MUTED,
                    font=(F, 11), justify="center")
    style.configure("Sidebar.TLabel", background=config.NAVY, foreground=config.WHITE)
    style.configure("SidebarTitle.TLabel", background=config.NAVY, foreground=config.WHITE,
                    font=(FS, 14))
    style.configure("SidebarMuted.TLabel", background=config.NAVY, foreground=config.SIDEBAR_TEXT,
                    font=(F, 9))
    style.configure("StatValue.TLabel", background=config.WHITE, foreground=config.NAVY,
                    font=(FS, 28))

    # ---- combobox
    style.configure("TCombobox", fieldbackground=config.WHITE, background=config.WHITE,
                    foreground=config.TEXT, padding=px(5), arrowsize=px(18), relief="flat",
                    arrowcolor=config.MUTED, bordercolor=config.BORDER_STRONG,
                    lightcolor=config.BORDER_STRONG, darkcolor=config.BORDER_STRONG)
    style.map("TCombobox",
              fieldbackground=[("readonly", config.WHITE), ("disabled", "#EEF2F6")],
              selectbackground=[("readonly", config.WHITE)],
              selectforeground=[("readonly", config.TEXT)],
              bordercolor=[("focus", config.GREEN)],
              lightcolor=[("focus", config.GREEN)], darkcolor=[("focus", config.GREEN)],
              background=[("active", config.WHITE), ("pressed", config.WHITE),
                          ("readonly", config.WHITE), ("disabled", "#EEF2F6")],
              arrowcolor=[("active", config.NAVY)])

    # ---- tables
    style.configure("Treeview", background=config.WHITE, fieldbackground=config.WHITE,
                    foreground=config.TEXT, rowheight=px(36), borderwidth=0, font=(F, 10))
    style.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])  # removes the border
    style.map("Treeview", background=[("selected", config.ROW_SELECT)],
              foreground=[("selected", config.NAVY)])
    style.configure("Treeview.Heading", background=config.HEADER_BG, foreground=config.LABEL,
                    font=(FS, 9), relief="flat", borderwidth=0, padding=(px(8), px(9)),
                    bordercolor=config.HEADER_BG, lightcolor=config.HEADER_BG,
                    darkcolor=config.HEADER_BG)
    style.map("Treeview.Heading", background=[("active", "#E6ECF3")])

    # ---- thin scrollbars without arrow buttons
    for orient, side in (("Vertical", "ns"), ("Horizontal", "ew")):
        name = f"Modern.{orient}.TScrollbar"
        style.layout(name, [(f"{orient}.Scrollbar.trough", {
            "sticky": side,
            "children": [(f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        style.configure(name, troughcolor=config.WHITE, background="#CBD5E1",
                        bordercolor=config.WHITE, lightcolor="#CBD5E1", darkcolor="#CBD5E1",
                        arrowsize=px(9), gripcount=0, relief="flat")
        style.map(name, background=[("active", "#94A3B8"), ("pressed", "#94A3B8")],
                  lightcolor=[("active", "#94A3B8")], darkcolor=[("active", "#94A3B8")])


# ====================================================================== buttons
BUTTON_VARIANTS = {
    "primary": dict(fill=config.GREEN, hover=config.GREEN_DARK, fg=config.WHITE, border=None),
    "secondary": dict(fill=config.NAVY, hover=config.NAVY_LIGHT, fg=config.WHITE, border=None),
    "danger": dict(fill=config.RED_TINT, hover="#F9D6D8", fg=config.RED_DARK, border=None),
    "dangerfill": dict(fill=config.RED, hover=config.RED_DARK, fg=config.WHITE, border=None),
    "ghost": dict(fill=config.WHITE, hover="#F1F5F9", fg=config.NAVY,
                  border=config.BORDER_STRONG),
    "darkghost": dict(fill=config.NAVY_MID, hover=config.NAVY_LIGHT, fg=config.WHITE,
                      border=config.NAVY_LINE),
}


class AppButton(tk.Canvas):
    """Rounded, anti-aliased button with hover and pressed effects.

    Use it like a normal button:  AppButton(parent, text="Save", style="Primary.TButton",
    command=...). Styles: Primary, Secondary, Danger, DangerFill, Ghost, DarkGhost.
    """

    def __init__(self, parent, text="", command=None, style="Primary.TButton", **kw):
        self._bg = widget_bg(parent)
        self._h = px(40)
        super().__init__(parent, height=self._h, bg=self._bg, highlightthickness=0, bd=0,
                         cursor="hand2", takefocus=1, **kw)
        self._text, self._command = text, command
        self._variant = self._variant_name(style)
        self._state = "normal"
        self._hover = self._pressed = self._focused = False
        self._font = tkfont.Font(family=config.FONT_SEMI, size=10)
        self._fit_width()
        for event, handler in (("<Enter>", self._on_enter), ("<Leave>", self._on_leave),
                               ("<ButtonPress-1>", self._on_press),
                               ("<ButtonRelease-1>", self._on_release),
                               ("<Configure>", lambda _e: self._draw()),
                               ("<FocusIn>", self._on_focus_in), ("<FocusOut>", self._on_focus_out),
                               ("<Return>", lambda _e: self.invoke()),
                               ("<space>", lambda _e: self.invoke())):
            self.bind(event, handler)
        self._draw()

    @staticmethod
    def _variant_name(style):
        name = str(style).split(".")[0].lower()
        return name if name in BUTTON_VARIANTS else "primary"

    def _fit_width(self):
        tk.Canvas.configure(self, width=self._font.measure(self._text) + 2 * px(22))

    def configure(self, cnf=None, **kw):
        if cnf:
            kw.update(cnf)
        if "text" in kw:
            self._text = kw.pop("text")
            self._fit_width()
        if "style" in kw:
            self._variant = self._variant_name(kw.pop("style"))
        if "command" in kw:
            self._command = kw.pop("command")
        if "state" in kw:
            self._state = kw.pop("state")
            tk.Canvas.configure(self, cursor="arrow" if self._state == "disabled" else "hand2")
        if kw:
            tk.Canvas.configure(self, **kw)
        self._draw()

    config = configure

    def invoke(self):
        if self._state != "disabled" and self._command:
            self._command()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 4)
        spec = BUTTON_VARIANTS[self._variant]
        if self._state == "disabled":
            fill, fg, border = "#E8EDF3", "#9AA7B8", None
        else:
            fill = spec["hover"] if (self._hover or self._pressed) else spec["fill"]
            fg, border = spec["fg"], spec["border"]
            if self._focused:
                border = config.GREEN
        graphics.draw_rounded(self, 0, 0, width, self._h, px(8), fill, self._bg, border)
        self.create_text(width / 2, self._h / 2, text=self._text, font=self._font, fill=fg)

    def _on_enter(self, _e):
        self._hover = True
        self._draw()

    def _on_leave(self, _e):
        self._hover = self._pressed = False
        self._draw()

    def _on_press(self, _e):
        self._pressed = True
        self._draw()

    def _on_release(self, event):
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self._h
        if was_pressed and inside:
            self.invoke()

    def _on_focus_in(self, _e):
        self._focused = True
        self._draw()

    def _on_focus_out(self, _e):
        self._focused = False
        self._draw()


class NavItem(tk.Canvas):
    """Sidebar entry with an icon; the active page is highlighted."""

    def __init__(self, parent, text, icon, command):
        self._bg = widget_bg(parent)
        self._h = px(46)
        super().__init__(parent, height=self._h, bg=self._bg, highlightthickness=0, bd=0,
                         cursor="hand2")
        self._text, self._icon, self._command = text, icon, command
        self._active = self._hover = False
        self._font = tkfont.Font(family=config.FONT_SEMI, size=10)
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))
        self.bind("<ButtonRelease-1>", lambda _e: self._command())

    def set_active(self, value):
        self._active = value
        self._draw()

    def _set_hover(self, value):
        self._hover = value
        self._draw()

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 4)
        if self._active:
            graphics.draw_rounded(self, 0, 0, width, self._h, px(10), config.NAVY_LIGHT, self._bg)
            graphics.draw_rounded(self, 0, px(11), px(4), self._h - 2 * px(11), px(2),
                                  config.GREEN, config.NAVY_LIGHT)
            icon_color, text_color = "#5FE0AE", config.WHITE
        elif self._hover:
            graphics.draw_rounded(self, 0, 0, width, self._h, px(10), config.NAVY_MID, self._bg)
            icon_color, text_color = config.WHITE, config.WHITE
        else:
            icon_color, text_color = config.SIDEBAR_TEXT, config.SIDEBAR_TEXT
        graphics.draw_icon(self, self._icon, px(30), self._h / 2, px(20), icon_color)
        self.create_text(px(52), self._h / 2, text=self._text, anchor="w", font=self._font,
                         fill=text_color)


# ====================================================================== inputs
class AppEntry(tk.Frame):
    """Text input with a thin border that turns green while you type."""

    def __init__(self, parent, textvariable=None, width=28, show=""):
        super().__init__(parent, bg=config.BORDER_STRONG, padx=1, pady=1)
        self.entry = tk.Entry(self, textvariable=textvariable, width=width, show=show,
                              relief="flat", bd=0, highlightthickness=0, bg=config.WHITE,
                              fg=config.TEXT, insertbackground=config.NAVY,
                              disabledbackground="#F1F5F9", disabledforeground=config.MUTED,
                              font=(config.FONT, 10), selectbackground=config.ROW_SELECT,
                              selectforeground=config.NAVY)
        self.entry.pack(fill="both", expand=True, ipady=px(7), ipadx=px(4))
        self.entry.bind("<FocusIn>", lambda _e: tk.Frame.configure(self, bg=config.GREEN))
        self.entry.bind("<FocusOut>", lambda _e: tk.Frame.configure(self, bg=config.BORDER_STRONG))

    def get(self):
        return self.entry.get()

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, value):
        self.entry.insert(index, value)

    def focus_set(self):
        self.entry.focus_set()

    def bind(self, sequence=None, func=None, add=None):
        return self.entry.bind(sequence, func, add)

    def configure(self, cnf=None, **kw):
        if "state" in kw:
            self.entry.configure(state=kw.pop("state"))
        if kw or cnf:
            tk.Frame.configure(self, cnf, **kw)

    config = configure

    def cget(self, key):
        return self.entry.cget(key) if key == "state" else tk.Frame.cget(self, key)


# ====================================================================== dialogs
class ModalDialog(tk.Toplevel):
    """Base for pop-up windows: white body, centred over the main window, modal."""

    def __init__(self, parent, title):
        self._owner = parent.winfo_toplevel() if parent is not None else tk._default_root
        super().__init__(self._owner)
        self.withdraw()
        self.title(title)
        self.configure(bg=config.WHITE)
        self.resizable(False, False)
        self.result = None
        self.body = ttk.Frame(self, style="Card.TFrame",
                              padding=(px(26), px(24), px(26), px(20)))
        self.body.pack(fill="both", expand=True)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.bind("<Escape>", lambda _e: self.cancel())

    def cancel(self):
        self.destroy()

    def finish(self, value):
        self.result = value
        self.destroy()

    def run(self):
        """Show the dialog, wait until it is closed, and return ``self.result``."""
        self.update_idletasks()
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        owner = self._owner
        x = owner.winfo_rootx() + (owner.winfo_width() - width) // 2
        y = owner.winfo_rooty() + (owner.winfo_height() - height) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.deiconify()
        self.transient(owner)
        self.wait_visibility()
        self.grab_set()
        self.focus_force()
        self.wait_window(self)
        return self.result


class MessageDialog(ModalDialog):
    """Success / warning / error message, or a confirmation question."""

    KINDS = {
        "info": ("Success", config.GREEN, "check"),
        "warning": ("Warning", config.AMBER, "!"),
        "error": ("Error", config.RED, "x"),
        "question": ("Please Confirm", config.NAVY_LIGHT, "?"),
    }

    def __init__(self, parent, kind, message, yes_text=None, no_text=None, danger=False):
        title, color, glyph = self.KINDS[kind]
        super().__init__(parent, title)
        self.result = False
        row = ttk.Frame(self.body, style="Card.TFrame")
        row.pack(fill="x")
        size = px(54)
        icon = tk.Canvas(row, width=size, height=size, bg=config.WHITE, highlightthickness=0)
        icon.pack(side="left", anchor="n", padx=(0, px(18)))
        graphics.draw_rounded(icon, 0, 0, size, size, size // 2, graphics.tint(color, 0.13),
                              config.WHITE)
        graphics.draw_glyph(icon, glyph, size / 2, size / 2, size * 0.4, color)
        text = ttk.Frame(row, style="Card.TFrame")
        text.pack(side="left", fill="both", expand=True)
        ttk.Label(text, text=title, style="DialogTitle.TLabel").pack(anchor="w")
        ttk.Label(text, text=message, style="Card.TLabel", wraplength=px(360),
                  justify="left").pack(anchor="w", pady=(px(6), 0))

        buttons = ttk.Frame(self.body, style="Card.TFrame")
        buttons.pack(fill="x", pady=(px(22), 0))
        if kind == "question":
            AppButton(buttons, text=yes_text or "Yes",
                      style="DangerFill.TButton" if danger else "Primary.TButton",
                      command=lambda: self.finish(True)).pack(side="right")
            AppButton(buttons, text=no_text or "No", style="Ghost.TButton",
                      command=self.cancel).pack(side="right", padx=(0, px(10)))
        else:
            AppButton(buttons, text="OK", style="Primary.TButton",
                      command=lambda: self.finish(True)).pack(side="right")
        self.bind("<Return>", lambda _e: self.finish(True))
        self.run()

    def cancel(self):
        self.result = False
        self.destroy()


class PasswordDialog(ModalDialog):
    """Asks for the admin password. ``check(password)`` must return True/False.
    ``result`` is True only when the password was accepted."""

    def __init__(self, parent, check, title="Admin Login"):
        super().__init__(parent, title)
        self.result = False
        self._check = check
        row = ttk.Frame(self.body, style="Card.TFrame")
        row.pack(fill="x")
        size = px(54)
        icon = tk.Canvas(row, width=size, height=size, bg=config.WHITE, highlightthickness=0)
        icon.pack(side="left", anchor="n", padx=(0, px(18)))
        graphics.draw_rounded(icon, 0, 0, size, size, size // 2,
                              graphics.tint(config.NAVY_LIGHT, 0.12), config.WHITE)
        graphics.draw_glyph(icon, "lock", size / 2, size / 2, size * 0.38, config.NAVY_LIGHT)
        text = ttk.Frame(row, style="Card.TFrame")
        text.pack(side="left", fill="both", expand=True)
        ttk.Label(text, text="Placement Officer Login", style="DialogTitle.TLabel").pack(anchor="w")
        ttk.Label(text, text="Enter the admin password to change application status.",
                  style="Card.TLabel", wraplength=px(300), justify="left").pack(
            anchor="w", pady=(px(4), px(12)))
        self.entry = AppEntry(text, width=28, show="*")
        self.entry.pack(fill="x")
        self.error = ttk.Label(text, text=" ", style="Error.TLabel")
        self.error.pack(anchor="w", pady=(px(6), 0))

        buttons = ttk.Frame(self.body, style="Card.TFrame")
        buttons.pack(fill="x", pady=(px(14), 0))
        AppButton(buttons, text="Unlock", style="Primary.TButton",
                  command=self.submit).pack(side="right")
        AppButton(buttons, text="Cancel", style="Ghost.TButton",
                  command=self.cancel).pack(side="right", padx=(0, px(10)))
        self.bind("<Return>", lambda _e: self.submit())
        self.after(100, self.entry.focus_set)
        self.run()

    def submit(self):
        if self._check(self.entry.get()):
            self.finish(True)
        else:
            self.error.config(text="Incorrect password. Please try again.")
            self.entry.delete(0, "end")
            self.entry.focus_set()

    def cancel(self):
        self.result = False
        self.destroy()


def show_info(message, parent=None):
    MessageDialog(parent, "info", message)


def show_warning(message, parent=None):
    MessageDialog(parent, "warning", message)


def show_error(message, parent=None):
    MessageDialog(parent, "error", message)


def confirm(message, parent=None, yes_text="Yes", no_text="No", danger=False):
    return MessageDialog(parent, "question", message, yes_text, no_text, danger).result


# ====================================================================== small graphics widgets
class IconBadge(tk.Canvas):
    """Round tinted badge with an icon inside (used on dashboard cards)."""

    def __init__(self, parent, icon, color, size=44):
        size = px(size)
        super().__init__(parent, width=size, height=size, bg=widget_bg(parent),
                         highlightthickness=0, bd=0)
        graphics.draw_rounded(self, 0, 0, size, size, size // 2, graphics.tint(color, 0.13),
                              widget_bg(parent))
        graphics.draw_icon(self, icon, size / 2, size / 2, size * 0.46, color)


class ResultBadge(tk.Canvas):
    """Big round badge for the eligibility result: neutral, eligible or not eligible."""

    STATES = {
        "none": (config.MUTED, "dash"),
        "ok": (config.GREEN, "check"),
        "bad": (config.RED, "cross"),
    }

    def __init__(self, parent, size=60):
        self._size = px(size)
        super().__init__(parent, width=self._size, height=self._size, bg=widget_bg(parent),
                         highlightthickness=0, bd=0)
        self.show("none")

    def show(self, state):
        color, icon = self.STATES[state]
        self.delete("all")
        graphics.draw_rounded(self, 0, 0, self._size, self._size, self._size // 2,
                              graphics.tint(color, 0.14), widget_bg(self.master))
        graphics.draw_icon(self, icon, self._size / 2, self._size / 2, self._size * 0.48, color)


class ProgressBar(tk.Canvas):
    """Thin rounded progress bar (value between 0 and 1)."""

    def __init__(self, parent, color):
        self._height = px(8)
        super().__init__(parent, height=self._height, bg=widget_bg(parent), highlightthickness=0,
                         bd=0)
        self._color, self._value = color, 0.0
        self.bind("<Configure>", lambda _e: self._draw())

    def set(self, value):
        self._value = max(0.0, min(1.0, value))
        self._draw()

    def _draw(self):
        self.delete("all")
        width = self.winfo_width()
        if width < 4:
            return
        bg = widget_bg(self.master)
        radius = self._height // 2
        graphics.draw_rounded(self, 0, 0, width, self._height, radius, "#EBF0F6", bg)
        if self._value > 0:
            filled = max(self._height, int(width * self._value))
            graphics.draw_rounded(self, 0, 0, filled, self._height, radius, self._color, "#EBF0F6")


# ====================================================================== containers
class Card(tk.Frame):
    """White panel with a hairline border and a soft shadow. Put widgets in ``card.inner``."""

    def __init__(self, parent, padding=18):
        super().__init__(parent, bg=config.SHADOW)
        border = tk.Frame(self, bg=config.BORDER)
        border.pack(fill="both", expand=True, pady=(0, 2))
        self.inner = ttk.Frame(border, style="Card.TFrame", padding=px(padding))
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)


class PageFrame(ttk.Frame):
    """Base class for each screen: a title, a subtitle and a ``body`` area."""

    def __init__(self, parent, app, title, subtitle=""):
        super().__init__(parent, padding=(px(30), px(26), px(30), px(24)))
        self.app = app
        self.db = app.db
        header = ttk.Frame(self)
        header.pack(fill="x")
        titles = ttk.Frame(header)
        titles.pack(side="left")
        ttk.Label(titles, text=title, style="Title.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(titles, text=subtitle, style="Subtitle.TLabel").pack(anchor="w")
        ttk.Label(header, text=datetime.now().strftime("%A, %d %B %Y"),
                  style="Date.TLabel").pack(side="right", anchor="n", pady=(px(8), 0))
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True, pady=(px(20), 0))

    def refresh(self):
        """Called every time the page is shown. Reload data from the database here."""


# ====================================================================== form
class Form:
    """Vertical list of labelled fields. Read values with ``get`` and fill with ``set``."""

    def __init__(self, parent):
        self.parent = parent
        self.parent.columnconfigure(0, weight=1)
        self._fields = {}
        self._row = 0

    def _label(self, text):
        ttk.Label(self.parent, text=text, style="Field.TLabel").grid(
            row=self._row, column=0, sticky="w", pady=(0, px(3)))
        self._row += 1

    def _place(self, widget):
        widget.grid(row=self._row, column=0, sticky="ew", pady=(0, px(11)))
        self._row += 1

    def add_entry(self, key, label):
        self._label(label)
        widget = AppEntry(self.parent, width=30)
        self._place(widget)
        self._fields[key] = ("entry", widget)

    def add_combo(self, key, label, values=(), editable=False):
        self._label(label)
        widget = ttk.Combobox(self.parent, values=list(values), width=30,
                              state="normal" if editable else "readonly")
        self._place(widget)
        self._fields[key] = ("combo", widget)

    def add_text(self, key, label, height=3):
        self._label(label)
        frame = tk.Frame(self.parent, bg=config.BORDER_STRONG, padx=1, pady=1)
        widget = tk.Text(frame, height=height, width=30, wrap="word", font=(config.FONT, 10),
                         relief="flat", bd=0, padx=px(8), pady=px(7), highlightthickness=0,
                         bg=config.WHITE, fg=config.TEXT, insertbackground=config.NAVY,
                         selectbackground=config.ROW_SELECT, selectforeground=config.NAVY)
        widget.pack(fill="both", expand=True)
        widget.bind("<FocusIn>", lambda _e: frame.configure(bg=config.GREEN))
        widget.bind("<FocusOut>", lambda _e: frame.configure(bg=config.BORDER_STRONG))
        self._place(frame)
        self._fields[key] = ("text", widget)

    def get(self, key):
        kind, widget = self._fields[key]
        if kind == "text":
            return widget.get("1.0", "end").strip()
        return widget.get().strip()

    def set(self, key, value):
        kind, widget = self._fields[key]
        value = "" if value is None else str(value)
        if kind == "entry":
            widget.delete(0, "end")
            widget.insert(0, value)
        elif kind == "combo":
            widget.set(value)
        else:
            widget.delete("1.0", "end")
            widget.insert("1.0", value)

    def set_values(self, key, values):
        self._fields[key][1]["values"] = list(values)

    def clear(self):
        for key in self._fields:
            self.set(key, "")


# ====================================================================== table
class DataTable(ttk.Frame):
    """A clean Treeview with thin auto-hiding scrollbars, striped rows, click-to-sort
    headings and an empty-state message.

    columns: list of (key, heading, width, anchor)
    rows:    list of (record_id, values_list) or (record_id, values_list, tag)
    """

    def __init__(self, parent, columns, on_select=None, height=10):
        super().__init__(parent, style="Card.TFrame")
        self.keys = [c[0] for c in columns]
        self.on_select = on_select
        self._descending = {}
        self._base_widths = {c[0]: px(c[2]) for c in columns}

        self.tree = ttk.Treeview(self, columns=self.keys, show="headings",
                                 selectmode="browse", height=height)
        for key, heading, width, anchor in columns:
            self.tree.heading(key, text=heading.upper(), anchor=anchor,
                              command=lambda k=key: self.sort_by(k))
            self.tree.column(key, width=px(width), minwidth=px(44), anchor=anchor, stretch=True)

        self.yscroll = ttk.Scrollbar(self, orient="vertical", style="Modern.Vertical.TScrollbar",
                                     command=self.tree.yview)
        self.xscroll = ttk.Scrollbar(self, orient="horizontal",
                                     style="Modern.Horizontal.TScrollbar",
                                     command=self.tree.xview)
        self.tree.configure(yscrollcommand=lambda a, b: self._autohide(self.yscroll, a, b, "ns", 0, 1),
                            xscrollcommand=lambda a, b: self._autohide(self.xscroll, a, b, "ew", 1, 0))
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        for tag, color in (("Applied", config.ROW_INFO), ("Selected", config.ROW_OK),
                           ("ok", config.ROW_OK), ("Rejected", config.ROW_BAD),
                           ("bad", config.ROW_BAD), ("Shortlisted", config.ROW_WARN),
                           ("stripe", config.ROW_STRIPE)):
            self.tree.tag_configure(tag, background=color)

        self.empty_label = ttk.Label(self.tree, text="", style="Empty.TLabel")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Configure>", self._fit_columns)

    def _fit_columns(self, _event=None):
        """Shrink columns a little (never below 72%) so more fits without scrolling."""
        available = self.tree.winfo_width() - px(6)
        total = sum(self._base_widths.values())
        if available < 100 or total <= 0:
            return
        factor = max(0.72, min(1.0, available / total))
        for key, width in self._base_widths.items():
            self.tree.column(key, width=int(width * factor))

    @staticmethod
    def _autohide(bar, first, last, sticky, row, column):
        bar.set(first, last)
        if float(first) <= 0.0 and float(last) >= 1.0:
            bar.grid_remove()
        else:
            bar.grid(row=row, column=column, sticky=sticky)

    def set_rows(self, rows, empty_message="No records found."):
        self.tree.delete(*self.tree.get_children())
        for index, row in enumerate(rows):
            tag = row[2] if len(row) > 2 else ""
            if tag:
                tags = (tag,)
            else:
                tags = ("stripe",) if index % 2 else ()
            self.tree.insert("", "end", iid=str(row[0]), values=row[1], tags=tags)
        if rows:
            self.empty_label.place_forget()
        else:
            self.empty_label.config(text=empty_message)
            self.empty_label.place(relx=0.5, rely=0.38, anchor="center")

    def selected_id(self):
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _on_tree_select(self, _event):
        record_id = self.selected_id()
        if record_id is not None and self.on_select:
            self.on_select(record_id)

    def sort_by(self, key):
        descending = not self._descending.get(key, True)
        self._descending[key] = descending

        def sort_key(item):
            text = item[0]
            try:
                return (0, float(text.split()[0]))
            except (ValueError, IndexError):
                return (1, text.lower())

        items = [(self.tree.set(iid, key), iid) for iid in self.tree.get_children("")]
        items.sort(key=sort_key, reverse=descending)
        for index, (_, iid) in enumerate(items):
            self.tree.move(iid, "", index)
            tags = [t for t in self.tree.item(iid, "tags") if t != "stripe"]
            if not tags and index % 2:
                tags = ["stripe"]
            self.tree.item(iid, tags=tags)


# ====================================================================== CRUD page
class CrudPage(PageFrame):
    """Shared layout for the Students, Companies and Jobs screens.

    Left:  a form with Add / Update / Delete / Clear buttons.
    Right: a search box and a table. Clicking a row loads it into the form.

    Subclasses set ``entity`` / ``entity_plural`` / ``columns`` and implement
    the hook methods listed in the "HOOKS" section below.
    """

    entity = "record"
    entity_plural = "records"
    columns = []

    def __init__(self, parent, app, title, subtitle):
        super().__init__(parent, app, title, subtitle)
        self.selected_id = None
        self.body.columnconfigure(1, weight=1)
        self.body.rowconfigure(0, weight=1)
        self._build_form_card()
        self._build_table_card()
        self.refresh()

    # ---------------------------------------------------------------- layout
    def _build_form_card(self):
        card = Card(self.body, padding=22)
        card.grid(row=0, column=0, sticky="ns", padx=(0, px(20)))
        ttk.Label(card.inner, text=f"{self.entity.title()} Details",
                  style="CardTitle.TLabel").pack(anchor="w", pady=(0, px(14)))

        fields = ttk.Frame(card.inner, style="Card.TFrame")
        fields.pack(fill="x")
        self.form = Form(fields)
        self.build_form(self.form)

        buttons = ttk.Frame(card.inner, style="Card.TFrame")
        buttons.pack(fill="x", pady=(px(6), 0))
        buttons.columnconfigure((0, 1), weight=1, uniform="crud")
        name = self.entity.title()
        specs = [
            (f"Add {name}", "Primary.TButton", self.on_add),
            (f"Update {name}", "Secondary.TButton", self.on_update),
            (f"Delete {name}", "Danger.TButton", self.on_delete),
            ("Clear Form", "Ghost.TButton", self.clear_form),
        ]
        for index, (text, style_name, command) in enumerate(specs):
            AppButton(buttons, text=text, style=style_name, command=command).grid(
                row=index // 2, column=index % 2, sticky="ew", padx=px(3), pady=px(4))

    def _build_table_card(self):
        card = Card(self.body, padding=20)
        card.grid(row=0, column=1, sticky="nsew")

        top = ttk.Frame(card.inner, style="Card.TFrame")
        top.pack(fill="x", pady=(0, px(14)))
        self.search_var = tk.StringVar()
        ttk.Label(top, text="SEARCH", style="Field.TLabel").pack(side="left", padx=(0, px(10)))
        AppEntry(top, textvariable=self.search_var, width=34).pack(side="left")
        AppButton(top, text="Clear", style="Ghost.TButton",
                  command=lambda: self.search_var.set("")).pack(side="left", padx=(px(10), 0))
        self.count_label = ttk.Label(top, text="", style="CardMuted.TLabel")
        self.count_label.pack(side="right")

        self.table = DataTable(card.inner, self.columns, on_select=self.on_row_selected)
        self.table.pack(fill="both", expand=True)

        extra = ttk.Frame(card.inner, style="Card.TFrame")
        extra.pack(fill="x", pady=(px(14), 0))
        self.build_extra_buttons(extra)

        self.search_var.trace_add("write", lambda *_: self.refresh_table())

    # ---------------------------------------------------------------- refresh
    def refresh(self):
        self.on_refresh()
        self.refresh_table()

    def refresh_table(self):
        query = self.search_var.get().strip()
        rows = self.get_rows(query)
        if query:
            message = f'No {self.entity_plural} found matching "{query}".'
        else:
            message = f"No {self.entity_plural} added yet.\nUse the form on the left to add one."
        self.table.set_rows(rows, message)
        count = len(rows)
        self.count_label.config(text=f"{count} {self.entity if count == 1 else self.entity_plural}")

    # ---------------------------------------------------------------- button handlers
    def clear_form(self):
        self.selected_id = None
        self.form.clear()
        self.table.tree.selection_remove(self.table.tree.selection())

    def on_row_selected(self, record_id):
        self.selected_id = record_id
        self.record_to_form(record_id)

    def _require_selection(self, action):
        if self.selected_id is None:
            show_warning(f"Select a {self.entity} from the table first, then click {action}.")
            return False
        return True

    def on_add(self):
        try:
            data = self.read_form()
            self.add_record(data)
        except ValidationError as err:
            show_warning(str(err))
            return
        self.clear_form()
        self.refresh()
        show_info(f"{self.entity.title()} added successfully.")

    def on_update(self):
        if not self._require_selection("Update"):
            return
        try:
            data = self.read_form()
            self.update_record(self.selected_id, data)
        except ValidationError as err:
            show_warning(str(err))
            return
        self.clear_form()
        self.refresh()
        show_info(f"{self.entity.title()} updated successfully.")

    def on_delete(self):
        if not self._require_selection("Delete"):
            return
        if not confirm(self.delete_prompt(self.selected_id), yes_text="Delete",
                       no_text="Cancel", danger=True):
            return
        try:
            note = self.delete_record(self.selected_id)
        except ValidationError as err:
            show_warning(str(err))
            return
        self.clear_form()
        self.refresh()
        show_info(f"{self.entity.title()} deleted successfully." + (f"\n{note}" if note else ""))

    # ---------------------------------------------------------------- HOOKS (override)
    def build_form(self, form):
        raise NotImplementedError

    def build_extra_buttons(self, bar):
        """Optional: add extra buttons under the table."""

    def on_refresh(self):
        """Optional: reload drop-down lists before the table is refreshed."""

    def get_rows(self, query):
        raise NotImplementedError

    def read_form(self):
        raise NotImplementedError

    def add_record(self, data):
        raise NotImplementedError

    def update_record(self, record_id, data):
        raise NotImplementedError

    def delete_record(self, record_id):
        raise NotImplementedError

    def delete_prompt(self, record_id):
        return f"Delete this {self.entity}?"

    def record_to_form(self, record_id):
        raise NotImplementedError
