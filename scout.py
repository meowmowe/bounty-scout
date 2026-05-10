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
        elif platform == "Bugcrowd":
            name = p.get("code", "")
            targets = set()
            for group in p.get("target_groups", []):
                for t in group.get("targets", []):
                    targets.add(t.get("name", ""))
        elif platform == "Intigriti":
            name = p.get("handle", p.get("id", ""))
            targets = set()
            for domain in p.get("domains", {}).get("content", []):
                targets.add(domain.get("endpoint", ""))
        if name:
            programs[name] = targets
    return programs

for platform, url in SOURCES.items():
    print(f"\n--- {platform} kontrol ediliyor ---")
    
    with urllib.request.urlopen(url) as r:
        current_data = json.loads(r.read())
    
    current_programs = get_programs(platform, current_data)
    filename = f"{platform.lower()}_programs.json"
    
    if os.path.exists(filename):
        with open(filename) as f:
            raw = json.load(f)
            old_programs = {k: set(v) for k, v in raw.items()}
        
        # 1. Yeni programlar
        new_programs = set(current_programs.keys()) - set(old_programs.keys())
        for name in new_programs:
            msg = f"🆕 <b>Yeni Program — {platform}</b>\n\n<b>{name}</b>"
            send_telegram(msg)
            print(f"Yeni program: {name}")
        
        # 2. Scope değişiklikleri
        for name, current_targets in current_programs.items():
            if name not in old_programs:
                continue
            old_targets = old_programs[name]
            
            added = current_targets - old_targets
            removed = old_targets - current_targets
            
            if added or removed:
                msg = f"📝 <b>Scope Değişti — {platform}</b>\n<b>{name}</b>\n\n"
                if added:
                    msg += "✅ <b>Eklendi:</b>\n" + "\n".join(f"• {t}" for t in added if t) + "\n\n"
                if removed:
                    msg += "❌ <b>Kaldırıldı:</b>\n" + "\n".join(f"• {t}" for t in removed if t)
                send_telegram(msg)
                print(f"Scope değişti: {name}")
    else:
        print(f"İlk çalışma, liste kaydedildi")
    
    # Güncel listeyi kaydet
    with open(filename, "w") as f:
        json.dump({k: list(v) for k, v in current_programs.items()}, f)
