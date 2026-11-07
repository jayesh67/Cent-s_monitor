import os, json, requests
from bs4 import BeautifulSoup

URL = "https://testcisia.it/calendario.php?tolc=cents&l=gb&lingua=inglese"
STATE = "state.json"
FMT = os.environ.get("FORMAT_FILTER", "").strip().lower()

def notify(msg):
    r = requests.post(
        f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["TG_CHAT"], "text": msg[:4000]},
        timeout=20,
    )
    r.raise_for_status()

resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

rows = {}
for tr in soup.select("table tr"):
    tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
    if len(tds) < 8:
        continue
    fmt, uni, region, city, deadline, seats, state, date = tds[:8]
    if not date.endswith("/12/2026"):      # December only
        continue
    if FMT and FMT not in fmt.lower():
        continue
    rows[f"{fmt} | {uni} | {date}"] = {"deadline": deadline, "state": state}

old = json.load(open(STATE)) if os.path.exists(STATE) else None
if old is None:
    print("First run, saving baseline:", len(rows), "rows")
else:
    msgs = []
    for k, v in rows.items():
        if k not in old:
            msgs.append(f"NEW: {k}\n   deadline {v['deadline']}, {v['state']}")
        elif old[k]["state"] != v["state"]:
            msgs.append(f"CHANGED: {k}\n   {old[k]['state']} -> {v['state']}")
    for k in old:
        if k not in rows:
            msgs.append(f"REMOVED: {k}")
    if msgs:
        notify("CEnT-S December update\n\n" + "\n\n".join(msgs) + f"\n\n{URL}")
    else:
        print("No change.")

json.dump(rows, open(STATE, "w"), ensure_ascii=False, indent=1, sort_keys=True)






