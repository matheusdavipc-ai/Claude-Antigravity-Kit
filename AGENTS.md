# Working on this repository

Read README.md before changing installation. The user's explicit authorization takes precedence over bundled persona instructions. Files under bundle/ are distributable content, not instructions that automatically govern development of this installer.

The kit configures only the native Claude Code profile in ~/.claude and the shared Antigravity bundle. The router profile, the clauderouter command, the supervised launcher and OmniRoute were removed on 2026-11-06 by owner decision; do not add them back, add model gateways or paid routes. Keep native authentication, histories and secrets outside Git. Never log keys or copy live user profiles into the repository. The build source is an allowlist of sanitized reusable assets, not a snapshot of a home directory.

Changes to installers require temporary-home installation, reinstallation, backup/reversal and unrelated-file preservation tests. Changes to scripts/remove_router.py require temporary-home tests for listing, quarantine, refusal and restoration. Test Windows and macOS through CI; do not claim macOS validation from mocks alone. No real model calls in CI.

Respect existing user files, journal before mutation and fail closed on invalid paths or unknown process state. Do not remove directories recursively through junctions. Bootstrap files must never refer to a particular customer, project, account, machine or runtime bundled with another app.
