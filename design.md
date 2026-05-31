# Design: Compact RDF/RDFS schema for the adventure

## Purpose
This small RDF/RDFS schema models the core entities needed to import a Dungeons & Dragons-style adventure document (like sample_adventure.md) into an RDF triplestore (e.g., Apache Jena Fuseki). The schema focuses on canonical named entities and basic attributes and provenance needed for queries such as:

- "List all NPCs, players, and monsters and their levels." 
- "Which scene mentions the merchant's chest and how much gold was taken?"
- "What is the quest reward for the adventure and which scene contains the quest description?"

Design goals:
- Compact and easy to import and extend later.
- Use only RDFS (no OWL features) as requested.
- Model core domain concepts: characters (player/NPC/monster), items (weapon/treasure/container), quests, locations (settlement/dungeon), scene and document provenance, and races.
- Provide practical properties with domain/range to support data import (names, counts, levels, gold amounts, locations, scene provenance).


## Main classes
(Each class is an rdfs:Class in the Turtle ontology)

- sw:Entity
  - Top-level, reusable class for named things in the adventure (used as domain for general properties like sw:name).

- sw:Character (rdfs:subClassOf sw:Entity)
  - Abstract class for person-like game entities (players, NPCs, monsters).

- sw:Player (rdfs:subClassOf sw:Character)
  - Player characters controlled by players.

- sw:Npc (rdfs:subClassOf sw:Character)
  - Non-player characters (villagers, merchants, elders).

- sw:Monster (rdfs:subClassOf sw:Character)
  - Hostile creatures (goblins, wolves, etc.).

- sw:Item (rdfs:subClassOf sw:Entity)
  - Generic item class (treasures, weapons, containers).

- sw:Weapon (rdfs:subClassOf sw:Item)
  - Items intended primarily as weapons (e.g., dagger).

- sw:Treasure (rdfs:subClassOf sw:Item)
  - Monetary or heirloom items (coins, family heirlooms).

- sw:Container (rdfs:subClassOf sw:Item)
  - Things that can contain other items (chests, bags).

- sw:Quest (rdfs:subClassOf sw:Entity)
  - Represents an objective or mission (e.g., retrieve stolen goods).

- sw:Location (rdfs:subClassOf sw:Entity)
  - Place where things happen (village, cave system).

- sw:Settlement (rdfs:subClassOf sw:Location)
  - Villages, towns.

- sw:Dungeon (rdfs:subClassOf sw:Location)
  - Caves, dungeons, burrows.

- sw:Scene (rdfs:subClassOf sw:Entity)
  - Document/scene unit (a header/section in a source file) that groups mentions.

- sw:SourceDocument (rdfs:Class)
  - Represents an input file or document (e.g., sample_adventure.md). Used for provenance.

- sw:Race (rdfs:Class)
  - Playable races (Human, Elf, Dwarf).


(Total classes in this schema: 16)


## Core properties
(Selected to be broad and practical; each has rdfs:domain / rdfs:range where appropriate.)

Datatype properties

- sw:name (xsd:string)
  - Human-readable canonical name for Entities, Locations, Scenes, etc.
  - Domain: sw:Entity

- sw:canonicalId (xsd:string)
  - Normalized identifier or slug for an entity (useful for stable URIs when generating instance IRIs).
  - Domain: sw:Entity

- sw:roleLabel (xsd:string)
  - Free-text role or label for characters (e.g., "merchant", "village elder").
  - Domain: sw:Character

- sw:count (xsd:integer)
  - Quantity of identical items or number of creatures.
  - Domain: sw:Item

- sw:level (xsd:integer)
  - NPC/Monster/Player level or recommended quest level.
  - Domain: sw:Character and sw:Quest

- sw:goldAmount (xsd:integer)
  - Numeric gold value (unit gp implied).
  - Domain: sw:Treasure and sw:Quest

- sw:currency (xsd:string)
  - Currency label (e.g., "gp").
  - Domain: sw:Treasure

- sw:description (xsd:string)
  - Short descriptive text for an entity/scene.
  - Domain: sw:Entity

- sw:sourceFile (xsd:string)
  - Filename literal (alternative to linking a full SourceDocument resource).
  - Domain: sw:SourceDocument

