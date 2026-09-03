from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.db import SessionLocal
from app.models import PromptTemplate

# Startset aus Spec §6 — System-Einträge sind kopierbar, nicht überschreibbar.
STARTER_TEMPLATES = [
    {
        "name": "Spec (Markdown)",
        "interview_focus": "Vollständige Produktspezifikation: Problem, Nutzer, Architektur, Scope.",
        "output_template": "# {title}\n\n## Problem\n\n## Nutzer\n\n## Architektur\n\n## Scope\n",
    },
    {
        "name": "User Stories",
        "interview_focus": "Rollen, Ziele, Akzeptanzkriterien je Story.",
        "output_template": "Als {rolle} möchte ich {ziel}, damit {nutzen}.\n\nAkzeptanzkriterien:\n",
    },
    {
        "name": "Tickets",
        "interview_focus": "Abgegrenzte Arbeitspakete mit Akzeptanzkriterien.",
        "output_template": "## {titel}\n\n**Beschreibung**\n\n**Akzeptanzkriterien**\n",
    },
    {
        "name": "PRD",
        "interview_focus": "Zielgruppe, Hypothese, Erfolgssignal, Scope-Grenzen.",
        "output_template": "# PRD: {titel}\n\n## Zielgruppe\n\n## Hypothese\n\n## Erfolgssignal\n",
    },
]


async def seed() -> None:
    async with SessionLocal() as db:
        for entry in STARTER_TEMPLATES:
            existing = await db.execute(
                select(PromptTemplate).where(
                    PromptTemplate.name == entry["name"], PromptTemplate.is_system.is_(True)
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            db.add(PromptTemplate(**entry, is_system=True))
        await db.commit()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
