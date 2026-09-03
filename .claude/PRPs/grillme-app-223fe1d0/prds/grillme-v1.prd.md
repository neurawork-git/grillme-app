# GrillMe v1 — Voice-first Ideen-Interview

## Problem Statement

Ideen entstehen oft unterwegs — im Auto, beim Joggen — und werden dort in zu
wenigen Worten gedacht. Wer sie sofort aufschreiben will, schreibt das
Offensichtliche auf und übersieht die Entscheidungen, die daran hängen. Ohne
erzwungene Rückfragen bleibt aus einem spontanen Einfall eine vage Notiz statt
eines nutzbaren Specs.

## Evidence

- Eigene wiederkehrende Erfahrung des Nutzers (Betreiber): Ideen werden zu knapp
  formuliert, wenn niemand nachfragt.
- Der bestehende `grilling`-CLI-Skill (vgl. `.claude/spec.md` §4.1) belegt, dass
  strukturiertes Interview-Fragen bereits als Muster funktioniert — GrillMe
  überträgt es in eine Voice-fähige App.
- Marktrecherche (2026-09-03): Voice-Notiz-Tools wie AudioPen und Speakwise
  strukturieren Gerambel zu Text, stellen aber keine Rückfragen. Ein
  akademischer Prototyp (ACM 2026, 5 Teilnehmer) zeigt, dass ein LLM-Voice-Agent
  für Requirements-Elicitation funktioniert (77,5 % Coverage), ist aber kein
  Produkt. Es existiert kein gefundenes Produkt, das Voice-Interview,
  Artefakt-Erzeugung und Hands-free-Nutzung unterwegs kombiniert — Annahme, dass
  diese Lücke real ist, gestützt auf die Abwesenheit eines Treffers in der
  Recherche, nicht auf vollständige Marktabdeckung.

## Proposed Solution

Eine Web-App (Next.js/CopilotKit-Frontend, FastAPI/AG-UI-Backend, Claude Agent
SDK), die eine Idee per Text oder Sprache entgegennimmt und sie über einen in
Postgres persistierten Entscheidungsbaum durchgrillt: Frage, Empfehlung,
Antwort, nächste Runde. Sprachein- und -ausgabe laufen v1 turn-based
(Sprachpausenerkennung → Transkription → Agent → Sprachausgabe, ~2–4 Sekunden
pro Zug). Jede Session zeigt ihren Frage-Antwort-Verlauf durchblätterbar an.
Nach explizitem Abschluss durch den Nutzer entsteht das Artefakt (Markdown-Spec
oder Tickets, je gewähltem Format).

Diese Lösung statt eines reinen Voice-Memo-Tools, weil das erzwungene
Nachfragen der eigentliche Kern des Werts ist (siehe Evidence); statt eines
text-only Web-Interviews, weil Voice-Input der explizit genannte
Haupt-Erfolgsfaktor ist ("am besten mit Voice", unterwegs nutzbar).

## Key Hypothesis

Wir glauben, ein Voice-first-Interview mit sichtbarem, durchblätterbarem
Frage-Antwort-Verlauf wird unterwegs entstandene, dünn ausformulierte Ideen zu
vollständigen Specs verdichten für den Solo-Nutzer/Betreiber.
Wir wissen, dass wir richtig liegen, wenn er regelmäßig (z. B. wöchentlich)
Sessions per Voice abschließt und die erzeugten Artefakte direkt
weiterverwendbar sind, ohne Nacharbeit von Hand.

## What We're NOT Building

- Hands-free-Bestätigung/-Steuerung ohne Bildschirmblick (z. B. am Steuer) —
  v1-Voice ist turn-based mit Moduswechsel und Abschluss-Bestätigung per Klick,
  das setzt Blickkontakt voraus. Für echtes Freihändig-Fahren wäre das ein
  eigenes, ungetestetes UX-Muster (Recherche: Read-back + verbales Bestätigen
  wie bei Android Auto/CarPlay); dediziert Phase 2.
- Vollduplex-Sprachdialog mit Unterbrechen des Agenten — Anthropic bietet keine
  Realtime-Sprach-API, Transkription/Sprachausgabe müssten getrennt gestreamt
  werden; Aufwand erst gerechtfertigt nach echten v1-Sessions.
- Mehrbenutzerbetrieb/Hosting — hart an API-Key-Credential statt
  Subscription-Token gekoppelt (Datenschutz-AVV-Grund, s. Spec §3.3); v1 hat
  genau einen Nutzer.
