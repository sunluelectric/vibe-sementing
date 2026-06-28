from __future__ import annotations

from rdflib import RDF, RDFS, Namespace, URIRef, XSD

from src.importer.csv_import import (
    CsvColumnMapping,
    CsvFileMapping,
    CsvImportPlan,
    CsvRelationshipMapping,
    csv_mapping_feedback_with_suggestions,
    fallback_csv_import_plan,
    generate_csv_instances,
    parse_csv_import_plan,
    repair_csv_import_plan,
    validate_csv_import_plan,
)
from src.common.rdf import parse_turtle


ONTOLOGY = """
@prefix sw: <http://example.org/semantic-web#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

sw:Triplestore a rdfs:Class .
sw:Organization a rdfs:Class .
sw:name a rdf:Property ; rdfs:domain rdfs:Resource ; rdfs:range xsd:string .
sw:licenseType a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range xsd:string .
sw:isOpenSource a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range xsd:boolean .
sw:rating a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range xsd:decimal .
sw:externalCode a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range xsd:string .
sw:maintainedBy a rdf:Property ; rdfs:domain sw:Triplestore ; rdfs:range sw:Organization .
"""


def _csv_fixture(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "stores.csv").write_text(
        "Triplestore Name,Developer/Maintainer,License Type,Open Source\n"
        "Apache Jena TDB,Apache Software Foundation,Apache 2.0,true\n"
        "GraphDB,Ontotext,Commercial / Free Edition,false\n",
        encoding="utf-8",
    )
    return data_dir


def _valid_plan() -> CsvImportPlan:
    return CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Triplestore",
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                label_template="{Triplestore Name}",
                column_mappings=(
                    CsvColumnMapping(
                        column="Triplestore Name",
                        property_uri="http://example.org/semantic-web#name",
                        datatype="string",
                    ),
                    CsvColumnMapping(
                        column="License Type",
                        property_uri="http://example.org/semantic-web#licenseType",
                        datatype="string",
                    ),
                    CsvColumnMapping(
                        column="Open Source",
                        property_uri="http://example.org/semantic-web#isOpenSource",
                        datatype="boolean",
                    ),
                ),
                relationship_mappings=(
                    CsvRelationshipMapping(
                        column="Developer/Maintainer",
                        property_uri="http://example.org/semantic-web#maintainedBy",
                        target_class_uri="http://example.org/semantic-web#Organization",
                        target_uri_template="http://example.org/semantic-web/instance/organization/{Developer/Maintainer|slug}",
                        target_label_template="{Developer/Maintainer}",
                    ),
                ),
            ),
        )
    )


def test_parse_csv_import_plan_from_mapping_json() -> None:
    plan = parse_csv_import_plan(
        {
            "mappings": [
                {
                    "csv_file": "stores.csv",
                    "row_class": "http://example.org/semantic-web#Triplestore",
                    "subject_uri_template": "http://example.org/item/{Name|slug}",
                    "column_mappings": [
                        {
                            "column": "Name",
                            "property": "http://example.org/semantic-web#name",
                            "datatype": "string",
                        }
                    ],
                }
            ]
        }
    )

    assert plan.mappings[0].csv_file == "stores.csv"
    assert plan.mappings[0].column_mappings[0].datatype == "string"


def test_validate_csv_import_plan_rejects_unknown_terms_and_columns(tmp_path) -> None:
    data_dir = _csv_fixture(tmp_path)
    ontology_graph = parse_turtle(ONTOLOGY)
    bad_plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Missing",
                subject_uri_template="http://example.org/item/{Missing Column|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="Missing Column",
                        property_uri="http://example.org/semantic-web#missingProperty",
                    ),
                ),
            ),
        )
    )

    result = validate_csv_import_plan(bad_plan, ontology_graph, data_dir)

    assert not result.ok
    errors = "; ".join(result.errors)
    assert "not defined in the ontology" in errors
    assert "unknown column" in errors or "does not exist" in errors


