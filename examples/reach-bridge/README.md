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
