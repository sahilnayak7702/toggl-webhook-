
import time
import requests
from datetime import datetime, timezone, timedelta

# ====== CONFIG ======
DISCORD_WEBHOOK_URL = "********"
TOGGL_API_TOKEN = "*****"
CHECK_INTERVAL_SECONDS = 5

# Timezone: Japan Standard Time (UTC+9)
JST = timezone(timedelta(hours=9))

# Track last state to avoid duplicate notifications
last_entry_id = None
last_running_status = None  # True if running (stop is None), False if stopped

# ====== HELPERS ======
def iso_to_jst_pretty(iso_str: str) -> str:
    """Convert ISO8601 string to JST and format like '30 August, 2025 15:50'."""
    dt_utc = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    dt_jst = dt_utc.astimezone(JST)
    return dt_jst.strftime("%d %B, %Y %H:%M")

def send_to_discord(message: str) -> None:
    resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    if resp.status_code != 204:
        print("Discord send failed:", resp.status_code, resp.text)

def get_latest_time_entry():
    """Fetch the most recently updated time entry (by 'at' or 'start')."""
    url = "https://api.track.toggl.com/api/v9/me/time_entries"
    r = requests.get(url, auth=(TOGGL_API_TOKEN, "api_token"))
    if r.status_code != 200:
        print("Toggl entries fetch error:", r.status_code, r.text)
        return None
    entries = r.json() or []
    if not entries:
        return None
    # Pick the entry with the latest update time
    return max(entries, key=lambda e: e.get("at", e.get("start", "")))

def get_users_map():
    """Return dict of {user_id: fullname or name} for all workspaces accessible by this token."""
    users_map = {}
    # Get workspaces for this user
    ws_resp = requests.get("https://api.track.toggl.com/api/v9/me/workspaces",
                           auth=(TOGGL_API_TOKEN, "api_token"))
    if ws_resp.status_code != 200:
        print("Workspace fetch error:", ws_resp.status_code, ws_resp.text)
        return users_map

    for ws in ws_resp.json() or []:
        ws_id = ws.get("id")
        if not ws_id:
            continue
        u_resp = requests.get(f"https://api.track.toggl.com/api/v9/workspaces/{ws_id}/users",
                              auth=(TOGGL_API_TOKEN, "api_token"))
        if u_resp.status_code != 200:
            print(f"Users fetch error for workspace {ws_id}:", u_resp.status_code, u_resp.text)
            continue
        for u in u_resp.json() or []:
            uid = u.get("id")
            name = u.get("fullname") or u.get("name") or u.get("email") or "Unknown User"
            if uid:
                users_map[uid] = name
    return users_map

def format_message(entry, users_map):
    """Build the Discord message with real username and JST time."""
    description = entry.get("description") or "No task name"
    user_id = entry.get("user_id")
    user_name = users_map.get(user_id, "Unknown User")

    if entry.get("stop") is None:
        # Started
        start_ts = iso_to_jst_pretty(entry["start"])
        return f"▶️ {user_name} started '{description}' Task at `{start_ts}`"
    else:
        # Ended
        stop_ts = iso_to_jst_pretty(entry["stop"])
        return f"⏹️ {user_name} ended '{description}' at `{stop_ts}`"

# ====== MAIN LOOP ======
if __name__ == "__main__":
    users_map = get_users_map()

    while True:
        entry = get_latest_time_entry()
        if entry:
            entry_id = entry.get("id")
            is_running = entry.get("stop") is None

            # If we see a new entry OR the running/stopped status changed → notify
            if entry_id != last_entry_id or is_running != last_running_status:
                # Refresh users_map if we don't know this user yet
                if entry.get("user_id") not in users_map:
                    users_map = get_users_map()

                msg = format_message(entry, users_map)
                send_to_discord(msg)
                print("Sent:", msg)

                last_entry_id = entry_id
                last_running_status = is_running
        else:
            print("No entries found.")

        time.sleep(CHECK_INTERVAL_SECONDS)
