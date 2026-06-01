from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


NULL_VALUES = {"", "na", "n/a", "null", "none", "nan"}
EXAMPLE_LIMIT = 8
DISTINCT_TRACK_LIMIT = 1000
SAMPLE_ROW_LIMIT = 5


@dataclass(frozen=True)
class CsvColumnProfile:
    name: str
    inferred_datatype: str
    null_count: int
    non_null_count: int
    distinct_count: int
    examples: tuple[str, ...]
    compatible_datatypes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class CsvProfile:
    path: Path
    row_count: int
    columns: tuple[CsvColumnProfile, ...]
    sample_rows: tuple[dict[str, str], ...]


def profile_csv(path: Path, sample_rows: int = SAMPLE_ROW_LIMIT) -> CsvProfile:
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = tuple(reader.fieldnames or ())
        stats = {
            name: {
                "null_count": 0,
                "non_null_count": 0,
                "examples": [],
                "distinct": set(),
                "distinct_overflow": False,
                "candidates": {"boolean", "integer", "decimal", "date", "datetime"},
                "leading_zero": False,
                "mixed_numeric": False,
            }
            for name in fieldnames
        }
        sampled: list[dict[str, str]] = []
        row_count = 0
        for row in reader:
            row_count += 1
            normalized_row = {name: (row.get(name) or "").strip() for name in fieldnames}
            if len(sampled) < sample_rows:
                sampled.append(normalized_row)
            for name, value in normalized_row.items():
                column = stats[name]
                if _is_null(value):
                    column["null_count"] += 1
                    continue
                column["non_null_count"] += 1
                if value not in column["examples"] and len(column["examples"]) < EXAMPLE_LIMIT:
                    column["examples"].append(value)
                if _has_leading_zero(value):
                    column["leading_zero"] = True
                if _looks_mixed_numeric(value):
                    column["mixed_numeric"] = True
                if not column["distinct_overflow"]:
                    column["distinct"].add(value)
                    if len(column["distinct"]) > DISTINCT_TRACK_LIMIT:
                        column["distinct_overflow"] = True
                        column["distinct"].clear()
                _narrow_candidates(column["candidates"], value)

    profiles: list[CsvColumnProfile] = []
    for name in fieldnames:
        column = stats[name]
        distinct_count = (
            DISTINCT_TRACK_LIMIT + 1
            if column["distinct_overflow"]
            else len(column["distinct"])
        )
        profiles.append(
            CsvColumnProfile(
                name=name,
                inferred_datatype=_choose_datatype(column["candidates"], column["non_null_count"]),
                null_count=int(column["null_count"]),
                non_null_count=int(column["non_null_count"]),
                distinct_count=distinct_count,
                examples=tuple(column["examples"]),
                compatible_datatypes=_compatible_datatypes(
                    name,
                    column["candidates"],
                    column["non_null_count"],
                    bool(column["leading_zero"]),
                    bool(column["mixed_numeric"]),
                ),
                warnings=_datatype_warnings(
                    name,
                    column["candidates"],
                    column["non_null_count"],
                    bool(column["leading_zero"]),
                    bool(column["mixed_numeric"]),
                ),
            )
        )
    return CsvProfile(
        path=path,
        row_count=row_count,
        columns=tuple(profiles),
        sample_rows=tuple(sampled),
    )


def render_csv_profile(profile: CsvProfile) -> str:
    lines = [
        f"# Source file: {profile.path.name}",
        "",
        "CSV profile:",
        f"- Rows: {profile.row_count}",
        f"- Columns: {', '.join(column.name for column in profile.columns)}",
        "",
        "Column profiles:",
    ]
    for column in profile.columns:
        examples = "; ".join(column.examples) if column.examples else "none"
        distinct = (
            f">{DISTINCT_TRACK_LIMIT}"
            if column.distinct_count > DISTINCT_TRACK_LIMIT
            else str(column.distinct_count)
        )
        compatible = ", ".join(column.compatible_datatypes or (column.inferred_datatype,))
        warnings = "; ".join(column.warnings) if column.warnings else "none"
        lines.append(
            f"- {column.name}: datatype={column.inferred_datatype}; "
            f"compatible_datatypes={compatible}; "
            f"nulls={column.null_count}; non_nulls={column.non_null_count}; "
            f"distinct={distinct}; warnings={warnings}; examples={examples}"
        )
    lines.extend(
        [
            "",
            "CSV datatype guidance:",
            "- Treat datatype as a recommendation, not a guarantee.",
            "- Prefer xsd:string for identifiers, codes, mixed values, leading-zero values, and uncertain columns.",
            "- Use numeric/date/boolean ranges only when all non-null values and the column meaning clearly support that type.",
        ]
    )
    lines.extend(["", "Sample rows:"])
    if not profile.sample_rows:
        lines.append("- No rows.")
    for index, row in enumerate(profile.sample_rows, start=1):
        values = "; ".join(f"{key}: {value}" for key, value in row.items())
        lines.append(f"- Row {index}: {values}")
    return "\n".join(lines).strip()