def test_generate_csv_instances_deterministically_converts_rows(tmp_path) -> None:
    data_dir = _csv_fixture(tmp_path)
    ontology_graph = parse_turtle(ONTOLOGY)
    sw = Namespace("http://example.org/semantic-web#")
    inst = Namespace("http://example.org/semantic-web/instance/")

    graph = generate_csv_instances(_valid_plan(), ontology_graph, data_dir)

    jena = URIRef(inst["triplestore/apache-jena-tdb"])
    apache = URIRef(inst["organization/apache-software-foundation"])
    assert (jena, RDF.type, sw.Triplestore) in graph
    assert (jena, RDFS.label, None) in graph
    assert (jena, sw.maintainedBy, apache) in graph
    assert (apache, RDF.type, sw.Organization) in graph
    assert (jena, sw.isOpenSource, None) in graph
    assert any(str(obj) == "true" and obj.datatype == XSD.boolean for obj in graph.objects(jena, sw.isOpenSource))


def test_fallback_csv_import_plan_uses_existing_string_properties(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "commonly seen triplestores.csv").write_text(
        "Triplestore Name,Developer/Maintainer,License Type\n"
        "GraphDB,Ontotext,Commercial / Free Edition\n",
        encoding="utf-8",
    )
    ontology_graph = parse_turtle(
        """
        @prefix sw: <http://example.org/semantic-web#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        sw:Entity a rdfs:Class .
        sw:Triplestore a rdfs:Class ; rdfs:subClassOf sw:Entity .
        sw:name a rdf:Property ; rdfs:domain sw:Entity ; rdfs:range xsd:string .
        sw:description a rdf:Property ; rdfs:domain sw:Entity ; rdfs:range xsd:string .
        """
    )
    sw = Namespace("http://example.org/semantic-web#")

    plan = fallback_csv_import_plan(ontology_graph, data_dir)
    validation = validate_csv_import_plan(plan, ontology_graph, data_dir)
    graph = generate_csv_instances(plan, ontology_graph, data_dir)

    assert validation.ok
    assert plan.mappings[0].row_class_uri == str(sw.Triplestore)
    assert {mapping.property_uri for mapping in plan.mappings[0].column_mappings} <= {str(sw.name), str(sw.description)}
    assert len(graph) >= 5


def test_csv_mapping_feedback_suggests_existing_property_for_missing_term(tmp_path) -> None:
    data_dir = _csv_fixture(tmp_path)
    ontology_graph = parse_turtle(ONTOLOGY)
    plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Triplestore",
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="Triplestore Name",
                        property_uri="http://example.org/semantic-web#triplestoreName",
                    ),
                ),
            ),
        )
    )

    feedback = csv_mapping_feedback_with_suggestions(plan, ontology_graph, data_dir)

    assert "http://example.org/semantic-web#triplestoreName does not exist" in feedback
    assert "consider using http://example.org/semantic-web#name" in feedback


def test_csv_mapping_feedback_suggestions_include_property_labels_and_comments(tmp_path) -> None:
    data_dir = _csv_fixture(tmp_path)
    ontology_graph = parse_turtle(
        """
        @prefix sw: <http://example.org/semantic-web#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        sw:Triplestore a rdfs:Class ;
            rdfs:label "Triplestore" ;
            rdfs:comment "A database system optimized for RDF triples." .
        sw:name a rdf:Property ;
            rdfs:label "name" ;
            rdfs:comment "The display name of a triplestore." ;
            rdfs:domain sw:Triplestore ;
            rdfs:range xsd:string .
        """
    )
    plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Triplestore",
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="Triplestore Name",
                        property_uri="http://example.org/semantic-web#triplestoreName",
                    ),
                ),
            ),
        )
    )

    feedback = csv_mapping_feedback_with_suggestions(plan, ontology_graph, data_dir)

    assert "consider using http://example.org/semantic-web#name" in feedback
    assert "label: name" in feedback
    assert "comment: The display name of a triplestore." in feedback


