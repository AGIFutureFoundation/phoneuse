# Reach × PhoneUse — the approval layer meets the execution layer

*This document is an additive addition in the AGIFutureFoundation fork of
PhoneUse Local. It describes an integration from the PhoneUse side. Nothing
here changes PhoneUse's own code, README, or behaviour.*

[Reach](https://github.com/AGIFutureFoundation/reach) is a relationship
action agent built for the Do Not Disturb: Phone Use Hackathon (Frontier
Tower, 2026-11-13). It runs today as a dependency-free PWA
([live demo](https://reach.agicorp.network/)). PhoneUse Local is the
sponsor's open-source stack, and this fork is where the two meet.

## The division of labour

Reach and PhoneUse solve opposite halves of the same problem:

- **Reach is the approval and rails front-end.** It surfaces who needs a
  reply, does a visible research step, and drafts a message from on-record
  facts only. Its rails are enforced as behaviour, not promises:
  draft-first **exact-copy approval** (a human taps "approve" on the exact
  text, or nothing moves), **suppression checked before drafting**
  (do-not-contact is a refusal, stated out loud), **caps as counters**
  (90 sends/day per mailbox, ≤250 cold/day, persisted; at the cap the send
  is refused), and **provenance on every item**.
- **PhoneUse is the execution layer.** It reads a real iPhone's screen
  (on-device OCR, accessibility as fallback), taps, types, and scrolls,
  driven from a Mac over USB through WebDriverAgent.

Reach deliberately claims no native phone control from a web build.
PhoneUse deliberately makes no judgement about *what* should be sent.
The contract between them is one sentence:

> **PhoneUse only ever receives text a human approved in Reach,
> byte-for-byte, and only after that approval.**

Nothing unapproved crosses the boundary. Nothing approved is paraphrased
on the way. If Reach's rails refuse — suppressed contact, cap reached,
no facts on record — there is nothing for PhoneUse to execute.

## The API surface a Reach client uses

All of it is the one authenticated API on `http://127.0.0.1:8765`
(see [INTEGRATIONS.md](INTEGRATIONS.md) upstream for the full reference).

| Step | Call | Notes |
| --- | --- | --- |
| Detect | `GET /health` | Unauthenticated. Reach's panel uses this to report "detected / not detected" where the browser permits the call. |
| Choose a phone | `GET /api/devices` | Bearer key required. Pick a device `id` (UDID). |
| Hand over an approved message | `POST /api/ai/tasks` | Body: `{"device_id": "<udid>", "task": "<task text>"}`. Runs a prompt task (needs the Codex CLI, per upstream docs). |
| Follow it | `GET /api/ai/tasks/{id}` | Poll for progress and the reported result. |
| Stop it | `POST /api/ai/tasks/{id}/cancel` | A running task can be stopped at any time. |
| Deterministic alternative | `POST /api/devices/{id}/actions`, `/api/workflows`, `/api/jobs` | Direct actions and recorded step sequences, for clients that don't want a model in the loop. |
| Agent alternative | MCP server (`platform/start-mcp.sh`) | Same API over stdio: `list_devices` → `acquire_device` → `screenshot` / `page_source` → `device_action` → `release_device`. |

Two client shapes, one invariant — the approved message itself is
never altered:

- The Reach PWA sends the approved text **as** the task payload,
  byte-for-byte (`task` === the card's text; its test suite asserts
  the equality against the captured request body).
- A Mac-side bridge composes a **fixed instruction template** with
  the approved message embedded verbatim — see
  [`examples/reach-bridge/`](../examples/reach-bridge/) for a runnable
  sketch that asserts the approved text survives composition
  unchanged.

## The browser reality, stated plainly

PhoneUse's API allowlists exactly two browser origins —
`http://localhost:3109` and `http://127.0.0.1:3109` (its own web UI) —
and refuses every other origin with 403. A public HTTPS page also faces
mixed-content and local-network blocking before origin checks even run.
So:

- **Supported bridge configuration:** Reach served from the allowlisted
  local origin on the same Mac as PhoneUse — the booth/local setup.
  There, an approved card can be handed to `POST /api/ai/tasks` directly.
- **From the public site** (`https://reach.agicorp.network/`), the
  handover POST is expected to be refused. Reach narrates that refusal,
  makes no claim of delivery, and the message still travels by its
  always-available bridge: the human's own Copy/Share tap.

Detection has the same shape: `/health` answers where the browser
permits a local call, and "not detected" is the normal result from a
public page — not an error state.

## Safety posture

- **Scoped keys for integrations.** Per upstream docs, give a client its
  own key, limited to one phone and with an expiry
  (`platform/create-key.py`). The administrator key stays in
  `platform/.state/admin-token`; Reach's panel stores any key only in
  the browser's on-device storage, never exports it, and sends it only
  to `127.0.0.1`.
- **Never expose the API.** Upstream is explicit: do not point a remote
  browser at this server or tunnel it publicly. The bridge works
  because both halves are on the same machine, under the same human.
- **Approval is the trigger, not a setting.** There is no "auto-send"
  mode in Reach to enable. The handover exists only on an approval
  card, only after the human's tap on the exact text.
- **Verify on the phone.** As upstream notes, a successful action only
  means the command reached the phone — read the screen back (or take
  the screenshot) before calling anything delivered.

## Status (2026-11-13)

- Reach detects PhoneUse from its connect panel (`GET /health`) and
  labels the result with the limits above.
- The approved-card → PhoneUse-task handover is implemented in Reach
  against `POST /api/ai/tasks`, with a test asserting the task payload
  carries the approved text byte-for-byte; it runs in the supported
  local configuration and degrades to narration + Copy/Share elsewhere.
- The client sketch in `examples/reach-bridge/` is a starting point for
  a Mac-side bridge process, where a local origin and a scoped key are
  both natural.

PhoneUse remains its authors' project, MIT-licensed; this fork adds
documentation and an example only, and keeps upstream attribution
intact.

## The fleet

The integration above runs one phone. The operator also runs a small
fleet — three PhoneUse console accounts, one per corporate holding,
with one phone assigned to each:

- **AGI Fellowship** — community and city-guide outreach, human
  handoff to a Fellowship steward.
- **AGI Future Foundation** — partner and funder warmth, human
  handoff to Russell Vacanti.
- **BuilderSpace** — builder and employer outreach, human handoff
  to Mike.

The contract does not change at fleet scale: Reach holds the approval
law, each phone executes only its own holding's approved items, and
the outreach programme's caps, suppression, and pacing are set
outside the fleet and never loosened by it. Houses never cross
queues — an item whose phone is unavailable waits rather than
migrating.

The fleet layer is documented in
[REACH-FLEET.md](REACH-FLEET.md) (role cards, rails, daily rhythm,
configuration), and the bridge sketch in
[`examples/reach-bridge/`](../examples/reach-bridge/) speaks fleet:
`--config` / `--holding` route an approved card to the right
holding's phone, re-check approval and suppression at the boundary,
and refuse any holding whose device is still unconfigured.

### Fleet assignments (approved 2026-11-13)

All five phones are Google Pixel 7 Pro (US) on the one console
account (`agent@agifellowship.church`), paid until 13 Dec 2026:

| Phone | Device ID | Assignment |
| --- | --- | --- |
| Fellowship phone | `ACP6BC9P8ZEML2Z1` | AGI Fellowship — manages `agent@agifellowship.church` |
| Foundation phone | `ACP6BD9Q64XX8XE9` | AGI Future Foundation — manages `x@agifuturefoundation.org` |
| BuilderSpace phone | `ACP6B99O2IWFKAA4` | BuilderSpace — manages `x@agicorp.network` |
| Demo phone | `ATP68K8IGMSLAIBB` | Reach booth/demo |
| Reserve phone | `ACP6BD9PTE0T2ASG` | Cold reserve (disabled in the fleet config) |

The full fleet record — role cards, rails, daily rhythm, and
configuration — lives in [REACH-FLEET.md](REACH-FLEET.md).
