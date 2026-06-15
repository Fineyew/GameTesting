# Full Code Audit Technical Debt Report

Audit date: 2026-06-15  
Branch audited: `cursor/brutal-architecture-review-92ee`  
Scope: Python backend, Alembic migration, content loader/validator, API endpoints, ORM models, tests, Godot scripts, Docker Compose, Nginx, and backup script.

This audit focuses on architecture quality and maintainability. It does not propose new gameplay features.

## Executive summary

The repository is still early enough to correct course. There are no active Python import cycles and no implemented gameplay systems directly querying the database yet. The highest-risk debt is structural: shared global ORM models, weak module-boundary enforcement, a process-global content catalog, broad untyped content rules, incomplete production security gates, and deployment readiness gaps.

If these issues are left in place while gameplay systems are added, the project will become a hidden monolith with fragile content, unsafe deployment paths, and expensive future refactors.

## Quick status

| Area | Current status |
| --- | --- |
| Python circular dependencies | None found by static import scan |
| GDScript circular dependencies | None found in current two-script scaffold |
| Direct DB access from gameplay modules | None implemented yet |
| Module-boundary enforcement | Present but incomplete |
| Content validation | Useful start, still too generic |
| Production deployment hardening | Partial, not production-ready |
| Authentication/security | Token creation only; auth system not implemented |
| Excessive file sizes | No extreme files yet; validator and shared ORM are early hotspots |

## Severity ranking

Severity reflects long-term impact if real gameplay systems are built on top of the current foundation.

## Critical

### C-1. Production can still launch with copied placeholder secrets

**References**

- `infra/.env.example`
- `backend/app/core/config.py`
- `infra/docker-compose.yml`

**Problem**

Compose now requires `POSTGRES_PASSWORD` and `VT_JWT_SECRET`, but the example file still provides usable placeholder values. Production validation only rejects the exact JWT value `change-me-in-production` and database URLs containing `://game:game@`. A copied `.env.example` using `change-this-development-password` and `change-this-jwt-secret` can still satisfy startup requirements.

**Long-term impact**

Critical. A production or public test deployment can accidentally use predictable database/JWT secrets. That enables token forgery, account compromise, and database compromise.

**Corrective refactor**

- Reject known placeholder patterns such as `change-this`, `change-me`, `example`, `password`, and `secret`.
- Enforce minimum secret length and basic entropy for non-local environments.
- Make `.env.example` use blank required values or obviously invalid comments instead of usable placeholders.
- Add a config unit test for production startup rejection.

### C-2. TLS/HTTPS is documented but not implemented

**References**

- `infra/nginx/default.conf`
- `infra/docker-compose.yml`
- `godot_project/autoload/api_client.gd`
- `docs/architecture/mobile_first_online_rpg_architecture.md`

**Problem**

The architecture says Nginx terminates TLS and APIs use HTTPS, but the deployed Nginx config only listens on port 80. There is no TLS listener, HTTP-to-HTTPS redirect, certificate mount, HSTS, or security headers. The Godot client defaults to `http://127.0.0.1/api/v1`, which is also not a valid default for Android devices because it points to the device itself.

**Long-term impact**

Critical for any public test. Access tokens and credentials can cross networks in plaintext if operators trust the docs. Mobile builds can silently target the wrong host.

**Corrective refactor**

- Split local and production Nginx configs.
- Add production `listen 443 ssl`, redirect port 80 to 443, HSTS, and security headers.
- Document certificate mounting/renewal.
- Add a Godot environment/profile config so plaintext localhost is editor/local only.
- Refuse non-local mobile builds with an `http://` API base URL.

### C-3. Shared global ORM model module undermines module ownership

**References**

- `backend/app/db/models.py`
- `backend/alembic/versions/0001_foundation_schema.py`
- `backend/app/modules/registry.py`

**Problem**

Accounts, characters, content, inventory, quests, combat, and social/chat tables live in one global model file and one foundation migration. Any future module can import `backend.app.db.models` and access another module's table without going through a port, repository, or service.

**Long-term impact**

Critical. This is the most direct path to a hidden monolith. It will make inventory, quests, combat, achievements, trading, and mail difficult to replace or extract later.

**Corrective refactor**

- Move model ownership toward module packages, e.g. `modules/inventory/models.py`, `modules/combat/models.py`.
- Keep Alembic metadata composition centralized, but source tables from module-owned models.
- Add a registry mapping modules to owned tables.
- Add architecture tests that fail if a module imports unowned models or repositories.

