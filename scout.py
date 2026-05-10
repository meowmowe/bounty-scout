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

def get_program_names(platform, data):
    names = set()
    if platform == "HackerOne":
        for p in data:
            names.add(p.get("handle", ""))
    elif platform == "Bugcrowd":
        for p in data:
            names.add(p.get("code", ""))
    elif platform == "Intigriti":
        for p in data:
            names.add(p.get("handle", p.get("id", "")))
    return names

for platform, url in SOURCES.items():
    # Güncel veriyi çek
    with urllib.request.urlopen(url) as r:
        current_data = json.loads(r.read())
    
    current_names = get_program_names(platform, current_data)
    
    # Önceki listeyi oku
    filename = f"{platform.lower()}_programs.json"
    if os.path.exists(filename):
        with open(filename) as f:
            old_names = set(json.load(f))
        
        # Yeni programları bul
        new_programs = current_names - old_names
        if new_programs:
            msg = f"🆕 <b>{platform}</b>'da yeni program(lar):\n\n"
            for name in new_programs:
                msg += f"• {name}\n"
            send_telegram(msg)
            print(f"Bildirim gönderildi: {new_programs}")
        else:
            print(f"{platform}: yeni program yok")
    else:
        print(f"{platform}: ilk çalışma, liste kaydedildi")
    
    # Güncel listeyi kaydet
    with open(filename, "w") as f:
        json.dump(list(current_names), f)
