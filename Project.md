# The Bazaar Simulator - Architektur & Status

Dieses Projekt simuliert die Kampfmechaniken von "The Bazaar" unter Verwendung eines **ECS-ähnlichen (Entity Component System) Ansatzes**. Das Ziel ist eine modulare, erweiterbare und performante Simulation, um Taktiken zu testen.

## 1. Kern-Architektur

Wir nutzen einen **Composition-over-Inheritance** Ansatz. Es gibt keine festen Klassen für "Schwert" oder "Zauberstab". Alles ist eine **Entity**, die durch ihre **Components** definiert wird.

### 🏛️ Die Bausteine

1.  **Entity (`entity.py`)**

    -   Ein generischer Container mit einer ID und einer Liste von Komponenten.
    -   Besitzt eine `tick_size` (z.B. 0.1s) für die deterministische Zeitsimulation.

2.  **Components (`component.py`)**

    -   Beinhalten Daten **und** spezifische Logik (Smart Components).
    -   Trennen Verantwortlichkeiten sauber auf:
        -   **Vitalität (Player):** `HealthComponent`, `ShieldComponent`, `StatusEffectContainer` (verwaltet Burn/Poison Ticks).
        -   **Item-Logik:** `TimeStore` (Cooldown Fortschritt), `ValueStore` (Stats wie Damage), `ModifierStore` (Buffs/Debuffs), `AmmoComponent`.
        -   **Meta:** `TagComponent` (Weapon, Magic), `ItemSize` (Small, Medium).

3.  **Action System (Transaktional)**

    -   Items "feuern" nicht einfach wahllos. Wir nutzen ein striktes **Condition-Cost-Effect** Modell:
        -   **Conditions (`condition.py`):** Stateless Checks. _"Ist der Cooldown fertig?", "Ist Munition da?"_.
        -   **Costs:** Wenn Conditions erfüllt -> _"Ziehe 1 Ammo ab", "Resette Cooldown timer"_.
        -   **Effects (`effect.py`):** Wenn Bezahlt -> _"Füge dem Gegner Schaden zu"_.
    -   Dies erlaubt komplexe Logik (z.B. Item lädt auf, feuert aber nicht weil Ammo fehlt -> Overcharge).

4.  **Status Effekte**
    -   Zentralisiert im `StatusEffectContainer`.
    -   Unterscheidet automatisch Logik-Typen:
        -   **Burn:** Schaden + Decay (wird weniger).
        -   **Poison:** Piercing Schaden (ignoriert Schild) + Kein Decay.
        -   **Freeze:** Im `ModifierStore` als Multiplier `0.0` implementiert.

---

## 2. Datenmodell Beispiele

Wie sieht ein Objekt in diesem System aus?

**Der Spieler (Entity):**

```python
Entity(
    components=[
        HealthComponent(max=1000),
        ShieldComponent(),          # Separat, da Poison es ignoriert
        StatusEffectContainer(),    # Managt Burn/Poison Timer
        BoardComponent()            # (TODO) Hält die Items
    ]
)
```

**Ein Item (z.B. Eis-Schwert):**

```python
Entity(
    components=[
        TimeStore(),                # Fortschrittsbalken
        ValueStore(cooldown=3.0, damage=10),
        TagComponent(["Weapon", "Ice"]),
        ModifierStore()             # Kann Haste/Slow/Freeze empfangen
    ],
    actions=[
        Action(
            conditions=[TimeCondition, AmmoCondition],
            costs=[ResetTime, ConsumeAmmo],
            effects=[DealDamageEffect]
        )
    ]
)
```

---

## 3. Fortschritts-Checkliste

Hier ist der aktuelle Stand der Implementierung basierend auf den Spielregeln.

### ✅ Implements (Fertig & Getestet)

-   [x] **Entity Basis:** Komponenten-System steht.
-   [x] **HP & Heilung:** `HealthComponent` mit Max-HP Logik.
-   [x] **Schild Mechanik:** `ShieldComponent` schützt vor Schaden, wird vor HP verbraucht.
-   [x] **Status Effekte Basis:**
    -   [x] **Burn:** Schaden über Zeit, reduziert sich selbst.
    -   [x] **Poison:** Schaden über Zeit, ignoriert Schild, reduziert sich nicht.
    -   [x] **Regeneration:** Heilung über Zeit.
-   [x] **Cooldown Mechanik:**
    -   [x] Aufladen basierend auf Zeit.
    -   [x] **Haste/Slow:** `ModifierStore` verändert Zeitfluss.
    -   [x] **Freeze:** Zeitfluss wird komplett gestoppt.
-   [x] **Ressourcen:** `AmmoComponent` (Munition).
-   [x] **Action Trigger:** Items feuern nur, wenn alle Bedingungen (Zeit + Ammo) erfüllt sind.

### 🚧 In Progress / TODO (Nächste Schritte)

-   [ ] **Das Board:** Logik für `BoardComponent`, das Items hält.
-   [ ] **Positionierung & Adjacency:**
    -   [ ] Items müssen wissen, wer links/rechts neben ihnen liegt.
    -   [ ] Effekte wie _"Items adjacent to this heal for 5"_.
-   [ ] **Event Bus (Reaktivität):**
    -   [ ] System für _"**When** you use an item..."_ Effekte.
    -   [ ] Items müssen auf Events hören können (Observer Pattern).
-   [ ] **Sandstorm:** Der globale Timer, der Schaden hochskaliert.
-   [ ] **Game Loop:** Der eigentliche Kampf-Loop, der zwei Spieler Entities gegeneinander ticken lässt.
-   [ ] **Item Loader:** Ein Weg, JSON/Datenbank-Daten in diese Entity-Struktur zu parsen.