## High

### H-1. Module-boundary test gives false confidence

**References**

- `backend/tests/test_module_boundaries.py`
- `backend/app/modules/registry.py`

**Problem**

The test only blocks direct imports between `backend.app.modules.*` packages. It does not block gameplay modules from importing `backend.app.db.models`, `backend.app.db.session`, or global infrastructure directly. It also does not enforce `allowed_dependencies` from `ModuleDescriptor`.

**Long-term impact**

High. Future quest/combat/inventory code can bypass contracts while the boundary test remains green.

**Corrective refactor**

- Extend the architecture test to block gameplay modules from importing global DB models/session directly.
- Enforce `allowed_dependencies` from `MODULES`.
- Add allowed exceptions only for repositories owned by the same module.
- Fail if registry dependencies reference modules that do not exist.

### H-2. Content catalog uses process-global lazy singleton state

**References**

- `backend/app/modules/content/router.py`
- `backend/app/modules/content/service.py`

**Problem**

`get_catalog()` is `@lru_cache` and returns a process-global `ContentCatalog`. The catalog then lazy-loads mutable state on the first content request. Validation therefore happens at request time, not startup. Multiple workers can hold different snapshots, and concurrent first requests can race through `_ensure_loaded`.

**Long-term impact**

High. Content errors can become live 500s. Content refresh semantics will be unclear. Tests and future admin publish flows will fight process-global state.

**Corrective refactor**

- Build an immutable content snapshot during FastAPI lifespan startup.
- Fail readiness before serving traffic if published content is invalid.
- Inject the snapshot through app state/dependencies.
- Later replace the snapshot atomically when a content publish occurs.

### H-3. Content rules are still too generic and weakly typed

**References**

- `backend/app/modules/content/schemas.py`
- `backend/app/modules/content/validation.py`
- `content/**/*.json`

**Problem**

`rules`, `assets`, `localization`, and `metadata` are `dict[str, Any]`. The validator checks references and some handler names, but it does not validate per-type semantics: valid quantities, stack limits, price shapes, combat targeting payloads, room structures, reward ranges, currency definitions, or objective-specific fields.

**Long-term impact**

High. Invalid economy, combat, crafting, and quest data can pass CI and fail at runtime. Some failures could become duplication or reward exploits.

**Corrective refactor**

- Introduce discriminated Pydantic schemas per content category.
- Add typed schemas for effect, condition, objective, price, reward, and targeting payloads.
- Keep JSON authoring, but validate it into typed structures before publication.
- Add negative tests for invalid content examples.

### H-4. Deployment can report healthy while schema/content are unusable

**References**

- `backend/app/main.py`
- `infra/docker-compose.yml`
- `README.md`
- `backend/alembic/env.py`

**Problem**

`/health` returns a static status and does not verify database connectivity, migration state, or content validity. Docker starts Uvicorn directly; migrations are a manual README step. Nginx depends on the backend health check, but that health check does not prove readiness.

**Long-term impact**

High. A deploy can look healthy while the database schema is missing or content is invalid. Runtime failures will occur after traffic starts.

**Corrective refactor**

- Split `/health` from `/ready`.
- Make `/ready` check DB connectivity, Alembic revision, and content snapshot validity.
- Add a migration job/entrypoint gate in Compose.
- Document deploy order around migration, content publish, readiness, and rollback.

### H-5. DB/session factory is import-time global state

**References**

- `backend/app/db/session.py`
- `backend/app/core/config.py`

**Problem**

Settings, async engine, and sessionmaker are created at import time with hardcoded pool sizing. Tests or app instances cannot reliably swap database URLs after import. Shutdown does not dispose the engine.

**Long-term impact**

High. This causes hidden coupling, harder integration tests, and potential connection pool pressure across multiple Uvicorn workers.

**Corrective refactor**

- Create a database provider during FastAPI lifespan startup.
- Store it in `app.state`.
- Inject sessions through dependencies.
- Make pool size/max overflow configurable.
- Dispose the engine during shutdown.

### H-6. Security primitives are incomplete and allow reserved JWT claim override

**References**

- `backend/app/core/security.py`

**Problem**

`create_access_token()` applies `extra_claims` after standard JWT claims, so callers can override `sub`, `iss`, `aud`, `iat`, or `exp`. There is no token verification dependency, password hashing helper, refresh token rotation, or authorization layer yet.

**Long-term impact**

