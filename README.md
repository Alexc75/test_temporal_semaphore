# Laugh Loop

A tiny Python application that runs a Temporal Workflow to fetch two jokes in
parallel from free, unauthenticated APIs:

- [JokeAPI](https://v2.jokeapi.dev/) (safe mode enabled)
- [icanhazdadjoke](https://icanhazdadjoke.com/api) (JSON response)

The Workflow only orchestrates work. Each HTTP request runs in an Activity,
with an explicit timeout and bounded retry policy. The Activities use async
HTTP with `httpx`, and validate the external responses before returning typed
data.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- [Temporal CLI](https://docs.temporal.io/cli)

## Run locally

In three terminals, from this directory:

1. Start Temporal's local development server:

   ```bash
   temporal server start-dev
   ```

2. Install the app and start the Worker:

   ```bash
   uv sync
   uv run python -m laugh_loop.worker
   ```

3. Start a Workflow and print its results:

   ```bash
   uv run python -m laugh_loop.cli
   ```

The app connects to `localhost:7233`, uses the `default` namespace, and polls
the `laugh-loop` task queue by default. Override these with
`TEMPORAL_ADDRESS`, `TEMPORAL_NAMESPACE`, and `TEMPORAL_TASK_QUEUE`.

## Tests

```bash
uv run python -m unittest discover -s tests -v
```

## Lint

[Ruff](https://docs.astral.sh/ruff/) checks and formats the code:

```bash
uv run ruff check .
uv run ruff format --check .
```

Run `uv run ruff check --fix .` and `uv run ruff format .` to apply fixes.

## CI/CD with Semaphore

The Semaphore pipeline runs the linter and the test suite for every push.
After both pass on `main`,
[python-semantic-release](https://python-semantic-release.readthedocs.io/)
picks the next version from the
[Conventional Commits](https://www.conventionalcommits.org/) messages since the
last release:

| Commit message                                      | Version bump      |
| --------------------------------------------------- | ----------------- |
| `fix: ...`, `perf: ...`                             | `0.1.0` → `0.1.1` |
| `feat: ...`                                         | `0.1.0` → `0.2.0` |
| `feat!: ...` or a `BREAKING CHANGE:` footer         | `0.1.0` → `1.0.0` |
| `chore:`, `docs:`, `test:`, `ci:`, `refactor:`, ... | no release        |

When a bump is due, the release job updates `version` in `pyproject.toml` and
`uv.lock`, updates `CHANGELOG.md`, commits them as
`chore(release): <version> [skip ci]`, tags the commit `v<version>`, pushes to
`main`, and publishes a GitHub Release with the wheel and source distribution.

Preview the next version locally (on `main`) without changing anything:

```bash
uv run semantic-release --noop version --print
```

To enable releases:

1. Connect this GitHub repository to Semaphore and use
   `.semaphore/semaphore.yml` as the pipeline configuration.
2. Create a GitHub token for the release job. In GitHub, open
   **Settings → Developer settings → Personal access tokens → Fine-grained
   tokens → Generate new token**, then:
   - Set **Repository access** to **Only select repositories** and pick this
     repository.
   - Under **Repository permissions**, set **Contents** to **Read and write**.
     This lets the job push the release commit and tag, create releases, and
     upload the `dist/*` files.
3. Add a Semaphore secret named `github-release` with a `GH_TOKEN`
   environment variable set to that token.
   - In the UI: **Organization → Settings → Secrets → New Secret**. You can
     also create it as a project secret under **Project → Settings →
     Secrets**.
   - With the `sem` CLI:

     ```bash
     sem create secret github-release -e GH_TOKEN=<token>
     ```

The release secret is only made available to the publish job, and that job
runs only for `main`. A lint or test failure prevents publishing. If `main` is
a protected branch, allow the token's owner to push to it, or the release
commit will be rejected.

## Practices reflected here

- Keep Workflow code deterministic and put network I/O in Activities.
- Set Activity timeouts and bounded retries for work that can fail transiently.
- Keep external requests bounded, validate their responses, and surface errors.
- Reuse an async HTTP client across Activities, and use environment variables
  for Temporal connection settings.
- Follow logs from the Worker and CLI to monitor Temporal connection, workflow
  execution, and external joke requests.

See Temporal's [Python Workflow basics](https://docs.temporal.io/develop/python/workflows/basics),
[Activity execution](https://docs.temporal.io/develop/python/activities/execution),
and [sync vs. async Activity guidance](https://docs.temporal.io/develop/python/best-practices/python-sdk-sync-vs-async).
