# dnd-adventure Semantic Schema (design.md)

## Overview

This document describes a compact RDF/RDFS schema for representing basic elements of a beginner Dungeons & Dragons adventure (the Goblin Cave of Ashenvale sample). The goal is a small, easy-to-import ontology suitable for Apache Jena Fuseki and later extension. The model uses only RDF and RDFS (no OWL).

Base namespace: http://example.org/dnd-adventure#
Prefixes used: dnd, rdf, rdfs, xsd

Design goals:
- Keep the model small and pragmatic, modeling core concepts that appear in the sample adventure: Adventure, Quest, Scene, Location, Characters (NPCs, Monsters, Players), Encounters, Items/Weapons, Checks, Rewards and Victory Conditions.
- Use broad, reusable properties rather than many specialized one-off predicates.
- Provide rdfs:label and rdfs:comment for important classes and properties to assist human readers and tools.
- Keep structure shallow and easy to extend.

## Core classes (15)
- Adventure — A full adventure or module that can contain quests and scenes.
- Quest — A goal-driven task inside an adventure (e.g., retrieve stolen goods).
- Scene — A narrative location/encounter node; a scene has description, exits and encounters.
- Location — A physical or descriptive place (village, cave entrance, chamber).
- Character — General role for beings in the adventure (players and non-players).
- Npc — Non-player character; subclass of Character (quest givers, villagers).
- Monster — Hostile creature; subclass of Character (goblins, bosses).
- Player — Player-controlled character (class, race chosen by players).
- PlayerOption — Options available to players (classes, races) for import and selection.
- Item — Generic item (loot, chest, potion, gear).
- Weapon — A kind of Item (scimitar, dagger); subclass of Item.
- Encounter — A measurable conflict or challenge inside a scene; links to participants.
- Check — A mechanical skill/ability check (DC and type) used for doors, sneaking, etc.
- Reward — Rewards for quests or NPC offers (gold, items, XP).
- VictoryCondition — A named condition describing success for a quest (e.g., "chest and dagger returned").

Notes on subclassing: Npc and Monster are shallow subclasses of Character. Weapon is a subclass of Item. This keeps reasoning simple and familiar for DnD users.

## Key properties (28)
Broad object and datatype properties were chosen so the schema can express the sample adventure without excessive specificity.

Object properties (domain → range shown):
- dnd:hasQuest (Adventure → Quest) — link an adventure to one or more quests.
- dnd:hasScene (Adventure → Scene) — scenes contained by an adventure.
- dnd:locatedIn (Scene → Location) — where the scene takes place.
- dnd:hasEncounter (Scene → Encounter) — encounters that occur in a scene.
- dnd:exitTo (Scene → Scene) — scene-to-scene navigation/exits.
- dnd:carries (Character → Item) — items carried by a character (loot, keys, weapons).
- dnd:includesItem (Reward → Item) — reward includes named items.
- dnd:hasReward (Quest → Reward) — reward(s) attached to the quest.
- dnd:victoryCondition (Quest → VictoryCondition) — success criteria for a quest.

Datatype properties (domain → xsd range shown):
- dnd:hasObjective (Quest → xsd:string) — short textual objective of a quest.
- dnd:recommendedPartySize (Quest → xsd:string) — human-friendly party size (e.g., "2–4").
- dnd:recommendedLevel (Quest → xsd:nonNegativeInteger) — recommended character level.
- dnd:difficultyLevel (Quest → xsd:string) — textual difficulty (e.g., "Beginner-friendly").
- dnd:name (rdfs:Resource → xsd:string) — general name for resources (characters, items, scenes).
- dnd:description (rdfs:Resource → xsd:string) — longer textual description usable for scenes, items, locations.
- dnd:role (Character → xsd:string) — short role text ("Quest Giver", "Merchant").
- dnd:personality (Character → xsd:string) — brief personality notes ("stern but fair").
- dnd:hp (Character → xsd:nonNegativeInteger) — hit points for creatures.
- dnd:armorClass (Character → xsd:nonNegativeInteger) — AC value.
- dnd:xpValue (Character → xsd:nonNegativeInteger) — XP awarded for defeating the creature.
- dnd:itemType (Item → xsd:string) — category ("Healing Potion", "Simple Melee Weapon").
- dnd:itemProperty (Item → xsd:string) — short string listing item properties ("Finesse, Light").
- dnd:damage (Weapon → xsd:string) — damage expression as text ("1d4+1 piercing").
- dnd:goldAmount (Reward → xsd:nonNegativeInteger) — gold coins amount.
- dnd:rewardXP (Reward → xsd:nonNegativeInteger) — XP granted for a reward.
- dnd:checkDC (Check → xsd:nonNegativeInteger) — numeric DC for checks.
- dnd:checkType (Check → xsd:string) — skill or ability type ("Dexterity/Stealth").
- dnd:conditionDescription (VictoryCondition → xsd:string) — textual description of victory.