High. Future auth code may accidentally mint malformed or over-privileged tokens. Security bugs introduced here will affect every endpoint.

**Corrective refactor**

- Reject reserved claim keys in `extra_claims`, or merge extras before canonical claims.
- Add token decode/verification with issuer/audience checks.
- Add password hashing and refresh-token rotation helpers.
- Add auth dependency tests before public endpoints exist.

### H-7. Godot autoloads are becoming a global service locator

**References**

- `godot_project/project.godot`
- `godot_project/autoload/api_client.gd`
- `godot_project/autoload/content_cache.gd`
- `godot_project/scripts/modules/README.md`

**Problem**

`ContentCache` directly calls global `ApiClient`, and planned module clients are instructed to consume these globals directly. There is no current circular dependency, but the pattern encourages hidden coupling and raw endpoint strings spread throughout UI/game code.

**Long-term impact**

High. Refactoring networking, offline behavior, testing, or API paths later will be expensive.

**Corrective refactor**

- Keep autoloads limited to bootstrap/session ownership.
- Add explicit module facades such as `QuestClient`, `InventoryClient`, and `CombatClient`.
- Pass dependencies into facades instead of calling globals directly.
- Keep UI code away from raw endpoint paths.

### H-8. Client request failures collapse into empty dictionaries

**References**

- `godot_project/autoload/api_client.gd`
- `godot_project/autoload/content_cache.gd`

**Problem**

Transport failures, HTTP errors, empty successful responses, and non-dictionary JSON all return `{}`. `ContentCache.refresh_manifest()` can emit `manifest_loaded(0)` after a failed request. `post_json()` makes idempotency optional.

**Long-term impact**

High. Mobile network failures will look like empty game state. Auth expiration and content failure will be difficult to distinguish. Mutating gameplay retries can duplicate actions if idempotency is not enforced elsewhere.

**Corrective refactor**

- Return a typed `ApiResult` containing success, status code, parsed body, transport error, and retryability.
- Add failure-specific signals.
- Make idempotency mandatory for mutating gameplay commands.
- Add token refresh handling before authenticated gameplay.

### H-9. Content asset paths are not validated against the Godot project

**References**

- `content/**/*.json`
- `backend/app/modules/content/validation.py`
- `godot_project/project.godot`

**Problem**

Content references many `res://` paths for icons, scenes, models, music, and VFX, but the repository does not contain those assets/scenes. The validator only checks that `assets` is an object.

**Long-term impact**

High. Backend content can pass CI while the client fails to load scenes or displays missing assets. This creates the exact client/server content drift the architecture wants to avoid.

**Corrective refactor**

- Decide whether asset paths are required runtime references or planned placeholders.
- If required, validate `res://` paths against `godot_project/`.
- If planned, use asset keys/status fields instead of runtime paths until assets exist.
- Add placeholder assets/scenes only when the client needs to load them.

### H-10. Backup script lacks restore, retention, encryption, and env consistency

**References**

- `infra/scripts/backup_postgres.sh`
- `README.md`

**Problem**

The script creates a local dump but does not source `infra/.env`, document restore, enforce retention, compress/encrypt archives, verify dumps, or sync off-host. It uses shell `POSTGRES_USER`/`POSTGRES_DB`, which may not match Compose env values unless manually exported.

**Long-term impact**

High. Backups can silently fail or be unusable during a restore incident. A single VPS disk failure can still lose player data.

**Corrective refactor**

- Add a restore script and restore runbook.
- Source/pass the same env file used by Compose.
- Add compression/encryption and retention.
- Periodically test `pg_restore`.
- Add optional encrypted off-host sync.

## Medium

### M-1. Content endpoints are unbounded

**References**

- `backend/app/modules/content/router.py`
- `backend/app/modules/content/service.py`

**Problem**

`GET /content` returns every content definition if no type filter is passed. Manifest and cold load behavior scale with the entire content tree.

**Long-term impact**

Medium now, high once content grows. Mobile clients may receive oversized payloads, and cold startup/first request latency grows with content count.

**Corrective refactor**

- Require a content type or add pagination.
- Add category manifests.
- Precompute checksums at snapshot build.
- Serve published content statically through Nginx later.

### M-2. Migration omits many database-side defaults present in ORM

**References**

- `backend/app/db/models.py`
- `backend/alembic/versions/0001_foundation_schema.py`

**Problem**

The ORM has Python defaults such as status, level, experience, JSON defaults, and moderation state. The migration creates many of those columns as `not null` without equivalent `server_default`s. `updated_at` has ORM `onupdate` but no database trigger.

