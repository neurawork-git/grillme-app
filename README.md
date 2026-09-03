# grillme-app

GrillMe — ein Interview-Agent, der eine Idee zu einem Requirements-Dokument
grillt. Die volle Spezifikation steht in `.claude/spec.md`.

## Quickstart (Phase 1: Grundgerüst)

```bash
cp .env.example .env
docker compose up
```

Bringt vier Dienste hoch: `postgres`, `minio`, `backend` (FastAPI, Port 8000),
`frontend` (Next.js, Port 3000). Beim ersten Start führt das Backend die
Alembic-Migration aus und seedet die Prompt-Bibliothek mit dem Startset aus
Spec §6 (`Spec (Markdown)`, `User Stories`, `Tickets`, `PRD`).

### Nutzer anlegen

Kein öffentlicher Signup — Nutzer werden per CLI angelegt:

```bash
docker compose exec backend python -m app.cli create-user <email>
```

Fragt interaktiv nach Passwort und Bestätigung.

### Ablauf prüfen

1. Im Browser `http://localhost:3000/login` öffnen und mit dem angelegten
   Nutzer anmelden.
2. Die (anfangs leere) Session-Liste unter `/sessions` erscheint.
3. Ein Format wählen und eine neue Session anlegen — sie erscheint in der
   Liste.
4. `docker compose restart backend` — die Session ist danach weiterhin da
   (Postgres ist die einzige Quelle der Wahrheit, spec §3.1).

Noch keine Claude-Agent-Anbindung, kein Entscheidungsbaum, kein Chat — das ist
Phase 2. Die `.env`-Platzhalter `CLAUDE_CODE_OAUTH_TOKEN`/`ANTHROPIC_API_KEY`
sind für Phase 2 schon vorgesehen (spec §3.3), in Phase 1 ungenutzt.
