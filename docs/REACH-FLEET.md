# The Reach fleet — five phones, three holdings, one console account

*This document is an additive addition in the AGIFutureFoundation fork of
PhoneUse Local. It describes how the fork's operator runs a small fleet of
PhoneUse phones behind [Reach](https://github.com/AGIFutureFoundation/reach).
Nothing here changes PhoneUse's own code, README, or behaviour. The
single-phone integration story lives in [REACH.md](REACH.md); this file is
the fleet layer on top of it.*

## The fleet at a glance

The operator runs a fleet of **five phones on one PhoneUse console
account** (`agent@agifellowship.church`). Three are working phones, one
per corporate holding; the fourth runs the Reach booth demo and the
fifth is a cold reserve. A working phone only ever works its own
holding's queue, and manages that holding's mailbox — the fleet works
the outreach across the holdings' mailboxes from the assigned phones.
The assignments below were **approved by Mike on 2026-11-13**; they are
the fleet's settled record, not a proposal. All five phones are Google
Pixel 7 Pro (US), paid until 13 Dec 2026.

| Phone | Device ID | Manages mailbox | Queue it serves | Human handoff |
| --- | --- | --- | --- | --- |
| Fellowship phone | `ACP6BC9P8ZEML2Z1` | `agent@agifellowship.church` | Community and city-guide outreach | A Fellowship steward |
| Foundation phone | `ACP6BD9Q64XX8XE9` | `x@agifuturefoundation.org` | Partner and funder warmth | Russell Vacanti |
| BuilderSpace phone | `ACP6B99O2IWFKAA4` | `x@agicorp.network` | Builder and employer outreach | Mike |
| Demo phone | `ATP68K8IGMSLAIBB` | — | Reach booth and demo work | Mike |
| Reserve phone | `ACP6BD9PTE0T2ASG` | — | Cold reserve — not in service | — |

Device IDs are fleet inventory, not secrets: they are the fleet's
public-to-the-team record, and they belong in this document and in
[`examples/reach-bridge/fleet-config.example.json`](../examples/reach-bridge/fleet-config.example.json).
API keys are a different matter entirely — no key ever appears in this
repo (see Configuration).

## Role cards

### Fellowship phone — community and city-guide outreach

- **Holding:** AGI Fellowship (California nonprofit religious corporation).
- **Device:** Google Pixel 7 Pro (US), console device `ACP6BC9P8ZEML2Z1`.
- **Manages mailbox:** `agent@agifellowship.church`.
- **Work:** community outreach for the Fellowship's city guides and local
  resource work — churches, shelters, food banks, and community partners in
  the guide cities; Sparks of Light programme conversation.
- **Voice:** the Fellowship's own. Fellowship material stays in Fellowship
  surfaces; this phone never carries Foundation or BuilderSpace copy.
- **Human handoff:** anyone who asks for a human leaves the automated
  thread and is flagged to a Fellowship steward the same day.

### Foundation phone — partner and funder warmth

- **Holding:** AGI Future Foundation (California nonprofit public benefit
  corporation).
- **Device:** Google Pixel 7 Pro (US), console device `ACP6BD9Q64XX8XE9`.
- **Manages mailbox:** `x@agifuturefoundation.org`.
- **Work:** partner and funder follow-up — programme applications,
  credit/partnership correspondence, interview and press threads,
  keeping warm relationships warm.
- **Voice:** gracious and informative, written from the agent's
  perspective, always offering a human connection.
- **Human handoff:** anyone who asks for a human leaves the automated
  thread and is flagged to Russell Vacanti, the Foundation's co-founder
  and director, the same day.

### BuilderSpace phone — builder and employer outreach

- **Holding:** BuilderSpace, the network's builder tour (AGI Corp lane).
- **Device:** Google Pixel 7 Pro (US), console device `ACP6B99O2IWFKAA4`.
- **Manages mailbox:** `x@agicorp.network`.
- **Work:** builder and employer outreach for tour towns — session
  follow-ups, partner venues, employer connections for builders.
- **Voice:** direct and practical; BuilderSpace pages carry no other
  holding's branding.
- **Human handoff:** anyone who asks for a human leaves the automated
  thread and is flagged to Mike the same day.

### Demo phone — Reach booth and demo work

- **Device:** Google Pixel 7 Pro (US), console device `ATP68K8IGMSLAIBB`.
- **Work:** the Reach demo — booth walkthroughs, judging, and trying
  fleet behaviour where nothing real is at stake.
- **Rails:** the demo phone carries no holding's live queue and sends
  nothing on any holding's behalf.

### Reserve phone — cold reserve

- **Device:** Google Pixel 7 Pro (US), console device `ACP6BD9PTE0T2ASG`.
- **State:** not in service — it ships disabled in the fleet config
  (`"enabled": false`). It joins the fleet only when a working phone
  is out of action and an assignment is approved; it does not silently
  inherit the down phone's queue, because houses never cross without a
  ruling.

## Division of labour

The split from [REACH.md](REACH.md) holds at fleet scale:

- **Reach decides what may be said.** It drafts from on-record facts only,
  checks suppression before drafting, enforces the caps, and puts the
  exact text in front of a human. Nothing moves without a tap on the
  exact copy.
- **PhoneUse executes what was approved.** A phone receives an approved
  Reach card and carries it out on the holding's own device — read the
  screen, tap, type, send — with the approved text byte-for-byte.
- **The fleet routes; it does not judge.** Fleet configuration answers
  one question only — *which holding's phone runs this approved item?* —
  and the answer is fixed by the queue the item came from. Routing never
  widens what may be sent, to whom, or how often.

## The rails

These are set outside the fleet, by the outreach programme and the
holdings' standing rules. The fleet inherits them and can never loosen
them:

- **Approved items only.** A phone executes queue items that already
  passed the programme's gates — personalisation gate, suppression diff,
  cap check. There is no path from "draft exists" to "phone executes"
  that skips human approval of the exact text.
- **Suppression is law.** Do-not-contact is checked before drafting in
  Reach and re-checked at the bridge before submission
  (see `examples/reach-bridge/`). A suppressed contact's item does not
  reach a phone; if one somehow arrives at the bridge, the bridge
  refuses it.
- **Caps stay caps.** 90 sends/day per mailbox and ≤250 cold/day across
  the programme, counted in Reach. A phone adds hands, not volume: the
  counters do not reset per device, and at the cap the item waits.
- **Pacing stays paced.** Social posting follows the standing pacing
  rule (one platform at a time, minutes between posts on the same
  platform). Five phones do not multiply the pace.
- **Houses never cross.** A Fellowship item never runs on the Foundation
  phone; a BuilderSpace queue never borrows the Fellowship phone. If the
  right phone is unavailable, the item waits — it does not migrate.
- **A submitted task is not a delivered message.** Execution is verified
  on the phone's screen, and outcomes are written back (below) before
  anything is reported as sent.

## Daily rhythm

Each phone runs the same day, on its own holding's clock of work:

1. **Brief.** The morning brief composes from the phone's own Reach
   state: follow-ups due, drafts waiting on approval, unread count, cap
   usage so far, the next best action.
2. **Queue.** The day's queue items arrive already gated by the outreach
   programme — verified, suppression-diffed, inside the caps.
3. **Approvals.** A human approves exact copy, item by item. Refusals —
   suppressed, capped, no facts on record — are narrated and logged,
   never overridden by the fleet.
4. **Execution.** Approved items route to the holding's phone through
   the bridge and are carried out; progress is polled, and anything can
   be stopped.
5. **Write-backs.** Every outcome lands back in the shared records the
   programme already keeps: sends and bounces update the send log,
   unsubscribes and do-not-contact replies update suppression
   everywhere (all lanes, all phones), and replies append contact
   events to the people graph. A reply that asks for a human exits the
   automated thread to that holding's handoff the same day.

## Configuration

Fleet configuration is an operator-local file, modelled by
`examples/reach-bridge/fleet-config.example.json`:

- **`device_id`** — per holding, the console device ID of that holding's
  phone. The example config carries the fleet's approved real IDs as
  the team record (assignments approved by Mike, 2026-11-13); the
  bridge reads the operator's private copy of the config, and still
  refuses any holding whose `device_id` is left as the placeholder.
- **`api_base`** — the PhoneUse API base the bridge submits to. The
  verified surface in this fork is the local API at
  `http://127.0.0.1:8765` (`GET /health`, `POST /api/ai/tasks`, Bearer
  auth). **PENDING:** how the hosted console exposes its phones to a
  client is not documented in this fork and is not assumed anywhere in
  the fleet setup; until it is verified, the fleet's bridge runs against
  the local API surface described in [REACH.md](REACH.md).
- **`reach_origin`** — `http://localhost:3109`, the allowlisted local
  origin Reach is served from in the supported bridge configuration.
- **API keys** — one scoped key per phone, created with the fork's
  `platform/create-key.py` (one phone, with an expiry). Keys live in the
  console / the operator's vault and in the environment of the bridge
  process (`PHONEUSE_API_KEY`). **A key never appears in this repo, in
  the fleet config, or in any committed file** — the example config has
  no key field by design.
- **Accounts** — one console account, `agent@agifellowship.church`,
  hosts all five phones; each working phone manages its holding's
  mailbox (table above). Signing in, password resets, and plan changes
  are the account holder's actions in the console, never the bridge's.

## Status (2026-11-13)

- Five phones are provisioned on the one console account, all Google
  Pixel 7 Pro (US), paid until 13 Dec 2026; per the account holder,
  they were set up on the console's $149 plan tier under the event's
  hackathon promo.
- Device assignments are **approved** (Mike, 2026-11-13) and recorded
  in the table above and in the example fleet config; the reserve
  phone ships disabled in the config, and the bridge refuses to run a
  holding whose `device_id` is still the placeholder.
- The bridge's fleet mode (`--config` / `--holding`) is implemented in
  `examples/reach-bridge/reach_bridge.py` against the verified local
  API; single-phone mode is unchanged.
- Reach's side of the fleet — per-holding profiles in the app — is
  tracked in the Reach repository, not here.

PhoneUse remains its authors' project, MIT-licensed; this fork adds
documentation and an example only, and keeps upstream attribution
intact.
