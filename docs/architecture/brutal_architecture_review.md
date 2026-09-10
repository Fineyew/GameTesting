# Brutal Architecture Review: 5-Year Solo Developer Survival

This review assumes _Veilbound Tides_ must survive five years of iterative development with one primary maintainer, low operating cost, and no tolerance for hidden monoliths. The initial scaffold is useful as a direction-setting artifact, but it is too optimistic. Without correction, it would accumulate content debt, deployment risk, and module coupling before the first meaningful gameplay loop ships.

## Executive verdict

The project should continue as a **modular monolith**, but the current plan needs stricter boundaries and a smaller execution surface. The most dangerous failure mode is not server scale; it is **solo-maintainer overload caused by too many half-built systems and under-validated content**.

### Keep

- FastAPI + PostgreSQL + Docker Compose + Nginx.
- Godot 4.x mobile-first client.
- Data-driven content.
- Turn-based combat as request/response.
- One deployable backend process for MVP.

### Change immediately

- Treat the first release as a **vertical slice**, not a broad MMO checklist.
- Make content validation fail fast before content reaches runtime.
- Add enforceable module contracts and module-boundary tests.
- Add migrations/backups/deployment hardening before production data exists.
- Stop using placeholder modules as proof of modularity.
- Move from "JSON can contain anything" to "JSON is flexible but validated."

## Current design flaws

### 1. Scope is still too large for one developer

The architecture lists accounts, characters, friends, parties, guilds, chat, trading, mail, crafting, gathering, mounts, shops, loot, achievements, dungeons, and world events as MVP-adjacent systems. Even if each system is simple, the interaction matrix is large.

**Why this will fail later:**

- Social systems multiply moderation, abuse, and support work.
- Trading and mail introduce duplication and fraud risk.
- Guilds add roles, permissions, invites, and edge cases.
- Dungeons, achievements, and world events require event correctness.
- Every additional content type creates validation and tooling obligations.

**Refactor:**

- MVP must be a vertical slice:
  - Auth.
  - Character.
  - Content manifest.
  - One zone.
  - Dialogue.
  - Quests.
  - Inventory/wallet.
  - Turn-based combat.
  - Loot/rewards.
- Social MVP should start as friends + local chat only.
- Trading, mail attachments, guild permissions, world events, and repeatable dungeons should remain behind explicit milestone gates.

### 2. "Modular monolith" is declared but not enforced

The scaffold has folders named after modules, but placeholder routers do not create real boundaries. A developer can still import another module's repository or mutate shared tables directly.

**Future bottleneck:**

After several systems are added, quest code will call inventory internals, achievement code will inspect combat rows, and social systems will lock item records directly. At that point, replacing a module becomes theoretical.

**Refactor:**

- Add module contracts/ports.
- Add a module registry documenting ownership and dependencies.
- Add architecture tests that fail on direct cross-module imports except from the composition root.
- Require cross-module work through service interfaces or domain events.

### 3. Content pipeline is too weak

The initial content test only checks type/key/version/display shape. It does not validate references, unknown effects, missing dependencies, duplicate semantic keys, impossible rewards, or client asset drift.

**Failure modes:**

- A quest references a missing item.
- A recipe references missing materials.
- An enemy references a removed spell.
- A dialogue option emits an unknown effect.
- A zone references a gathering node that has no definition.
- Client downloads a manifest that points to content the backend cannot resolve.

**Refactor:**

- Add strict content tree validation.
- Validate references across content categories.
- Validate known condition/effect/objective handler names.
- Add `schema_version` to every content file.
- Fail tests before invalid content can be merged.
- Keep arbitrary scripting out of content files.

### 4. File-backed content loads are not production-safe

The scaffold reloads and parses all JSON files on every content request. That is fine for a demo but wrong as a runtime default.

**Risks:**

- Request latency grows with content count.
- Invalid content can fail at request time.
- Manifest and definition responses can disagree if files change mid-request.
- No clear publish boundary exists.

**Refactor:**

- Build an immutable in-process content index at startup for the file-backed scaffold.
- Validate before serving.
- Later replace the index with a database-backed published manifest without changing consumers.

### 5. Database schema is under-specified for real operations

The schema is a good sketch but lacks enough operational guardrails.

**Risks:**

- Missing check constraints allow negative quantities, invalid levels, and invalid amounts.
- UUID ORM typing is wrong if Python values are strings while the dialect returns UUID objects.
- No migration scaffold means schema drift starts immediately.
- JSONB action logs can grow until combat rows become bloated.
- Chat table can grow indefinitely.
- Trade/mail item transfers need locks and item reservation states before implementation.

**Refactor:**

- Use UUID-typed ORM fields.
- Add basic database constraints and indexes.
- Add migration tooling before any production data.
- Split high-growth logs into append-only tables when combat implementation begins.
- Add retention policies for chat/mail/events.

### 6. Deployment defaults are unsafe

