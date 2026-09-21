# Fast path: fetch YouTube's own auto-captions (no audio, no CPU). Usage: python captions.py
# Reads order.txt, writes out/<id>.txt ("[m:ss] text"), skips existing, logs to out/progress.log
import os, sys, json, time, urllib.request
import yt_dlp

os.makedirs("out", exist_ok=True)

def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open("out/progress.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def fetch(url, tries=6):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except Exception as e:
            time.sleep(15 * (i + 1))
    raise RuntimeError("caption download failed (rate limit?)")

items = [l.strip().split("|") for l in open("order.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
ydl = yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True})
for date, vid in items:
    final = f"out/{vid}.txt"
    if os.path.exists(final):
        continue
    try:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        caps = info.get("automatic_captions") or {}
        origs = [k for k in caps if k.endswith("-orig")]
        lang = next((k for k in ("ur-orig", "hi-orig", "en-orig") if k in origs), origs[0] if origs else None)
        if not lang:
            log(f"NOCAP {date} {vid} ({info.get('title')}) -> needs whisper")
            continue
        url = next(f["url"] for f in caps[lang] if f["ext"] == "json3")
        data = json.loads(fetch(url))
        tmp = final + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"# {date} | {info.get('title')} | {info.get('duration')}s | https://www.youtube.com/watch?v={vid} | captions={lang}\n")
            for ev in data.get("events", []):
                text = "".join(s.get("utf8", "") for s in ev.get("segs", [])).replace("\n", " ").strip()
                if text:
                    t = ev.get("tStartMs", 0) // 1000
                    f.write("[%d:%02d] %s\n" % (t // 60, t % 60, text))
        os.replace(tmp, final)
        log(f"DONE  {date} {vid} ({info.get('title')}) [{lang}]")
        time.sleep(4)
    except Exception as e:
        log(f"FAIL  {date} {vid}: {e}")
log("CAPTIONS PASS FINISHED")
