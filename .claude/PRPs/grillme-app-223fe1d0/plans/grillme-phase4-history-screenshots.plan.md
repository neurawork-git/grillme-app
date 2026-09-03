# Verlauf & Screenshots — durchblätterbare Session-Historie mit Bild-Uploads

**Plan ID:** `grillme-phase4-history-screenshots`
**Source PRD:** `/home/felix/projects/grillme-app-grillme-v1-phase1-grundgeruest/.claude/PRPs/grillme-app-223fe1d0/prds/grillme-v1.prd.md` (liegt physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`, nicht im Hauptcheckout)
**PRD Phase:** `4 — Verlauf & Screenshots`
**Source Issue:** None
**Plan Publication:** None

## Outcome

**Problem:** Ein Screenshot ist oft der Kern einer Anforderung; ohne durchblätterbaren Verlauf und dauerhaft mitgeschickte Bilder vergisst der Agent in späteren Runden, was er in Runde eins gesehen hat, und der Nutzer kann frühere Fragen/Antworten nicht nachvollziehen.

**Affected user:** Der Solo-Betreiber, während und nach einer Grill-Session.

**User outcome:** Zu jeder laufenden oder abgeschlossenen Session lässt sich der komplette Fragenkatalog mit Antworten durchblättern; Screenshots werden Teil dieses Verlaufs und bleiben für den Agenten über die ganze Session hinweg sichtbar.

**Invariant:** Ein Screenshot, der einmal Teil einer Session ist, wird bei jedem Folge-Aufruf wieder an den Agenten mitgeschickt — "anything not in this round's prompt does not exist" (Spec §5.3, Knowledge Base `connections/agent-state-and-decision-tree`). Der Verlauf zeigt Frage, Empfehlung, Antwort und Status je Knoten (Spec §4.2).

**Success signal:** Nutzer kann zu jeder abgeschlossenen oder laufenden Session den kompletten Fragenkatalog mit Antworten durchblättern (PRD, Phase-4-Erfolgssignal).

**Approach:** Verlaufs-UI liest direkt die `decision_node`-Zeilen (Phase 2) einer Session und rendert sie durchblätterbar; Screenshot-Upload legt Bilder in MinIO ab und schreibt eine `image`-Zeile, referenziert an die Session; der Phase-2-Prompt-Builder wird um einen Schritt erweitert, der alle Session-Bilder als Bild-Content-Blöcke in jede Runde einfügt.

## Recommendation

Kein separates Verlaufs-Datenmodell: `decision_node` (Phase 2) ist bereits die vollständige Wahrheit über Fragen/Empfehlungen/Antworten — die Verlaufs-UI ist eine reine Leseansicht darauf, kein zweiter Speicherort. Bilder brauchen echten neuen State (`image`-Tabelle + MinIO-Objekt), weil es dafür in Phase 2 keine Entsprechung gibt; das ist laut Spec-Datenmodell (§9) ohnehin als eigene Tabelle vorgesehen.

Der einzige echte Integrationspunkt ist der Prompt-Builder aus Phase 2 (Task 4 dort): der muss um Bild-Content-Blöcke erweitert werden, damit die "immer wieder mitschicken"-Invariante gilt. Das ist eine Erweiterung eines bestehenden Eigentümers (Phase-2-Route), keine neue Koordinationsschicht — **aber** Phase 3 erweitert dieselbe Route parallel um die Sprachausgabe-Anbindung (siehe Risks: Koordination mit Phase 3 nötig, beide Worktrees ändern `backend/app/grill.py`).

Ohne Obergrenze wächst der pro Runde mitgeschickte Bild-Kontext mit Bildanzahl × -größe × Rundenzahl unbegrenzt — Spec §5.3 benennt das Problem selbst ("wenn Sessions so lang werden, dass die Bild-Tokens schmerzen") und verschiebt nur die *Lösung* (Text-Ersatz) auf später, nicht das Risiko. Diese Phase braucht deshalb ein Downsampling/Größenlimit beim Upload als Interimsmaßnahme (Task 2), auch ohne die volle Optimierung zu bauen.

### Evidence

- `.claude/spec.md:184-192` (§5.3) — Screenshots dauerhaft Teil des Verlaufs, bei jedem Folge-Aufruf wieder mitgeschickt; spätere Optimierung (Text-Ersatz bei Token-Druck) explizit nicht v1.
- `.claude/spec.md:136-145` (§4.2) — Baum-Knoten-Struktur (Frage, Empfehlung, Antwort, Status), Basis für die Verlaufsansicht.
- PRD `grillme-v1.prd.md:197,225-231` — Phase-4-Scope: Verlaufs-UI je Knoten, Screenshot-Upload und -Anzeige im Verlauf.
- Knowledge Base `connections/agent-state-and-decision-tree.md` — "anything not in this round's prompt does not exist", explizit auf §5.3/Screenshots bezogen.
- Codebase-Analyst (dieser Planungslauf) — `"MinIO (S3-compatible object store with Object Lock/WORM)"` ist nur unter dem **nicht aktiven** `soc2`-Framework katalogisiert (`compliance-base/config.json` filtert auf `["gdpr"]`); eine Erwähnung im Plan würde vom Gate als `orphaned` eingestuft, nicht als `off_stack` — kein Blocker, aber keine Compliance-Aussage über die MinIO-Wahl selbst.

### Alternatives considered

- **Verlauf als eigene Read-Model-Tabelle (denormalisiert aus `decision_node`):** verworfen — `decision_node` ist bereits die Wahrheit; eine zweite Repräsentation müsste synchron gehalten werden, ohne dass ein Performance-Problem das rechtfertigt.

## Implementation Context

### Mandatory reading

| File | Why it matters |
|---|---|
| `.claude/spec.md:184-192` | Screenshot-Persistenz-Invariante |
| `grillme-phase2-decision-tree-agent.plan.md` (Task 4) | Prompt-Builder, der um Bild-Content-Blöcke erweitert wird |

### Existing patterns and primitives

- **`decision_node`-Tabelle (Phase 2)** — alleinige Datenquelle der Verlaufs-UI, keine Duplikation.
- **Phase-2-Prompt-Builder** — Integrationspunkt für das erneute Mitschicken der Bilder jede Runde.

## Scope

### In scope

- Verlaufs-UI: durchblätterbare Liste aller `decision_node`-Einträge einer Session (Frage/Empfehlung/Antwort/Status), erreichbar für laufende und abgeschlossene Sessions.
- Screenshot-Upload (Browser-Datei/Paste) → MinIO-Objekt + `image`-Zeile mit Session-Referenz.
- Screenshot-Anzeige inline im Verlauf, an der Stelle, an der es hochgeladen wurde.
- Erweiterung des Phase-2-Prompt-Builders: alle Session-Bilder werden jede Runde als Bild-Content-Blöcke mitgeschickt.

### Not building

- Ersetzen alter Bilder durch Textbeschreibungen bei Token-Druck (Spec §5.3, explizit Phase 2 des Produkts).
- Kaskadierte MinIO-Objekt-Löschung bei Kontolöschung (Spec §8) — **kein PRD-Phase 2-5 besitzt diese Aufgabe** (siehe Risks); wird hier bewusst nicht mitgebaut, um Scope-Grenzen nicht stillschweigend zu verschieben.

## Compliance

**Capabilities**: none — liefert nur Bild-Speicherung, keinen GDPR-Mechanismus dafür

`gdpr/rectification-erasure-restriction-processing` und `gdpr/data-minimisation-accuracy-retention-lifecycle` sind für Bilddaten anwendbar, `chosen: null`, und bleiben in diesem Plan offen (keine Löschkaskade, keine Aufbewahrungsfrist, keine Sonderkategorien-Behandlung) — siehe Risks zur Lücke zwischen Spec §8 und der PRD-Phasenliste.

## Implementation

### 1. Verlaufs-UI

**Files and integration points**
- Next.js-Screen, z. B. `frontend/app/sessions/[id]/history` (Struktur folgt Phase-1/2-Frontend-Layout) — CREATE

**Implementation**
- Liest `decision_node`-Zeilen einer Session über einen Read-Endpoint (neuer, einfacher GET, oder Erweiterung eines bestehenden Session-Detail-Endpoints aus Phase 1).
- Rendert Frage, Empfehlung, Antwort, Status je Knoten, chronologisch/hierarchisch nach `parent_id`, durchblätterbar.
- **Paginierung:** Backend-Endpoint liefert die Knoten seitenweise (z. B. 30 pro Seite, `?cursor=`), Frontend lädt bei Bedarf nach ("mehr laden") statt alles auf einmal zu rendern — feste Entscheidung, kein "je nach Sessionlänge" offen gelassen, weil eine lange Session genau der Kernanwendungsfall ist, für den diese UI gebaut wird.
- Erreichbar sowohl für laufende als auch abgeschlossene Sessions (kein Statusfilter, der abgeschlossene Sessions ausblendet).

**Tests**
- Backend-Test: Read-Endpoint paginiert korrekt (Seitengröße, Cursor, letzte Seite).
- Kein dediziertes Frontend-Testframework in diesem Repo (Phase-1-Entscheidung) — Rendering wird über den manuellen Durchlauf unten geprüft, inklusive einer Session mit realistisch vielen Knoten (>100).

**Validation**
- `uv run --directory backend pytest tests/test_history.py` — Paginierung grün.

### 2. Screenshot-Upload-Endpoint

**Files and integration points**
- Neue Backend-Route, z. B. `POST /sessions/{id}/images` — CREATE

**Implementation**
- Nimmt Bild-Upload entgegen, validiert Format (Whitelist: PNG/JPEG/WebP) und Größe (Hard-Cap, z. B. 10 MB, `413` bei Überschreitung, bevor der Body vollständig gelesen wird).
- Downsampled auf eine Obergrenze (z. B. max. 1568px lange Kante — verbreitete Empfehlung für Vision-Modell-Eingaben, reduziert Bild-Tokens ohne Informationsverlust für Screenshot-Inhalte) vor der MinIO-Ablage.
- Legt das Bild in MinIO ab (Bucket/Key-Schema z. B. `sessions/{session_id}/{image_id}`), schreibt eine `image`-Zeile (MinIO-Objektschlüssel, Session-Referenz, `created_at` als Ordnungsfeld für Task 3) nach Spec §9 — DB-Insert erst nach bestätigtem MinIO-Schreibvorgang (keine Zeile für ein nicht existierendes Objekt).
- Im Gegensatz zu Voice-Audio (Phase 3) werden Screenshots **dauerhaft** gespeichert — kein Lösch-Schritt nach Verarbeitung.

**Tests**
- Test: erfolgreicher Upload erzeugt genau eine `image`-Zeile und ein MinIO-Objekt unter dem erwarteten Key, Bild ist downgesampelt.
- Test: fehlgeschlagener/abgebrochener MinIO-Schreibvorgang (inkl. simuliertem Teilschreiben) erzeugt keine verwaiste `image`-Zeile.
- Test: Upload über dem Größenlimit → `413`; Upload mit nicht erlaubtem Format → `415`, jeweils ohne MinIO-Schreibversuch.

**Validation**
- `uv run --directory backend pytest tests/test_images.py` — grün.

### 3. Screenshot-Anzeige im Verlauf

**Files and integration points**
- Verlaufs-UI aus Task 1 — UPDATE

**Implementation**
- Bilder werden inline an der Stelle im Verlauf angezeigt, einsortiert nach `image.created_at` relativ zu `decision_node.created_at` (Ordnungsfeld aus Task 2).

**Tests**
- Kein dediziertes Frontend-Testframework — abgedeckt durch den manuellen Durchlauf (Task 1), erweitert um eine Session mit gemischtem Text-/Bild-Verlauf.

**Validation**
- Manuell, Teil des End-to-End-Durchlaufs (siehe Validation-Tabelle unten).

### 4. Prompt-Builder-Erweiterung: Bilder jede Runde mitschicken

**Files and integration points**
- Phase-2-Prompt-Builder (`/grill`-Route, Task 4 dort) — UPDATE

**Implementation**
- Vor jedem Agent-Aufruf werden alle `image`-Zeilen der Session geladen und als Bild-Content-Blöcke zusätzlich zum Text-Prompt (Baum+Verlauf) an die SDK-Anfrage angehängt.
- Gilt für jede Runde, unabhängig davon, in welcher Runde das Bild ursprünglich hochgeladen wurde — erfüllt die "nichts vergessen"-Invariante aus Spec §5.3.

**Tests**
- Integrationstest: Session mit einem in Runde 1 hochgeladenen Bild — Runde 8 des Agent-Aufrufs enthält das Bild weiterhin im Prompt-Payload.
- Integrationstest: Session mit 15 Bildern über 20 Runden — Prompt-Aufbau bleibt innerhalb einer definierten Bild-Byte-Obergrenze (misst die Wirkung von Task 2s Downsampling, keine harte Assertion auf Modell-Tokenzahlen).

**Validation**
- `uv run --directory backend pytest tests/test_grill_images.py` — grün, beweist AC2.

## Acceptance

1. **AC1 — Durchblätterbarer Verlauf:** Jede Session (laufend oder abgeschlossen) zeigt ihren vollständigen Frage/Empfehlung/Antwort-Verlauf durchblätterbar an, auch bei >100 Knoten (Paginierung greift).
2. **AC2 — Bilder bleiben sichtbar:** Ein einmal hochgeladenes Bild wird bei jeder folgenden Agent-Runde erneut mitgeschickt, unabhängig vom Abstand zur Upload-Runde.
3. **AC3 — Bilder im Verlauf sichtbar:** Hochgeladene Screenshots erscheinen inline im Verlauf an der Stelle ihres Uploads.
4. **AC4 — Upload-Konsistenz:** Erfolgreicher Upload erzeugt genau ein Bild-Objekt plus eine `image`-Zeile; ein fehlgeschlagener Upload (Größe, Format, MinIO-Fehler) erzeugt keins von beidem.

## Validation

| Gate | Command or procedure | Proves |
|---|---|---|
| Verlaufs-Paginierungstest | `uv run --directory backend pytest tests/test_history.py` | AC1 |
| Upload-Konsistenz-/Validierungstest | `uv run --directory backend pytest tests/test_images.py` | AC4 |
| Prompt-Bild-Persistenz-/Budget-Integrationstest | `uv run --directory backend pytest tests/test_grill_images.py` | AC2 |
| Manueller Durchlauf | Session mit Screenshot und >100 Knoten anlegen, mehrere Runden später Verlauf durchblättern | AC1, AC2, AC3 |

## Risks and Decisions

| Decision or risk | Recommendation | Evidence / mitigation | Consequence if different |
|---|---|---|---|
| Spec §8 fordert für v1 kaskadierte MinIO-Löschung und Session-JSON-Export | Gelöst — beide sind jetzt Task 6/7 in `grillme-phase5-export-completion.plan.md` (Konto-Löschung über `ON DELETE CASCADE` + expliziten MinIO-Cleanup, Session-Export als eigener JSON-Endpoint) | War eine echte Lücke der PRD-Phasenaufteilung, keine offene Spec-Frage; auf Nutzer-Rückmeldung hin in Phase 5 nachgetragen | Kein Risiko mehr für diesen Plan; Phase 4 legt weiterhin nur die MinIO-Schreib-/Downsample-Logik an, die Phase 5 beim Löschen konsumiert |
| Phase 3 und Phase 4 ändern beide `backend/app/grill.py` (Sprachausgabe-Anbindung bzw. Bild-Content-Blöcke) in parallelen Worktrees | Beide Änderungen als eigenständige, komponierbare Funktionen schreiben (z. B. `attach_images()`, separater `/messages/{id}/speech`-Endpoint statt Response-Feld — bereits so in Phase 3 Task 4 angepasst), damit ein Merge beider Worktrees keine der beiden Änderungen verliert; wer zuerst mergt, rebased der andere Worktree kurz vor der eigenen Fertigstellung | Devil's-Advocate-Review beider Pläne | Ohne Koordination: stiller Verlust einer der beiden Änderungen bei naiver Merge-Auflösung |
| MinIO ist im Compliance-Katalog nur unter dem inaktiven `soc2`-Framework gelistet, erscheint bei Erwähnung als `orphaned` statt `on_stack` | Als reines Labeling-Artefakt der GDPR-only-Scope-Filterung akzeptieren, nicht als Blocker werten | Codebase-Analyst: `gate_lib.component_index()` indiziert alle Frameworks, `stack.json` enthält aber nur gdpr-Keys | Kein Blocker; falls SOC2 später aktiviert wird, sollte MinIO dort explizit durchlaufen werden |

## Related Plans

- **Depends on:** `grillme-phase2-decision-tree-agent.plan.md`
- **Followed by:** `grillme-phase5-export-completion.plan.md`

## Agent Notes

- PRD/Phase-1-Plan liegen physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest` (vom Nutzer bestätigt), nicht im Hauptcheckout.
