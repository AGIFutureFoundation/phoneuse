#!/usr/bin/env python3
"""Reach -> PhoneUse bridge sketch (stdlib only).

Takes ONE message a human already approved in Reach, as JSON, and submits
it to a locally running PhoneUse API as a prompt task. This is a sketch:
it shows the shape of the handover, not a production daemon.

Input JSON (file path as argv[1], or stdin):

    {
      "recipient": "Ana Ruiz",
      "channel": "Messages",
      "text": "Hi Ana — thank you for the intro last week. ...",
      "device_id": "00008110-..."        // optional; else first device
    }

The one invariant this file exists to demonstrate:

    The approved "text" is embedded in the PhoneUse task VERBATIM.
    The surrounding instruction is a fixed template; the message itself
    is never edited, trimmed, or paraphrased. An assertion checks the
    composed task contains the approved text byte-for-byte before
    anything is sent.

Usage:

    python3 reach_bridge.py approved.json [--dry-run]

Fleet mode (three holdings, one phone each -- see docs/REACH-FLEET.md):

    python3 reach_bridge.py approved.json \
        --config fleet-config.json --holding fellowship [--dry-run]

    The config selects the holding's api_base and device_id. Fleet mode
    adds three checks before submitting: the input must carry
    "approved": true; it must not carry "suppressed": true; and if it
    carries "text_sha256", the hash must match the SHA-256 of "text".
    A holding whose device_id is still the config placeholder is
    refused before any network call. Without --config, behaviour is
    exactly the single-phone sketch above.

Environment:

    PHONEUSE_API_URL   default http://127.0.0.1:8765
    PHONEUSE_API_KEY   bearer key; if unset, read from
    PHONEUSE_TOKEN_FILE (default platform/.state/admin-token relative to
    a phoneuse checkout) -- see docs/INTEGRATIONS.md. Prefer a scoped key
    made with platform/create-key.py over the administrator key.

Exit codes: 0 submitted (or dry-run printed), 1 usage/input error,
2 API unreachable or refused.
"""

import hashlib
import json
import os
import sys
import urllib.request
import urllib.error

API_URL = os.environ.get("PHONEUSE_API_URL", "http://127.0.0.1:8765").rstrip("/")

# Fixed instruction template. {text} is the ONLY variable part, and it is
# filled with the approved message exactly as the human approved it.
TASK_TEMPLATE = (
    "Open {channel}. Find the conversation with {recipient}. "
    "Type the following message exactly as written, character for "
    "character, do not change any word, and send it:\n\n{text}"
)


# The device_id written in fleet-config.example.json. A holding still
# carrying it has no confirmed console device yet, and fleet mode
# refuses to run it.
PLACEHOLDER_DEVICE_ID = "REPLACE_WITH_CONSOLE_DEVICE_ID"


