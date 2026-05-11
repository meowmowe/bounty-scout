import json
import urllib.request
import os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SOURCES = {
    "HackerOne": "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/hackerone_data.json",
    "Bugcrowd": "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json",
    "Intigriti": "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/intigriti_data.json",
}

def send_telegram(msg):
    msg = msg[:4000]
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def get_programs(platform, data):
    programs = {}
    for p in data:
        if platform == "HackerOne":
            name = p.get("handle", "")
            targets = set()
            for t in p.get("targets", {}).get("in_scope", []):
                targets.add(t.get("asset_identifier", ""))
            extra = {"url": f"https://hackerone.com/{name}"}
        elif platform == "Bugcrowd":
            name = p.get("code", "")
            targets = set()
            for group in p.get("target_groups", []):
                for t in group.get("targets", []):
                    targets.add(t.get("name", ""))
            extra = {"url": f"https://bugcrowd.com/{name}"}
        elif platform == "Intigriti":
            name = p.get("handle", p.get("id", p.get("name", "")))
            targets = set()
            for domain in p.get("domains", {}).get("content", []):
                endpoint = domain.get("endpoint", "")
                if endpoint:
                    targets.add(endpoint)
            extra = {
                "url": p.get("url", f"https://app.intigriti.com/programs/{name}"),
                "min_bounty": p.get("min_bounty", ""),
                "max_bounty": p.get("max_bounty", ""),
            }
            # Debug: ilk programin tum keylerini yazdir
            if not programs:
                print(f"Intigriti ornek keys: {list(p.keys())}")
        else:
            name = ""
            targets = set()
            extra = {}

        if name:
            programs[name] = {"targets": targets, "extra": extra}
    return programs

def format_new_program_msg(platform, name, info):
    extra = info.get("extra", {})
    targets = info.get("targets", set())
    msg = f"🆕 <b>Yeni Program — {platform}</b>\n\n<b>{name}</b>\n"
    url = extra.get("url", "")
    if url:
        msg += f"🔗 {url}\n"
    min_b = extra.get("min_bounty", "")
    max_b = extra.get("max_bounty", "")
    if min_b or max_b:
        msg += f"💰 Bounty: {min_b} - {max_b}\n"
    if targets:
        msg += f"\n🎯 <b>Scope ({len(targets)}):</b>\n"
        msg += "\n".join(f"• {t}" for t in list(targets)[:15] if t)
    return msg

for platform, url in SOURCES.items():
    print(f"\n--- {platform} kontrol ediliyor ---")

    with urllib.request.urlopen(url) as r:
        current_data = json.loads(r.read())

    current_programs = get_programs(platform, current_data)
    filename = f"{platform.lower()}_programs.json"

    if os.path.exists(filename):
        with open(filename) as f:
            raw = json.load(f)

        if isinstance(raw, list):
            old_programs = {name: {"targets": set(), "extra": {}} for name in raw}
        else:
            old_programs = {}
            for k, v in raw.items():
                if isinstance(v, dict):
                    old_programs[k] = {"targets": set(v.get("targets", [])), "extra": v.get("extra", {})}
                else:
                    old_programs[k] = {"targets": set(v), "extra": {}}

        # Yeni programlar
        new_programs = set(current_programs.keys()) - set(old_programs.keys())
        for name in new_programs:
            msg = format_new_program_msg(platform, name, current_programs[name])
            send_telegram(msg)
            print(f"Yeni program: {name}")

        # Scope degisiklikleri
        if not isinstance(raw, list):
            for name, info in current_programs.items():
                if name not in old_programs:
                    continue
                current_targets = info["targets"]
                old_targets = old_programs[name]["targets"]
                added = current_targets - old_targets
                removed = old_targets - current_targets
                if added or removed:
                    extra = info.get("extra", {})
                    msg = f"📝 <b>Scope Değişti — {platform}</b>\n<b>{name}</b>\n"
                    if extra.get("url"):
                        msg += f"🔗 {extra['url']}\n"
                    if added:
                        items = "\n".join(f"• {t}" for t in list(added)[:15] if t)
                        msg += f"\n✅ <b>Eklendi:</b>\n{items}\n"
                    if removed:
                        items = "\n".join(f"• {t}" for t in list(removed)[:15] if t)
                        msg += f"\n❌ <b>Kaldırıldı:</b>\n{items}"
                    send_telegram(msg)
                    print(f"Scope degisti: {name}")
    else:
        print(f"İlk calisma, liste kaydedildi")

    # Kaydet
    with open(filename, "w") as f:
        save_data = {}
        for k, v in current_programs.items():
            save_data[k] = {"targets": list(v["targets"]), "extra": v["extra"]}
        json.dump(save_data, f)
