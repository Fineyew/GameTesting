# Follow-Up Architecture Audit After Mandatory Debt Refactors

Audit date: 2026-06-15  
Branch audited: `cursor/brutal-architecture-review-92ee`  
Scope: mandatory corrective refactors for placeholder secrets, HTTPS/TLS deployment, content catalog lifecycle, database provider lifecycle, module-boundary tests, Godot autoload coupling, and JWT claim hardening.

## Refactors completed

1. **Placeholder secret prevention**
   - `Settings` now uses a stdlib environment loader with explicit runtime validation.
   - Staging/production reject known placeholder secret text, short JWT secrets, scaffold DB usernames, placeholder DB passwords, and debug mode.
   - `.env.example` now leaves secret values blank instead of providing usable placeholders.

2. **HTTPS/TLS deployment**
   - Nginx now redirects HTTP to HTTPS.
   - Nginx listens on 443 with TLS certificate/key mounts.
   - Security headers and HSTS are configured.
   - Docker Compose exposes 443 and mounts `infra/certs` read-only.
   - README documents required certificate paths.

3. **Process-global content catalog removal**
   - Content catalog is now an immutable snapshot built during FastAPI lifespan startup.
   - Content validation happens before the app serves requests.
   - Content routes receive the catalog through request/app dependency state instead of `@lru_cache`.

4. **Import-time database singleton removal**
   - `backend/app/db/session.py` no longer creates settings, engine, or sessionmaker at import time.
   - A `DatabaseProvider` is created during FastAPI lifespan startup and disposed on shutdown.
   - Session dependency reads the provider from `app.state`.

5. **Stronger module-boundary tests**
   - Tests still block direct gameplay-module imports of other module internals.
   - Tests now block gameplay modules from importing global DB/session/model infrastructure.
   - Tests validate registry dependency names against known boundaries.

6. **Godot service locator prevention**
   - `ContentCache` is no longer a Godot autoload.
   - Content access is now represented by `ContentRepository`, which receives an API client dependency explicitly.
   - Module README now instructs modules to receive dependencies instead of directly calling autoload globals.
   - `ApiClient` no longer defaults to plaintext localhost and rejects non-HTTPS base URLs outside editor-local testing.

7. **JWT claim hardening**
   - Reserved JWT claims cannot be overridden by `extra_claims`.
   - Token creation no longer imports an unavailable external JWT package.
   - Tests cover reserved-claim rejection and production config validation.

## Verification performed

- `python3 -m unittest discover backend/tests`
  - Result: 11 tests passed.
- `python3 -m compileall backend/app backend/alembic`
  - Result: passed.
- `git diff --check`
  - Result: passed.
- Static Python import-cycle scan
  - Result: 0 cycles found.
- Static pattern scan
  - Confirmed no cached content-catalog dependency, no `ContentCache` autoload, no `python-jose` import, no `pydantic-settings`, no import-time `AsyncSessionLocal`, and no plaintext `http://127.0.0.1/api/v1` client default.

## Remaining risks ranked by severity

## High

### H-1. TLS deployment is configured but not operationally automated

**Problem**

The Nginx production config now requires `infra/certs/fullchain.pem` and `infra/certs/privkey.pem`, but certificate issuance and renewal are not automated.

**Why it matters**

If certificates expire or are not provisioned before deployment, Nginx will fail to start. Manual certificate operations are easy to forget on a solo-maintained VPS.

**Long-term impact**

High. A production server can go offline on certificate expiry, or a developer may bypass TLS to recover quickly.

**Corrective refactor**

- Add a documented certificate runbook.
- Add a certbot/acme companion profile or scripted host-level renewal.
- Add a deployment preflight that checks certificate presence and expiry.

### H-2. Readiness still does not verify DB migrations or content snapshot

**Problem**

Content is built at lifespan startup, but `/health` remains a static liveness endpoint. There is still no `/ready` endpoint that verifies database connectivity, current Alembic revision, and loaded content snapshot state.

**Why it matters**

Docker health checks can still pass when the schema is missing or database access is broken after startup.

**Long-term impact**

High once public testing begins. Deploys can accept traffic before persistence is truly usable.

**Corrective refactor**

- Add `/ready`.
- Check database connectivity and migration revision.
- Check that `app.state.content_catalog` exists and has a manifest.
- Point container/Nginx readiness checks at `/ready`, while keeping `/health` as liveness.

### H-3. Shared ORM model file still undermines module ownership

**Problem**

Global import-time DB singleton state was removed, but `backend/app/db/models.py` still contains models for all domains.