def test_repair_csv_import_plan_preserves_valid_columns_and_repairs_invalid_relationships(tmp_path) -> None:
    data_dir = _csv_fixture(tmp_path)
    ontology_graph = parse_turtle(ONTOLOGY)
    sw = Namespace("http://example.org/semantic-web#")
    plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri=str(sw.Triplestore),
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="License Type",
                        property_uri=str(sw.licenseType),
                    ),
                    CsvColumnMapping(
                        column="Triplestore Name",
                        property_uri="http://example.org/semantic-web#triplestoreName",
                    ),
                ),
                relationship_mappings=(
                    CsvRelationshipMapping(
                        column="Developer/Maintainer",
                        property_uri="http://example.org/semantic-web#developedBy",
                        target_class_uri=str(sw.Organization),
                        target_uri_template="http://example.org/semantic-web/instance/organization/{Developer/Maintainer|slug}",
                    ),
                ),
            ),
        )
    )

    repaired = repair_csv_import_plan(plan, ontology_graph, data_dir)
    validation = validate_csv_import_plan(repaired, ontology_graph, data_dir)
    mapping = repaired.mappings[0]

    assert validation.ok
    assert any(column.column == "License Type" and column.property_uri == str(sw.licenseType) for column in mapping.column_mappings)
    assert any(column.column == "Triplestore Name" and column.property_uri == str(sw.name) for column in mapping.column_mappings)
    assert any(column.column == "Developer/Maintainer" and column.property_uri == str(sw.name) for column in mapping.column_mappings)
    assert mapping.relationship_mappings == ()


def test_csv_import_widens_integer_mapping_to_decimal_range(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "stores.csv").write_text(
        "Triplestore Name,Rating\n"
        "Apache Jena TDB,5\n"
        "GraphDB,4.5\n",
        encoding="utf-8",
    )
    ontology_graph = parse_turtle(ONTOLOGY)
    sw = Namespace("http://example.org/semantic-web#")
    inst = Namespace("http://example.org/semantic-web/instance/")
    plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Triplestore",
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="Rating",
                        property_uri="http://example.org/semantic-web#rating",
                        datatype="integer",
                    ),
                ),
            ),
        )
    )

    validation = validate_csv_import_plan(plan, ontology_graph, data_dir)
    graph = generate_csv_instances(plan, ontology_graph, data_dir)

    assert validation.ok
    graphdb = URIRef(inst["triplestore/graphdb"])
    assert any(str(obj) == "4.5" and obj.datatype == XSD.decimal for obj in graph.objects(graphdb, sw.rating))


def test_csv_import_falls_back_to_string_when_range_allows_string(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "stores.csv").write_text(
        "Triplestore Name,External Code\n"
        "Apache Jena TDB,00123\n"
        "GraphDB,A-45\n",
        encoding="utf-8",
    )
    ontology_graph = parse_turtle(ONTOLOGY)
    sw = Namespace("http://example.org/semantic-web#")
    inst = Namespace("http://example.org/semantic-web/instance/")
    plan = CsvImportPlan(
        mappings=(
            CsvFileMapping(
                csv_file="stores.csv",
                row_class_uri="http://example.org/semantic-web#Triplestore",
                subject_uri_template="http://example.org/semantic-web/instance/triplestore/{Triplestore Name|slug}",
                column_mappings=(
                    CsvColumnMapping(
                        column="External Code",
                        property_uri="http://example.org/semantic-web#externalCode",
                        datatype="integer",
                    ),
                ),
            ),
        )
    )

    validation = validate_csv_import_plan(plan, ontology_graph, data_dir)
    graph = generate_csv_instances(plan, ontology_graph, data_dir)

    assert validation.ok
    graphdb = URIRef(inst["triplestore/graphdb"])
    assert any(str(obj) == "A-45" and obj.datatype == XSD.string for obj in graph.objects(graphdb, sw.externalCode))
