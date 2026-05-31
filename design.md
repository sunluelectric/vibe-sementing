# Design for semantic-web (design.md)

## Overview

This document describes a compact RDF/RDFS schema to represent the provided Dungeons & Dragons beginner adventure "The Goblin Cave of Ashenvale". The schema is intentionally small and pragmatic so it can be imported into Apache Jena Fuseki and extended later. It covers the core concepts required to import the adventure text and to answer common queries such as: which scenes belong to the adventure, which NPCs and monsters appear in each scene, what items or loot are present, numeric stats (HP, AC, XP), and adventure-level metadata (difficulty, recommended party size, reward).

Design goals
- Keep the vocabulary small (about a dozen classes and a few dozen properties).
- Use only RDF and RDFS (no OWL) as requested.
- Use domain terminology from the adventure (Adventure, Scene, Npc, Monster, Player, Item, Weapon, Chest, Potion, PlayerClass, Race, Location).
- Provide practical datatype properties for numeric values used in gameplay (hp, armorClass, xpValue, goldAmount, recommendedLevel, party size, DCs).
- Provide object properties to link scenes, characters, items and to express containment and carrying relationships.
- Provide rdfs:label and rdfs:comment for important classes and properties to aid manual browsing and programmatic use.

## Modeling decisions and rationale
- Adventure is the top-level container for the scenario (metadata, recommended level/party, available player classes/races, scenes).
- Scene models each gameplay scene (Village, Hillside Trail, Goblin Warren, Return). Scenes link to a Location for short place metadata and to other scenes via sw:leadsTo for exits.
- Character is a general class; Player, Npc, and Monster are shallow subclasses. This allows queries that want "all Characters in a Scene" or only Monsters/NPCs.
- Items are grouped under Item with obvious subclasses (Weapon, Potion, Chest). Chests may contain items; characters may carry items. Items have descriptive/damage fields suitable for import of the provided item text (e.g., "1d4+1 piercing").
- Numeric/stat properties (hp, armorClass, xpValue, goldAmount) are datatype properties with xsd:integer/decimal types so they can be used in numerical queries and aggregations.
- Several textual properties (sceneDescription, objectiveText, abilityText, attack descriptions) are modeled as datatype properties (xsd:string). These allow the DM notes and flavor text to be imported and displayed.

This model avoids fine-grained constructs such as separate Attack objects, multiple attack entries per monster, or skill proficiencies; those can be added later if needed.

## Classes (short description)
- sw:Adventure — top-level scenario container (difficulty, scenes, reward, recommendations).
- sw:Scene — a scene in the adventure (has location, objectives, description, exits).
- sw:Location — short place metadata (e.g. "Millhaven", "Hillside Trail").
- sw:Character — abstract character superclass for all sentient actors.
- sw:Player — playable character (subclass of Character).
- sw:Npc — non-player characters (quest givers, villagers) (subclass of Character).
- sw:Monster — monsters/enemies (subclass of Character).
- sw:Item — generic item.
- sw:Weapon — weapon (subclass of Item).
- sw:Potion — consumable healing potion (subclass of Item).
- sw:Chest — container item that can contain items (subclass of Item).
- sw:PlayerClass — player class option (Fighter, Wizard, Rogue).
- sw:Race — player race option (Human, Elf, Dwarf).

## Important properties (short description)
Object properties
- sw:hasScene (Adventure -> Scene): lists scenes that belong to an adventure.
- sw:hasLocation (Scene -> Location): associates a scene with a named place.
- sw:leadsTo (Scene -> Scene): links scene exits to other scenes.
- sw:hasNPC (Scene -> Npc): NPCs present in a scene.
- sw:hasMonster (Scene -> Monster): Monsters present in a scene.
- sw:hasItem (Scene -> Item): Items placed in the scene environment.
- sw:carries (Character -> Item): items carried by a character (loot, equipment).
- sw:offersClass (Adventure -> PlayerClass): player classes available for the adventure.
- sw:hasRaceOption (Adventure -> Race): player race options for the adventure.
- sw:contains (Chest -> Item): items contained in a chest.
- sw:encounters (Scene -> Character): a flexible scene->character link for any encounter listing.