Most properties include rdfs:label and rdfs:comment in the Turtle schema.

## Mapping the sample adventure to the schema
(Advice on how to convert the sample_adventure.md fields into triples)

- The whole scenario is an instance of dnd:Adventure. Attach dnd:hasQuest pointing to a Quest instance representing "Recover merchant's chest".
- Quest fields: dnd:hasObjective (short summary), dnd:difficultyLevel ("Beginner-friendly"), dnd:recommendedPartySize ("2–4"), dnd:recommendedLevel (1), dnd:hasReward linking to a Reward instance (gold 50 and possible extra), and dnd:victoryCondition describing returned chest + dagger.
- Scenes are instances of dnd:Scene; each scene links to a dnd:Location via dnd:locatedIn and links to one or more dnd:Encounter with dnd:hasEncounter. Scene exits use dnd:exitTo to link scenes.
- Encounters list participants by creating Character instances (npc, monster, player) and linking them to the Encounter with dnd:carries and character properties such as dnd:hp, dnd:armorClass and dnd:xpValue.
- Items in the text (Heirloom Dagger, Healing Potion, Gold Chest) are instances of dnd:Item or dnd:Weapon and receive dnd:itemType, dnd:itemProperty and dnd:damage (for weapons). Characters carrying items use dnd:carries; rewards include items via dnd:includesItem.
- Checks (lockpicking DCs, stealth DCs, strength checks) are instances of dnd:Check with dnd:checkType and dnd:checkDC and can be attached to Scenes or Encounters using dnd:description or captured in a lightweight linking property in data instances (e.g., attach a blank-check node in data stage — avoided in the ontology).

Example (conceptual, not actual triples in this schema):
- :quest1 a dnd:Quest; dnd:hasObjective "Retrieve merchant's chest"; dnd:recommendedPartySize "2–4"; dnd:hasReward :reward1; dnd:victoryCondition :vc1.
- :scene2 a dnd:Scene; dnd:locatedIn :HillsideTrail; dnd:hasEncounter :enc1; dnd:exitTo :scene3.
- :goblin1 a dnd:Monster; dnd:name "Goblin"; dnd:hp 7; dnd:armorClass 15; dnd:xpValue 50; dnd:carries :scimitar1.

(Do not add example data in this schema file; instances are to be added when importing the sample adventure.)

## Extension notes / best practices
- This RDFS schema intentionally avoids deep modeling of dice mechanics (individual attack entries, roll formulas as structured objects). For now, damage and special abilities are textual. If later you need structured mechanics (dice types, attack bonuses), add small structured classes (DiceRoll, Attack) or move to OWL for richer constraints.
- Use consistent URIs for repeated concepts (e.g., a canonical goblin species resource) when you want to reuse definitions across instances.
- Keep textual fields (description, itemProperty) short and human-readable; indexing/searching these in Fuseki is straightforward.

## Loading into Jena Fuseki
1. Save the Turtle ontology (ontology.ttl) and load it into Fuseki as a separate graph or into the default graph.
2. When importing adventure instances, use the class URIs from this ontology. Instances may be placed in a dataset graph dedicated to instance data, with the ontology kept in the dataset's ontology graph.
3. Start with a small number of triples for scenes, characters and items and iterate: small schema changes are inexpensive.

## Summary
This schema provides a compact, practical vocabulary for importing and querying the provided Goblin Cave adventure. It balances expressivity against simplicity and is intended as a starting point for iterative improvement.


---
Schema version: 1.0
Author: dnd-adventure semantic designer

## Designer Generation Log

# Semantic Web Designer Progress

- Model: `gpt-5-mini`
- Max attempts: 2
- Started: 2026-05-30T12:56:47+00:00

## Attempt 1

- Status: LLM request started
- Timestamp: 2026-05-30T12:56:47+00:00
- Retry feedback included: no

