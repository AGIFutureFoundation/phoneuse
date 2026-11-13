# examples/reach-bridge

A small, stdlib-only Python sketch of the Reach → PhoneUse handover:
it takes one message a human approved in Reach (as JSON) and submits it
to a locally running PhoneUse API as a prompt task.

```sh
cat > approved.json <<'EOF'
{"recipient": "Ana Ruiz", "channel": "Messages",
 "text": "Hi Ana — thank you for the intro last week. Coffee Thursday?",
 "device_id": "YOUR_DEVICE_UDID"}
EOF

# with a scoped key (see docs/INTEGRATIONS.md for create-key.py):
PHONEUSE_API_KEY="<scoped key>" \
  python3 reach_bridge.py approved.json --dry-run   # prints the exact request
python3 reach_bridge.py approved.json               # submits it
```

Key handling follows upstream `docs/INTEGRATIONS.md`: prefer a scoped,
expiring key from `platform/create-key.py` (one phone, printed once)
over the administrator key in `platform/.state/admin-token`.

The sketch's one hard rule, asserted in code before anything is sent:
the approved `text` reaches PhoneUse **byte-for-byte** — embedded
verbatim in a fixed instruction template, never edited or paraphrased.
See [`docs/REACH.md`](../../docs/REACH.md) for the full integration
story and safety posture.

## Fleet mode

One bridge sketch can also serve the operator's fleet — three PhoneUse
console accounts, one per holding, one phone each (the full picture is
in [`docs/REACH-FLEET.md`](../../docs/REACH-FLEET.md)). A fleet config
tells the bridge which holding an approved card belongs to; the bridge
routes it to that holding's phone and no other.

```sh
cp fleet-config.example.json fleet-config.json   # private copy, never committed
# edit fleet-config.json: replace each REPLACE_WITH_CONSOLE_DEVICE_ID
# with the console device ID of that holding's phone

PHONEUSE_API_KEY="<scoped key for the Fellowship phone>" \
  python3 reach_bridge.py approved.json \
    --config fleet-config.json --holding fellowship
```

How routing works:

- `--config <path>` loads the fleet config; `--holding <name>` selects
  one entry (`fellowship`, `foundation`, or `builderspace`). Without
  `--config`, the sketch behaves exactly as the single-phone version
  above — nothing about that path changes.
- The selected entry supplies the `api_base` the bridge submits to and
  the `device_id` the task runs on. Routing is fixed by the holding:
  an item never falls back to another holding's phone.
- If the input JSON also carries a `device_id` and it differs from the
  config's, the bridge refuses — a disagreement about which phone
  should run is a stop, not a coin flip.
- If the selected holding's `device_id` is still the
  `REPLACE_WITH_CONSOLE_DEVICE_ID` placeholder, the bridge refuses to
  run, before any network call. A fleet with unconfirmed device
  inventory submits nothing.
- Keys never come from the config — there is no key field in it. Set
  `PHONEUSE_API_KEY` to the scoped key for the selected holding's
  phone, as in single-phone mode.

Before submitting, fleet mode runs three safety checks on the input
(the single-phone path is unchanged and does not require them):

1. **Approved flag present.** The input must carry `"approved": true` —
   the marker that a human approved this exact card in Reach. Missing
   or false, the bridge refuses.
2. **Suppression flag absent.** If the input carries
   `"suppressed": true`, the bridge refuses. Reach checks suppression
   before drafting; this is the same law re-checked at the boundary,
   so a suppressed contact's item cannot execute even if it is handed
   to the bridge by mistake.
3. **Text hash matches the approved card.** If the input carries
   `"text_sha256"`, the bridge recomputes the SHA-256 of `text` and
   refuses on any mismatch — the text that would execute is provably
   the text that was approved. The byte-for-byte composition assertion
   from single-phone mode still runs on top of this.