**Why it matters**

Future gameplay modules can still be tempted to import shared models or depend on unowned table shapes.

**Long-term impact**

High. This remains the largest path toward hidden monolith behavior once real repositories are added.

**Corrective refactor**

- Move models into module-owned packages before adding real gameplay persistence.
- Keep Alembic metadata composition centralized.
- Extend registry descriptors with owned table names and enforce ownership in tests.

### H-4. Content rules remain weakly typed

**Problem**

The content catalog lifecycle is safer, but content `rules` are still generic dictionaries with partial graph validation.

**Why it matters**

Invalid economy, combat, quest, shop, or crafting semantics can still pass validation if references and handler names are correct.

**Long-term impact**

High. Bad content can produce runtime bugs or reward/economy exploits.

**Corrective refactor**

- Add discriminated Pydantic schemas for effects, conditions, objectives, prices, rewards, targeting, and each content category.
- Add negative validation tests for malformed content.

## Medium

### M-1. API client still collapses failure types to empty dictionaries

**Problem**

`ApiClient` now rejects insecure/missing base URLs, but transport errors, HTTP errors, and non-dictionary JSON still collapse to `{}`.

**Why it matters**

Mobile UI and future module clients cannot distinguish expired auth, missing content, server errors, and offline transport failures.

**Long-term impact**

Medium now, high before gameplay UI ships.

**Corrective refactor**

- Introduce a typed Godot `ApiResult` object or dictionary convention containing success, status, body, error, and retryability.
- Make mutating gameplay calls require idempotency keys.

### M-2. Godot still has one global `ApiClient` autoload

**Problem**

The content repository no longer directly uses the global service locator, but `ApiClient` remains an autoload.

**Why it matters**

This can be acceptable as a bootstrap/session object, but future modules must not call it directly from UI or gameplay code.

**Long-term impact**

Medium. Without discipline, raw endpoint strings can still spread through GDScript.

**Corrective refactor**

- Add a composition/root script that creates module clients with explicit dependencies.
- Add lint or review rules forbidding direct `ApiClient` calls outside composition and low-level network modules.

### M-3. Nginx rate limits are still coarse

**Problem**

The deployment has a single `/api/` rate-limit zone.

**Why it matters**

Auth, chat, content downloads, and gameplay mutation endpoints need different limits.

**Long-term impact**

Medium. The single limit may either throttle legitimate users or under-protect abuse-prone endpoints.

**Corrective refactor**

- Add endpoint-specific zones for auth, chat, content, and general mutating APIs.
- Add account/device-level rate limiting in the backend before public auth/chat.

### M-4. Backup still lacks restore, retention, encryption, and off-host sync

**Problem**

The backup script exists, but operational recovery remains incomplete.

**Why it matters**

Backups that are not restorable, retained, encrypted, and copied off the VPS do not fully protect player data.

**Long-term impact**

Medium until production, high once player data exists.

**Corrective refactor**

- Add restore script/runbook.
- Add retention pruning.
- Add encrypted archive option.
- Add off-host sync option.
- Test restore periodically.

### M-5. Migration/deployment is still manual

**Problem**

Alembic exists, but Compose does not run migrations as a gated deployment step.

**Why it matters**

Manual migrations can be skipped or run out of order.

**Long-term impact**

Medium. Deployment failures will become more likely as schema changes grow.

**Corrective refactor**

- Add a one-shot migration service or backend entrypoint gate.
- Record expected migration revision in readiness.

## Low

### L-1. Content validator remains a future file-size hotspot

**Problem**

`backend/app/modules/content/validation.py` remains the largest Python file at 244 lines.

**Why it matters**

It is not excessive yet, but it combines constants, graph walking, and semantic validation.

**Long-term impact**

Low now, medium as content types grow.

**Corrective refactor**

- Split into constants, loader, graph reference validation, and per-category validators.

### L-2. Previous audit report now contains resolved findings

**Problem**

`docs/audits/full_code_audit_technical_debt_report.md` intentionally records the earlier state and now includes findings that are partially or fully resolved.

**Why it matters**

Future readers may mistake historical findings for current status.

**Long-term impact**

Low.

**Corrective refactor**

- Keep this follow-up audit linked from the PR.
- Later add an audit index that marks findings as open/resolved/superseded.

## Final audit conclusion

The seven mandatory debt areas were addressed. The project is safer to continue, but it is not ready for gameplay expansion until the remaining high-severity items are handled: readiness checks, module-owned ORM models, typed content schemas, and operational TLS automation.