- sw:sourceSceneHeading (xsd:string)
  - The heading text of the scene where an entity occurs (from the source document).
  - Domain: sw:Scene

Object properties

- sw:occursInScene (range sw:Scene)
  - Link an entity (character/item/quest) to the Scene where it is mentioned.
  - Domain: sw:Entity

- sw:locatedIn (range sw:Location)
  - Spatial containment: where an entity currently or originally is (e.g., "Aldric Thorn locatedIn Millhaven").
  - Domain: sw:Entity

- sw:containsItem (range sw:Item)
  - Container -> Item containment (e.g., chest contains dagger).
  - Domain: sw:Container

- sw:hasResident (range sw:Character)
  - Location -> Character membership (who resides in or is found at a location).
  - Domain: sw:Location

- sw:reward (range sw:Treasure)
  - Quest -> Treasure link for reward amounts or items.
  - Domain: sw:Quest

- sw:provenanceDocument (range sw:SourceDocument)
  - Links a Scene to the SourceDocument (file) it comes from.
  - Domain: sw:Scene

- sw:hasRace (range sw:Race)
  - Player -> Race link.
  - Domain: sw:Player


(Total properties in this schema: 17 — intentionally broad and reusable.)


## How this maps to the supplied data
From the sample_adventure.md example, the following mappings would be used when converting the document into RDF:

- "Aldric Thorn" -> instance of sw:Npc with sw:name "Aldric Thorn"; sw:roleLabel "merchant"; sw:locatedIn -> instance sw:Settlement "Millhaven"; occurrences linked to a sw:Scene whose sw:sourceSceneHeading is the heading text; the Scene sw:provenanceDocument points to a sw:SourceDocument for sample_adventure.md (and that SourceDocument may have sw:sourceFile "sample_adventure.md").

- "chest containing 200 gold pieces and a family heirloom dagger" -> sw:Container (chest) with sw:containsItem some sw:Treasure (200 gp) and sw:containsItem some sw:Weapon (dagger). The sw:Treasure would have sw:goldAmount 200 and sw:currency "gp".

- "The village elder has offered a reward of 50 gold pieces" -> a sw:Quest instance with sw:reward linking to a sw:Treasure instance (goldAmount 50, currency "gp") and sw:occursInScene pointing to the Scene that contains this text.

- "Available Player Classes" and "Available Races" -> sw:Race instances (Human, Elf, Dwarf) associated with sw:Player instances via sw:hasRace as needed.

- Party size and recommended level -> sw:recommended party size is not modeled as dedicated properties in this first compact schema; recommended level is modeled via sw:level on sw:Quest. If needed, cheap additions can be made later (sw:recommendedPartySizeMin/Max).


## URI patterns and import notes
- Ontology base: http://example.org/semantic-web#
- Instance URIs (recommended patterns):
  - Characters: http://example.org/adventure/character/{slug}
  - Items: http://example.org/adventure/item/{slug}
  - Scenes: http://example.org/adventure/scene/{slug}
  - Documents: http://example.org/adventure/doc/{filename}

Use sw:canonicalId to store the slug (lowercase, hyphenated) and map that into instance IRIs when generating data.

When importing text sections into RDF:
- Create a sw:Scene resource for each logical section/header and attach sw:sourceSceneHeading and sw:provenanceDocument.
- For each mention in the scene, create a typed instance (sw:Npc, sw:Treasure, etc.), set sw:name and numerical properties (level, goldAmount), then link to the scene using sw:occursInScene.


## Extension ideas (future versions)
- Add sw:GameClass as a class and properties for class abilities, spells, or level progression.
- Model ability scores, HP, armor class as datatype properties or a related class.
- Add a more formal provenance model (e.g., Dublin Core or PROV) if needed.
- Add constraints or shapes (SHACL) for validation after the schema stabilizes.


## RDFS-only rationale
This schema intentionally uses only rdfs:Class and rdf:Property with rdfs:domain and rdfs:range. That keeps the ontology simple to load into Fuseki and simple to expand later with OWL or SHACL if richer semantics are required.