def csv_profiles_from_dir(data_dir: Path) -> list[CsvProfile]:
    return [
        profile_csv(path)
        for path in sorted(data_dir.glob("*"))
        if path.is_file() and path.suffix.lower() == ".csv"
    ]


def _is_null(value: str) -> bool:
    return value.strip().lower() in NULL_VALUES


def _narrow_candidates(candidates: set[str], value: str) -> None:
    if "boolean" in candidates and value.lower() not in {"true", "false", "yes", "no", "y", "n", "1", "0"}:
        candidates.discard("boolean")
    if "integer" in candidates:
        try:
            int(value)
        except ValueError:
            candidates.discard("integer")
    if "decimal" in candidates:
        try:
            Decimal(value)
        except InvalidOperation:
            candidates.discard("decimal")
    if "date" in candidates and not _matches_datetime(value, ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]):
        candidates.discard("date")
    if "datetime" in candidates and not _matches_datetime(
        value,
        ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"],
    ):
        candidates.discard("datetime")


def _choose_datatype(candidates: set[str], non_null_count: int) -> str:
    if non_null_count == 0:
        return "string"
    for datatype in ("integer", "decimal", "boolean", "date", "datetime"):
        if datatype in candidates:
            return datatype
    return "string"


def _compatible_datatypes(
    name: str,
    candidates: set[str],
    non_null_count: int,
    leading_zero: bool,
    mixed_numeric: bool,
) -> tuple[str, ...]:
    if non_null_count == 0:
        return ("string",)
    if _name_looks_identifier(name) or leading_zero or mixed_numeric:
        return ("string",)
    values: list[str] = []
    if "integer" in candidates:
        values.extend(["integer", "decimal", "string"])
    elif "decimal" in candidates:
        values.extend(["decimal", "string"])
    elif "boolean" in candidates:
        values.extend(["boolean", "string"])
    elif "date" in candidates:
        values.extend(["date", "string"])
    elif "datetime" in candidates:
        values.extend(["datetime", "string"])
    else:
        values.append("string")
    return tuple(dict.fromkeys(values))


def _datatype_warnings(
    name: str,
    candidates: set[str],
    non_null_count: int,
    leading_zero: bool,
    mixed_numeric: bool,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if non_null_count == 0:
        warnings.append("all values are null; use string unless requirements say otherwise")
    if _name_looks_identifier(name):
        warnings.append("column name looks like an identifier/code; prefer string even if values look numeric")
    if leading_zero:
        warnings.append("values include leading zeros; prefer string to preserve lexical form")
    if mixed_numeric:
        warnings.append("values mix digits with non-numeric characters; prefer string")
    if not candidates:
        warnings.append("values do not consistently match numeric, boolean, date, or datetime formats")
    return tuple(warnings)


def _name_looks_identifier(name: str) -> bool:
    lowered = name.lower().replace("_", " ").replace("-", " ")
    terms = set(lowered.split())
    return bool(terms & {"id", "identifier", "code", "key", "number", "no"})


def _has_leading_zero(value: str) -> bool:
    text = value.strip()
    return len(text) > 1 and text.isdigit() and text.startswith("0")


def _looks_mixed_numeric(value: str) -> bool:
    text = value.strip()
    return any(char.isdigit() for char in text) and any(char.isalpha() for char in text)


def _matches_datetime(value: str, formats: list[str]) -> bool:
    for date_format in formats:
        try:
            datetime.strptime(value, date_format)
            return True
        except ValueError:
            pass
    return False