**Long-term impact**

Medium. Raw SQL, imports, admin scripts, or future services writing outside the ORM must supply every value manually. This causes inconsistent data creation paths.

**Corrective refactor**

- Decide which defaults are database invariants.
- Add `server_default`s for invariant defaults.
- Add an `updated_at` trigger or accept app-managed timestamps explicitly.
- Add schema drift tests comparing ORM expectations to migrations.

### M-3. High-growth data is modeled as unbounded JSONB blobs

**References**

- `backend/app/db/models.py`
- `backend/alembic/versions/0001_foundation_schema.py`

**Problem**

`combat_sessions.action_log`, `participants`, and `rewards` are JSONB blobs. This is acceptable for scaffold state but risky for long sessions, analytics, moderation, and concurrent updates.

**Long-term impact**

Medium now, high if combat ships this way. Rows can bloat, updates can lock large records, and querying action history becomes painful.

**Corrective refactor**

- Keep `combat_sessions` small.
- Move turn/action logs to append-only `combat_actions` or `combat_events`.
- Keep reward claims in auditable rows with idempotency keys.

### M-4. Nginx rate limiting is too blunt

**References**

- `infra/nginx/default.conf`

**Problem**

A single per-IP `10r/s` zone applies to all `/api/` routes. This is too coarse for auth abuse, chat spam, NATed mobile users, and content downloads.

**Long-term impact**

Medium. Operators may loosen the global limit and weaken abuse protection, or keep it and throttle legitimate users behind shared mobile networks.

**Corrective refactor**

- Add endpoint-specific rate zones.
- Use strict limits for login/register.
- Use separate limits for chat and mutating gameplay.
- Relax/cache content manifest and definitions.
- Add account/device-level app rate limits for authenticated abuse.

### M-5. API composition eagerly imports every module router

**References**

- `backend/app/api/router.py`

**Problem**

The API composition root imports every module router at import time. This is fine while routers are placeholders, but as routers import services/repositories, it increases circular import and startup side-effect risk.

**Long-term impact**

Medium. Real modules can create cycles between routers, services, contracts, and repositories.

**Corrective refactor**

- Keep routers thin.
- Make routers call dependency-provided services rather than constructing them.
- Consider router factory functions registered by module descriptors.
- Keep all wiring in the composition layer/lifespan.

### M-6. Module registry is passive and can drift from reality

**References**

- `backend/app/modules/registry.py`

**Problem**

The registry documents module ownership and allowed dependencies, but nothing enforces owned tables, package ownership, or dependency direction beyond the limited boundary test.

**Long-term impact**

Medium. Architecture documentation can diverge from code and give false confidence.

**Corrective refactor**

- Add owned table names to descriptors.
- Validate migrations/models against table ownership.
- Validate imports against `allowed_dependencies`.
- Fail if registry entries reference missing modules.

### M-7. ORM lacks explicit deletion and retention policy

**References**

- `backend/app/db/models.py`
- `backend/alembic/versions/0001_foundation_schema.py`

**Problem**

Foreign keys lack explicit `ondelete` behavior. Chat, combat sessions, quests, and item records do not yet have retention/archive policies.

**Long-term impact**

Medium. Delete behavior becomes accidental, and future cleanup jobs may violate data integrity or preserve too much data.

**Corrective refactor**

- Define deletion policy per aggregate.
- Prefer soft-delete/audit for player/economy records.
- Add retention windows for chat and combat logs before launch.
- Index high-use foreign keys consistently.

### M-8. Documentation mixes target architecture, current scaffold, and resolved risks

**References**

- `README.md`
- `docs/architecture/brutal_architecture_review.md`
- `docs/architecture/mobile_first_online_rpg_architecture.md`

**Problem**

Some docs describe target architecture as if implemented. Some review items are now partially resolved but still stated as open. README says the stack includes JWT auth even though auth is only a primitive and planned module.

**Long-term impact**

Medium. Future maintainers may trust non-existent guarantees or skip necessary hardening.

**Corrective refactor**

- Add an implementation status matrix: implemented, scaffolded, planned.
- Mark resolved, partially resolved, and open review items.
- Separate production runbooks from aspirational architecture.

### M-9. Test coverage is not yet sufficient for architecture promises

**References**

- `backend/tests/test_content_definitions.py`
- `backend/tests/test_module_boundaries.py`

**Problem**

