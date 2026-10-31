"""영상 '읽기': 유튜브·인스타 릴스·틱톡 주소 → 음성만 받기(yt-dlp) → 글로 바꾸기(faster-whisper).
사용: python watch.py <url> [--model small|base|medium] [--lang ko|en]
결과: ~/.klik/watch/<id>.json {url, title, uploader, caption, transcript, segments}  + 콘솔에 캡션과 전체 자막 인쇄
준비: python -m pip install --user yt-dlp faster-whisper av numpy   (ffmpeg 필요 없음)
"""
import sys, json, re, pathlib, argparse, tempfile

ap = argparse.ArgumentParser()
ap.add_argument("url"); ap.add_argument("--model", default="small"); ap.add_argument("--lang", default="ko")
a = ap.parse_args()

out = pathlib.Path.home() / ".klik" / "watch"; out.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(tempfile.gettempdir()) / "klik-watch"; tmp.mkdir(exist_ok=True)

try:
    import yt_dlp, av, numpy as np
    from faster_whisper import WhisperModel
except ModuleNotFoundError as e:
    sys.exit(f"준비물이 없습니다 ({e.name}). 먼저 실행:  python -m pip install --user --upgrade yt-dlp faster-whisper av numpy")

opts = {"format": "bestaudio[ext=m4a]/bestaudio/best", "outtmpl": str(tmp / "%(id)s.%(ext)s"), "quiet": True, "noplaylist": True, "no_warnings": True}
with yt_dlp.YoutubeDL(opts) as y:
    info = y.extract_info(a.url, download=True)
    path = pathlib.Path(y.prepare_filename(info))
vid = info.get("id") or "video"
safe = re.sub(r"[^A-Za-z0-9_-]", "_", vid)
cache = out / f"{safe}.json"
if cache.exists():
    rec = json.loads(cache.read_text(encoding="utf-8"))
    print(f"(이미 읽은 영상, 저장된 결과 사용) {rec.get('uploader')} · {rec.get('title','')[:60]}")
    print("=== 캡션\n" + (rec.get("caption") or "(없음)"))
    print("=== 자막\n" + (rec.get("transcript") or "(말소리 없음)"))
    sys.exit(0)
if not path.exists():
    c = list(tmp.glob(f"{vid}.*"))
    if not c: sys.exit("다운로드 실패: 받은 파일이 없습니다. 비공개 영상이거나 주소가 잘못됐을 수 있어요.")
    path = c[0]
print(f"받음: {info.get('uploader')} · {info.get('title','')[:60]} ({path.stat().st_size//1024}KB)")

def load_audio(p, sr=16000):
    # faster-whisper 내장 디코더가 최신 PyAV와 안 맞을 수 있어 직접 디코딩: 16kHz 모노 float32
    with av.open(str(p)) as c:
        stream = next(s for s in c.streams if s.type == "audio")
        res = av.AudioResampler(format="s16", layout="mono", rate=sr)
        chunks = []
        for frame in c.decode(stream):
            for f in res.resample(frame): chunks.append(f.to_ndarray().reshape(-1))
        for f in res.resample(None): chunks.append(f.to_ndarray().reshape(-1))
    return (np.concatenate(chunks).astype(np.float32) / 32768.0) if chunks else np.zeros(0, np.float32)

audio = load_audio(path)
print(f"음성 {len(audio)/16000:.1f}초 → 글로 바꾸는 중 (모델 {a.model}, 처음이면 모델 내려받기 1~2분)")
model = WhisperModel(a.model, device="cpu", compute_type="int8")
segments, meta = model.transcribe(audio, language=a.lang, vad_filter=True)
segs = [{"start": round(s.start, 1), "end": round(s.end, 1), "text": s.text.strip()} for s in segments]
text = " ".join(s["text"] for s in segs)
rec = {"url": a.url, "id": vid, "title": info.get("title"), "uploader": info.get("uploader"), "caption": info.get("description"),
       "duration": info.get("duration"), "language": meta.language, "transcript": text, "segments": segs}
cache.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
try: path.unlink()
except OSError: pass
print("=== 캡션\n" + (rec["caption"] or "(없음)"))
print(f"=== 자막 ({len(segs)}문장, {meta.language}) → {cache}\n" + (text or "(말소리 없음)"))