## Minimal example (not data, just an example of triple intent)
- :goblin-ambush a sw:Scene ; sw:sourceSceneHeading "The Goblin Cave of Ashenvale" ; sw:provenanceDocument :sample_adventure_md .
- :aldric-thorn a sw:Npc ; sw:name "Aldric Thorn" ; sw:roleLabel "merchant" ; sw:locatedIn :millhaven ; sw:occursInScene :goblin-ambush .

This shows how scene provenance ties back to the source document and how characters and items are linked to scenes and locations.


## Loading into Fuseki
- Save the Turtle (ontology_turtle below) into a file (e.g., sw-schema.ttl).
- Load it into Fuseki as a dataset's ontology graph or default graph. Use the Fuseki web UI or `tdbloader2` / `s-put` / curl. Data files (instances) can then be uploaded into the same dataset.


## Contact and next steps
- After the first data import, review typical queries and add targeted properties (e.g., HP, armorClass, or recommended party size) only if they are actually needed by queries. This keeps the schema compact and practical.


---

End of design.md

## Designer Generation Log

## Retrieval Focus Planning

- Status: LLM request started
- Timestamp: 2026-05-31T10:02:11+00:00
- Max focuses: 2

## Retrieval Focus Planning Result

- Status: passed
- Focus count: 2
- Query: Find all named entity mentions and instantiations: Npc, Player, Monster, Weapon, Item (treasure), Location, Scene, Quest; return entity name, asserted type/role label, numeric attributes (count, level, gold), and source context (file and scene heading).
- Query: Find all relational and event statements: ambushed, attacked-by, owns/loses, gives/pays (reward), exit-to (scene links), occurs-at/time-of-day, victory-condition, XP-reward; return subject, verb/predicate phrase, object, quantitative values, and scene context.

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T10:02:25+00:00
- Query: Find all named entity mentions and instantiations: Npc, Player, Monster, Weapon, Item (treasure), Location, Scene, Quest; return entity name, asserted type/role label, numeric attributes (count, level, gold), and source context (file and scene heading).
- Context characters: 1200

## Schema Slice Draft Result

- Status: passed
- Query: Find all named entity mentions and instantiations: Npc, Player, Monster, Weapon, Item (treasure), Location, Scene, Quest; return entity name, asserted type/role label, numeric attributes (count, level, gold), and source context (file and scene heading).
- Notes characters: 6833

## Schema Slice Draft

- Status: LLM request started
- Timestamp: 2026-05-31T10:03:00+00:00
- Query: Find all relational and event statements: ambushed, attacked-by, owns/loses, gives/pays (reward), exit-to (scene links), occurs-at/time-of-day, victory-condition, XP-reward; return subject, verb/predicate phrase, object, quantitative values, and scene context.
- Context characters: 1200

## Schema Slice Draft Result

- Status: passed
- Query: Find all relational and event statements: ambushed, attacked-by, owns/loses, gives/pays (reward), exit-to (scene links), occurs-at/time-of-day, victory-condition, XP-reward; return subject, verb/predicate phrase, object, quantitative values, and scene context.
- Notes characters: 8055

# Semantic Web Designer Progress

- Model: `gpt-5-mini`
- Max attempts: 2
- Started: 2026-05-31T10:03:37+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-05-31T10:03:37+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-05-31T10:06:36+00:00
- Response characters: 15770

## Attempt 1 Validation

- Status: passed
- Triple count: 148

### Candidate Design

# Design: Compact RDF/RDFS schema for the adventure

## Purpose
This small RDF/RDFS schema models the core entities needed to import a Dungeons & Dragons-style adventure document (like sample_adventure.md) into an RDF triplestore (e.g., Apache Jena Fuseki). The schema focuses on canonical named entities and basic attributes and provenance needed for queries such as:

- "List all NPCs, players, and monsters and their levels." 
- "Which scene mentions the merchant's chest and how much gold was taken?"
- "What is the quest reward for the adventure and which scene contains the quest description?"

Design goals:
- Compact and easy to import and extend later.
- Use only RDFS (no OWL features) as requested.
- Model core domain concepts: characters (player/NPC/monster), items (weapon/treasure/container), quests, locations (settlement/dungeon), scene and document provenance, and races.
- Provide practical properties with domain/range to support data import (names, counts, levels, gold amounts, locations, scene provenance).


