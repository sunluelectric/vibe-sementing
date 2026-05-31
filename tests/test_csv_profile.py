from __future__ import annotations

from src.common.csv_profile import profile_csv, render_csv_profile
from src.common.files import load_project_data


def test_csv_profile_infers_datatypes_and_samples_rows(tmp_path) -> None:
    csv_path = tmp_path / "records.csv"
    csv_path.write_text(
        "name,count,price,active,created,notes\n"
        "Alpha,10,12.50,true,2026-01-02,First\n"
        "Beta,,9.75,false,2026-01-03,\n",
        encoding="utf-8",
    )

    profile = profile_csv(csv_path)

    assert profile.row_count == 2
    columns = {column.name: column for column in profile.columns}
    assert columns["count"].inferred_datatype == "integer"
    assert columns["count"].null_count == 1
    assert columns["price"].inferred_datatype == "decimal"
    assert columns["active"].inferred_datatype == "boolean"
    assert columns["created"].inferred_datatype == "date"
    assert profile.sample_rows[0]["name"] == "Alpha"


def test_csv_profile_rendering_does_not_dump_all_rows(tmp_path) -> None:
    csv_path = tmp_path / "many.csv"
    rows = ["name,value"] + [f"Row {index},{index}" for index in range(20)]
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    rendered = render_csv_profile(profile_csv(csv_path))

    assert "Rows: 20" in rendered
    assert "Row 1: name: Row 0" in rendered
    assert "Row 6: name: Row 5" not in rendered


def test_project_data_uses_csv_profile_instead_of_full_csv_dump(tmp_path) -> None:
    (tmp_path / "table.csv").write_text(
        "name,value\n"
        + "\n".join(f"Record {index},{index}" for index in range(12)),
        encoding="utf-8",
    )

    data = load_project_data(tmp_path)

    assert "CSV profile:" in data
    assert "Rows: 12" in data
    assert "Record 0" in data
    assert "Record 10,10" not in data