## Attempt 1 Response

- Status: LLM response received
- Timestamp: 2026-05-30T12:58:14+00:00
- Response characters: 17212

## Attempt 1 Validation

- Status: passed
- Triple count: 188

### Candidate Design

# dnd-adventure Semantic Schema (design.md)

## Overview

This document describes a compact RDF/RDFS schema for representing basic elements of a beginner Dungeons & Dragons adventure (the Goblin Cave of Ashenvale sample). The goal is a small, easy-to-import ontology suitable for Apache Jena Fuseki and later extension. The model uses only RDF and RDFS (no OWL).

Base namespace: http://example.org/dnd-adventure#
Prefixes used: dnd, rdf, rdfs, xsd

Design goals:
- Keep the model small and pragmatic, modeling core concepts that appear in the sample adventure: Adventure, Quest, Scene, Location, Characters (NPCs, Monsters, Players), Encounters, Items/Weapons, Checks, Rewards and Victory Conditions.
- Use broad, reusable properties rather than many specialized one-off predicates.
- Provide rdfs:label and rdfs:comment for important classes and properties to assist human readers and tools.
- Keep structure shallow and easy to extend.

## Core classes (15)
- Adventure — A full adventure or module that can contain quests and scenes.
- Quest — A goal-driven task inside an adventure (e.g., retrieve stolen goods).
- Scene — A narrative location/encounter node; a scene has description, exits and encounters.
- Location — A physical or descriptive place (village, cave entrance, chamber).
- Character — General role for beings in the adventure (players and non-players).
- Npc — Non-player character; subclass of Character (quest givers, villagers).
- Monster — Hostile creature; subclass of Character (goblins, bosses).
- Player — Player-controlled character (class, race chosen by players).
- PlayerOption — Options available to players (classes, races) for import and selection.
- Item — Generic item (loot, chest, potion, gear).
- Weapon — A kind of Item (scimitar, dagger); subclass of Item.
- Encounter — A measurable conflict or challenge inside a scene; links to participants.
- Check — A mechanical skill/ability check (DC and type) used for doors, sneaking, etc.
- Reward — Rewards for quests or NPC offers (gold, items, XP).
- VictoryCondition — A named condition describing success for a quest (e.g., "chest and dagger returned").

Notes on subclassing: Npc and Monster are shallow subclasses of Character. Weapon is a subclass of Item. This keeps reasoning simple and familiar for DnD users.

## Key properties (28)
Broad object and datatype properties were chosen so the schema can express the sample adventure without excessive specificity.

Object properties (domain → range shown):
- dnd:hasQuest (Adventure → Quest) — link an adventure to one or more quests.
- dnd:hasScene (Adventure → Scene) — scenes contained by an adventure.
- dnd:locatedIn (Scene → Location) — where the scene takes place.
- dnd:hasEncounter (Scene → Encounter) — encounters that occur in a scene.
- dnd:exitTo (Scene → Scene) — scene-to-scene navigation/exits.
- dnd:carries (Character → Item) — items carried by a character (loot, keys, weapons).
- dnd:includesItem (Reward → Item) — reward includes named items.
- dnd:hasReward (Quest → Reward) — reward(s) attached to the quest.
- dnd:victoryCondition (Quest → VictoryCondition) — success criteria for a quest.

Datatype properties (domain → xsd range shown):
- dnd:hasObjective (Quest → xsd:string) — short textual objective of a quest.
- dnd:recommendedPartySize (Quest → xsd:string) — human-friendly party size (e.g., "2–4").
- dnd:recommendedLevel (Quest → xsd:nonNegativeInteger) — recommended character level.
- dnd:difficultyLevel (Quest → xsd:string) — textual difficulty (e.g., "Beginner-friendly").
- dnd:name (rdfs:Resource → xsd:string) — general name for resources (characters, items, scenes).
- dnd:description (rdfs:Resource → xsd:string) — longer textual description usable for scenes, items, locations.
- dnd:role (Character → xsd:string) — short role text ("Quest Giver", "Merchant").
- dnd:personality (Character → xsd:string) — brief personality notes ("stern but fair").
- dnd:hp (Character → xsd:nonNegativeInteger) — hit points for creatures.
- dnd:armorClass (Character → xsd:nonNegativeInteger) — AC value.
- dnd:xpValue (Character → xsd:nonNegativeInteger) — XP awarded for defeating the creature.
- dnd:itemType (Item → xsd:string) — category ("Healing Potion", "Simple Melee Weapon").
- dnd:itemProperty (Item → xsd:string) — short string listing item properties ("Finesse, Light").
- dnd:damage (Weapon → xsd:string) — damage expression as text ("1d4+1 piercing").
- dnd:goldAmount (Reward → xsd:nonNegativeInteger) — gold coins amount.
- dnd:rewardXP (Reward → xsd:nonNegativeInteger) — XP granted for a reward.
- dnd:checkDC (Check → xsd:nonNegativeInteger) — numeric DC for checks.
- dnd:checkType (Check → xsd:string) — skill or ability type ("Dexterity/Stealth").
- dnd:conditionDescription (VictoryCondition → xsd:string) — textual description of victory.

