"""Input validation and small helpers shared by the placement screens."""
import math
import re
import webbrowser
from datetime import datetime

import config


class ValidationError(ValueError):
    """Raised when user-provided data does not meet the application's rules."""


def clean_text(value, label, minimum=1, maximum=200):
    text = str(value or "").strip()
    if not minimum <= len(text) <= maximum:
        raise ValidationError(f"{label} must be between {minimum} and {maximum} characters.")
    if any(ord(char) < 32 for char in text):
        raise ValidationError(f"{label} contains invalid characters.")
    return text


def clean_person_name(value):
    text = clean_text(value, "Name", 2, 80)
    if not all(char.isalpha() or char in " '-." for char in text):
        raise ValidationError("Name may contain letters, spaces, apostrophes, periods and hyphens only.")
    if not any(char.isalpha() for char in text):
        raise ValidationError("Please enter a valid name.")
    return text


def clean_email(value, required=True):
    email = str(value or "").strip()
    if not email and not required:
        return ""
    if len(email) > 254 or not re.fullmatch(
            r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",
            email):
        raise ValidationError("Please enter a valid email address.")
    return email


def clean_phone(value):
    phone = str(value or "").strip()
    digits = re.sub(r"\D", "", phone)
    if not re.fullmatch(r"[+().\-\s\d]{7,20}", phone) or not 7 <= len(digits) <= 15:
        raise ValidationError("Please enter a valid phone number (7 to 15 digits).")
    return phone


def clean_url(value, label):
    url = str(value or "").strip()
    if not url:
        return ""
    if len(url) > 2048 or any(char.isspace() for char in url):
        raise ValidationError(f"{label} must be a valid http:// or https:// URL.")
    match = re.fullmatch(r"https?://([^/?#]+)(?:[/?#].*)?", url, re.IGNORECASE)
    if not match or "." not in match.group(1).split("@")[-1]:
        raise ValidationError(f"{label} must be a valid http:// or https:// URL.")
    return url


def open_url(url):
    """Open a validated URL; return False when the desktop has no browser handler."""
    try:
        return bool(webbrowser.open(url))
    except (OSError, webbrowser.Error):
        return False


def parse_cgpa(value, label="CGPA"):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{label} must be a number between 0 and 10.") from None
    if not math.isfinite(number) or not 0 <= number <= 10:
        raise ValidationError(f"{label} must be a number between 0 and 10.")
    return number


def parse_package(value):
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Package must be a positive number in LPA.") from None
    if not math.isfinite(number) or number <= 0 or number > 10000:
        raise ValidationError("Package must be a positive number in LPA.")
    return number


def format_package(value):
    return f"{float(value):g} LPA"


def parse_skills(value, required=True):
    raw = str(value or "").strip()
    if not raw:
        if required:
            raise ValidationError("Please enter at least one skill.")
        return []
    skills, seen = [], set()
    for item in raw.split(","):
        skill = item.strip()
        if not skill:
            continue
        if len(skill) > 50 or any(ord(char) < 32 for char in skill):
            raise ValidationError("Each skill must be 1 to 50 valid characters.")
        key = skill.casefold()
        if key not in seen:
            skills.append(skill)
            seen.add(key)
    if not skills and required:
        raise ValidationError("Please enter at least one skill.")
    return skills


def skills_to_text(skills):
    return ", ".join(str(skill) for skill in (skills or []))


def clean_description(value):
    description = str(value or "").strip()
    if len(description) > 5000:
        raise ValidationError("Job description must be 5000 characters or fewer.")
    return description


def clean_date(value, label="Date"):
    text = str(value or "").strip()
    try:
        parsed = datetime.strptime(text, config.DATE_FORMAT)
    except ValueError:
        raise ValidationError(f"{label} must be a valid date in YYYY-MM-DD format.") from None
    if parsed.strftime(config.DATE_FORMAT) != text:
        raise ValidationError(f"{label} must be a valid date in YYYY-MM-DD format.")
    return text