Datatype properties
- sw:objectiveText (Scene -> xsd:string): short in-scene objective text.
- sw:sceneDescription (Scene -> xsd:string): descriptive/DM notes for the scene.
- sw:hp (Character -> xsd:integer): hit points for a character/monster.
- sw:armorClass (Character -> xsd:integer): armor class.
- sw:attackBonus (Character -> xsd:integer): numeric attack bonus used in the adventure text.
- sw:damage (Item -> xsd:string): textual damage expression (e.g. "1d4+1 piercing").
- sw:abilityText (Character -> xsd:string): textual abilities (e.g. "Nimble Escape").
- sw:xpValue (Character -> xsd:integer): XP awarded for defeating a monster.
- sw:goldAmount (Item -> xsd:decimal): gold amount (for chest contents or found coins).
- sw:quantity (Item -> xsd:integer): numeric quantity of an item stack.
- sw:dc (Scene -> xsd:integer): difficulty class for a scene check (e.g. DC 13 Stealth).
- sw:rewardAmount (Adventure -> xsd:decimal): gold reward offered by the village.
- sw:recommendedLevel (Adventure -> xsd:integer): recommended party level.
- sw:partySizeMin / sw:partySizeMax (Adventure -> xsd:integer): recommended party size bounds.
- sw:difficulty (Adventure -> xsd:string): textual difficulty label ("Beginner-friendly").

All properties include rdfs:label and rdfs:comment in the schema to help human readers and tooling.

