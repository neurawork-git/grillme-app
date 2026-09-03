# Abschluss & Export — expliziter Session-Abschluss mit Artefakt-Erzeugung

**Plan ID:** `grillme-phase5-export-completion`
**Source PRD:** `/home/felix/projects/grillme-app-grillme-v1-phase1-grundgeruest/.claude/PRPs/grillme-app-223fe1d0/prds/grillme-v1.prd.md` (liegt physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`, nicht im Hauptcheckout)
**PRD Phase:** `5 — Abschluss & Export`
**Source Issue:** None
**Plan Publication:** None

## Outcome

**Problem:** Ein Sprachmodell hört zu früh auf, wenn man es allein über den Session-Abschluss entscheiden lässt; ohne bewussten Bestätigungsschritt entstehen entweder verfrüht abgeschlossene Sessions oder gar keine verwertbaren Artefakte.

**Affected user:** Der Solo-Betreiber, am Ende einer Grill-Session.

**User outcome:** Eine bestätigte Session erzeugt zuverlässig ein direkt weiterverwendbares Markdown-Artefakt (bzw. Tickets, je gewähltem Format); eine nicht bestätigte Session bleibt offen und wiederaufnehmbar statt automatisch abgeschlossen zu werden.

**Invariant:** Der Abschluss selbst ist immer ein expliziter Klick des Nutzers, ausgelöst nachdem der Agent eine leere Frontier gemeldet hat (Phase 2, Task 5) — kein Codepfad schließt eine Session ohne diesen Klick, auch nicht ein zweiter Klick auf eine bereits abgeschlossene Session oder zwei gleichzeitige Klicks. Dieser Klick ist zugleich das einzige Ereignis, das für Gamification zählt (Spec §4.3, §7).

**Success signal:** Bestätigte Session erzeugt ein herunterladbares Markdown-Artefakt; unbestätigte Sessions bleiben offen und wiederaufnehmbar (PRD, Phase-5-Erfolgssignal).

**Approach:** Frontend zeigt den Abschluss-Bestätigungs-Button, sobald Phase 2s Leere-Frontier-Flag ankommt; ein Bestätigungs-Endpoint erzeugt aus dem vollständigen `decision_node`-Baum plus dem gewählten `prompt_template` das Artefakt über einen abschließenden Agent-Turn (Entscheidung siehe Recommendation), schreibt danach `artifact`-Zeile, Session-Status und Gamification-Inkrement in einer einzigen DB-Transaktion, atomar gegen Doppelklick und Re-Abschluss abgesichert. Zusätzlich (Task 6/7): Konto-Löschung über `ON DELETE CASCADE` plus expliziten MinIO-Cleanup, und ein separater JSON-Export-Endpoint je Session (Spec §8).

## Recommendation

Kein separater "Abschluss-Service": der Bestätigungs-Endpoint ist die einzige neue Route dieser Phase, alles andere (Baum, Verlauf, Prompt-Template-Daten) existiert bereits aus Phase 1/2.

**Artefakt-Erzeugung: abschließender Agent-Turn, nicht deterministisches Templating — als Plan-Entscheidung, nicht als offene Risk-Zeile.** Formate wie "User Stories"/"Tickets" verlangen Synthese (Akzeptanzkriterien, Formulierung) über einen reinen Q&A-Dump hinaus; Spec §6 beschreibt Formate als "Ausgabevorlage + Interview-Fokus", was mehr als reines Templating impliziert, und das Erfolgssignal fordert ein "direkt weiterverwendbares" Artefakt. Diese Entscheidung bestimmt direkt die Transaktionsarchitektur von Task 2: der Agent-Turn ist ein externer, nicht zurückrollbarer HTTP-Aufruf und muss deshalb **vor** dem Öffnen der DB-Transaktion abgeschlossen sein — die Transaktion selbst umfasst nur noch die drei nachgelagerten DB-Writes.

Gamification wird bewusst nicht als eigenes Event-System gebaut: der Zähler wird direkt in derselben (rein-DB-)Transaktion wie Status-Update und Artefakt-Zeile inkrementiert (ein Ort, eine Quelle der Wahrheit), keine Message-Queue oder asynchrone Verarbeitung für vier Sticker-Stufen.

**Nebenläufigkeit ist kein Nebeneffekt, sondern Teil des Kernmechanismus:** ein Doppelklick, zwei Tabs oder ein Netz-Retry dürfen nie zwei Artefakte oder ein doppeltes Gamification-Inkrement erzeugen. Ein einfaches "Frontier nicht mehr leer → ablehnen" schützt nicht gegen zwei *gleichzeitige* Aufrufe, die beide denselben leeren Zustand lesen (Check-then-act ohne Sperre). Task 2 löst das über einen atomaren, bedingten Status-Übergang (`UPDATE session SET status='completed' WHERE id=? AND status='open'`), der pro Session nur genau einem gleichzeitigen Aufruf einen Erfolg erlaubt — kein zusätzlicher Lock-Mechanismus nötig, derselbe Primitive schützt zugleich gegen Re-Abschluss einer bereits abgeschlossenen Session.

### Evidence

- `.claude/spec.md:147-154` (§4.3) — Abschluss ist expliziter Nutzer-Schritt; nicht bestätigte Sessions bleiben offen/wiederaufnehmbar; Bestätigungsklick zählt für Gamification.
- `.claude/spec.md:226-241` (§6) — Prompt-Bibliothek: Format+Interview-Fokus je Eintrag, Startset (Spec (Markdown), User Stories, Tickets, PRD), beim Session-Anlegen gewählt.
- `.claude/spec.md:242-256` (§7) — Gamification: nur abgeschlossene (bestätigte) Sessions zählen, feste Sticker-Assets, Schwellen als Seed-Daten.
- `.claude/spec.md:258-286` (§8) — Datenschutz: Session-Export als JSON, Kontolöschungskaskade — **nicht dasselbe** wie das hier gebaute Markdown/Tickets-Artefakt (siehe Risks).
- PRD `grillme-v1.prd.md:198,233-239` — Phase-5-Scope: Abschluss-Bestätigung (Klick), Artefakt-Generierung je Format, Export-Screen, Gamification-Zähler im Header.
- Knowledge Base — kein Artikel beschreibt die Export-Pipeline-Mechanik über die Datenmodell-Skizze hinaus (Gap, von der KB-Recherche dieses Planungslaufs explizit benannt).
- Devil's-Advocate-Review (dieser Planungslauf) — benannte den Transaktions-/Nebenläufigkeits-Widerspruch der ersten Fassung (Task 2 unten korrigiert) und dass die Templating-vs-Agent-Turn-Frage vor Fertigstellung des Plans entschieden gehört, nicht als offene Risk-Zeile.

### Alternatives considered

- **Artefakt asynchron per Background-Job erzeugen:** verworfen — die Erfolgssignal-Anforderung ("herunterladbares Artefakt" nach Bestätigung) impliziert eine synchrone, für den Nutzer sofort sichtbare Erzeugung; ein Job-System für einen einzelnen, kurzen Agent-Turn wäre unnötige Infrastruktur für v1.
- **Deterministisches Templating statt Agent-Turn:** verworfen als Standard (siehe Recommendation), bleibt als dokumentierte Kostenoptimierung möglich, falls sich die Agent-Turn-Kosten pro Abschluss als problematisch erweisen — kein Umbau der Transaktionsarchitektur nötig, da Task 3 hinter derselben Schnittstelle austauschbar ist.

## Implementation Context

### Mandatory reading

| File | Why it matters |
|---|---|
| `.claude/spec.md:147-154, 226-256` | Abschluss-Semantik, Prompt-Bibliothek, Gamification-Regeln |
| `grillme-phase2-decision-tree-agent.plan.md` (Task 4-5) | Leere-Frontier-Flag und Session-Lock-Muster, das dieser Plan wiederverwendet |

### Existing patterns and primitives

- **`decision_node`-Baum (Phase 2)** — alleinige Quelle für die Artefakt-Erzeugung, keine Zweit-Repräsentation.
- **`prompt_template`-Tabelle (Phase-1-Schema)** — liefert Ausgabevorlage + Interview-Fokus je Format; Startset kommt aus Seed-Daten (spätere Verwaltungsoberfläche explizit nicht v1).
- **`achievement`-Tabelle (Seed-Daten)** — Schwellen/Titel für Gamification, code-änderungsfrei anpassbar.
- **Bedingter Status-Update als atomares Gate (Phase 2, Task 4: `SELECT ... FOR UPDATE`)** — dieselbe Grundidee (DB-Zeile als Serialisierungspunkt), hier als `UPDATE ... WHERE status='open'` mit Rowcount-Check statt explizitem Lock, weil der Agent-Turn ohnehin außerhalb der Transaktion läuft.

## Scope

### In scope

- Abschluss-Bestätigungs-UI (Button), sichtbar sobald Phase 2s Leere-Frontier-Flag ankommt, deaktiviert nach dem ersten Klick.
- Bestätigungs-Endpoint: Artefakt-Erzeugung (Agent-Turn, außerhalb der Transaktion), atomarer Status-Übergang, `artifact`-Zeile, Gamification-Inkrement — Doppelklick- und Re-Abschluss-sicher.
- Export-Screen: Anzeige + Download des generierten Markdown-Artefakts.
- Gamification-Anzeige im Header (kleine Anzeige, kein eigener Screen, Spec §2).
- Startset-Formate (Spec (Markdown), User Stories, Tickets, PRD) aus Seed-Daten.
- Konto-Löschung: `ON DELETE CASCADE` auf allen `user_id`/`session_id`-Fremdschlüsseln der Phase-1-Migration, Lösch-Endpoint, expliziter MinIO-Cleanup vor dem DB-Delete (Spec §8).
- Session-Export als JSON: eigener Endpoint, liefert Baum + Verlauf + Bildreferenzen einer Session strukturiert (Spec §8) — getrennt vom Markdown/Tickets-Artefakt dieser Phase.

### Not building

- Verwaltungsoberfläche für die Prompt-Bibliothek (Spec §6, explizit nicht v1).
- Ticket-Erzeugung direkt in GitHub Issues (Spec §10, Phase 2 des Produkts).

## Compliance

**Capabilities**: gdpr/rectification-erasure-restriction-processing, gdpr/data-portability-structured-export

Task 6 liefert die tatsächliche Löschung (Erasure) über `ON DELETE CASCADE` plus expliziten MinIO-Cleanup; Task 7 liefert den strukturierten Session-Export nach Spec §8 (getrennt vom Markdown/Tickets-Artefakt aus Task 3, das ein Produkt-Deliverable ist, keine Art.-20-Auskunft). Beide Capabilities sind laut `stack.json` anwendbar, `chosen: null` — dieser Plan liefert die Funktionalität, aber keine formale Komponentenwahl (`st-select` bleibt ein separater Schritt); `data-portability-structured-export` ist bereits mit SeaweedFS als Top-Rationale geranked (`stack-base/reports/rank-2026-09-03.md`), Task 7 nutzt v1 aber eine einfache DB-Query statt SeaweedFS — siehe Risks.

## Implementation

### 1. Abschluss-Bestätigungs-UI

**Files and integration points**
- Chat-Screen aus Phase 2/3, erweitert — UPDATE

**Implementation**
- Sobald die `/grill`-Antwort das Leere-Frontier-Flag (Phase 2, Task 5) trägt, erscheint ein deutlich sichtbarer Bestätigungs-Button statt (oder zusätzlich zu) dem normalen Eingabefeld.
- Klick löst den Bestätigungs-Endpoint (Task 2) aus und deaktiviert den Button sofort (zeigt Ladezustand bis zur Antwort) — reduziert den häufigsten Doppelklick-Fall bereits clientseitig; Task 2s atomarer Status-Übergang bleibt die verbindliche Absicherung.
- Kein automatischer Trigger ohne diesen Klick.

**Tests**
- Kein dediziertes Frontend-Testframework in diesem Repo (Phase-1-Entscheidung) — abgedeckt durch den manuellen Durchlauf (Validation-Tabelle).

**Validation**
- Manuell, Teil des End-to-End-Durchlaufs.

### 2. Bestätigungs-Endpoint

**Files and integration points**
- Neue Backend-Route, z. B. `POST /sessions/{id}/complete` — CREATE

**Implementation**
- Lädt den vollständigen `decision_node`-Baum, prüft `session.status == 'open'` und dass die Frontier (Phase-2-Funktion) leer ist — ist eine der beiden Bedingungen nicht erfüllt, `409 Conflict`, keine weitere Aktion.
- Erzeugt das Artefakt über den Agent-Turn (Task 3) — **außerhalb** jeder DB-Transaktion, da es ein externer, nicht zurückrollbarer HTTP-Aufruf ist. Schlägt dieser Aufruf fehl (Timeout, 5xx), bricht die Route mit definiertem Fehler ab, bevor irgendein DB-Write passiert — Session bleibt unverändert `open`.
- Danach, in **einer** DB-Transaktion: atomarer Status-Übergang `UPDATE session SET status='completed', completed_at=now() WHERE id=? AND status='open'` — liefert der Rowcount `0` (eine parallele Anfrage war schneller oder die Session wurde bereits abgeschlossen), bricht die Transaktion ab, kein `artifact`-Insert, kein Zähler-Inkrement, `409` an den Aufrufer. Liefert er `1`, schreibt dieselbe Transaktion die `artifact`-Zeile und inkrementiert den Gamification-Zähler, dann Commit. Dieser bedingte Update ist zugleich der Schutz gegen Doppelklick/zwei-Tabs (nur eine gleichzeitige Anfrage gewinnt den Rowcount-`1`-Fall) und gegen Re-Abschluss (ein zweiter Aufruf auf eine bereits `completed`-Session trifft immer Rowcount `0`).

**Tests**
- Test: erfolgreicher Abschluss erzeugt genau eine `artifact`-Zeile, setzt Status korrekt, inkrementiert Zähler.
- Test: Frontier bei Aufruf nicht leer → `409`, kein Teilzustand.
- Test: Session bereits `completed` → zweiter Aufruf liefert `409`, keine zweite `artifact`-Zeile, kein zweites Zähler-Inkrement.
- Nebenläufigkeitstest: zwei parallele Aufrufe für dieselbe offene Session (z. B. via `asyncio.gather`) → genau einer erhält `200`+Artefakt, der andere `409`; am Ende existiert genau eine `artifact`-Zeile und genau ein Zähler-Inkrement.
- Test: Agent-Turn (Task 3) schlägt fehl → Route liefert definierten Fehler, Session bleibt `open`, keine DB-Writes.

**Validation**
- `uv run --directory backend pytest tests/test_complete.py` — alle obigen Fälle grün, beweist AC1, AC3, AC4.

### 3. Artefakt-Erzeugung

**Files and integration points**
- Backend-Modul, z. B. `backend/app/artifact.py` — CREATE

**Implementation**
- Nimmt Baum + `prompt_template` (Ausgabevorlage, Interview-Fokus) entgegen, ruft einen abschließenden Agent-Turn mit dem `prompt_template`-Ausgabevorlage-Text als System-Prompt und dem vollständigen Baum als Kontext auf, erhält das fertige Markdown-Artefakt (bzw. mehrere Ticket-Blöcke in einer Markdown-Datei für das Tickets-Format) als Rückgabewert.
- Kein `resume=`; dieser Turn ist wie jede Phase-2-Runde eine frische SDK-Session (dieselbe Invariante wie im Interview selbst).

**Tests**
- Test je Startset-Format (Spec (Markdown), User Stories, Tickets, PRD): erzeugtes Artefakt enthält alle beantworteten Knoten, respektiert die Ausgabevorlage des gewählten Formats (gegen einen gemockten Agent-Aufruf, der ein festes Beispiel-Artefakt zurückgibt — kein echter API-Call in der Unit-Test-Suite).
- Test: Agent-Aufruf schlägt fehl/Timeout → Funktion propagiert einen definierten Fehler statt eines leeren/halben Artefakts.

**Validation**
- `uv run --directory backend pytest tests/test_artifact.py` — grün.

### 4. Export-Screen

**Files and integration points**
- Neuer Next.js-Screen, z. B. `frontend/app/sessions/[id]/export` — CREATE

**Implementation**
- Zeigt das generierte Artefakt (Markdown gerendert) und bietet einen Download an.
- Erreichbar nach erfolgreichem Abschluss (Task 2), verlinkt von der Session-Liste für bereits abgeschlossene Sessions.

**Tests**
- Kein dediziertes Frontend-Testframework — abgedeckt durch den manuellen Durchlauf.

**Validation**
- Manuell, Teil des End-to-End-Durchlaufs.

### 5. Gamification-Zähler im Header

**Files and integration points**
- Header-Komponente (Struktur folgt Phase-1-Frontend-Layout) — UPDATE

**Implementation**
- Liest `achievement`-Seed-Daten (Schwellen: 1/5/10/25/50 abgeschlossene Sessions; 50/250/1000 beantwortete Fragen) und den aktuellen Nutzer-Stand, zeigt eine kleine Anzeige — kein eigener Screen (Spec §2, §7).

**Tests**
- Kein dediziertes Frontend-Testframework — abgedeckt durch den manuellen Durchlauf.

**Validation**
- Manuell, Teil des End-to-End-Durchlaufs.

### 6. Konto-Löschung (kaskadierend, inkl. MinIO)

**Files and integration points**
- Migration, die die `user_id`-FK auf `session.user_id → user.id` sowie die `session_id`-FKs auf `message`, `decision_node`, `image`, `artifact` (und `token_usage`) explizit auf `ON DELETE CASCADE` setzt, sofern die Phase-1-Migration sie ohne diese Klausel anlegt (Default in Postgres ist `NO ACTION`) — CREATE
- Neue Backend-Route, z. B. `DELETE /account` — CREATE

**Implementation**
- **Nicht RLS/RBAC** — das sind Zugriffskontrolle (wer darf lesen/schreiben), keine Löschautomatik. Der Mechanismus ist `ON DELETE CASCADE`: löscht die `user`-Zeile, räumt Postgres selbst alle abhängigen Zeilen über die FK-Kette (`user → session → message/decision_node/image/artifact`, `session → token_usage`). Das ist der "einfach anschalten"-Teil und stimmt für alles, was in Postgres liegt.
- MinIO-Objekte liegen außerhalb Postgres — CASCADE erreicht sie nicht. Endpoint liest **vor** dem DB-Delete alle `image`-Zeilen des Nutzers (über dessen Sessions), löscht die zugehörigen MinIO-Objekte, und löscht erst danach die `user`-Zeile (CASCADE räumt den Rest). Reihenfolge MinIO-zuerst: schlägt der MinIO-Cleanup fehl, bricht die Route vor dem DB-Delete ab — lieber ein noch existierendes Konto mit einem Fehler melden als eine gelöschte DB-Zeile mit verwaisten MinIO-Objekten.
- Erfordert Passwort-Reauth im Request (destruktive, irreversible Aktion) — kein Löschen allein durch einen gültigen Session-Cookie.
- Kein Soft-Delete/Undo-Fenster in v1 (Spec macht dazu keine Aussage, PRD nennt keine Nachfrist) — Löschung ist sofort endgültig, im Frontend mit einer expliziten Bestätigung (Task 1-Muster: zweiter Klick/Texteingabe) abgesichert.

**Tests**
- Test: Konto mit Sessions, Nachrichten, Knoten, Bildern, Artefakten anlegen, löschen → alle zugehörigen Zeilen sind weg (Query über jede Tabelle liefert 0 Treffer für die `user_id`).
- Test: MinIO-Objekte des Nutzers existieren nach Löschung nicht mehr.
- Test: MinIO-Cleanup schlägt fehl (gemockt) → `user`-Zeile bleibt bestehen, kein Teilzustand.
- Test: falsches Passwort bei Reauth → `401`, Konto bleibt bestehen.

**Validation**
- `uv run --directory backend pytest tests/test_account_delete.py` — grün.

### 7. Session-Export als JSON

**Files and integration points**
- Neue Backend-Route, z. B. `GET /sessions/{id}/export.json` — CREATE

**Implementation**
- Serialisiert `decision_node`-Baum, `message`-Verlauf und `image`-Referenzen (MinIO-Objektschlüssel, nicht die Bild-Bytes selbst) einer Session zu einem JSON-Dokument — eine einfache, direkte DB-Query plus `json`-Serialisierung, kein separates Speicher-/Queue-System (die in `stack.json` geführte SeaweedFS-Empfehlung ist für einen späteren, größer skalierten Export gedacht, nicht für v1s Umfang von wenigen Sessions).
- Getrennt vom Markdown/Tickets-Artefakt aus Task 3: dieser Export ist eine vollständige, maschinenlesbare Rohdaten-Kopie der Session (Spec §8), das Artefakt ist der aufbereitete Produkt-Output.

**Tests**
- Test: Export einer Session mit Text, Voice-Nachrichten und Bildern enthält alle drei Datentypen strukturiert.
- Test: Export einer fremden Session (anderer Nutzer) → `404`, kein Datenleck über die Ownership-Prüfung hinweg.

**Validation**
- `uv run --directory backend pytest tests/test_session_export.py` — grün.

## Acceptance

1. **AC1 — Bestätigung erzeugt Artefakt:** Genau der explizite Bestätigungsklick — kein anderer Codepfad — erzeugt eine `artifact`-Zeile und setzt die Session auf abgeschlossen.
2. **AC2 — Unbestätigt bleibt offen:** Eine Session ohne Bestätigungsklick bleibt beliebig lange offen und ist über die Session-Liste wiederaufnehmbar.
3. **AC3 — Gamification nur bei echtem Abschluss:** Der Zähler erhöht sich ausschließlich beim Bestätigungsklick, nie beim bloßen Anlegen oder Fortsetzen einer Session, nie zweimal für dieselbe Session.
4. **AC4 — Kein Teilzustand unter Nebenläufigkeit oder Re-Abschluss:** Zwei gleichzeitige Bestätigungsklicks und ein zweiter Klick auf eine bereits abgeschlossene Session erzeugen nie ein zweites Artefakt oder ein doppeltes Zähler-Inkrement.
5. **AC5 — Vollständige Konto-Löschung:** Löschen des Kontos entfernt alle zugehörigen Postgres-Zeilen (über alle neun Tabellen) und alle MinIO-Objekte des Nutzers; ein fehlschlagender MinIO-Cleanup verhindert die DB-Löschung statt einen Teilzustand zu hinterlassen.
6. **AC6 — Session-Export als JSON:** Jede eigene Session lässt sich als strukturiertes JSON (Baum, Verlauf, Bildreferenzen) exportieren; fremde Sessions sind über den Export-Endpoint nicht einsehbar.

## Validation

| Gate | Command or procedure | Proves |
|---|---|---|
| Bestätigungs-Endpoint-Tests (inkl. Nebenläufigkeit, Re-Abschluss) | `uv run --directory backend pytest tests/test_complete.py` | AC1, AC3, AC4 |
| Format-Artefakt-Tests | `uv run --directory backend pytest tests/test_artifact.py` | Task 3 Korrektheit |
| Konto-Löschungs-Tests | `uv run --directory backend pytest tests/test_account_delete.py` | AC5 |
| Session-Export-Tests | `uv run --directory backend pytest tests/test_session_export.py` | AC6 |
| Manueller Durchlauf | Session bis Frontier leer führen, bestätigen, Export prüfen; separat: Session ohne Bestätigung verlassen, in Liste als offen wiederfinden; separat: zweimal auf Bestätigen klicken; separat: Konto mit Daten löschen und Postgres/MinIO leer vorfinden | AC1, AC2, AC3, AC4, AC5 |

## Risks and Decisions

| Decision or risk | Recommendation | Evidence / mitigation | Consequence if different |
|---|---|---|---|
| Agent-Turn-basierte Artefakt-Erzeugung kostet einen zusätzlichen API-Aufruf pro Abschluss und liefert nicht-deterministischen Output | Akzeptieren — Formatqualität (Kernanforderung: "direkt weiterverwendbar") wiegt schwerer als der zusätzliche Aufruf; Format-Tests (Task 3) laufen gegen einen gemockten Agent, nicht gegen den echten nicht-deterministischen Output, um deterministisch zu bleiben | Recommendation oben; Devil's-Advocate-Review markierte die vorherige unentschiedene Fassung als Kernarchitektur-Lücke | Bei realen Kostenproblemen: Wechsel auf deterministisches Templating als dokumentierte Alternative (siehe Alternatives considered), ohne Task-2-Transaktionsarchitektur zu ändern |
| `ON DELETE CASCADE` auf den Phase-1-FKs ist eine Annahme über deren aktuelle Definition (Phase-1-Plan nennt bei den FKs keine explizite `ON DELETE`-Klausel) | Vor Task 6 gegen den tatsächlichen Stand der Phase-1-Migration prüfen; falls dort bereits `CASCADE` gesetzt ist, entfällt die Migration aus Task 6, der Rest (MinIO-Cleanup, Endpoint) bleibt unverändert | Spec §9 trifft dazu keine Aussage, Postgres-Default ist `NO ACTION` | Ohne Prüfung könnte Task 6s Migration einen bereits vorhandenen Constraint redundant ändern — harmlos, aber unnötig |
| MinIO-Cleanup vor DB-Delete lässt ein kurzes Fenster, in dem MinIO-Objekte bereits gelöscht sind, aber die `user`-Zeile (und damit sichtbarer Zugriff) noch existiert | Akzeptiert für v1 — kein Saga-/Outbox-Pattern für eine einmalige, seltene, manuell bestätigte Aktion; bei einem Absturz zwischen beiden Schritten bleibt ein Konto ohne Bilder, aber mit allen anderen Daten bestehen, kein Datenverlust anderer Nutzer | Konsistenzkosten-Nutzen-Abwägung dieses Plans | Bei Bedarf: Aufräum-Skript, das verwaiste `user`-Zeilen ohne zugehörige MinIO-Objekte findet — nicht in v1 |

## Related Plans

- **Depends on:** `grillme-phase3-voice-io.plan.md`, `grillme-phase4-history-screenshots.plan.md`
- **Followed by:** None

## Agent Notes

- PRD/Phase-1-Plan liegen physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest` (vom Nutzer bestätigt), nicht im Hauptcheckout.
