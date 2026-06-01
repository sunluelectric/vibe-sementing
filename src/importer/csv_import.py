from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, RDF, RDFS, URIRef, XSD

from src.common.csv_profile import NULL_VALUES, CsvProfile, profile_csv
from src.importer.validation import inspect_ontology_terms


DATATYPE_URIS = {
    "string": XSD.string,
    "integer": XSD.integer,
    "decimal": XSD.decimal,
    "boolean": XSD.boolean,
    "date": XSD.date,
    "datetime": XSD.dateTime,
    "anyURI": XSD.anyURI,
}
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")
SLUG_RE = re.compile(r"[^A-Za-z0-9]+")


@dataclass(frozen=True)
class CsvColumnMapping:
    column: str
    property_uri: str
    datatype: str = "string"


@dataclass(frozen=True)
class CsvRelationshipMapping:
    column: str
    property_uri: str
    target_class_uri: str
    target_uri_template: str
    target_label_template: str | None = None


@dataclass(frozen=True)
class CsvFileMapping:
    csv_file: str
    row_class_uri: str
    subject_uri_template: str
    label_template: str | None = None
    column_mappings: tuple[CsvColumnMapping, ...] = ()
    relationship_mappings: tuple[CsvRelationshipMapping, ...] = ()
    skip_nulls: bool = True


@dataclass(frozen=True)
class CsvImportPlan:
    mappings: tuple[CsvFileMapping, ...] = ()


@dataclass(frozen=True)
class CsvMappingValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)

    def raise_for_errors(self) -> None:
        if not self.ok:
            raise ValueError("; ".join(self.errors))


def parse_csv_import_plan(payload: dict[str, Any]) -> CsvImportPlan:
    items = payload.get("mappings", payload.get("csv_mappings", []))
    if isinstance(items, dict):
        items = [items]
    mappings: list[CsvFileMapping] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        column_items = item.get("column_mappings", [])
        relationship_items = item.get("relationship_mappings", [])
        mappings.append(
            CsvFileMapping(
                csv_file=str(item.get("csv_file", "")).strip(),
                row_class_uri=str(item.get("row_class", item.get("row_class_uri", ""))).strip(),
                subject_uri_template=str(item.get("subject_uri_template", "")).strip(),
                label_template=_optional_str(item.get("label_template")),
                column_mappings=tuple(
                    CsvColumnMapping(
                        column=str(column.get("column", "")).strip(),
                        property_uri=str(column.get("property", column.get("property_uri", ""))).strip(),
                        datatype=str(column.get("datatype", "string")).strip() or "string",
                    )
                    for column in column_items
                    if isinstance(column, dict)
                ),
                relationship_mappings=tuple(
                    CsvRelationshipMapping(
                        column=str(relationship.get("column", "")).strip(),
                        property_uri=str(relationship.get("property", relationship.get("property_uri", ""))).strip(),
                        target_class_uri=str(
                            relationship.get("target_class", relationship.get("target_class_uri", ""))
                        ).strip(),
                        target_uri_template=str(relationship.get("target_uri_template", "")).strip(),
                        target_label_template=_optional_str(relationship.get("target_label_template")),
                    )
                    for relationship in relationship_items
                    if isinstance(relationship, dict)
                ),
                skip_nulls=bool(item.get("skip_nulls", True)),
            )
        )
    return CsvImportPlan(mappings=tuple(mappings))