## Example mapping notes (how to map supplied data to the model)
- Create one sw:Adventure resource for "The Goblin Cave of Ashenvale".
  - sw:difficulty = "Beginner-friendly".
  - sw:rewardAmount = 50 (for the elder's reward)
  - sw:recommendedLevel = 1
  - sw:partySizeMin = 2, sw:partySizeMax = 4
  - sw:offersClass links to sw:PlayerClass resources for Fighter/Wizard/Rogue (these are classes in the schema, not instances here; when adding data you may create instances like sw:FighterClass).
  - sw:hasRaceOption links to sw:Race instances (Human/Elf/Dwarf).
- For each scene create a sw:Scene and link with sw:hasScene on the adventure; set sw:sceneDescription and sw:objectiveText accordingly.
- For characters (Aldric, Elder Mira, goblins, Grix), create instances of sw:Npc or sw:Monster and set sw:hp, sw:armorClass, sw:abilityText, sw:xpValue where appropriate; link them to the scene via sw:hasNPC or sw:hasMonster (or sw:encounters).
- For items (Heirloom Dagger, Healing Potion, Chest) create sw:Item or appropriate subclass and set sw:damage, sw:goldAmount, sw:quantity; link carrier via sw:carries and place via sw:hasItem or sw:contains (for chest contents).

## Importing into Apache Jena Fuseki
1. Save the supplied Turtle (ontology + instances) into a .ttl file.
2. Load the file into a Jena TDB dataset or upload via Fuseki UI.
3. Use SPARQL to query scenes, monsters, items, and adventure metadata. Numeric datatype properties (hp, xpValue, goldAmount) allow numeric queries (SUM, COUNT, FILTER by numeric range).

## Extension suggestions (later versions)
- Add Attack and Skill classes to model multiple attacks per monster as first-class resources.
- Add detailed typed dice objects for damage rather than free text.
- Add a simple event model (Encounter, CombatRound) for logging play sessions.
- Add provenance properties for DM notes, source text excerpts, and localization.

## Notes
- The schema intentionally keeps several textual fields (abilityText, attack text, damage) as literals so the DM's natural language content can be imported directly. If you need machine-parseable combat rules later, introduce separate classes for Attack and DamageRoll.



---

Schema namespace: http://example.org/semantic-web#

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5-mini`
- Max attempts: 2
- Started: 2026-05-31T01:40:17+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-05-31T01:40:17+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-05-31T01:41:37+00:00
- Response characters: 15960

## Attempt 1 Validation

- Status: passed
- Triple count: 185

### Candidate Design

# Design for semantic-web (design.md)

## Overview

This document describes a compact RDF/RDFS schema to represent the provided Dungeons & Dragons beginner adventure "The Goblin Cave of Ashenvale". The schema is intentionally small and pragmatic so it can be imported into Apache Jena Fuseki and extended later. It covers the core concepts required to import the adventure text and to answer common queries such as: which scenes belong to the adventure, which NPCs and monsters appear in each scene, what items or loot are present, numeric stats (HP, AC, XP), and adventure-level metadata (difficulty, recommended party size, reward).

Design goals
- Keep the vocabulary small (about a dozen classes and a few dozen properties).
- Use only RDF and RDFS (no OWL) as requested.
- Use domain terminology from the adventure (Adventure, Scene, Npc, Monster, Player, Item, Weapon, Chest, Potion, PlayerClass, Race, Location).
- Provide practical datatype properties for numeric values used in gameplay (hp, armorClass, xpValue, goldAmount, recommendedLevel, party size, DCs).
- Provide object properties to link scenes, characters, items and to express containment and carrying relationships.
- Provide rdfs:label and rdfs:comment for important classes and properties to aid manual browsing and programmatic use.

## Modeling decisions and rationale
- Adventure is the top-level container for the scenario (metadata, recommended level/party, available player classes/races, scenes).
- Scene models each gameplay scene (Village, Hillside Trail, Goblin Warren, Return). Scenes link to a Location for short place metadata and to other scenes via sw:leadsTo for exits.
- Character is a general class; Player, Npc, and Monster are shallow subclasses. This allows queries that want "all Characters in a Scene" or only Monsters/NPCs.
- Items are grouped under Item with obvious subclasses (Weapon, Potion, Chest). Chests may contain items; characters may carry items. Items have descriptive/damage fields suitable for import of the provided item text (e.g., "1d4+1 piercing").
- Numeric/stat properties (hp, armorClass, xpValue, goldAmount) are datatype properties with xsd:integer/decimal types so they can be used in numerical queries and aggregations.
- Several textual properties (sceneDescription, objectiveText, abilityText, attack descriptions) are modeled as datatype properties (xsd:string). These allow the DM notes and flavor text to be imported and displayed.

This model avoids fine-grained constructs such as separate Attack objects, multiple attack entries per monster, or skill proficiencies; those can be added later if needed.

## Classes (short description)
- sw:Adventure — top-level scenario container (difficulty, scenes, reward, recommendations).
- sw:Scene — a scene in the adventure (has location, objectives, description, exits).
- sw:Location — short place metadata (e.g. "Millhaven", "Hillside Trail").
- sw:Character — abstract character superclass for all sentient actors.
- sw:Player — playable character (subclass of Character).
- sw:Npc — non-player characters (quest givers, villagers) (subclass of Character).
- sw:Monster — monsters/enemies (subclass of Character).
- sw:Item — generic item.
- sw:Weapon — weapon (subclass of Item).
- sw:Potion — consumable healing potion (subclass of Item).
- sw:Chest — container item that can contain items (subclass of Item).
- sw:PlayerClass — player class option (Fighter, Wizard, Rogue).
- sw:Race — player race option (Human, Elf, Dwarf).

## Important properties (short description)
Object properties
- sw:hasScene (Adventure -> Scene): lists scenes that belong to an adventure.
- sw:hasLocation (Scene -> Location): associates a scene with a named place.
- sw:leadsTo (Scene -> Scene): links scene exits to other scenes.
- sw:hasNPC (Scene -> Npc): NPCs present in a scene.
- sw:hasMonster (Scene -> Monster): Monsters present in a scene.
- sw:hasItem (Scene -> Item): Items placed in the scene environment.
- sw:carries (Character -> Item): items carried by a character (loot, equipment).
- sw:offersClass (Adventure -> PlayerClass): player classes available for the adventure.
- sw:hasRaceOption (Adventure -> Race): player race options for the adventure.
- sw:contains (Chest -> Item): items contained in a chest.
- sw:encounters (Scene -> Character): a flexible scene->character link for any encounter listing.

Datatype properties
- sw:objectiveText (Scene -> xsd:string): short in-scene objective text.
- sw:sceneDescription (Scene -> xsd:string): descriptive/DM notes for the scene.
- sw:hp (Character -> xsd:integer): hit points for a character/monster.
- sw:armorClass (Character -> xsd:integer): armor class.
- sw:attackBonus (Character -> xsd:integer): numeric attack bonus used in the adventure text.
- sw:damage (Item -> xsd:string): textual damage expression (e.g. "1d4+1 piercing").
- sw:abilityText (Character -> xsd:string): textual abilities (e.g. "Nimble Escape").
- sw:xpValue (Character -> xsd:integer): XP awarded for defeating a monster.
- sw:goldAmount (Item -> xsd:decimal): gold amount (for chest contents or found coins).
- sw:quantity (Item -> xsd:integer): numeric quantity of an item stack.
- sw:dc (Scene -> xsd:integer): difficulty class for a scene check (e.g. DC 13 Stealth).
- sw:rewardAmount (Adventure -> xsd:decimal): gold reward offered by the village.
- sw:recommendedLevel (Adventure -> xsd:integer): recommended party level.
- sw:partySizeMin / sw:partySizeMax (Adventure -> xsd:integer): recommended party size bounds.
- sw:difficulty (Adventure -> xsd:string): textual difficulty label ("Beginner-friendly").

All properties include rdfs:label and rdfs:comment in the schema to help human readers and tooling.

## Example mapping notes (how to map supplied data to the model)
- Create one sw:Adventure resource for "The Goblin Cave of Ashenvale".
  - sw:difficulty = "Beginner-friendly".
  - sw:rewardAmount = 50 (for the elder's reward)
  - sw:recommendedLevel = 1
  - sw:partySizeMin = 2, sw:partySizeMax = 4
  - sw:offersClass links to sw:PlayerClass resources for Fighter/Wizard/Rogue (these are classes in the schema, not instances here; when adding data you may create instances like sw:FighterClass).
  - sw:hasRaceOption links to sw:Race instances (Human/Elf/Dwarf).
- For each scene create a sw:Scene and link with sw:hasScene on the adventure; set sw:sceneDescription and sw:objectiveText accordingly.
- For characters (Aldric, Elder Mira, goblins, Grix), create instances of sw:Npc or sw:Monster and set sw:hp, sw:armorClass, sw:abilityText, sw:xpValue where appropriate; link them to the scene via sw:hasNPC or sw:hasMonster (or sw:encounters).
- For items (Heirloom Dagger, Healing Potion, Chest) create sw:Item or appropriate subclass and set sw:damage, sw:goldAmount, sw:quantity; link carrier via sw:carries and place via sw:hasItem or sw:contains (for chest contents).

## Importing into Apache Jena Fuseki
1. Save the supplied Turtle (ontology + instances) into a .ttl file.
2. Load the file into a Jena TDB dataset or upload via Fuseki UI.
3. Use SPARQL to query scenes, monsters, items, and adventure metadata. Numeric datatype properties (hp, xpValue, goldAmount) allow numeric queries (SUM, COUNT, FILTER by numeric range).

## Extension suggestions (later versions)
- Add Attack and Skill classes to model multiple attacks per monster as first-class resources.
- Add detailed typed dice objects for damage rather than free text.
- Add a simple event model (Encounter, CombatRound) for logging play sessions.
- Add provenance properties for DM notes, source text excerpts, and localization.

## Notes
- The schema intentionally keeps several textual fields (abilityText, attack text, damage) as literals so the DM's natural language content can be imported directly. If you need machine-parseable combat rules later, introduce separate classes for Attack and DamageRoll.



---

Schema namespace: http://example.org/semantic-web#

