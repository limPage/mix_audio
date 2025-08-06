from pydub import AudioSegment
from pathlib import Path
import json
import os

# 폴더 및 파일 경로 설정
base_dir = Path("Y:/AI-DATA/raw-data")
voice_dir = base_dir / "voice_hjict/white_list"
bg_dir = base_dir / "work/극한환경소음 10초/audio_clips"
output_dir = base_dir / "mix_sounds"
output_dir.mkdir(exist_ok=True, parents=True)
voice_json = base_dir / "cut_labeling.json"
bg_json = base_dir / "cut_dataset.json"
progress_json = base_dir / "progress.json"
result_json = base_dir / "mix_result.json"

MAX_VOICE_LENGTH_MS = 10 * 1000
TRIM_LEADING_BG_MS = 1000
MIN_OUTPUT_LENGTH_MS = 3000
SAVE_INTERVAL = 1000  # 1000개마다 저장

# JSON 로딩
with open(voice_json, "r", encoding="utf-8") as f:
    voice_meta = json.load(f)
with open(bg_json, "r", encoding="utf-8") as f:
    bg_meta = json.load(f)

voice_dict = {v["audio"]: v for v in voice_meta if "audio" in v}
bg_dict = {Path(b["audio"]).name: b for b in bg_meta if "audio" in b}

# 이미 처리된 리스트 로드 (voice_audio, bg_audio로 키를 만듦)
def load_progress():
    if progress_json.exists():
        with open(progress_json, "r", encoding="utf-8") as f:
            progress = json.load(f)
        done_set = set((item["audio"], item.get("bg_name", "")) for item in progress)
    else:
        progress = []
        done_set = set()
    return progress, done_set

# mix_result.json에서 no 갱신
def load_result_idx():
    if result_json.exists():
        with open(result_json, "r", encoding="utf-8") as f:
            result = json.load(f)
        if result:
            return len(result) + 1
    return 1

progress, done_set = load_progress()
result_idx = load_result_idx()

voice_files = list(voice_dir.glob("*.wav"))
# cut_dataset.json 기준으로 실제 존재하는 bg 파일만 사용
bg_files_set = set(Path(b["audio"]).name for b in bg_meta if "audio" in b)
bg_files = [bg_dir / f for f in bg_files_set if (bg_dir / f).exists()]

# mix_result.json도 실시간 누적
if result_json.exists():
    with open(result_json, "r", encoding="utf-8") as f:
        mix_result = json.load(f)
else:
    mix_result = []

cnt = 0

for voice_path in voice_files:
    voice = AudioSegment.from_wav(voice_path)
    voice_len = len(voice)
    if voice_len > MAX_VOICE_LENGTH_MS:
        print(f"⏭️  {voice_path.name} 스킵됨 (길이 {voice_len}ms > 10초)")
        continue

    vmeta = voice_dict.get(voice_path.name)
    if not vmeta:
        print(f"⏭️  {voice_path.name}에 labeling.json 정보 없음")
        continue

    for i, bg_path in enumerate(bg_files):
        progress_key = (voice_path.name, bg_path.name)
        if progress_key in done_set:
            continue

        bg = AudioSegment.from_wav(bg_path)
        if len(bg) <= TRIM_LEADING_BG_MS:
            print(f"⏭️  {bg_path.name} 스킵됨 (길이 {len(bg)}ms <= 1초)")
            continue

        bg = bg[TRIM_LEADING_BG_MS:]
        target_len = max(voice_len, MIN_OUTPUT_LENGTH_MS)
        if len(bg) < target_len:
            repeat_count = (target_len // len(bg)) + 1
            bg = (bg * repeat_count)
        bg = bg[:target_len]

        mixed = (bg - 10).overlay(voice)
        output_name = f"mix_{voice_path.stem}_[{i+1}].wav"
        output_path = output_dir / output_name
        mixed.export(output_path, format="wav")
        print(f"✅ 저장 완료: {output_name}", end="\r")

        # bgmeta는 파일명만으로 정확히 매칭
        bgmeta = bg_dict.get(bg_path.name, None)

        info = {
            "no": str(result_idx),
            "transcripts": vmeta.get("transcripts", ""),
            "audio": output_name,
            "bg_name": bg_path.name,
            "label": vmeta.get("label", ""),
            "sound_category": bgmeta.get("sound_category", "") if bgmeta else "",
            "sound_subcategory": bgmeta.get("sound_subcategory", "") if bgmeta else "",
            "sound_comment": bgmeta.get("sound_comment", "") if bgmeta else ""
        }
        mix_result.append(info)
        progress.append(info)
        result_idx += 1
        cnt += 1

        # 1000개마다 저장
        if cnt % SAVE_INTERVAL == 0:
            with open(result_json, "w", encoding="utf-8") as f:
                json.dump(mix_result, f, ensure_ascii=False, indent=2)
            with open(progress_json, "w", encoding="utf-8") as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
            print(f"\n🟢 {cnt}개 저장! 중간 저장 완료.")

# 마지막 남은 것도 저장
with open(result_json, "w", encoding="utf-8") as f:
    json.dump(mix_result, f, ensure_ascii=False, indent=2)
with open(progress_json, "w", encoding="utf-8") as f:
    json.dump(progress, f, ensure_ascii=False, indent=2)

print(f"\n✨ mix_result.json 저장 완료 ({len(mix_result)}개) → {result_json}")
print(f"✨ progress.json 저장 완료 ({len(progress)}개) → {progress_json}")