def validate_csv_import_plan(
    plan: CsvImportPlan,
    ontology_graph: Graph,
    data_dir: Path,
) -> CsvMappingValidationResult:
    terms = inspect_ontology_terms(ontology_graph)
    errors: list[str] = []
    if not plan.mappings:
        errors.append("CSV import plan has no mappings.")
    for mapping in plan.mappings:
        path = data_dir / mapping.csv_file
        if not mapping.csv_file:
            errors.append("CSV mapping is missing csv_file.")
            continue
        if not path.is_file():
            errors.append(f"CSV file {mapping.csv_file} does not exist.")
            continue
        profile = profile_csv(path)
        columns = {column.name for column in profile.columns}
        row_class = URIRef(mapping.row_class_uri)
        if row_class not in terms.classes:
            errors.append(f"CSV row class {mapping.row_class_uri} is not defined in the ontology.")
        _validate_template(mapping.subject_uri_template, columns, f"{mapping.csv_file} subject_uri_template", errors)
        if mapping.label_template:
            _validate_template(mapping.label_template, columns, f"{mapping.csv_file} label_template", errors, allow_relative=True)
        for column_mapping in mapping.column_mappings:
            _validate_column(column_mapping.column, columns, mapping.csv_file, errors)
            property_uri = URIRef(column_mapping.property_uri)
            if property_uri not in terms.properties:
                errors.append(f"CSV property {column_mapping.property_uri} is not defined in the ontology.")
            if column_mapping.datatype not in DATATYPE_URIS:
                errors.append(f"CSV datatype {column_mapping.datatype} is not supported.")
            _validate_property_range(ontology_graph, property_uri, DATATYPE_URIS.get(column_mapping.datatype), errors)
        for relationship in mapping.relationship_mappings:
            _validate_column(relationship.column, columns, mapping.csv_file, errors)
            property_uri = URIRef(relationship.property_uri)
            target_class = URIRef(relationship.target_class_uri)
            if property_uri not in terms.properties:
                errors.append(f"CSV relationship property {relationship.property_uri} is not defined in the ontology.")
            if target_class not in terms.classes:
                errors.append(f"CSV relationship target class {relationship.target_class_uri} is not defined in the ontology.")
            _validate_template(
                relationship.target_uri_template,
                columns,
                f"{mapping.csv_file} target_uri_template",
                errors,
            )
            if relationship.target_label_template:
                _validate_template(
                    relationship.target_label_template,
                    columns,
                    f"{mapping.csv_file} target_label_template",
                    errors,
                    allow_relative=True,
                )
            _validate_property_range(ontology_graph, property_uri, target_class, errors)
    return CsvMappingValidationResult(ok=not errors, errors=errors)


def generate_csv_instances(
    plan: CsvImportPlan,
    ontology_graph: Graph,
    data_dir: Path,
) -> Graph:
    validate_csv_import_plan(plan, ontology_graph, data_dir).raise_for_errors()
    graph = Graph()
    for prefix, namespace in ontology_graph.namespaces():
        graph.bind(prefix, namespace)
    graph.bind("inst", "http://example.org/semantic-web/instance/")
    for mapping in plan.mappings:
        path = data_dir / mapping.csv_file
        with path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                normalized_row = {key: (value or "").strip() for key, value in row.items()}
                subject = URIRef(_render_template(mapping.subject_uri_template, normalized_row))
                graph.add((subject, RDF.type, URIRef(mapping.row_class_uri)))
                if mapping.label_template:
                    graph.add((subject, RDFS.label, Literal(_render_template(mapping.label_template, normalized_row))))
                for column_mapping in mapping.column_mappings:
                    value = normalized_row.get(column_mapping.column, "")
                    if mapping.skip_nulls and _is_null(value):
                        continue
                    property_uri = URIRef(column_mapping.property_uri)
                    graph.add(
                        (
                            subject,
                            property_uri,
                            _literal_for_property(
                                value,
                                column_mapping.datatype,
                                ontology_graph,
                                property_uri,
                            ),
                        )
                    )
                for relationship in mapping.relationship_mappings:
                    value = normalized_row.get(relationship.column, "")
                    if mapping.skip_nulls and _is_null(value):
                        continue
                    target = URIRef(_render_template(relationship.target_uri_template, normalized_row))
                    graph.add((subject, URIRef(relationship.property_uri), target))
                    graph.add((target, RDF.type, URIRef(relationship.target_class_uri)))
                    if relationship.target_label_template:
                        graph.add((target, RDFS.label, Literal(_render_template(relationship.target_label_template, normalized_row))))
                    else:
                        graph.add((target, RDFS.label, Literal(value)))
    return graph


def csv_profiles_for_prompt(data_dir: Path) -> str:
    profiles = [
        profile_csv(path)
        for path in sorted(data_dir.glob("*"))
        if path.is_file() and path.suffix.lower() == ".csv"
    ]
    return "\n\n".join(_mapping_profile(profile) for profile in profiles).strip()


def _mapping_profile(profile: CsvProfile) -> str:
    lines = [
        f"CSV file: {profile.path.name}",
        f"Rows: {profile.row_count}",
        "Columns:",
    ]
    for column in profile.columns:
        examples = "; ".join(column.examples) if column.examples else "none"
        lines.append(
            f"- {column.name}: datatype={column.inferred_datatype}; "
            f"compatible_datatypes={', '.join(column.compatible_datatypes or (column.inferred_datatype,))}; "
            f"nulls={column.null_count}; examples={examples}"
        )
    return "\n".join(lines)


