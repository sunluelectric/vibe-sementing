from __future__ import annotations

from rdflib import RDF, RDFS, Namespace, URIRef, XSD

from src.importer.csv_import import (
    CsvColumnMapping,
    CsvFileMapping,
    CsvImportPlan,
    CsvRelationshipMapping,
    generate_csv_instances,
    parse_csv_import_plan,
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
