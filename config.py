"""Application-wide settings: file locations, colours, fonts and fixed lists.

Change values here (for example the admin password) instead of searching
through the other modules.
"""
import os
import sys

# When packaged with PyInstaller the data folder is created next to the .exe,
# otherwise it is created next to this file.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

APP_TITLE = "Student Placement Management System"

# Password the placement officer must enter before changing application status.
ADMIN_PASSWORD = "admin123"

STATUSES = ["Applied", "Shortlisted", "Selected", "Rejected"]
DEFAULT_STATUS = "Applied"

DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics",
    "Electrical",
    "Mechanical",
    "Civil",
    "Chemical",
    "MBA",
    "MCA",
]

DATE_FORMAT = "%Y-%m-%d"  # dates are stored and typed as YYYY-MM-DD

# ---- Display scaling (set once the window exists, see init_scale) ----
SCALE = 1.0


def px(value):
    """Scale a pixel size so the interface looks the same on high-DPI screens."""
    return int(round(value * SCALE))


def init_scale(root):
    global SCALE
    SCALE = max(1.0, root.winfo_fpixels("1i") / 96.0)


# ---- Colour palette: deep navy, crisp white and emerald green ----
NAVY = "#0B1B34"
NAVY_MID = "#102646"
NAVY_LIGHT = "#173561"
NAVY_LINE = "#264069"
SIDEBAR_TEXT = "#9FB0C8"

GREEN = "#0EA371"
GREEN_DARK = "#0B8A60"
GREEN_TINT = "#E4F5EC"

WHITE = "#FFFFFF"
BG = "#F4F6FA"
BORDER = "#E2E8F0"
BORDER_STRONG = "#D3DBE6"
SHADOW = "#E8ECF2"
TEXT = "#0F1B2D"
LABEL = "#475569"
MUTED = "#64748B"

RED = "#E5484D"
RED_DARK = "#C93A3F"
RED_TINT = "#FDECEC"
AMBER = "#D98A00"
BLUE = "#3B82F6"

# Colour of each placement status (used for bars and tinted table rows)
STATUS_COLORS = {
    "Applied": BLUE,
    "Shortlisted": AMBER,
    "Selected": GREEN,
    "Rejected": RED,
}

# Table colours
HEADER_BG = "#F1F5F9"
ROW_STRIPE = "#F9FBFD"
ROW_SELECT = "#CFEEDD"
ROW_OK = "#EAF7F0"
ROW_BAD = "#FDEFEF"
ROW_WARN = "#FFF8E5"
ROW_INFO = "#EEF4FF"

FONT = "Segoe UI"
FONT_SEMI = "Segoe UI Semibold"
