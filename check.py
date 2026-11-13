import os, json, requests
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

URL = "https://testcisia.it/calendario.php?tolc=cents&l=gb&lingua=inglese"
STATE = "state.json"

def env_list(name):
    return [x.strip().lower() for x in os.environ.get(name, "").split(",") if x.strip()]

FORMATS = env_list("FORMAT_FILTER")
UNIS = env_list("UNI_FILTER")
DATE_PART = os.environ.get("DATE_FILTER", "").strip()

def notify(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["TG_CHAT"], "text": msg[:4000]},
        timeout=20,
    )
    r.raise_for_status()

def is_open(state):
    s = state.lower()
    return "available" in s and "not longer" not in s

def describe(r):
    flag = "🟢 BOOKABLE NOW" if is_open(r["state"]) else "🔴 CLOSED / SOLD OUT"
    return (f"{flag}\n"
            f"Format: {r['format']}\n"
            f"University: {r['uni']} ({r['city']})\n"
            f"Test date: {r['date']}\n"
            f"Booking deadline: {r['deadline']} (2 PM CET = 6:30 PM IST)\n"
            f"Seats: {r.get('seats', '-')}\n"
            f"Status: {r['state']}")

resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

rows = {}
for tr in soup.select("table tr"):
    tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
    if len(tds) < 8:
        continue
    fmt, uni, region, city, deadline, seats, state, date = tds[:8]
    if FORMATS and not any(f in fmt.lower() for f in FORMATS):
        continue
    if UNIS and not any(u in uni.lower() for u in UNIS):
        continue
    if DATE_PART and DATE_PART not in date:
        continue
    rows[f"{fmt} | {uni} | {date}"] = {
        "format": fmt, "uni": uni, "city": city, "date": date,
        "deadline": deadline, "state": state, "seats": seats,
    }

saved = {k: {x: v[x] for x in ("format", "uni", "city", "date", "deadline", "state")}
         for k, v in rows.items()}

old = json.load(open(STATE)) if os.path.exists(STATE) else None
if old is None:
    print("First run, saving baseline:", len(rows), "rows")
else:
    msgs = []
    for k, v in rows.items():
        if k not in old:
            msgs.append("NEW DATE\n" + describe(v))
        elif old[k]["state"] != v["state"]:
            msgs.append(f"STATUS CHANGED: {old[k]['state']} -> {v['state']}\n" + describe(v))
    for k in old:
        if k not in rows:
            msgs.append("REMOVED\n" + describe(old[k]))
    if msgs:
        ist = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %H:%M IST")
        notify("CEnT-S calendar update\n\n" + "\n\n".join(msgs) + f"\n\nChecked at {ist}\n{URL}")
    else:
        print("No change.")

json.dump(saved, open(STATE, "w"), ensure_ascii=False,