- Ticket-Erzeugung direkt in GitHub Issues — v1 exportiert Markdown-Dateien.
- Verwaltungsoberfläche für die Prompt-Bibliothek — v1 nutzt Seed-Daten.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|---------------|
| Abgeschlossene Sessions/Woche | ≥ 1 | Zähler in `session`-Tabelle (Status = abgeschlossen) |
| Anteil Sessions per Voice gestartet oder mit Voice-Anteil | ≥ 50 % | `message.mode` in der Verlaufstabelle |
| Artefakt ohne manuelle Nacharbeit direkt weiterverwendbar (subjektiv) | Ja, in ≥ 4 von 5 Sessions | Selbstauskunft Nutzer nach Export |

## Open Questions

- [ ] Visualisierung des Verlaufs — Baumdarstellung vs. lineare
      Frage-Antwort-Liste? (UI-Detail, gehört in die Implementierungsplanung,
      nicht in dieses PRD.)
- [ ] Hands-free-Bestätigungsmuster für eine spätere Phase ist ungetestet —
      Read-back + verbales "Bestätigen" ist der recherchierte Kandidat, aber
      ohne eigene Nutzerdaten.
- [ ] Deepgram als Standard-Provider (Nova-3/Aura-2) ist im Spec gesetzt; noch
      nicht an echten deutschen Aufnahmen mit Fachvokabular gegen Alternativen
      getestet.

---

## Users & Context

**Primary User**
- **Who**: Der Betreiber selbst — Solo-Dev/PM, einziger Nutzer der Instanz.
- **Current behavior**: Ideen unterwegs (Auto, Joggen) entstehen, werden aber
  zu knapp gedacht/notiert, weil niemand nachfragt.
- **Trigger**: Ein spontaner Einfall während einer Aktivität ohne freie Hände
  für Tippen.
- **Success state**: Eine per Voice geführte, abgeschlossene Session liefert
  einen Spec/PRD, den der Nutzer direkt weiterverwenden kann.

**Job to Be Done**
Wenn mir unterwegs eine Idee kommt, will ich sie sofort einsprechen und
durchgrillen lassen, damit ich zu Hause einen fertigen Spec/PRD statt einer
vagen Notiz vorfinde.

**Non-Users**
Teams/mehrere Personen — v1 ist hart auf Einzelnutzer und ein
OAuth-Token-Credential gekoppelt (Spec §3.3), ein geteilter Zugriff würde den
bereits einmal gelösten Compliance-Fall (API-Key-Pflicht bei mehreren
Betroffenen) wieder aufreißen. Nutzer, die ausschließlich am Schreibtisch
tippen wollen, sind kein Treiber für diese App — dafür reicht der bestehende
`grilling`-CLI-Skill.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Voice-Input: Sprache diktieren, turn-based ans Backend | Kern-Werttreiber laut Nutzer — "am besten mit Voice" |
| Must | Voice-Output: Agent antwortet per Sprachausgabe | Vollständiger Sprachdialog, nicht nur Diktat |
| Must | Text-Modus mit editierbarem Transkript, jederzeit umschaltbar | Fehlerkorrektur; falsch erkannte Wörter erzeugen sonst falsche Baumknoten (Spec §5.1) |
| Must | Entscheidungsbaum in Postgres, Frontier-Berechnung pro Runde | Ohne persistenten Baum verliert der Agent bei langen Sessions den Überblick |
| Must | Session-Verlauf durchblätterbar (Frage/Empfehlung/Antwort je Session) | Explizit vom Nutzer gefordert |
| Must | Login (E-Mail/Passwort), Session-Liste | Ohne Konto keine Session-Historie |
| Must | Explizite Abschluss-Bestätigung durch Nutzer, Artefakt-Export | Ein Sprachmodell hört sonst zu früh auf (Spec §4.3) |
| Should | Screenshots als Teil des Verlaufs, dauerhaft mitgeschickt | Oft Kern einer Anforderung, aber nicht Voice-kritisch |
| Should | Gamification-Anzeige im Header | Motivation für regelmäßige Nutzung, kein Blocker für Kern-Hypothese |
| Could | Mehrere Ausgabeformate (User Stories, Tickets, PRD) über die Startset-Vorlagen hinaus | Nice-to-have, Startset genügt für v1-Validierung |
| Won't | Hands-free-Bestätigung ohne Bildschirmblick | Ungetestetes UX-Muster, eigene Phase |
| Won't | Vollduplex-Sprachdialog mit Unterbrechen | Kein Realtime-API bei Anthropic, hoher Aufwand |
| Won't | Mehrbenutzerbetrieb/Hosting | An API-Key-Wechsel gekoppelt, Phase 2 |

### MVP Scope

Login → Session anlegen (Format wählen) → Interview per Voice oder Text
(jederzeit umschaltbar) → Verlauf einsehbar → explizite Abschluss-Bestätigung →
Markdown-Artefakt-Export. Betrieb via `docker compose up`, ein Nutzer, ein
OAuth-Token-Credential.

### User Flow