def load_fleet_config(path):
    """Load a fleet config file; return its holdings dict or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            config = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read fleet config {path}: {exc}", file=sys.stderr)
        return None
    holdings = config.get("holdings")
    if not isinstance(holdings, dict) or not holdings:
        print(f"fleet config {path} has no \"holdings\" object", file=sys.stderr)
        return None
    return holdings


def load_key():
    key = os.environ.get("PHONEUSE_API_KEY")
    if key:
        return key.strip()
    token_file = os.environ.get("PHONEUSE_TOKEN_FILE")
    if token_file and os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    return None


def call(method, path, key, body=None):
    data = None
    headers = {"Accept": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API_URL + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.status, json.loads(res.read().decode("utf-8") or "{}")


def main(argv):
    global API_URL
    dry_run = "--dry-run" in argv
    config_path = None
    holding_name = None
    args = []
    tokens = list(argv[1:])
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("--config", "--holding"):
            if i + 1 >= len(tokens):
                print(f"{tok} needs a value", file=sys.stderr)
                return 1
            if tok == "--config":
                config_path = tokens[i + 1]
            else:
                holding_name = tokens[i + 1]
            i += 2
        elif tok.startswith("--"):
            i += 1
        else:
            args.append(tok)
            i += 1
    if len(args) > 1:
        print(__doc__)
        return 1
    raw = open(args[0], "r", encoding="utf-8").read() if args else sys.stdin.read()
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"input is not valid JSON: {exc}", file=sys.stderr)
        return 1

    text = msg.get("text")
    recipient = msg.get("recipient")
    channel = msg.get("channel", "Messages")
    if not isinstance(text, str) or not text:
        print('input JSON needs a non-empty "text" (the approved message)', file=sys.stderr)
        return 1
    if not recipient:
        print('input JSON needs a "recipient"', file=sys.stderr)
        return 1

    task = TASK_TEMPLATE.format(channel=channel, recipient=recipient, text=text)
    # The invariant, checked before anything leaves this process:
    assert text in task and task.endswith(text), "approved text was altered by composition"

    fleet_device_id = None
    if config_path is not None:
        holdings = load_fleet_config(config_path)
        if holdings is None:
            return 1
        if not holding_name:
            holding_name = msg.get("holding")
        if not holding_name or holding_name not in holdings:
            print("fleet mode needs --holding <name> naming one of: "
                  + ", ".join(sorted(holdings)), file=sys.stderr)
            return 1
        entry = holdings[holding_name]
        # Fleet safety checks -- the boundary re-checks Reach's law:
        if msg.get("approved") is not True:
            print("fleet mode refuses: input does not carry \"approved\": true "
                  "(no human approval marker, nothing is submitted)",
                  file=sys.stderr)
            return 1
        if msg.get("suppressed") is True:
            print("fleet mode refuses: input is marked suppressed "
                  "(do-not-contact is law, checked again at the bridge)",
                  file=sys.stderr)
            return 1
        expected_hash = msg.get("text_sha256")
        if expected_hash is not None:
            actual_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if actual_hash != expected_hash:
                print("fleet mode refuses: text_sha256 does not match the text "
                      "(the text to execute is not provably the approved text)",
                      file=sys.stderr)
                return 1
        fleet_device_id = entry.get("device_id")
        if not fleet_device_id or fleet_device_id == PLACEHOLDER_DEVICE_ID:
            print(f"fleet mode refuses: holding \"{holding_name}\" still has "
                  "the placeholder device_id; confirm the console device "
                  "inventory and set the real device_id in your private "
                  "fleet config", file=sys.stderr)
            return 1
        api_base = entry.get("api_base")
        if api_base:
            API_URL = api_base.rstrip("/")
        print(f"fleet mode: holding \"{holding_name}\" "
              f"({entry.get('holding', holding_name)}) -> device "
              f"{fleet_device_id} via {API_URL}")

    key = load_key()

    try:
        status, health = call("GET", "/health", None)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"PhoneUse API not reachable at {API_URL}: {exc}", file=sys.stderr)
        return 2
    if not health.get("ok"):
        print(f"PhoneUse API health check did not return ok: {health}", file=sys.stderr)
        return 2

    device_id = msg.get("device_id")
    if fleet_device_id:
        if device_id and device_id != fleet_device_id:
            print("fleet mode refuses: input device_id "
                  f"{device_id} does not match the config's device "
                  f"{fleet_device_id} for this holding", file=sys.stderr)
            return 1
        device_id = fleet_device_id
    if not device_id:
        if not key:
            print("no API key available (PHONEUSE_API_KEY / PHONEUSE_TOKEN_FILE) "
                  "and no device_id in input; cannot list devices", file=sys.stderr)
            return 1
        _, devices = call("GET", "/api/devices", key)
        found = devices.get("devices") or devices.get("phones") or []
        if not found:
            print("no devices reported by PhoneUse; connect and unlock the iPhone first",
                  file=sys.stderr)
            return 1
        device_id = found[0].get("id") or found[0].get("udid")

    body = {"device_id": device_id, "task": task}
    if dry_run:
        print("DRY RUN — would POST /api/ai/tasks with body:")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        return 0

    if not key:
        print("no API key available; refusing to submit unauthenticated", file=sys.stderr)
        return 1
    try:
        status, result = call("POST", "/api/ai/tasks", key, body)
    except urllib.error.HTTPError as exc:
        print(f"PhoneUse refused the task: HTTP {exc.code} {exc.read().decode('utf-8', 'replace')}",
              file=sys.stderr)
        return 2
    task_id = result.get("id") or result.get("task_id")
    print(f"submitted: task {task_id} on device {device_id} (HTTP {status})")
    print(f"poll with: GET {API_URL}/api/ai/tasks/{task_id}")
    print("Reminder: a submitted task is not a delivered message. "
          "Read the phone screen back before calling it sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