## Main classes
(Each class is an rdfs:Class in the Turtle ontology)

- sw:Entity
  - Top-level, reusable class for named things in the adventure (used as domain for general properties like sw:name).

- sw:Character (rdfs:subClassOf sw:Entity)
  - Abstract class for person-like game entities (players, NPCs, monsters).

- sw:Player (rdfs:subClassOf sw:Character)
  - Player characters controlled by players.

- sw:Npc (rdfs:subClassOf sw:Character)
  - Non-player characters (villagers, merchants, elders).

- sw:Monster (rdfs:subClassOf sw:Character)
  - Hostile creatures (goblins, wolves, etc.).

- sw:Item (rdfs:subClassOf sw:Entity)
  - Generic item class (treasures, weapons, containers).

- sw:Weapon (rdfs:subClassOf sw:Item)
  - Items intended primarily as weapons (e.g., dagger).

- sw:Treasure (rdfs:subClassOf sw:Item)
  - Monetary or heirloom items (coins, family heirlooms).

- sw:Container (rdfs:subClassOf sw:Item)
  - Things that can contain other items (chests, bags).

- sw:Quest (rdfs:subClassOf sw:Entity)
  - Represents an objective or mission (e.g., retrieve stolen goods).

- sw:Location (rdfs:subClassOf sw:Entity)
  - Place where things happen (village, cave system).

- sw:Settlement (rdfs:subClassOf sw:Location)
  - Villages, towns.

- sw:Dungeon (rdfs:subClassOf sw:Location)
  - Caves, dungeons, burrows.

- sw:Scene (rdfs:subClassOf sw:Entity)
  - Document/scene unit (a header/section in a source file) that groups mentions.

- sw:SourceDocument (rdfs:Class)
  - Represents an input file or document (e.g., sample_adventure.md). Used for provenance.

- sw:Race (rdfs:Class)
  - Playable races (Human, Elf, Dwarf).


(Total classes in this schema: 16)


## Core properties
(Selected to be broad and practical; each has rdfs:domain / rdfs:range where appropriate.)

Datatype properties

- sw:name (xsd:string)
  - Human-readable canonical name for Entities, Locations, Scenes, etc.
  - Domain: sw:Entity

- sw:canonicalId (xsd:string)
  - Normalized identifier or slug for an entity (useful for stable URIs when generating instance IRIs).
  - Domain: sw:Entity

- sw:roleLabel (xsd:string)
  - Free-text role or label for characters (e.g., "merchant", "village elder").
  - Domain: sw:Character

- sw:count (xsd:integer)
  - Quantity of identical items or number of creatures.
  - Domain: sw:Item

- sw:level (xsd:integer)
  - NPC/Monster/Player level or recommended quest level.
  - Domain: sw:Character and sw:Quest

- sw:goldAmount (xsd:integer)
  - Numeric gold value (unit gp implied).
  - Domain: sw:Treasure and sw:Quest

- sw:currency (xsd:string)
  - Currency label (e.g., "gp").
  - Domain: sw:Treasure

- sw:description (xsd:string)
  - Short descriptive text for an entity/scene.
  - Domain: sw:Entity

- sw:sourceFile (xsd:string)
  - Filename literal (alternative to linking a full SourceDocument resource).
  - Domain: sw:SourceDocument

- sw:sourceSceneHeading (xsd:string)
  - The heading text of the scene where an entity occurs (from the source document).
  - Domain: sw:Scene

Object properties

- sw:occursInScene (range sw:Scene)
  - Link an entity (character/item/quest) to the Scene where it is mentioned.
  - Domain: sw:Entity

- sw:locatedIn (range sw:Location)
  - Spatial containment: where an entity currently or originally is (e.g., "Aldric Thorn locatedIn Millhaven").
  - Domain: sw:Entity

- sw:containsItem (range sw:Item)
  - Container -> Item containment (e.g., chest contains dagger).
  - Domain: sw:Container

- sw:hasResident (range sw:Character)
  - Location -> Character membership (who resides in or is found at a location).
  - Domain: sw:Location

- sw:reward (range sw:Treasure)
  - Quest -> Treasure link for reward amounts or items.
  - Domain: sw:Quest

