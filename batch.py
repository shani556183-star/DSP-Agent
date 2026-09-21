# Sequential batch: python batch.py [model=medium] [language=ur]
# Reads order.txt, writes out/<id>.txt (atomic), skips finished ones, logs to out/progress.log
import sys, os, time, glob
import yt_dlp
from faster_whisper import WhisperModel

model_name = sys.argv[1] if len(sys.argv) > 1 else "medium"
lang = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "auto" else None
os.makedirs("out", exist_ok=True)

def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open("out/progress.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

items = [l.strip().split("|") for l in open("order.txt", encoding="utf-8") if l.strip() and not l.startswith("#")]
model = WhisperModel(model_name, device="cpu", compute_type="int8")
for date, vid in items:
    final = f"out/{vid}.txt"
    if os.path.exists(final):
        continue
    try:
        log(f"START {date} {vid}")
        opts = {"format": "bestaudio[ext=m4a]/bestaudio", "outtmpl": f"out/{vid}.%(ext)s", "quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(opts) as y:
            info = y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
            audio = y.prepare_filename(info)
            title, dur = info.get("title"), info.get("duration")
        segs, ti = model.transcribe(audio, language=lang, vad_filter=True, beam_size=1)
        tmp = final + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"# {date} | {title} | {dur}s | https://www.youtube.com/watch?v={vid}\n")
            for s in segs:
                f.write("[%d:%02d] %s\n" % (int(s.start) // 60, int(s.start) % 60, s.text.strip()))
                f.flush()
        os.replace(tmp, final)
        os.remove(audio)
        log(f"DONE  {date} {vid} ({title})")
    except Exception as e:
        log(f"FAIL  {date} {vid}: {e}")
log("ALL FINISHED")
