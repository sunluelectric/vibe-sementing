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


def fallback_csv_import_plan(
    ontology_graph: Graph,
    data_dir: Path,
    namespace: str = "http://example.org/semantic-web#",
) -> CsvImportPlan:
    terms = inspect_ontology_terms(ontology_graph)
    string_properties = _string_compatible_properties(ontology_graph, terms.properties)
    if not terms.classes or not string_properties:
        return CsvImportPlan()

    mappings: list[CsvFileMapping] = []
    for path in sorted(data_dir.glob("*")):
        if not path.is_file() or path.suffix.lower() != ".csv":
            continue
        profile = profile_csv(path)
        if not profile.columns:
            continue
        column_names = [column.name for column in profile.columns]
        row_class = _best_row_class(terms.classes, path.stem, column_names)
        subject_column = _best_subject_column(column_names)
        mappings.append(
            CsvFileMapping(
                csv_file=path.name,
                row_class_uri=str(row_class),
                subject_uri_template=(
                    "http://example.org/semantic-web/instance/"
                    f"{_slug(path.stem)}/{{{subject_column}|slug}}"
                ),
                label_template=f"{{{subject_column}}}",
                column_mappings=tuple(
                    CsvColumnMapping(
                        column=column_name,
                        property_uri=str(_best_string_property(string_properties, column_name, is_subject=column_name == subject_column)),
                        datatype="string",
                    )
                    for column_name in column_names
                ),
            )
        )
    return CsvImportPlan(mappings=tuple(mappings))


def csv_mapping_feedback_with_suggestions(
    plan: CsvImportPlan,
    ontology_graph: Graph,
    data_dir: Path,
) -> str:
    validation = validate_csv_import_plan(plan, ontology_graph, data_dir)
    if validation.ok:
        return ""
    suggestions = _csv_mapping_suggestions(plan, ontology_graph, data_dir)
    if suggestions:
        return "; ".join(validation.errors + suggestions)
    return "; ".join(validation.errors)


def repair_csv_import_plan(
    plan: CsvImportPlan,
    ontology_graph: Graph,
    data_dir: Path,
) -> CsvImportPlan:
    terms = inspect_ontology_terms(ontology_graph)
    string_properties = _string_compatible_properties(ontology_graph, terms.properties)
    if not string_properties:
        return plan

    repaired_mappings: list[CsvFileMapping] = []
    for mapping in plan.mappings:
        path = data_dir / mapping.csv_file
        if not mapping.csv_file or not path.is_file():
            repaired_mappings.append(mapping)
            continue
        profile = profile_csv(path)
        columns = {column.name for column in profile.columns}
        column_names = [column.name for column in profile.columns]
        row_class_uri = mapping.row_class_uri
        if URIRef(row_class_uri) not in terms.classes and terms.classes:
            row_class_uri = str(_best_row_class(terms.classes, path.stem, column_names))

        repaired_columns: list[CsvColumnMapping] = []
        mapped_columns: set[str] = set()
        for column_mapping in mapping.column_mappings:
            if column_mapping.column not in columns:
                repaired_columns.append(column_mapping)
                continue
            property_uri = URIRef(column_mapping.property_uri)
            datatype_uri = DATATYPE_URIS.get(column_mapping.datatype)
            if (
                property_uri in terms.properties
                and datatype_uri is not None
                and _property_accepts_range(ontology_graph, property_uri, datatype_uri)
            ):
                repaired_columns.append(column_mapping)
            else:
                repaired_columns.append(
                    CsvColumnMapping(
                        column=column_mapping.column,
                        property_uri=str(_best_string_property(string_properties, column_mapping.column, is_subject=False)),
                        datatype="string",
                    )
                )
            mapped_columns.add(column_mapping.column)

        repaired_relationships: list[CsvRelationshipMapping] = []
        for relationship in mapping.relationship_mappings:
            if relationship.column not in columns:
                repaired_relationships.append(relationship)
                continue
            property_uri = URIRef(relationship.property_uri)
            target_class = URIRef(relationship.target_class_uri)
            if (
                property_uri in terms.properties
                and target_class in terms.classes
                and _property_accepts_range(ontology_graph, property_uri, target_class)
            ):
                repaired_relationships.append(relationship)
            elif relationship.column not in mapped_columns:
                repaired_columns.append(
                    CsvColumnMapping(
                        column=relationship.column,
                        property_uri=str(_best_string_property(string_properties, relationship.column, is_subject=False)),
                        datatype="string",
                    )
                )
                mapped_columns.add(relationship.column)

        repaired_mappings.append(
            CsvFileMapping(
                csv_file=mapping.csv_file,
                row_class_uri=row_class_uri,
                subject_uri_template=mapping.subject_uri_template,
                label_template=mapping.label_template,
                column_mappings=tuple(repaired_columns),
                relationship_mappings=tuple(repaired_relationships),
                skip_nulls=mapping.skip_nulls,
            )
        )
    return CsvImportPlan(mappings=tuple(repaired_mappings))


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
    if not _property_accepts_range(ontology_graph, property_uri, expected_range):
        errors.append(f"CSV property {property_uri} range does not match expected {expected_range}.")