Most properties include rdfs:label and rdfs:comment in the Turtle schema.

## Mapping the sample adventure to the schema
(Advice on how to convert the sample_adventure.md fields into triples)

- The whole scenario is an instance of dnd:Adventure. Attach dnd:hasQuest pointing to a Quest instance representing "Recover merchant's chest".
- Quest fields: dnd:hasObjective (short summary), dnd:difficultyLevel ("Beginner-friendly"), dnd:recommendedPartySize ("2–4"), dnd:recommendedLevel (1), dnd:hasReward linking to a Reward instance (gold 50 and possible extra), and dnd:victoryCondition describing returned chest + dagger.
- Scenes are instances of dnd:Scene; each scene links to a dnd:Location via dnd:locatedIn and links to one or more dnd:Encounter with dnd:hasEncounter. Scene exits use dnd:exitTo to link scenes.
- Encounters list participants by creating Character instances (npc, monster, player) and linking them to the Encounter with dnd:carries and character properties such as dnd:hp, dnd:armorClass and dnd:xpValue.
- Items in the text (Heirloom Dagger, Healing Potion, Gold Chest) are instances of dnd:Item or dnd:Weapon and receive dnd:itemType, dnd:itemProperty and dnd:damage (for weapons). Characters carrying items use dnd:carries; rewards include items via dnd:includesItem.
- Checks (lockpicking DCs, stealth DCs, strength checks) are instances of dnd:Check with dnd:checkType and dnd:checkDC and can be attached to Scenes or Encounters using dnd:description or captured in a lightweight linking property in data instances (e.g., attach a blank-check node in data stage — avoided in the ontology).

Example (conceptual, not actual triples in this schema):
- :quest1 a dnd:Quest; dnd:hasObjective "Retrieve merchant's chest"; dnd:recommendedPartySize "2–4"; dnd:hasReward :reward1; dnd:victoryCondition :vc1.
- :scene2 a dnd:Scene; dnd:locatedIn :HillsideTrail; dnd:hasEncounter :enc1; dnd:exitTo :scene3.
- :goblin1 a dnd:Monster; dnd:name "Goblin"; dnd:hp 7; dnd:armorClass 15; dnd:xpValue 50; dnd:carries :scimitar1.

(Do not add example data in this schema file; instances are to be added when importing the sample adventure.)

## Extension notes / best practices
- This RDFS schema intentionally avoids deep modeling of dice mechanics (individual attack entries, roll formulas as structured objects). For now, damage and special abilities are textual. If later you need structured mechanics (dice types, attack bonuses), add small structured classes (DiceRoll, Attack) or move to OWL for richer constraints.
- Use consistent URIs for repeated concepts (e.g., a canonical goblin species resource) when you want to reuse definitions across instances.
- Keep textual fields (description, itemProperty) short and human-readable; indexing/searching these in Fuseki is straightforward.

## Loading into Jena Fuseki
1. Save the Turtle ontology (ontology.ttl) and load it into Fuseki as a separate graph or into the default graph.
2. When importing adventure instances, use the class URIs from this ontology. Instances may be placed in a dataset graph dedicated to instance data, with the ontology kept in the dataset's ontology graph.
3. Start with a small number of triples for scenes, characters and items and iterate: small schema changes are inexpensive.

## Summary
This schema provides a compact, practical vocabulary for importing and querying the provided Goblin Cave adventure. It balances expressivity against simplicity and is intended as a starting point for iterative improvement.


---
Schema version: 1.0
Author: dnd-adventure semantic designer