Login → Session-Liste → neue Session (Format wählen, z. B. "Spec (Markdown)")
→ Chat-Screen: Sprache einsprechen oder tippen, Agent fragt zurück (Text +
Sprachausgabe), Verlauf scrollt mit → Frontier leer → Agent meldet Abschluss →
Nutzer bestätigt per Klick → Export-Screen mit generiertem Artefakt.

---

## Technical Approach

**Feasibility**: HIGH — Architektur ist bereits im Detail spezifiziert
(`.claude/spec.md` §3), inklusive Provider-Interfaces für Transkription/
Sprachausgabe. Kein bestehender Code, aber auch keine offene Architekturfrage
für den v1-Scope.

**Architecture Notes**
- Next.js + CopilotKit (Frontend) ↔ FastAPI + `ag-ui-claude-agent-sdk`
  (Backend) ↔ Claude Agent SDK, Transport per AG-UI/SSE.
- Agent-State lebt ausschließlich in Postgres; jede Interview-Runde startet
  eine frische SDK-Session mit Baum+Verlauf als Prompt (Spec §3.1) — kein
  `resume=<session_id>`.
- `Transcriber`/`Speaker`-Interfaces mit Deepgram (Nova-3/Aura-2) als
  Standard-Implementierung, austauschbar gegen Groq/AssemblyAI/faster-whisper/
  Piper.
- Audio wird nach erfolgreicher Transkription gelöscht (Spec §5.4).

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `ag-ui-claude-agent-sdk` ist ein frühes Paket (Version auf 0.1.0 gepinnt) | M | Adapter ist klein genug, im Notfall zu vendoren (Spec §3.2) |
| Deepgram trifft deutsches Fachvokabular nicht gut genug | M | Provider-Interface erlaubt Wechsel ohne Umbau; an echten Aufnahmen prüfen |
| Turn-based Voice (2–4 s/Zug) fühlt sich unterwegs zu langsam an | L | v1-Annahme laut Spec, echte Sessions zeigen ob spürbar |
| Compliance-Fall (geteilter Zugriff) wird versehentlich wieder geöffnet | L | Harte Kopplung API-Key/Multi-User bereits im Schema verankert (Spec §3.3) |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: phases that can run concurrently (e.g., "with 3" or "-")
  DEPENDS: phases that must complete first (e.g., "1, 2" or "-")
  PLAN: link to generated plan file once created
  REPORT: link to the implementation report once implemented
  PR: link to the pull request once opened
-->

| # | Phase | Description | Status | Parallel | Depends | Plan | Report | PR |
|---|-------|-------------|--------|----------|---------|------|--------|----|
| 1 | Grundgerüst | Docker-Compose-Stack, Postgres-Schema, Login/Session-CRUD, MinIO-Anbindung | in-progress | - | - | /home/felix/projects/grillme-app/.claude/PRPs/grillme-app-223fe1d0/plans/grillme-v1-phase1-grundgeruest.plan.md | /home/felix/projects/grillme-app/.claude/PRPs/grillme-app-223fe1d0/reports/grillme-v1-phase1-grundgeruest-report.md | https://github.com/neurawork-git/grillme-app/pull/1 |
| 2 | Entscheidungsbaum-Agent | AG-UI/Claude-Agent-SDK-Integration, Baum-Persistenz, Frontier-Berechnung, Text-Chat | pending | - | 1 | - | - | - |
| 3 | Voice-Input/Output | Transcriber/Speaker-Interfaces, Deepgram-Implementierung, Moduswechsel Text/Voice | pending | with 4 | 2 | - | - | - |
| 4 | Verlauf & Screenshots | Durchblätterbarer Frage-Antwort-Verlauf je Session, Bild-Upload in MinIO | pending | with 3 | 2 | - | - | - |
| 5 | Abschluss & Export | Explizite Bestätigung, Artefakt-Generierung (Markdown/Tickets), Export-Screen, Gamification-Anzeige | pending | - | 3, 4 | - | - | - |

### Phase Details

**Phase 1: Grundgerüst**
- **Goal**: Lauffähiger Compose-Stack mit Login und leerer Session-Liste.
- **Scope**: Postgres-Schema (Spec §9), Argon2-Auth, Session-Cookie,
  CLI-Nutzeranlage, MinIO-Service.
- **Success signal**: `docker compose up` startet, Login funktioniert, Session
  anlegen/auflisten funktioniert ohne Agent-Anbindung.

**Phase 2: Entscheidungsbaum-Agent**
- **Goal**: Text-basiertes Interview mit persistiertem Baum funktioniert
  end-to-end.
- **Scope**: `ag-ui-claude-agent-sdk`-Integration, `decision_node`-Tabelle,
  Frontier-Berechnung pro Runde, frische SDK-Session je Runde.
- **Success signal**: Eine Text-Session lässt sich vollständig durchführen und
  überlebt einen Backend-Neustart mitten in der Session.