def _property_accepts_range(
    ontology_graph: Graph,
    property_uri: URIRef,
    expected_range: URIRef | None,
) -> bool:
    if expected_range is None:
        return True
    ranges = set(ontology_graph.objects(property_uri, RDFS.range))
    if not ranges:
        return True
    allowed = _compatible_ranges(expected_range)
    if expected_range in {XSD.string, XSD.integer, XSD.decimal, XSD.boolean, XSD.date, XSD.dateTime, XSD.anyURI}:
        allowed.add(RDFS.Literal)
    return any(range_value in allowed for range_value in ranges)


def _compatible_ranges(expected_range: URIRef) -> set[URIRef]:
    allowed = {expected_range, RDFS.Resource, RDFS.Literal}
    if expected_range == XSD.integer:
        allowed.update({XSD.decimal, XSD.string})
    elif expected_range in {XSD.decimal, XSD.boolean, XSD.date, XSD.dateTime, XSD.anyURI}:
        allowed.add(XSD.string)
    return allowed


def _string_compatible_properties(ontology_graph: Graph, properties: set[URIRef]) -> list[URIRef]:
    compatible: list[URIRef] = []
    for property_uri in sorted(properties, key=str):
        ranges = set(ontology_graph.objects(property_uri, RDFS.range))
        if not ranges or any(range_value in _compatible_ranges(XSD.string) for range_value in ranges):
            compatible.append(property_uri)
    return compatible


def _best_row_class(classes: set[URIRef], file_stem: str, columns: list[str]) -> URIRef:
    evidence = _tokens(file_stem)
    for column in columns:
        evidence.update(_tokens(column))
    ranked = sorted(
        classes,
        key=lambda class_uri: (
            -len(_tokens(_local_name(class_uri)) & evidence),
            str(class_uri),
        ),
    )
    return ranked[0]


def _best_subject_column(columns: list[str]) -> str:
    for column in columns:
        if "name" in _tokens(column) or "title" in _tokens(column):
            return column
    return columns[0]


def _best_string_property(properties: list[URIRef], column: str, is_subject: bool) -> URIRef:
    column_tokens = _tokens(column)
    preferred = ("name", "title", "officialname", "label") if is_subject else ("description", "name", "title", "officialname")
    for preferred_name in preferred:
        for property_uri in properties:
            if _local_name(property_uri).lower() == preferred_name:
                return property_uri
    ranked = sorted(
        properties,
        key=lambda property_uri: (
            -len(_tokens(_local_name(property_uri)) & column_tokens),
            str(property_uri),
        ),
    )
    return ranked[0]


def _csv_mapping_suggestions(plan: CsvImportPlan, ontology_graph: Graph, data_dir: Path) -> list[str]:
    terms = inspect_ontology_terms(ontology_graph)
    string_properties = _string_compatible_properties(ontology_graph, terms.properties)
    suggestions: list[str] = []
    if not string_properties:
        return suggestions
    for mapping in plan.mappings:
        path = data_dir / mapping.csv_file
        if not mapping.csv_file or not path.is_file():
            continue
        profile = profile_csv(path)
        columns = {column.name for column in profile.columns}
        for column_mapping in mapping.column_mappings:
            if column_mapping.column not in columns:
                continue
            property_uri = URIRef(column_mapping.property_uri)
            datatype_uri = DATATYPE_URIS.get(column_mapping.datatype)
            replacement = _best_string_property(string_properties, column_mapping.column, is_subject=False)
            replacement_description = _property_suggestion_description(terms, replacement)
            if property_uri not in terms.properties:
                suggestions.append(
                    f"{column_mapping.property_uri} does not exist; consider using {replacement_description} "
                    f"for column {column_mapping.column} instead"
                )
            elif datatype_uri is None or not _property_accepts_range(ontology_graph, property_uri, datatype_uri):
                suggestions.append(
                    f"{column_mapping.property_uri} is incompatible for column {column_mapping.column}; "
                    f"consider using {replacement_description} as a string literal property instead"
                )
        for relationship in mapping.relationship_mappings:
            if relationship.column not in columns:
                continue
            property_uri = URIRef(relationship.property_uri)
            target_class = URIRef(relationship.target_class_uri)
            replacement = _best_string_property(string_properties, relationship.column, is_subject=False)
            replacement_description = _property_suggestion_description(terms, replacement)
            if property_uri not in terms.properties:
                suggestions.append(
                    f"{relationship.property_uri} does not exist; consider using {replacement_description} "
                    f"for column {relationship.column} as a literal mapping instead"
                )
            elif target_class not in terms.classes or not _property_accepts_range(ontology_graph, property_uri, target_class):
                suggestions.append(
                    f"{relationship.property_uri} is incompatible for relationship column {relationship.column}; "
                    f"consider using {replacement_description} as a string literal property instead"
                )
    return suggestions


def _property_suggestion_description(terms, property_uri: URIRef) -> str:
    parts = [str(property_uri)]
    label = terms.labels.get(property_uri, "")
    comment = terms.comments.get(property_uri, "")
    if label:
        parts.append(f"label: {label}")
    if comment:
        parts.append(f"comment: {comment}")
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} ({'; '.join(parts[1:])})"


def _local_name(uri: URIRef) -> str:
    text = str(uri)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def _tokens(value: str) -> set[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    return {token.lower() for token in SLUG_RE.split(spaced) if token}


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
