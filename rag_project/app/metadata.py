"""Pull retrieval fields out of a document name and its opening text."""
from __future__ import annotations

import re

_IR_NUMBER = re.compile(r"IR-[0-9A-F]{6,}", re.IGNORECASE)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_PERIOD = re.compile(
    r"(?i)(?:(?:from|period(?:\s+of)?)\s+)?(\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{2}/\d{4})"
    r"\s+to\s+(\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{2}/\d{4})"
)
_OFFICE = re.compile(
    r"(?i)(?:audit of (?:the )?office of|name of the office audited)\s*[:\-]?\s*(.+)"
)
_GO = re.compile(r"(?i)G[.\-\s]*O[.\-\s]*(?:Ms[.\-\s]*)?No[.\-\s]*[\w.\-]+")

_STATES = (
    ("andhra pradesh", "Andhra Pradesh"),
    ("maharashtra", "Maharashtra"),
    ("haryana", "Haryana"),
    ("punjab", "Punjab"),
)
_PLACES = (
    ("aurangabad", "Maharashtra", "Aurangabad"),
    ("amritsar", "Punjab", "Amritsar"),
    ("vijayawada", "Andhra Pradesh", "Vijayawada"),
    ("amaravati", "Andhra Pradesh", "Amaravati"),
    ("nagpur", "Maharashtra", "Nagpur"),
)
_DEPARTMENTS = (
    (("energy", "power", "apcpdcl", "discom", "electrical"), "Energy"),
    (("finance", "special pay", "allowance", "pay revision"), "Finance"),
    (("stamp", "registrar", "registration"), "Registration and Stamps"),
    (("medical", "esi", "hospital", "health"), "Medical and Health"),
)


def _contains(text: str, needle: str) -> bool:
    return re.search(rf"(?i)\b{re.escape(needle)}\b", text) is not None


def _department(filename: str, title: str, sample: str) -> str | None:
    for source in (f"{filename}\n{title}", sample):
        for needles, label in _DEPARTMENTS:
            if any(_contains(source, needle) for needle in needles):
                return label
    return None


def extract_metadata(text: str, filename: str, document_type: str) -> dict[str, str | None]:
    sample = text[:6000]
    title = _title(sample, filename, document_type)
    heading = f"{filename}\n{title}"
    state = None
    government = re.search(
        r"(?i)government of (andhra pradesh|maharashtra|haryana|punjab)",
        heading + "\n" + sample[:1500],
    )
    if government:
        state = next(label for needle, label in _STATES if needle == government.group(1).lower())
    if state is None:
        state = next((label for needle, label in _STATES if _contains(heading, needle)), None)
    if state is None:
        state = next((label for needle, label in _STATES if _contains(sample, needle)), None)
    district = None
    for needle, place_state, place_name in _PLACES:
        if _contains(sample, needle) or _contains(filename, needle):
            district = district or place_name
            state = state or place_state
    ir_match = _IR_NUMBER.search(filename) or _IR_NUMBER.search(sample)
    period = _PERIOD.search(sample)
    office = _OFFICE.search(sample)
    office_name = None
    if office:
        office_name = office.group(1).split("\n")[0]
        office_name = re.split(r"(?i)\s+for the period\b", office_name)[0]
        office_name = office_name.replace("|", " ")
        office_name = re.sub(r"(?i)^the\s+", "", office_name).strip(" .")[:240] or None
    if document_type == "ir_document":
        department = _department("", office_name or "", sample[:900])
    else:
        department = _department(filename, title, sample)
    years = _YEAR.findall(filename + " " + sample[:800])
    year = None
    year_match = _YEAR.search(filename) or _YEAR.search(sample[:800])
    if period and document_type == "ir_document":
        year = re.search(r"(19|20)\d{2}", period.group(2))
        year = year.group(0) if year else None
    elif year_match:
        year = year_match.group(0)
    elif years:
        year = years[0]

    if document_type == "ir_document":
        kind = "inspection_report"
    elif _GO.search(filename):
        kind = "government_order"
    elif re.search(r"(?i)\brules\b", f"{title}\n{filename}\n{sample[:1500]}"):
        kind = "rules"
    elif _GO.search(sample[:1500]):
        kind = "government_order"
    elif re.search(r"(?i)\bact\b", f"{title}\n{filename}"):
        kind = "act"
    else:
        kind = "criteria_document"

    return {
        "state": state,
        "department": department,
        "office_name": office_name,
        "district": district,
        "audit_period": f"{period.group(1)} to {period.group(2)}" if period else None,
        "ir_number": ir_match.group(0).upper() if ir_match else None,
        "document_title": title,
        "instrument_kind": kind,
        "year": year,
        "auditee": office_name,
    }


def _title(sample: str, filename: str, document_type: str) -> str:
    lines = []
    for line in sample.splitlines():
        cleaned = re.sub(r"^#+\s*", "", line).strip()
        if len(cleaned) < 12:
            continue
        if re.match(r"(?i)^(page \d+|government of|abstract|part[\s\-]*i+\b|contents|preface)\b", cleaned):
            continue
        lines.append(cleaned[:240])
    if document_type == "ir_document" and lines:
        return lines[0]
    for line in lines:
        if re.search(r"(?i)\b(act|rules|g\.?\s*o\.?)\b", line):
            return line
    return lines[0] if lines else filename
