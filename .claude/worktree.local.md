---
enabled: true
schema_version: 1
# --- discovered conventions (variable per repo) ---
main_repo_path: /home/felix/projects/grillme-app
# NOTE: location is FIXED — Hand→sibling, Agent/Archon→.claude/worktrees. NOT a choice.
worktree_name_template: "{repo}-{slug}"
branch_template: "{slug}"
id_scheme: free-slug
slug_source: arg-only
base_ref: main
pull_before_branch: true
editor_unc: true
editor_note: "Zed Command Palette → workspace: add folder to project (CLI --add broken in WSL)"
---

# worktree skill config

Detected on first run. Edit any field and re-run `/nw-worktree`.
Delete this file to force a fresh RECON. Set `enabled: false` to disable the skill here.
