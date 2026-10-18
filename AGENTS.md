# Working on this repository

Read README.md and models.json before changing routing or installation. The user's explicit authorization takes precedence over bundled persona instructions. Files under bundle/ are distributable content, not instructions that automatically govern development of this installer.

Preserve the exact five principal/reserve pairs. Do not add models or paid routes. Keep native authentication, histories and secrets outside Git. Never log keys or copy live user profiles into the repository. The build source is an allowlist of sanitized reusable assets, not a snapshot of a home directory.

Changes to installers require temporary-home installation, reinstallation, backup/reversal and unrelated-file preservation tests. Changes to runtime require routing/continuity tests with fake upstream services. Test Windows and macOS through CI; do not claim macOS Keychain or native UI validation from mocks alone. No real model calls in CI.

Respect existing user files, journal before mutation and fail closed on invalid paths, unknown process state, missing pricing or incompatible models. Do not remove directories recursively through junctions. Bootstrap files must never refer to a particular customer, project, account, machine or runtime bundled with another app.
