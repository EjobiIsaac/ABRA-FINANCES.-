import os
import json
import hmac
import hashlib
import datetime
from pathlib import Path
from abra.config import LICENSE_FILE, BASE_DIR, SAVVY_SECRET, ensure_dirs

TRIAL_DAYS = 14

def _machine_id():
    # Simple machine ID - based on PC username + computer name
    user = os.environ.get("USERNAME", "user")
    pc = os.environ.get("COMPUTERNAME", "pc")
    raw = f"{user}-{pc}-ABRA".encode()
    return hashlib.sha256(raw).hexdigest()[:12].upper()

def _make_key(machine_id, days):
    msg = f"{machine_id}:{days}".encode()
    sig = hmac.new(SAVVY_SECRET.encode(), msg, hashlib.sha256).hexdigest()[:16].upper()
    return f"ABRA-{machine_id}-{days}-{sig}"

def check_license():
    ensure_dirs()
    # First run - start trial
    if not LICENSE_FILE.exists():
        data = {
            "first_run": datetime.date.today().isoformat(),
            "machine_id": _machine_id(),
            "key": None,
            "days": None
        }
        LICENSE_FILE.write_text(json.dumps(data))
        return {"status": "trial", "days_left": TRIAL_DAYS, "machine_id": _machine_id()}

    data = json.loads(LICENSE_FILE.read_text())
    machine_id = data.get("machine_id", _machine_id())

    # Has a key? Check if key is real
    if data.get("key"):
        days = data.get("days", 0)
        expected = _make_key(machine_id, days)
        if data["key"] == expected:
            return {"status": "licensed", "days": days, "machine_id": machine_id}

    # No key - count trial days
    first = datetime.date.fromisoformat(data["first_run"])
    used = (datetime.date.today() - first).days
    left = TRIAL_DAYS - used

    if left < 0:
        return {"status": "expired", "days_left": 0, "machine_id": machine_id}
    return {"status": "trial", "days_left": left, "machine_id": machine_id}

def activate_key(key):
    # Key format: ABRA-XXXX-365-XXXX
    try:
        parts = key.strip().split("-")
        days = int(parts[2])
        machine_id = _machine_id()
        expected = _make_key(machine_id, days)
        if key.strip() == expected:
            data = json.loads(LICENSE_FILE.read_text())
            data["key"] = key.strip()
            data["days"] = days
            LICENSE_FILE.write_text(json.dumps(data))
            return True
    except:
        pass
    return False
