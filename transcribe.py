# Usage: python transcribe.py "<youtube_url>" [model=small] [language=auto]
# Setup once:  pip install yt-dlp faster-whisper   (free, CPU only, no ffmpeg needed)
# Output: out/<video_id>.txt  ("[m:ss] text" per line)
import sys, os, re
import yt_dlp
from faster_whisper import WhisperModel

url = sys.argv[1]
model_name = sys.argv[2] if len(sys.argv) > 2 else "small"   # small = fast, medium = more accurate/slower
lang = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "auto" else None  # e.g. ur, en, hi
os.makedirs("out", exist_ok=True)
vid = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([\w-]{11})", url).group(1)

# 1) download only the audio from YouTube
opts = {"format": "bestaudio[ext=m4a]/bestaudio", "outtmpl": f"out/{vid}.%(ext)s", "quiet": True}
with yt_dlp.YoutubeDL(opts) as y:
    info = y.extract_info(url, download=True)
    audio = y.prepare_filename(info)
print("audio saved:", audio)

# 2) speech-to-text on this computer
m = WhisperModel(model_name, device="cpu", compute_type="int8")
segs, info = m.transcribe(audio, language=lang, vad_filter=True, beam_size=1)
print("detected language:", info.language)
with open(f"out/{vid}.txt", "w", encoding="utf-8") as f:
    for s in segs:
        f.write("[%d:%02d] %s\n" % (int(s.start) // 60, int(s.start) % 60, s.text.strip()))
        f.flush()
print("done -> out/%s.txt" % vid)
