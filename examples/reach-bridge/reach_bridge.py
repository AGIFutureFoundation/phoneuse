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

Environment:

    PHONEUSE_API_URL   default http://127.0.0.1:8765
    PHONEUSE_API_KEY   bearer key; if unset, read from
    PHONEUSE_TOKEN_FILE (default platform/.state/admin-token relative to
    a phoneuse checkout) -- see docs/INTEGRATIONS.md. Prefer a scoped key
    made with platform/create-key.py over the administrator key.

Exit codes: 0 submitted (or dry-run printed), 1 usage/input error,
2 API unreachable or refused.
"""

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
    dry_run = "--dry-run" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
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