- sw:provenanceDocument (range sw:SourceDocument)
  - Links a Scene to the SourceDocument (file) it comes from.
  - Domain: sw:Scene

- sw:hasRace (range sw:Race)
  - Player -> Race link.
  - Domain: sw:Player


(Total properties in this schema: 17 — intentionally broad and reusable.)


## How this maps to the supplied data
From the sample_adventure.md example, the following mappings would be used when converting the document into RDF:

- "Aldric Thorn" -> instance of sw:Npc with sw:name "Aldric Thorn"; sw:roleLabel "merchant"; sw:locatedIn -> instance sw:Settlement "Millhaven"; occurrences linked to a sw:Scene whose sw:sourceSceneHeading is the heading text; the Scene sw:provenanceDocument points to a sw:SourceDocument for sample_adventure.md (and that SourceDocument may have sw:sourceFile "sample_adventure.md").

- "chest containing 200 gold pieces and a family heirloom dagger" -> sw:Container (chest) with sw:containsItem some sw:Treasure (200 gp) and sw:containsItem some sw:Weapon (dagger). The sw:Treasure would have sw:goldAmount 200 and sw:currency "gp".

- "The village elder has offered a reward of 50 gold pieces" -> a sw:Quest instance with sw:reward linking to a sw:Treasure instance (goldAmount 50, currency "gp") and sw:occursInScene pointing to the Scene that contains this text.

- "Available Player Classes" and "Available Races" -> sw:Race instances (Human, Elf, Dwarf) associated with sw:Player instances via sw:hasRace as needed.

- Party size and recommended level -> sw:recommended party size is not modeled as dedicated properties in this first compact schema; recommended level is modeled via sw:level on sw:Quest. If needed, cheap additions can be made later (sw:recommendedPartySizeMin/Max).


## URI patterns and import notes
- Ontology base: http://example.org/semantic-web#
- Instance URIs (recommended patterns):
  - Characters: http://example.org/adventure/character/{slug}
  - Items: http://example.org/adventure/item/{slug}
  - Scenes: http://example.org/adventure/scene/{slug}
  - Documents: http://example.org/adventure/doc/{filename}

Use sw:canonicalId to store the slug (lowercase, hyphenated) and map that into instance IRIs when generating data.

When importing text sections into RDF:
- Create a sw:Scene resource for each logical section/header and attach sw:sourceSceneHeading and sw:provenanceDocument.
- For each mention in the scene, create a typed instance (sw:Npc, sw:Treasure, etc.), set sw:name and numerical properties (level, goldAmount), then link to the scene using sw:occursInScene.


## Extension ideas (future versions)
- Add sw:GameClass as a class and properties for class abilities, spells, or level progression.
- Model ability scores, HP, armor class as datatype properties or a related class.
- Add a more formal provenance model (e.g., Dublin Core or PROV) if needed.
- Add constraints or shapes (SHACL) for validation after the schema stabilizes.


## RDFS-only rationale
This schema intentionally uses only rdfs:Class and rdf:Property with rdfs:domain and rdfs:range. That keeps the ontology simple to load into Fuseki and simple to expand later with OWL or SHACL if richer semantics are required.


## Minimal example (not data, just an example of triple intent)
- :goblin-ambush a sw:Scene ; sw:sourceSceneHeading "The Goblin Cave of Ashenvale" ; sw:provenanceDocument :sample_adventure_md .
- :aldric-thorn a sw:Npc ; sw:name "Aldric Thorn" ; sw:roleLabel "merchant" ; sw:locatedIn :millhaven ; sw:occursInScene :goblin-ambush .

This shows how scene provenance ties back to the source document and how characters and items are linked to scenes and locations.


## Loading into Fuseki
- Save the Turtle (ontology_turtle below) into a file (e.g., sw-schema.ttl).
- Load it into Fuseki as a dataset's ontology graph or default graph. Use the Fuseki web UI or `tdbloader2` / `s-put` / curl. Data files (instances) can then be uploaded into the same dataset.


## Contact and next steps
- After the first data import, review typical queries and add targeted properties (e.g., HP, armorClass, or recommended party size) only if they are actually needed by queries. This keeps the schema compact and practical.


---

End of design.md

