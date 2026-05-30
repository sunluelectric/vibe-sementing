# DnD Adventure RDF/RDFS Schema Design

## Goal

This first version defines a deliberately small RDF/RDFS schema for representing a DnD adventure. It is designed for simple import into Apache Jena Fuseki and for later extension when adventure instances are added.

The schema uses only RDF and RDFS. It does not use OWL, restrictions, cardinality rules, RDF lists, blank nodes, or complex ontology patterns.

## Namespace

Base namespace:

`http://example.org/dnd-adventure#`

Preferred prefix:

`dnd:`

## Modeling approach

The schema represents an adventure as a set of related resources:

- An `Adventure` has quests, scenes, and available player options.
- A `Quest` has a quest giver, rewards, and victory conditions.
- A `Scene` has a location, objective, encounters, checks, rewards, exits, characters, and items.
- Characters include player characters, NPCs, and monsters.
- Monsters and NPCs are simple subclasses of `Character`.
- Weapons are a simple subclass of `Item`.
- Checks represent ability or skill checks such as DC 13 Dexterity or Stealth.
- Encounters represent combat, social, exploration, trap, or mixed challenges.
- Rewards represent gold, XP, services, or items granted by quest or scene outcomes.

This is intentionally broad. For example, `containsItem`, `featuresCharacter`, `hasReward`, and `hasCheck` can be reused on different kinds of resources instead of creating many one-off properties.

## Classes

The schema contains 15 classes:

1. `Adventure` - a complete playable adventure module.
2. `Quest` - a goal or mission inside an adventure.
3. `Scene` - a sequential or reachable unit of play.
4. `Location` - a physical place such as a village, trail, cave, or chamber.
5. `Character` - any acting creature or person.
6. `Player` - a player character, subclass of `Character`.
7. `Npc` - a non-player character, subclass of `Character`.
8. `Monster` - a hostile or challenge creature, subclass of `Character`.
9. `PlayerOption` - an available race, class, background, or other player-facing choice.
10. `Item` - an object that can be found, carried, rewarded, or used.
11. `Weapon` - a damaging item, subclass of `Item`.
12. `Encounter` - a combat, social, exploration, or mixed challenge.
13. `Check` - a roll with a difficulty class and ability or skill.
14. `Reward` - gold, XP, items, services, or other benefits.
15. `VictoryCondition` - a condition that marks success or completion.

## Properties

The schema contains 35 properties: 15 object properties and 20 datatype properties.

### Main object properties

- `hasQuest` links an adventure to a quest.
- `hasScene` links an adventure to a scene.
- `nextScene` links one scene to another scene.
- `hasLocation` links a scene to its location.
- `hasEncounter` links a scene to an encounter.
- `hasCheck` links any relevant resource to a check.
- `hasReward` links any relevant resource to a reward.
- `hasVictoryCondition` links any relevant resource to a victory condition.
- `featuresCharacter` links any relevant resource to a character.
- `questGiver` links a quest to the NPC who gives or authorizes it.
- `containsItem` links any relevant resource to an item.
- `carriesItem` links a character to an item they carry.
- `usesWeapon` links a character to a weapon.
- `involvesMonster` links an encounter to a monster.
- `hasPlayerOption` links an adventure to an available player option.

### Main datatype properties

- `title` and `description` provide reusable human-readable text.
- `adventureType`, `difficulty`, `recommendedPartySize`, and `recommendedLevel` describe an adventure.
- `objective`, `dmNotes`, and `exitDescription` describe scene play.
- `optionCategory` categorizes player options, such as class or race.
- `monsterCount` gives the number of monsters in an encounter.
- `difficultyClass`, `ability`, and `skill` describe checks.
- `hitPoints`, `armorClass`, `xpValue`, and `damage` describe creatures and weapons.
- `itemEffect` describes usable item effects.
- `rewardAmount` describes a reward amount in flexible text form, such as 50 gp or 100 XP.

## Instance modeling guidance for the sample adventure

When adding the sample adventure later, create one `Adventure` instance for The Goblin Cave of Ashenvale. Then create scene instances for Millhaven, the Hillside Trail, the Goblin Warren, and the Return to Millhaven.

Suggested future instance patterns:

- Make Aldric Thorn and Elder Mira instances of `Npc`.
- Make Goblin and Grix instances of `Monster`.
- Make Heirloom Dagger an instance of `Weapon`.
- Make Healing Potion and Gold Chest instances of `Item`.
- Use `hasEncounter` for the goblin sentries and final boss fight.
- Use `hasCheck` for Stealth, Strength, Thieves Tools, and chase checks.
- Use `hasReward` for gold, XP, potions, healing services, and quest completion awards.
- Use `hasVictoryCondition` for retrieving the chest and heirloom dagger.

## URI guidance

Use stable readable IRIs later, for example:

- `dnd:goblin-cave-of-ashenvale`
- `dnd:scene-1-millhaven`
- `dnd:aldric-thorn`
- `dnd:grix`
- `dnd:heirloom-dagger`

Prefer lowercase hyphenated names for individuals. This schema file itself contains only classes and properties, not adventure instances.

## Known limitations

This first schema intentionally does not model complex rules such as initiative, spell slots, exact inventory quantities, challenge rating, advantage, resistance, action economy, or conditional branching logic. These can be added later after real adventure data has been loaded and queried.