**Phase 3: Voice-Input/Output**
- **Goal**: Voice-Modus als vollwertige Alternative zu Text, jederzeit
  umschaltbar.
- **Scope**: `Transcriber`/`Speaker`-Interfaces, Deepgram-Implementierung,
  editierbares Transkript, Audio-Löschung nach Transkription.
- **Success signal**: Eine Session lässt sich komplett per Voice führen,
  Moduswechsel mitten in der Session funktioniert ohne Verlauf-Bruch.

**Phase 4: Verlauf & Screenshots**
- **Goal**: Jede Session zeigt ihren vollständigen Frage-Antwort-Verlauf
  durchblätterbar.
- **Scope**: Verlaufs-UI (Frage, Empfehlung, Antwort, Status je Knoten),
  Screenshot-Upload und -Anzeige im Verlauf.
- **Success signal**: Nutzer kann zu jeder abgeschlossenen oder laufenden
  Session den kompletten Fragenkatalog mit Antworten durchblättern.

**Phase 5: Abschluss & Export**
- **Goal**: Session-Abschluss ist ein bewusster Schritt, Artefakt entsteht
  zuverlässig.
- **Scope**: Abschluss-Bestätigung (Klick), Artefakt-Generierung je
  Prompt-Template-Format, Export-Screen, Gamification-Zähler im Header.
- **Success signal**: Bestätigte Session erzeugt ein herunterladbares
  Markdown-Artefakt; unbestätigte Sessions bleiben offen und wiederaufnehmbar.

### Parallelism Notes

Phasen 3 (Voice) und 4 (Verlauf/Screenshots) berühren unterschiedliche
Domänen — Sprach-Pipeline vs. Verlaufs-UI — und können nach Abschluss von
Phase 2 parallel in getrennten Worktrees laufen.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Voice-Modus v1 | Turn-based | Vollduplex | Keine Realtime-Sprach-API bei Anthropic; turn-based genügt für v1-Validierung (Spec §5.2) |
| Hands-free-Bestätigung | Nicht in v1 | Read-back+Verbal-Confirm sofort mitbauen | Ungetestetes Muster, kein Treffer für ein Produkt mit dieser Kombination in der Recherche; Risiko lieber nach echten Sessions angehen |
| Speech-Provider-Standard | Deepgram (Nova-3/Aura-2) | Groq, AssemblyAI, faster-whisper, Piper | Ein Anbieter/ein Schlüssel, Deutsch-Unterstützung, günstig; hinter Interface austauschbar (Spec §5.4) |
| Tenancy | Einzelnutzer, OAuth-Token | Multi-User mit geteiltem API-Key | Kein AVV auf Subscription-Tarif; Mehrbenutzerbetrieb reißt gelösten Compliance-Fall wieder auf (s. Recherche) |

---

## Research Summary

**Market Context**
Keine gefundene Konkurrenz kombiniert Voice-Decision-Tree-Interview,
Artefakt-Erzeugung und Hands-free-Nutzung unterwegs. Nächste Nachbarn:
Voice-Note-zu-Text-Tools (AudioPen, Speakwise — nur Einweg-Capture, keine
Rückfrage) und ein akademischer Voice-Elicitation-Prototyp (ACM 2026,
Prototyp-Stadium). Vollduplex-Infrastruktur (OpenAI Realtime, Deepgram Flux)
ist 2025/26 produktionsreif, liefert aber keine native
"explizite Bestätigung vor Abschluss" — das wäre Eigenbau. Branchenmuster für
Hands-free-Bestätigung: Read-back + verbales Ja (Android Auto/CarPlay);
autonomes LLM-Judgment-Session-Ende (ElevenLabs `end_call`) gilt als
Anti-Pattern für GrillMes Anforderung an expliziten Nutzer-Abschluss.

**Technical Context**
Repo enthält aktuell keinen Anwendungscode — `.claude/spec.md` ist die einzige
Anforderungsquelle. Architektur ist vollständig spezifiziert (Spec §3):
Next.js/CopilotKit, FastAPI/AG-UI, Claude Agent SDK, Postgres als einzige
State-Quelle, MinIO für Bilder, Transcriber/Speaker-Interfaces. Der
Compliance-Compiler hat 24 anwendbare GDPR-Capabilities für dieses Produkt
gescoped (u. a. Consent-Capture, Datenminimierung, Sonderkategorie-Daten,
Drittlandtransfer — alle mit Bezug zu Voice/Screenshot-Daten), noch keine
Komponente dafür gewählt. Kein Artefakt im Repo erwähnt Hands-free/
Fahren/Joggen — das ist neuer Scope gegenüber der bestehenden Spec.

---

*Generated: 2026-09-03*
*Status: DRAFT - needs validation*
