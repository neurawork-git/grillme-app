# Voice-Input/Output — Sprachmodus als vollwertige Alternative zu Text

**Plan ID:** `grillme-phase3-voice-io`
**Source PRD:** `/home/felix/projects/grillme-app-grillme-v1-phase1-grundgeruest/.claude/PRPs/grillme-app-223fe1d0/prds/grillme-v1.prd.md` (liegt physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest`, nicht im Hauptcheckout)
**PRD Phase:** `3 — Voice-Input/Output`
**Source Issue:** None
**Plan Publication:** None

## Outcome

**Problem:** Ideen entstehen oft unterwegs (Auto, Joggen), wo Tippen nicht praktikabel ist; ohne Sprachein-/-ausgabe bleibt GrillMe auf Situationen beschränkt, in denen der Nutzer tippen kann.

**Affected user:** Der Solo-Betreiber, unterwegs ohne freie Hände zum Tippen.

**User outcome:** Eine Session lässt sich komplett per Sprache führen — diktieren, Agent antwortet vor, jederzeit mitten in der Session zurück zu Text wechselbar, ohne den Verlauf zu brechen.

**Invariant:** Text- und Voice-Modus teilen sich denselben Baum/Verlauf (Phase 2) — der Modus ist nur, wie eine Runde ein- und ausgegeben wird, nicht ein zweiter Session-Typ. Audio wird nach erfolgreicher Transkription gelöscht; nur der Text bleibt (Spec §5.4). Erkannte Sprache erscheint vor dem Absenden editierbar (Spec §5.1) — falsch erkannte Wörter erzeugen sonst falsche Baumknoten.

**Success signal:** Eine Session lässt sich komplett per Voice führen, Moduswechsel mitten in der Session funktioniert ohne Verlauf-Bruch (PRD, Phase-3-Erfolgssignal).

**Approach:** `Transcriber`/`Speaker`-Interfaces (Python-ABCs) mit einer Deepgram-Implementierung (Nova-3 Batch-STT, Aura-2 Batch-TTS, beide bestätigt Deutsch-fähig) hinter einem austauschbaren Provider-Switch; Audio wird transient verarbeitet (kein MinIO, keine Persistenz), Frontend nutzt Pausenerkennung zum Auslösen des Uploads und zeigt das Transkript vor dem Absenden editierbar an.

## Recommendation

Kein eigener Streaming-/Realtime-Voice-Stack: Spec und PRD sind bewusst turn-based (2–4 s/Zug), Anthropic bietet ohnehin keine Realtime-Sprach-API — Vollduplex ist explizit Phase 2 (spätere Produktphase, nicht dieser PRP-Phase). Turn-based reduziert Voice auf zwei Batch-HTTP-Aufrufe (Transkription, Sprachausgabe) um denselben `/grill`-Endpoint aus Phase 2 herum — kein neuer Session-Typ, kein Parallelzustand zu Text.

Nur Deepgram wird verdrahtet. Die vier in der Spec genannten Alternativen (Groq, AssemblyAI, faster-whisper, Piper) hinter demselben Interface zusätzlich zu bauen, ohne dass v1 sie nutzt, wäre spekulative Arbeit — das Interface selbst ist der Beweis, dass ein Wechsel eine Konfigurationsentscheidung bleibt (Spec §5.4), nicht vier weitere Integrationen im MVP.

### Evidence

- `.claude/spec.md:156-224` (§5) — Zwei Modi ein Verlauf, jederzeit umschaltbar, editierbares Transkript, turn-based Sprachdialog, Provider-Interfaces, Audio-Löschung nach Transkription.
- PRD `grillme-v1.prd.md:196,217-223` — Phase-3-Scope: `Transcriber`/`Speaker`-Interfaces, Deepgram-Implementierung, Moduswechsel Text/Voice, editierbares Transkript, Audio-Löschung.
- Web-Recherche (dieser Planungslauf) — Deepgram Nova-3 Batch-Endpoint `POST /v1/listen?model=nova-3` unterstützt `de`/`de-CH` (monolingual und im 10-Sprachen-Multilingual-Set); Aura-2 Batch-Endpoint `POST /v1/speak?model=<voice>`, sieben deutsche Stimmen (`aura-2-elara-de` u. a.); Preise $0,0043/Min. STT, $0,030/1.000 Zeichen TTS, $200 Startguthaben. Groq `whisper-large-v3-turbo` Free-Tier aktuell bestätigt: 2.000 Requests/Tag, 25 MB/Datei.
- Knowledge Base — `concepts/input-channels.md`: Modus jederzeit umschaltbar, Audio-Löschung nach Transkription, ElevenLabs ausdrücklich ausgeschlossen (Nutzungsrechte/Attribution); `connections/agent-state-and-decision-tree.md`: "anything not in this round's prompt does not exist" — Voice ändert nur den Ein-/Ausgabekanal einer Runde, nicht den Prompt-Aufbau aus Phase 2.
- Codebase-Analyst (dieser Planungslauf) — "Deepgram" ist in keiner Katalog-Komponente in `capabilities.json` gelistet; das Compliance-Gate hat zur Provider-Wahl selbst keine Meinung. Die GDPR-Capabilities, die die Deepgram-*Beziehung* betreffen (`processor-joint-controller-contracting`, `cross-border-transfer-safeguards`), sind anwendbar, aber `chosen: null`.

### Alternatives considered

- **Alle vier Alternativ-Provider (Groq/AssemblyAI/faster-whisper/Piper) sofort mitbauen:** verworfen — YAGNI; das Interface macht den späteren Wechsel billig, vier ungenutzte Integrationen jetzt sind reine Vorratsarbeit.
- **Streaming/Realtime-Voice statt Batch:** verworfen laut Spec (§5.2) — kein Anthropic-Realtime-API, Aufwand nur gerechtfertigt nach echten v1-Sessions.

## Implementation Context

### Mandatory reading

| File | Why it matters |
|---|---|
| `.claude/spec.md:156-224` | Vollständige Voice-Spezifikation: Modi, Editierbarkeit, Provider-Interfaces, Löschpflicht |
| `grillme-phase2-decision-tree-agent.plan.md` | `/grill`-Route und Prompt-Aufbau, um die dieser Plan nur Ein-/Ausgabe legt |

### Existing patterns and primitives

- **`/grill`-Route aus Phase 2** — Voice fügt nur einen vorgelagerten Transkriptions-Schritt und einen nachgelagerten Sprachausgabe-Schritt hinzu; die Route selbst und der Prompt-Aufbau ändern sich nicht.
- **`message.mode`-Spalte** — Teil der vollständigen Spec-§9-Migration aus Phase 1 (`grillme-v1-phase1-grundgeruest.plan.md`, Task 2); existiert bereits. Dieser Plan setzt sie nur (`'text'`/`'voice'`), legt sie nicht an.
- **Session-Lock aus Phase 2 (`/grill`-Route, `SELECT ... FOR UPDATE`)** — Voice ruft dieselbe Route auf und erbt denselben Nebenläufigkeitsschutz; kein eigener Lock-Mechanismus nötig.

## Scope

### In scope

- `Transcriber`/`Speaker`-Interfaces (Python-ABCs) mit Deepgram-Implementierung (Nova-3 STT, Aura-2 TTS, Deutsch).
- Frontend: Mikrofon-Aufnahme mit Pausenerkennung, Upload, editierbares Transkript vor dem Absenden.
- Backend: Transkriptions-Endpoint (Audio rein, Text raus, Datei danach gelöscht — keine MinIO-Persistenz für Audio).
- Sprachausgabe der Agent-Antwort, automatisches Abspielen im Voice-Modus.
- Moduswechsel mitten in der Session (UI-Toggle, `message.mode` je Nachricht gesetzt).

### Not building

- Vollduplex/Unterbrechen des Agenten (Spec §5.2, explizit Phase 2 des Produkts, außerhalb dieses PRPs).
- Alternative Provider (Groq, AssemblyAI, faster-whisper, Piper) — Interface ist bereit, Implementierung folgt bei Bedarf.
- Verlaufs-Durchblättern (Phase 4) und Abschluss/Export (Phase 5).

## Compliance

**Capabilities**: gdpr/data-minimisation-accuracy-retention-lifecycle

Dieser Plan liefert die konkrete Löschung der Audiodatei unmittelbar nach erfolgreicher Transkription (Task 3) — eine echte Minimisierungs-/Aufbewahrungskontrolle, kein reines Datenmodell. `gdpr/processor-joint-controller-contracting` und `gdpr/cross-border-transfer-safeguards` bleiben offen (Deepgram als Auftragsverarbeiter, US-Anbieter): beide sind anwendbar, `chosen: null`, und werden von diesem Plan bewusst nicht adressiert — AVV/Drittlandtransfer-Dokumentation ist laut Spec §8 explizit erst beim Hosting nachzuziehen, nicht v1.

## Implementation

### 1. `Transcriber`/`Speaker`-Interfaces

**Files and integration points**
- Backend-Modul, z. B. `backend/speech/interfaces.py` (Struktur folgt Phase-1/2-Backend-Layout) — CREATE

**Implementation**
- `Transcriber.transcribe(audio_bytes: bytes, language: str) -> str` — abstrakte Basisklasse.
- `Speaker.synthesize(text: str, language: str) -> bytes` — abstrakte Basisklasse.
- Konkrete Auswahl der Implementierung über Konfiguration (Env-Var), Default `deepgram`.

**Tests**
- Keine — reine Interface-Definition, geprüft über die konkrete Implementierung (Task 2).

**Validation**
- Typprüfung/Import der Module.

### 2. Deepgram-Implementierung

**Files and integration points**
- `backend/speech/deepgram.py` — CREATE

**Implementation**
- `DeepgramTranscriber`: `POST https://api.deepgram.com/v1/listen?model=nova-3&language=de` (Rohdaten im Body), gibt den erkannten Text zurück.
- `DeepgramSpeaker`: `POST https://api.deepgram.com/v1/speak?model=aura-2-elara-de` (feste Stimme für v1, keine UI-Auswahl), gibt Audio-Bytes zurück.
- API-Key aus Config/Secret, kein Hardcoding.
- Timeout auf beiden HTTP-Aufrufen (z. B. 15s Connect/Read) — ein hängender Deepgram-Request darf die Runde nicht unbegrenzt blockieren; Timeout wird wie ein 5xx behandelt (siehe Fehlerpfad unten).

**Tests**
- Unit-Test mit gemocktem HTTP-Client: korrekte Endpoint-/Parameter-Konstruktion, Fehlerpfad (4xx **und** 5xx **und** Timeout von Deepgram) wird nicht stillschweigend geschluckt, sondern als eine der drei Klassen propagiert (Client-Fehler/Server-Fehler/Timeout — das Frontend braucht diese Unterscheidung für die Fehlermeldung in Task 5).

**Validation**
- `uv run --directory backend pytest tests/test_speech_deepgram.py` — Deepgram-Unit-Tests grün.

### 3. Transkriptions-Endpoint mit Lösch-Pflicht

**Files and integration points**
- Neue Backend-Route, z. B. `POST /transcribe` — CREATE

**Implementation**
- Nimmt Audio-Upload entgegen, hält es nur im Arbeitsspeicher/temporärer Datei, ruft `Transcriber.transcribe`, gibt den Text zurück.
- Audiodatei/-Bytes werden nach dem Aufruf explizit gelöscht/verworfen (auch im Fehlerfall, `finally`-Block) — kein Schreibpfad nach MinIO oder ins Dateisystem, der die Löschung umgehen könnte.
- Zugriffs-/Request-Logging (Uvicorn/FastAPI-Middleware) für diese Route explizit ohne Body-Logging konfigurieren — sonst umgeht ein Access-Log die Löschpflicht.
- Größenlimit auf dem Upload (z. B. 25 MB, an Groqs Free-Tier-Grenze angelehnt als Referenzwert) — Ablehnung mit `413`, bevor der Body überhaupt vollständig gelesen wird.
- Timeout/5xx von `Transcriber.transcribe` (Task 2) wird zu einem definierten Fehler-Response gemappt (`{"error": "timeout"|"provider_error"}`), nie zu einem stillen 200 mit leerem Text.

**Tests**
- Test, der nach einem erfolgreichen Aufruf verifiziert, dass keine Audiodatei im temporären Verzeichnis zurückbleibt (z. B. `tmp`-Verzeichnis vor/nach Aufruf vergleichen).
- Test für den Fehlerfall: Transkription schlägt fehl (4xx/5xx/Timeout) → Audio wird trotzdem nicht dauerhaft persistiert, Response enthält die passende Fehlerklasse.
- Test: Upload über dem Größenlimit wird mit `413` abgelehnt, ohne den vollständigen Body zu verarbeiten.

**Validation**
- `uv run --directory backend pytest tests/test_transcribe.py` — beweist AC3 (keine Audio-Persistenz) und die Fehlerklassifizierung.

### 4. Sprachausgabe der Agent-Antwort

**Files and integration points**
- Neue Backend-Route `GET /messages/{message_id}/speech` — CREATE
- `/grill`-Response-Pfad aus Phase 2 (selbe Route) — unverändert (siehe Implementation)

**Implementation**
- Kein Binär-Audio inline in der `/grill`-AG-UI-Antwort: der Adapter streamt Tool-Argumente/Text nach dem AG-UI-Protokoll (Phase-2-Plan, Recommendation), ein eingebetteter Audio-Blob dort wäre ein unverifizierter Protokollbruch. Stattdessen liefert `/grill` wie in Phase 2 nur Text zurück; wenn die Runde im Voice-Modus lief, ruft das Frontend anschließend `GET /messages/{message_id}/speech` ab, das synchron `Speaker.synthesize` auf den bereits gespeicherten `message`-Text anwendet und die Audio-Bytes zurückgibt (kein separater Persistenz-Schritt für die Ausgabe-Audio, wird bei jedem Abruf neu synthetisiert oder kurzlebig serverseitig gecacht — Cache ist eine Implementierungsfreiheit, keine Persistenzpflicht).
- Timeout/5xx von `Speaker.synthesize` → definierter Fehler-Response; das Frontend fällt in diesem Fall auf reinen Text zurück (Antwort ist bereits da, nur die Vorlesung schlägt fehl).

**Tests**
- Unit-Test: `GET /messages/{id}/speech` liefert Audio-Bytes für eine existierende Text-Nachricht; `404` für eine fremde/nicht existierende `message_id` (Ownership-Check über `require_user`/Session-Zugehörigkeit).
- Unit-Test: Speaker-Timeout/5xx → definierter Fehler-Response, kein stiller 200 mit leerem Body.

**Validation**
- `uv run --directory backend pytest tests/test_speech_endpoint.py` — grün.

### 5. Frontend: Mikrofon, Pausenerkennung, editierbares Transkript

**Files and integration points**
- Chat-Screen aus Phase 2, erweitert um Voice-UI — UPDATE

**Implementation**
- Mikrofon-Aufnahme im Browser, Sprachpausenerkennung löst Upload an `POST /transcribe` aus. Hartes Aufnahme-Limit (z. B. 5 Minuten) als Fallback, falls Hintergrundgeräusche (Auto, Joggen — der im Problem Statement genannte Nutzungskontext) die Pausenerkennung nie auslösen.
- Ergebnis erscheint im selben Eingabefeld wie der Text-Modus, editierbar, manuelles Absenden (kein Auto-Send direkt aus der Transkription — Spec §5.1: falsch erkannte Wörter dürfen nicht automatisch zu falschen Baumknoten führen).
- Aufnahme-/Sendesteuerung ist gesperrt, solange eine Runde in-flight ist (Upload läuft, `/grill` wartet auf Antwort) — verhindert clientseitig, dass eine zweite Aufnahme startet, während Transkript/Antwort der ersten noch unterwegs sind; Phase 2s Session-Lock ist die serverseitige Absicherung, falls die Sperre umgangen wird (zweiter Tab).
- Nach Upload wird die vom Browser gehaltene Audio-Object-URL explizit freigegeben (`URL.revokeObjectURL`) — kein Audio-Blob bleibt im Tab-Speicher hängen.
- Moduswechsel **während** einer laufenden Aufnahme: verwirft die laufende Aufnahme, kein Upload wird ausgelöst. Moduswechsel **während** laufender Sprachausgabe (Task 4): stoppt die Wiedergabe sofort. Moduswechsel zwischen Runden (Normalfall): wechselt nur Ein-/Ausgabemethode der nächsten Runde, Session/Baum unberührt.
- Fehleranzeige bei Transkriptions-/Sprachausgabe-Fehlern (Task 2/3/4-Fehlerklassen): sichtbarer Hinweis + Möglichkeit, die Aufnahme zu wiederholen oder auf Text umzuschalten — kein hängender Ladezustand ohne Ausweg.

**Tests**
- Kein dediziertes Frontend-Testframework in diesem Repo (Phase-1-Entscheidung) — abgedeckt durch den manuellen End-to-End-Durchlauf unten.

**Validation**
- Manuell: vollständige Session per Voice, Moduswechsel mitten in der Session (inkl. Wechsel während laufender Aufnahme und während laufender Wiedergabe), editiertes Transkript wird korrekt statt der Originalerkennung übernommen, kein Auto-Send beobachtbar.
- Manuell, mit Abbruchschwelle: 3-5 typische GrillMe-Runden mit deutschem Fachvokabular (Produktbegriffe wie "Frontier", "Decision Node", "AG-UI") einsprechen — wenn mehr als eine von drei Antworten eine Korrektur im Transkript braucht, ist das ein Befund für die Risks-Zeile unten, kein Grund, die Phase als gescheitert zu werten (Provider bleibt austauschbar).

## Acceptance

1. **AC1 — Vollständige Voice-Session:** Ein Nutzer kann eine Session komplett per Sprache führen, inklusive Sprachausgabe der Agent-Antworten.
2. **AC2 — Nahtloser Moduswechsel:** Der Wechsel zwischen Text und Voice mitten in der Session bricht den Verlauf/Baum nicht (nutzt dieselbe Phase-2-Route und denselben Prompt-Aufbau).
3. **AC3 — Keine Audio-Persistenz:** Nach jeder erfolgreichen Transkription existiert keine Kopie der Audiodatei mehr im System.
4. **AC4 — Editierbares Transkript:** Erkannte Sprache wird nie automatisch abgeschickt; der Nutzer sieht und kann den Text vor dem Senden korrigieren.

## Validation

| Gate | Command or procedure | Proves |
|---|---|---|
| Deepgram-Unit-Tests | `uv run --directory backend pytest tests/test_speech_deepgram.py` | Task 2 Korrektheit, Fehlerklassifizierung |
| Audio-Lösch-/Größenlimit-Test | `uv run --directory backend pytest tests/test_transcribe.py` | AC3 |
| Sprachausgabe-Endpoint-Test | `uv run --directory backend pytest tests/test_speech_endpoint.py` | AC1 |
| Manueller End-to-End-Durchlauf | Volle Voice-Session im Browser, Moduswechsel mittendrin (auch während Aufnahme/Wiedergabe) | AC1, AC2, AC4 |
| Manueller Qualitäts-Check | 3-5 Runden mit GrillMe-Fachvokabular, Korrekturquote beobachten | Risks-Zeile Spracherkennungsqualität |

## Risks and Decisions

| Decision or risk | Recommendation | Evidence / mitigation | Consequence if different |
|---|---|---|---|
| Deutsche Spracherkennungsqualität mit Fachvokabular ist unverifiziert | Als offene v1-Annahme akzeptieren (Spec-Entscheidung), im Rahmen der ohnehin geplanten manuellen E2E-Validierung (Task 5) mit Abbruchschwelle prüfen statt vor Implementierung zu spiken | Spec §5.4 akzeptiert diese Unsicherheit bewusst; Provider-Interface macht einen späteren Wechsel billig | Falls Nova-3 auf Deutsch/Fachvokabular schlecht abschneidet, Wechsel zu AssemblyAI o. ä. hinter demselben Interface, kein Umbau |
| Deepgram erhält als Auftragsverarbeiter tatsächlich Sprachdaten, bevor eine AVV steht — ist keine abstrakte Zukunftsfrage, sondern eine mit Task 2 getroffene Tatsache | Vor Go-Live von Task 2 mindestens Deepgrams Zero-Retention-/Standard-DPA-Option aktivieren, falls verfügbar, statt das komplett auf "beim Hosting" zu verschieben; als vom Produktverantwortlichen bewusst getroffene Entscheidung behandeln, nicht als reine Dokumentationslücke | Devil's-Advocate-Review: Single-User mindert das Risiko (Betreiber ist selbst betroffene Person), hebt es aber nicht auf; `processor-joint-controller-contracting`, `cross-border-transfer-safeguards` beide `chosen: null` | Ohne Minimalmaßnahme verlässt sich v1 vollständig auf Deepgrams Standard-Auftragsverarbeitung ohne eigene Prüfung |

## Related Plans

- **Depends on:** `grillme-phase2-decision-tree-agent.plan.md`
- **Followed by:** `grillme-phase5-export-completion.plan.md`

## Agent Notes

- PRD/Phase-1-Plan liegen physisch im Sibling-Worktree `grillme-app-grillme-v1-phase1-grundgeruest` (vom Nutzer bestätigt), nicht im Hauptcheckout — Pfade nach einem `git worktree remove` neu prüfen.