The Docker Compose file uses development defaults for secrets and passwords. Nginx has no rate limits. Backend containers run as root. There is no backup script.

**Risks:**

- Production accidentally launches with known secrets.
- Login/chat endpoints can be abused cheaply.
- A container breakout or app exploit has more privilege than necessary.
- A VPS disk failure destroys all player data.

**Refactor:**

- Reject production startup with default JWT secret.
- Require explicit database password in deployed environments.
- Run backend as non-root.
- Add Nginx request limits and timeouts.
- Add a simple PostgreSQL backup script.

### 7. Client architecture is still too optimistic

The Godot scaffold has no timeout policy, no retry classification, no token refresh behavior, and no persisted content cache.

**Risks:**

- Mobile networks create duplicate or lost commands.
- Players see silent failures.
- Content redownloads waste bandwidth.
- Client starts depending on raw API paths instead of module facades.

**Refactor:**

- Add request timeouts and error signals.
- Keep idempotency keys mandatory for mutating gameplay commands.
- Persist content cache after manifest validation in a later client milestone.
- Keep Godot modules thin and generated from API/content contracts where practical.

### 8. Security is not designed deeply enough yet

JWT creation exists, but auth is not implemented. There are no password policies, refresh-token rotation, role checks, rate limits, or audit records.

**Risks:**

- Account takeover or brute force.
- Admin content imports without robust authorization.
- Chat and display name abuse.
- Economy exploits through duplicate reward claims.

**Refactor:**

- Implement auth before any public test.
- Add refresh token rotation.
- Add idempotency table before reward-affecting endpoints.
- Add audit log for economy-affecting actions.
- Add moderation hooks before global chat.

### 9. Testing strategy is too shallow

Syntax checks and shape tests are not enough for a data-driven RPG.

**Missing tests:**

- Content reference graph validation.
- Module boundary import tests.
- API contract tests.
- Database transaction tests.
- Idempotency tests.
- Reward duplication tests.
- Migration tests.

**Refactor:**

- Add content graph tests now.
- Add module boundary tests now.
- Add endpoint contract tests as modules become real.
- Add transaction tests before inventory, trade, mail, or rewards ship.

### 10. Operational cost target is realistic, but only if restraint holds

The server target is fine for 10-100 active users if gameplay stays low-frequency. The problem is feature creep, not raw performance.

**Scaling risks:**

- Polling chat across too many channels.
- Unbounded chat/combat/event rows.
- Large JSON payloads for inventory and quest state.
- Nginx serving all content through backend instead of static files.
- Too many Uvicorn workers for database pool limits.

**Refactor:**

- Keep chat polling scoped and capped.
- Add retention/archival jobs.
- Add cursor pagination early.
- Serve published content through Nginx/static files later.
- Keep backend pool sizes conservative.

## Refactored architecture rules

These rules supersede the softer language in the initial architecture.

1. **No gameplay feature begins until its content schema and validation rules exist.**
2. **No module may import another module's repository, models, or service directly.**
3. **Cross-module commands go through ports; cross-module observations go through events.**
4. **Every reward-affecting endpoint must be idempotent.**
5. **Every item transfer must use a transaction and an item reservation/lock state.**
6. **Every growing table needs retention, pagination, or archival strategy before launch.**
7. **Every content reference must be validated in CI.**
8. **Every production deploy must fail closed on default secrets.**
9. **The MVP is a vertical slice, not a checklist of all eventual MMO systems.**
10. **If a solo developer cannot test and operate a system alone, it is not MVP.**

## Revised MVP gate

Do not implement additional gameplay systems until the following foundation is true:

- Content validator checks references and handler names.
- Module registry documents ownership and allowed dependencies.
- Module boundary tests run in CI/local validation.
- Runtime config rejects unsafe production defaults.
- Docker/Nginx have basic hardening.
- Database models use correct UUID typing and basic constraints.
- Backup script exists and restore process is documented.

## Refactored milestone order

1. Foundation hardening.
2. Auth + character.
3. Content manifest + local client cache.
4. Dialogue + quest vertical slice.
5. Inventory/wallet + reward idempotency.
6. Turn-based combat with bounded logs.
7. Loot/reward claims.
8. Friends + limited chat.
9. Crafting/gathering.
10. Parties.
11. Dungeons.
12. Mail/trade.
13. Guilds.
14. World events.

## Explicit non-goals until after the first public test

- Guild roles and permissions.
- Direct player-to-player item trade.
- Mail attachments.
- Auction house or marketplace.
- Large repeatable dungeon library.
- WebSocket chat infrastructure.
- World events with global state.
- Any real-time authoritative movement system.

## Architecture conclusion

The current project is salvageable because it is still early. The right move is to harden the foundation now, reduce the MVP surface, and make content validation and module boundaries enforceable before adding more gameplay. If this corrective pass is skipped, the project will appear productive for a short time and then slow down under invisible coupling, invalid content, unsafe economy actions, and solo-maintainer operational burden.