def _validate_column(column: str, columns: set[str], csv_file: str, errors: list[str]) -> None:
    if column not in columns:
        errors.append(f"CSV column {column} does not exist in {csv_file}.")


def _validate_template(
    template: str,
    columns: set[str],
    field_name: str,
    errors: list[str],
    allow_relative: bool = False,
) -> None:
    if not template:
        errors.append(f"CSV mapping {field_name} is empty.")
        return
    if not allow_relative and not template.startswith(("http://", "https://")):
        errors.append(f"CSV mapping {field_name} must be an absolute HTTP URI template.")
    for placeholder in PLACEHOLDER_RE.findall(template):
        column, transform = _split_placeholder(placeholder)
        if column not in columns:
            errors.append(f"CSV mapping {field_name} references unknown column {column}.")
        if transform and transform != "slug":
            errors.append(f"CSV mapping {field_name} uses unsupported transform {transform}.")


def _validate_property_range(
    ontology_graph: Graph,
    property_uri: URIRef,
    expected_range: URIRef | None,
    errors: list[str],
) -> None:
    if expected_range is None:
        return
    ranges = set(ontology_graph.objects(property_uri, RDFS.range))
    if not ranges:
        return
    allowed = _compatible_ranges(expected_range)
    if expected_range in {XSD.string, XSD.integer, XSD.decimal, XSD.boolean, XSD.date, XSD.dateTime, XSD.anyURI}:
        allowed.add(RDFS.Literal)
    if not any(range_value in allowed for range_value in ranges):
        errors.append(f"CSV property {property_uri} range does not match expected {expected_range}.")


def _compatible_ranges(expected_range: URIRef) -> set[URIRef]:
    allowed = {expected_range, RDFS.Resource, RDFS.Literal}
    if expected_range == XSD.integer:
        allowed.update({XSD.decimal, XSD.string})
    elif expected_range in {XSD.decimal, XSD.boolean, XSD.date, XSD.dateTime, XSD.anyURI}:
        allowed.add(XSD.string)
    return allowed


def _render_template(template: str, row: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        column, transform = _split_placeholder(match.group(1))
        value = row.get(column, "")
        if transform == "slug":
            return _slug(value)
        return value

    return PLACEHOLDER_RE.sub(replace, template)


def _split_placeholder(placeholder: str) -> tuple[str, str | None]:
    if "|" not in placeholder:
        return placeholder.strip(), None
    column, transform = placeholder.split("|", 1)
    return column.strip(), transform.strip()


def _literal(value: str, datatype: str) -> Literal:
    if datatype == "integer":
        return Literal(int(value), datatype=XSD.integer)
    if datatype == "decimal":
        try:
            Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid decimal value {value}") from exc
        return Literal(value, datatype=XSD.decimal)
    if datatype == "boolean":
        return Literal(_boolean_value(value), datatype=XSD.boolean)
    if datatype == "date":
        return Literal(value, datatype=XSD.date)
    if datatype == "datetime":
        return Literal(value, datatype=XSD.dateTime)
    if datatype == "anyURI":
        return Literal(value, datatype=XSD.anyURI)
    return Literal(value, datatype=XSD.string)


def _literal_for_property(
    value: str,
    datatype: str,
    ontology_graph: Graph,
    property_uri: URIRef,
) -> Literal:
    ranges = set(ontology_graph.objects(property_uri, RDFS.range))
    preferred_datatype = _datatype_for_ranges(datatype, ranges, value)
    try:
        return _literal(value, preferred_datatype)
    except ValueError:
        if _range_allows_string(ranges):
            return Literal(value, datatype=XSD.string)
        raise


def _datatype_for_ranges(datatype: str, ranges: set[URIRef], value: str) -> str:
    if datatype == "integer" and XSD.decimal in ranges and not _is_integer_literal(value):
        return "decimal"
    if datatype in DATATYPE_URIS:
        return datatype
    return "string"


def _range_allows_string(ranges: set[URIRef]) -> bool:
    return not ranges or bool(ranges & {XSD.string, RDFS.Literal, RDFS.Resource})


def _is_integer_literal(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def _boolean_value(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"true", "yes", "y", "1"}:
        return True
    if lowered in {"false", "no", "n", "0"}:
        return False
    raise ValueError(f"Invalid boolean value {value}")


def _is_null(value: str) -> bool:
    return value.strip().lower() in NULL_VALUES


def _slug(value: str) -> str:
    slug = SLUG_RE.sub("-", value.strip().lower()).strip("-")
    return slug or "row"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