Tests cover content graph validity and limited import boundaries. There are no FastAPI contract tests, migration tests, config safety tests, DB constraint tests, or security token tests.

**Long-term impact**

Medium. Regressions will show up during manual runtime testing once real endpoints exist.

**Corrective refactor**

- Add config safety tests for production secret rejection.
- Add token claim tests.
- Add migration upgrade/downgrade smoke tests.
- Add FastAPI endpoint contract tests as endpoints become real.
- Add transaction/idempotency tests before rewards or inventory mutation.

## Low

### L-1. Content validator is the first file-size hotspot

**References**

- `backend/app/modules/content/validation.py`

**Problem**

At 244 lines, the validator is not excessive yet, but it already combines category definitions, handler definitions, base shape validation, graph walking, reference validation, and type-specific rules.

**Long-term impact**

Low now, medium later. As content schemas grow, this file can become a "content manager" in disguise.

**Corrective refactor**

- Split into `constants.py`, `loader.py`, `graph.py`, and per-content validators.
- Keep graph walking generic.
- Keep category-specific semantics in small validators.

### L-2. Content service still contains unused path-loading helpers

**References**

- `backend/app/modules/content/service.py`

**Problem**

The catalog now loads from a validation report, but `_definition_paths()` remains. This is minor, but dead helpers make ownership less clear.

**Long-term impact**

Low. Dead code creates confusion and can become a stale alternate path.

**Corrective refactor**

- Remove unused helpers once no tests or future import tooling need them.
- Keep one content loading path per runtime mode.

### L-3. Placeholder module routers provide little architectural value

**References**

- `backend/app/modules/characters/router.py`
- `backend/app/modules/inventory/router.py`
- `backend/app/modules/quests/router.py`
- `backend/app/modules/combat/router.py`
- `backend/app/modules/social/router.py`

**Problem**

`/module-status` endpoints prove folders exist but not real module isolation. They also expose internal architecture status over the public API.

**Long-term impact**

Low now. Medium if public clients start depending on these endpoints.

**Corrective refactor**

- Move module registry/status to admin-only or development-only endpoints.
- Remove placeholder routers when real module endpoints are added.
- Keep architecture status in docs/tests, not public gameplay API.

## Explicit checks requested

### Circular dependencies

No current Python import cycles were found by static scan. No GDScript circular dependency exists in the current two-script scaffold. Risk remains medium because API router composition eagerly imports all routers and future routers may import services/repositories.

### Singleton abuse

Current risks:

- `backend/app/modules/content/router.py` uses a cached process-global content catalog.
- `backend/app/db/session.py` creates import-time engine/sessionmaker globals.
- Godot autoloads are global singletons and `ContentCache` directly depends on `ApiClient`.

### Hidden coupling

Current risks:

- Shared ORM model file couples all domains.
- Content rules are generic dictionaries understood implicitly by future systems.
- Godot scripts use raw endpoint strings.
- Docs and registry can drift from actual implementation.

### Module-boundary violations

No active direct cross-gameplay-module imports were found. The boundary test is too narrow and does not prevent global DB/session/model imports from gameplay modules.

### Direct database access from gameplay systems

No gameplay module currently performs direct database access. This is mainly because gameplay systems are placeholders. The shared `backend/app/db/models.py` and global `backend/app/db/session.py` make future direct access likely unless tests are strengthened.

### Excessive file sizes

No file is excessive yet. Static scan largest files:

- `backend/app/modules/content/validation.py`: 244 lines
- `backend/app/db/models.py`: 159 lines
- `backend/alembic/versions/0001_foundation_schema.py`: 148 lines
- `backend/app/modules/content/service.py`: 115 lines
- `godot_project/autoload/api_client.gd`: 79 lines

The validator and shared model file are the early hotspots.

## Recommended corrective sequence

1. Fix production secret validation and `.env.example`.
2. Split `/health` and `/ready`; validate DB/migrations/content before readiness.
3. Replace router-level content singleton with lifespan-built immutable snapshot.
4. Strengthen architecture tests for DB/model imports and registry dependencies.
5. Move ORM ownership toward module-owned model/repository files.
6. Add typed content schemas for effects, conditions, objectives, rewards, prices, and targeting.
7. Add token claim safety tests and auth verification helpers.
8. Add production TLS config and Godot environment profile handling.
9. Add backup restore/retention/encryption runbook and script support.
10. Split content validator before it becomes a large manager-like module.

Do not add additional gameplay systems until items 1-6 are addressed.
