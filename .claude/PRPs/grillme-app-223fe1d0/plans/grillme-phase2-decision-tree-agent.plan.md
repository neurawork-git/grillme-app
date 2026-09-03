# Entscheidungsbaum-Agent — text-basiertes Interview mit persistiertem Baum

**Plan ID:** `grillme-phase2-decision-tree-agent`
**Source PRD:** `/home/felix/projects/grillme-app-grillme-v1-phase1-grundgeruest/.claude/PRPs/grillme-app-223fe1d0/prds/grillme-v1.prd.md` (liegt physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`, nicht im Hauptcheckout — siehe Agent Notes)
**PRD Phase:** `2 — Entscheidungsbaum-Agent`
**Source Issue:** None
**Plan Publication:** None

## Outcome

**Problem:** Ohne einen server-seitig persistierten Entscheidungsbaum verliert ein LLM-Interview bei langen Sessions den Überblick über offene Fragen und fragt im Kreis (Spec §4.2).

**Affected user:** Der Solo-Betreiber, während einer laufenden Grill-Session.

**User outcome:** Eine Text-Session lässt sich vollständig durchführen — Frage, Empfehlung, Antwort, nächste Runde — und überlebt einen Backend-Neustart mitten in der Session, weil der gesamte Fortschritt in Postgres liegt statt im Dateisystem einer SDK-Session.

**Invariant:** Jede Interview-Runde startet eine frische Claude-Agent-SDK-Session; `resume=<session_id>` wird nie verwendet. Baum plus bisheriger Verlauf werden jede Runde vollständig als Prompt-Kontext mitgeliefert — was nicht im aktuellen Prompt steht, existiert für den Agenten nicht (Spec §3.1; siehe [[connections/agent-state-and-decision-tree]] in der Knowledge Base). Pro Session läuft immer nur eine Runde gleichzeitig — zwei überlappende Anfragen dürfen den Baum nie inkonsistent machen.

**Success signal:** Eine Text-Session lässt sich vollständig durchführen und überlebt einen Backend-Neustart mitten in der Session (PRD, Phase-2-Erfolgssignal).

**Approach:** FastAPI-Backend mit dem AG-UI-Adapter für das Claude Agent SDK (`ag-ui-claude-sdk`, korrigierter Paketname — siehe Evidence) verdrahtet einen Grill-Agenten, der pro Runde ohne `resume=` aufgerufen wird; der vendorierte `grilling`-Skill liefert die Interview-Logik, `decision_node` (bereits durch die Phase-1-Migration angelegt) liefert Baum-Persistenz, eine reine Frontier-Funktion die Fortschrittsberechnung, CopilotKit den Text-Chat im Next.js-Frontend.

## Recommendation

Kein eigener SSE-Layer und kein eigenes Interview-Prompting von Grund auf: `ag-ui-claude-sdk` liefert laut Web-Recherche bereits alle fünf benötigten Fähigkeiten (Frisch-Session mit injiziertem Kontext, Tool-Argument-Streaming, `adapter.interrupt()`, Frontend-Tools mit Human-in-the-Loop-Stop, bidirektionaler State-Sync) — das selbst zu bauen wäre Wochen Protokollarbeit für etwas, das bereits existiert und laut Commit-Historie seit 0.1.0 nur gehärtet, nie breaking geändert wurde. **Phase 2 nutzt und verifiziert davon konkret nur zwei:** Frisch-Session-mit-injiziertem-Kontext (Task 3) und minimalen State-Sync für den Text-Chat (Task 6); `adapter.interrupt()` und Frontend-Tools/HITL bleiben ungenutzt, bis Phase 3 (Sprachunterbrechung ist explizit Produkt-Phase 2, außerhalb dieses PRPs) bzw. eine spätere Phase sie braucht — das ist keine Lücke dieses Plans, sondern schlicht noch nicht der Punkt, an dem diese Fähigkeiten gebraucht werden.

Der `grilling`-Skill (MIT, bereits im Plugin-Cache vorhanden) liefert das Interview-Muster (Frage/Empfehlung/Antwort/nächste Runde); GrillMe erweitert ihn nur um die Persistenz nach `decision_node` und lässt die Artefakt-Erzeugung aus (das ist Phase 5, nicht hier).

Der Baum selbst ist echter neuer Domain-State — aber die Tabelle dafür existiert bereits: der Phase-1-Plan (`grillme-v1-phase1-grundgeruest.plan.md`, Task 2) legt das **vollständige** Spec-§9-Schema inklusive `decision_node` in einer einzigen Alembic-Migration an, ausdrücklich damit spätere Phasen keine riskante Nachmigration mit Fremdschlüsseln brauchen. Phase 2 baut also nur noch die Frontier-Funktion (reine Berechnung über bestehende Zeilen, kein eigener State) und den Schreibpfad, der `decision_node`-Zeilen befüllt — keine eigene Migration.

### Evidence

- `.claude/spec.md:56-70` (§3.1) — Postgres als einzige Wahrheit, `resume=<session_id>` wird nicht verwendet, Baum+Verlauf jede Runde neu als Prompt.
- `.claude/spec.md:78-82` — Beispielverdrahtung `ClaudeAgentAdapter` + `add_claude_fastapi_endpoint`, Version auf `0.1.0` gepinnt (spec.md:89) — **Korrektur nötig, siehe Risks**.
- `.claude/spec.md:126-145` (§4) — Herkunft des Interviews (`grilling`-Skill, mattpocock-skills, MIT), Entscheidungsbaum-Struktur (Status, Frage, Empfehlung, Antwort, Elternknoten), Frontier-Definition.
- `.claude/spec.md:287-299` (§9) — Datenmodell-Skizze: `decision_node`-Tabelle (Frage, Empfehlung, Antwort, Status, Elternknoten), `session`, `message` (Rolle, Text, Modus, Bildreferenzen).
- `grillme-v1-phase1-grundgeruest.plan.md:152-171,299-306` (Sibling-Worktree) — Phase 1 legt **alle neun** Spec-§9-Tabellen (inkl. `decision_node`) in einer Alembic-Migration an, async SQLAlchemy 2.0 (`asyncpg`), Backend-Testläufer ist verbindlich **pytest** (`uv run --directory backend pytest ...`), kein dediziertes Frontend-Testframework (Begründung dort: reine Formular/Fetch-Seiten ohne Zustandsmaschine).
- Web-Recherche (dieser Planungslauf) — `ag-ui-claude-sdk` (nicht `ag-ui-claude-agent-sdk`) ist der korrekte PyPI-Paketname, aktuell `0.1.5` (0.1.0 ist Erstrelease, drei reine Bugfix/Hardening-Patches dahinter, keine Breaking Changes in den Commit-Titeln); alle fünf im Approach genannten Fähigkeiten sind laut offiziellem README dokumentiert und unterstützt. Primärquellen: PyPI JSON API, `ag-ui-protocol/ag-ui` GitHub (Issue #439, PR #916, Commit-Log, README).
- Codebase-Explorer (dieser Planungslauf) — kein Anwendungscode existierte zu Planungsbeginn im Repo; der `grilling`-Skill ist nicht vendort, existiert nur im Plugin-Cache (`~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/productivity/grilling/`), MIT-lizenziert, Lizenzdatei vorhanden.
- Knowledge Base — `concepts/agent-state-in-postgres.md` und `connections/agent-state-and-decision-tree.md`: "Throwing away the SDK session is only survivable because the tree already carries everything a fresh session needs" — der Baum ist kein Cache neben SDK-Speicher, sondern der einzige Zustand.
- Codebase-Analyst (dieser Planungslauf) — `compliance-base/catalog/stack.json` hat für alle 25 GDPR-Capabilities `chosen: null`; das Gate kann für keinen Plan-Inhalt blockieren (`validate_mode: warn`, kein `off_stack` möglich ohne gewählte Komponente). `ag-ui-claude-agent-sdk`/Claude Agent SDK ist kein Katalog-Component — der Gate hat dazu keine Meinung.
- Devil's-Advocate-Review (dieser Planungslauf) — benannte drei reale Lücken der ersten Fassung: fehlende Nebenläufigkeits-Sperre pro Session, fehlende Zyklus-Validierung für `parent_id`, fehlende Dedup-Prüfung gegen vom Agenten doppelt vorgeschlagene Fragen. Alle drei sind in Task 4 unten eingearbeitet.

### Alternatives considered

- **Eigener SSE/WebSocket-Layer statt AG-UI-Adapter:** verworfen — würde Streaming, Interrupt, Human-in-the-Loop und State-Sync von Grund auf nachbauen, obwohl `ag-ui-claude-sdk` das bereits liefert (siehe Recommendation).
- **SDK-Session-Resume statt Baum-Rehydrierung:** verworfen laut Spec selbst (§3.1) — bricht bei Container-Neustart, Mehrtage-Pause und späterem Multi-User; genau der Fehlermodus, den die Architektur vermeiden soll.

## Implementation Context

### Mandatory reading

| File | Why it matters |
|---|---|
| `.claude/spec.md:39-70` | Architektur + Agent-State-Invariante — jede Backend-Route muss dagegen entworfen werden |
| `.claude/spec.md:126-154` | Entscheidungsbaum-Semantik, Frontier, Abschluss-Signal |
| `.claude/spec.md:287-299` | Datenmodell-Skizze für `decision_node`, `session`, `message` |
| `grillme-v1-phase1-grundgeruest.plan.md` (Sibling-Worktree, Task 1-4) | Backend-Paketform, `models.py`/`db.py`, Auth-Dependency (`require_user`), bereits angelegtes Schema — Phase 2 baut direkt darauf |
| `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/productivity/grilling/` | Zu vendorender Interview-Skill (MIT) — Ausgangspunkt für Fragenlogik |

### Existing patterns and primitives

- **AG-UI-Adapter-Verdrahtung:** `.claude/spec.md:78-82` — `ClaudeAgentAdapter(name=..., options={"model": ...})` + `add_claude_fastapi_endpoint(app=app, adapter=adapter, path="/grill")`; Paketname/Version korrigieren (siehe Risks).
- **`backend/app/models.py`, `backend/app/db.py`, `require_user`-Dependency** (Phase 1) — `decision_node`-ORM-Modell, Async-Session-Factory und Auth-Guard existieren bereits; Phase 2 fügt keine neuen Basis-Primitive hinzu, sondern Logik darüber.

### Integration points

- **Phase-1-Postgres-Schema** — `session`, `message`, `decision_node` und die Login/Auth-Tabellen existieren bereits vollständig aus Phase 1; Phase 2 legt keine eigene Migration an.
- **CopilotKit-Frontend** — Chat-Screen aus dem User Flow; Voice-Umschaltung ist Phase 3, hier nur Text.

## Scope

### In scope

- `grilling`-Skill nach `grillme-app` vendort (mit Copyright-Hinweis), als Ausgangspunkt für Interview-Fragenlogik angepasst.
- FastAPI-Route mit `ag-ui-claude-sdk`-Adapter, frische SDK-Session pro Runde, Baum+Verlauf als injizierter Kontext, Session-Lock gegen überlappende Runden, Zyklus- und Dedup-Schutz beim Persistieren neuer Knoten.
- Frontier-Berechnung als reine Funktion, pro Runde neu ausgewertet.
- Agent signalisiert leere Frontier (Abschluss-Kandidat).
- CopilotKit-Text-Chat im Frontend, verdrahtet gegen die Route.

### Not building

- `decision_node`-Tabelle/-Migration — bereits Teil der Phase-1-Migration.
- Voice-Ein-/Ausgabe (Phase 3).
- Verlaufs-UI zum Durchblättern und Screenshot-Upload (Phase 4).
- Abschluss-Bestätigung per Klick und Artefakt-Generierung (Phase 5) — der Agent meldet nur die leere Frontier, löst aber keine Artefakt-Erzeugung aus.
- `adapter.interrupt()`, Frontend-Tools/HITL-Nutzung — vom Adapter unterstützt, aber in Phase 2 nicht gebraucht (siehe Recommendation).
- Alternative Ausgabeformate über das Startset hinaus (PRD MoSCoW: Could).

## Compliance

**Capabilities**: none — dieser Plan legt nur die Schreiblogik über eine bereits existierende Tabelle an; er baut keinen Consent-Mechanismus, keine Aufbewahrungsfrist und keinen Export. Alle 25 anwendbaren GDPR-Capabilities in `compliance-base/catalog/stack.json` haben `chosen: null` (siehe Risks) — Komponentenwahl ist ein separater, noch offener Schritt (`/neurawork-cc-harness:st-select`), keine Aufgabe dieses Plans.

## Implementation

### 1. `ag-ui-claude-sdk`-Abhängigkeit korrekt pinnen

**Files and integration points**
- `backend/pyproject.toml` (Phase 1, hier nur die zusätzliche Zeile) — UPDATE

**Implementation**
- `ag-ui-claude-sdk>=0.1.5` (nicht `ag-ui-claude-agent-sdk==0.1.0` — der Spec-Paketname existiert nicht auf PyPI, siehe Evidence). `.claude/spec.md:89` entsprechend korrigieren, sobald die Implementierung startet.
- Smoke-Test: `pip install ag-ui-claude-sdk`, `ClaudeAgentAdapter`/`add_claude_fastapi_endpoint` importieren, Instanz mit frischer (nicht resumter) `ClaudeAgentOptions` und injiziertem Kontext-Text anlegen — bestätigt Konstruktor-Signatur vor dem eigentlichen Ausbau.

**Tests**
- Der Smoke-Test selbst ist die Prüfung (kein Unit-Test nötig für einen Import-Check).

**Validation**
- `uv run --directory backend python -c "import ag_ui_claude_sdk; print(ag_ui_claude_sdk.__version__)"` — Version `>=0.1.5`.

### 2. `grilling`-Skill vendoren

**Files and integration points**
- Neues Verzeichnis, z. B. `backend/app/grilling/` — CREATE

**Implementation**
- Skill-Inhalt aus `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/1.2.3/skills/productivity/grilling/` kopieren, MIT-Copyright-Hinweis erhalten (Spec §4.1).
- Anpassung: das Original interviewt nur; die GrillMe-Variante muss den Baum in `decision_node` schreiben statt in einem transienten Format, und darf am Ende kein eigenes Artefakt erzeugen (das bleibt Phase 5).

**Tests**
- Keine automatisierten Tests für den vendorierten Prompt-Text selbst; Verhalten wird über Task 3/4 geprüft.

**Validation**
- Manuelle Diff-Prüfung: vendorierte Kopie vs. Original, Copyright-Hinweis vorhanden.

### 3. Frontier-Berechnung

**Files and integration points**
- Reines Funktionsmodul (kein SDK-Import), z. B. `backend/app/frontier.py` — CREATE

**Implementation**
- Eingabe: Liste aller `decision_node`-Zeilen einer Session. Ausgabe: die Teilmenge "offen", deren `parent_id` entschieden ist (oder `null`).
- Wird bei jeder Runde neu berechnet, nie gespeichert — vermeidet einen zweiten Wahrheits-Ort neben der `decision_node`-Tabelle.
- Terminiert auch bei einem fehlerhaften Baum (Zyklus) garantiert: iterative Berechnung mit einem besuchten-Knoten-Set, kein unbegrenzter rekursiver Abstieg — ein Zyklus führt zu einem klar erkennbaren Zustand (betroffene Knoten bleiben "nicht erreichbar"), nicht zu einer Endlosschleife. Zyklen selbst werden bereits beim Insert verhindert (Task 4), diese Funktion ist die zweite Verteidigungslinie.

**Tests**
- Unit-Tests: leerer Baum, ein-Ebenen-Baum, mehrstufiger Baum mit teilweise entschiedenen Zweigen, Baum mit einem noch offenen Blatt (Frontier nicht leer trotz größtenteils entschiedenem Baum), Baum mit einem konstruierten Zyklus (`A.parent_id=B, B.parent_id=A`) — Berechnung terminiert und liefert ein definiertes Ergebnis statt zu hängen.

**Validation**
- `uv run --directory backend pytest tests/test_frontier.py` — grün.

### 4. FastAPI-Route mit AG-UI-Adapter, frische Session pro Runde, Nebenläufigkeits- und Integritätsschutz

**Files and integration points**
- Backend-Modul für den `/grill`-Endpoint, z. B. `backend/app/grill.py` — CREATE

**Implementation**
- `ClaudeAgentAdapter` + `add_claude_fastapi_endpoint` wie in Spec §3.2 skizziert, aber ohne `resume=<session_id>` — jede Anfrage baut den Prompt aus: vollständigem `decision_node`-Baum der Session, dem bisherigen `message`-Verlauf, und dem vendorierten Grilling-System-Prompt.
- **Session-Lock:** vor Prompt-Aufbau und Agent-Aufruf `SELECT ... FOR UPDATE` auf die `session`-Zeile — eine zweite gleichzeitige Anfrage für dieselbe `session_id` wartet auf die DB-Transaktion oder wird mit `409 Conflict` abgewiesen, statt denselben Baum-Snapshot parallel zu verändern.
- **Persistenz-Transaktion:** Agent-Aufruf liegt außerhalb der DB-Transaktion (externer HTTP-Call zur Claude API kann nicht transaktional zurückgerollt werden); erst nach erfolgreicher Antwort öffnet die Route eine Transaktion, die neue/aktualisierte `decision_node`-Zeilen und die neue `message`-Zeile (`mode='text'`) gemeinsam schreibt und committet — schlägt einer der Writes fehl, rollt die gesamte Transaktion zurück, kein Teilzustand.
- **Zyklus-Schutz:** jeder Insert/Update einer `decision_node`-Zeile mit `parent_id` prüft, dass `parent_id` zur selben `session_id` gehört und nicht bereits (direkt oder transitiv) ein Kind des einzufügenden Knotens ist — Ablehnung mit definiertem Fehler statt eines stillen Zyklus im Baum.
- **Dedup-Schutz:** vor dem Insert einer neuen Frage wird geprüft, ob innerhalb derselben Session bereits eine `decision_node`-Zeile mit normalisiert (whitespace/case) identischem `question`-Text existiert; falls ja, wird der bestehende Knoten aktualisiert statt ein Duplikat angelegt — Schutz gegen einen Agenten, der dieselbe Frage zweimal vorschlägt.
- **Fehlerpfad:** schlägt der Agent-Aufruf selbst fehl (Timeout, 5xx, Adapter-Fehler), liefert die Route einen definierten Fehler-Response (kein stiller 200 mit leerem Inhalt) und schreibt nichts — die Session bleibt im Zustand vor dem fehlgeschlagenen Aufruf, der nächste Versuch sieht denselben Baum.
- Rate-/Session-Ownership: Route setzt den eingeloggten Nutzer aus dem Phase-1-Session-Cookie voraus (`require_user`-Dependency).

**Tests**
- Integrationstest: zwei aufeinanderfolgende Runden gegen denselben `session_id`, dazwischen der Backend-Prozess simuliert neu gestartet (frischer Adapter/Prozess, neue DB-Verbindung) — der zweite Aufruf muss den Baum korrekt aus Postgres rekonstruieren, ohne `resume=` zu verwenden; Test liest die tatsächlich vom Adapter erzeugten SDK-Session-Identifier beider Runden und beweist, dass sie unterschiedlich sind (nicht nur ein Grep auf `resume=` im Code).
- Nebenläufigkeitstest: zwei parallele Requests gegen dieselbe `session_id` (z. B. via `asyncio.gather`) — erwartet genau einen erfolgreichen Schreibvorgang, der zweite wartet oder wird mit `409` abgewiesen; kein Zustand mit doppelten/inkonsistenten `decision_node`-Zeilen.
- Zyklus-Test: Insert-Versuch mit `parent_id`, der einen Zyklus erzeugen würde → wird abgelehnt, Baum bleibt unverändert.
- Dedup-Test: zwei Runden, die dieselbe (normalisierte) Frage vorschlagen → zweite Runde aktualisiert den bestehenden Knoten statt einen zweiten anzulegen.
- Fehlerpfad-Test: Agent-Aufruf schlägt fehl (gemockt) → Route liefert definierten Fehler, keine `decision_node`-/`message`-Zeile wird geschrieben.
- Unit-Test: Prompt-Builder nimmt Baum+Verlauf und erzeugt den erwarteten injizierten Kontext (keine SDK-Aufrufe nötig).

**Validation**
- `uv run --directory backend pytest tests/test_grill.py` — alle obigen Fälle grün.
- Manuell: `docker compose up`, Backend-Container neu starten mitten in einer Session, Session fortsetzen — Baum ist vollständig erhalten.

### 5. Abschluss-Signal (nur Melden, kein Trigger)

**Files and integration points**
- Response-Schema der `/grill`-Route (selbe Datei wie Task 4) — UPDATE

**Implementation**
- Wenn Frontier nach Task 3 leer ist, enthält die Agent-Antwort ein explizites Flag/Feld, das das Frontend zur Anzeige des Abschluss-Bestätigungs-UI (Phase 5) nutzen kann. Diese Route selbst erzeugt kein Artefakt und schließt die Session nicht — das bleibt Phase 5s expliziter Klick.

**Tests**
- Unit-Test: Route-Antwort enthält das Flag genau dann, wenn Frontier leer ist.

**Validation**
- Abgedeckt durch denselben Testlauf wie Task 4 (`pytest tests/test_grill.py`).

### 6. CopilotKit-Text-Chat im Frontend

**Files and integration points**
- Next.js-Chat-Screen, z. B. `frontend/app/sessions/[id]/chat/page.tsx` — CREATE

**Implementation**
- CopilotKit-Client gegen `/grill` verdrahtet (AG-UI-Protokoll, spricht dasselbe Protokoll wie der Backend-Adapter, Spec §3.2).
- Zeigt aktuelle Frage/Empfehlung, nimmt Text-Antwort entgegen, sendet sie ab; Verlauf scrollt mit (nur bis zur aktuellen Runde — vollständiges Durchblättern älterer Runden ist Phase 4).
- Sendebutton wird während einer laufenden Runde deaktiviert (verhindert den häufigsten Fall paralleler Requests bereits clientseitig; Task 4s Session-Lock bleibt die verbindliche Absicherung).

**Tests**
- Kein dediziertes Frontend-Testframework in diesem Repo (Phase-1-Entscheidung) — abgedeckt durch den manuellen End-to-End-Durchlauf unten, analog zu Phase 1s Task 6/8.

**Validation**
- Manuell: vollständige Text-Session end-to-end im Browser durchspielen (deckt AC1 ab).

## Acceptance

1. **AC1 — Vollständige Text-Session:** Ein Nutzer kann eine Session anlegen, per Text durchgängig grillen lassen, bis die Frontier leer ist, und das Backend meldet den Abschluss-Kandidaten — ohne dass Phase-5-Funktionalität nötig ist, um den Interview-Teil zu beobachten.
2. **AC2 — Überlebt Neustart:** Ein Backend-Neustart mitten in einer Session verliert keinen Baum-Fortschritt; die nächste Runde setzt korrekt fort, mit einer nachweislich neuen SDK-Session-ID.
3. **AC3 — Keine SDK-Session-Wiederverwendung:** Kein Codepfad ruft den Adapter mit `resume=<session_id>` auf; jede Runde injiziert Baum+Verlauf frisch.
4. **AC4 — Konsistenz unter Nebenläufigkeit:** Zwei gleichzeitige Anfragen für dieselbe Session erzeugen nie doppelte oder inkonsistente `decision_node`-Zeilen; ein fehlerhafter Agent-Vorschlag (Zyklus, Duplikat) beschädigt den Baum nicht.

## Validation

| Gate | Command or procedure | Proves |
|---|---|---|
| Frontier-Unit-Tests | `uv run --directory backend pytest tests/test_frontier.py` | AC1, Zyklus-Terminierung |
| Grill-Route-Tests (Neustart, Nebenläufigkeit, Zyklus, Dedup, Fehlerpfad) | `uv run --directory backend pytest tests/test_grill.py` | AC2, AC3, AC4 |
| Code-Review des Adapter-Aufrufs | Grep/Review: kein `resume=` im gesamten `/grill`-Pfad | AC3 (ergänzend zum Verhaltenstest) |
| Manueller End-to-End-Durchlauf | `docker compose up`, volle Text-Session im Browser | AC1, AC2 |

## Risks and Decisions

| Decision or risk | Recommendation | Evidence / mitigation | Consequence if different |
|---|---|---|---|
| Spec nennt falschen AG-UI-Paketnamen/Version (`ag-ui-claude-agent-sdk==0.1.0`) | Auf `ag-ui-claude-sdk>=0.1.5` korrigieren, Spec §3.2 nachziehen | Web-Recherche: Paket existiert nur unter `ag-ui-claude-sdk`, 0.1.0→0.1.5 sind reine Hardening-Patches ohne Breaking Changes | Ohne Korrektur schlägt `pip install` fehl, bevor überhaupt Code läuft |
| Der TTS-/Interrupt-freie Teilumfang von `ag-ui-claude-sdk`, den Phase 2 tatsächlich nutzt, ist schmaler als die volle Fähigkeitsliste, mit der die Adapter-Wahl begründet wird | Bewusst akzeptieren — die volle Fähigkeitsliste rechtfertigt die Abhängigkeit für das Gesamtprodukt (Phase 3 braucht Interrupt-Vorstufen, spätere Phasen HITL), nicht jede Phase muss jede Fähigkeit einzeln beweisen | Devil's-Advocate-Review dieses Planungslaufs | Kein Blocker; wird transparent gemacht statt stillschweigend überclaimt |
| `compliance-base/catalog/stack.json` hat für alle GDPR-Capabilities `chosen: null` (Consent-Capture, Datenminimierung u. a. sind für diese Session-Daten anwendbar, aber unentschieden) | Vor Implementierungsstart `/neurawork-cc-harness:st-select` für die Phase-2-relevanten Capabilities laufen lassen, oder bewusst als offenen Gap akzeptieren | Codebase-Analyst: Gate kann heute nicht blockieren (`validate_mode: warn`, `chosen_total == 0`), ist aber ein echter Compliance-Gap, kein reines Tooling-Artefakt | Ohne Selection bleibt unklar, mit welcher Komponente z. B. Consent-Capture für Sessions umgesetzt wird — kein Blocker für Phase 2 selbst, aber ein wachsender Rückstand |
| PRD/Phase-1-Plan liegen physisch im Sibling-Worktree, nicht im Hauptcheckout | Sobald der Phase-1-Worktree gemergt/entfernt wird, referenzierte Pfade in diesem Plan (Source PRD, Mandatory Reading) auf den dann gültigen Ort aktualisieren | Vom Nutzer bestätigt: PRD "ist in einen Worktree gewandert" | Ohne Nachpflege verweisen die Pfade nach einem `git worktree remove` ins Leere |

## Related Plans

- **Depends on:** `grillme-v1-phase1-grundgeruest.plan.md` (Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`) — liefert Backend-Skeleton, vollständiges Schema (inkl. `decision_node`), Auth, Testläufer.
- **Followed by:** `grillme-phase3-voice-io.plan.md`, `grillme-phase4-history-screenshots.plan.md` (beide hängen von diesem Plan ab).

## Agent Notes

- Die PRD-Datei und `project.json` unter `.claude/PRPs/grillme-app-223fe1d0/` waren zu Beginn dieses Planungslaufs im Hauptcheckout vorhanden und sind während der Arbeit verschwunden; sie liegen jetzt im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`. Vom Nutzer bestätigt als bekanntes Verhalten ("in einen Worktree gewandert"), nicht als Datenverlust behandelt.
