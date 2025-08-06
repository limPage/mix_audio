import json
from pathlib import Path
from collections import defaultdict

bg_json = Path("D:/mix/merged_dataset.json")
cut_json = Path("D:/mix/cut_dataset.json")

with open(bg_json, "r", encoding="utf-8") as f:
    data = json.load(f)

# sound_comment별 최대 10개만 저장
comment_dict = defaultdict(list)
for item in data:
    comment = item.get("sound_comment", "")
    if len(comment_dict[comment]) < 10:
        comment_dict[comment].append(item)

# cut_list 생성
cut_list = []
for items in comment_dict.values():
    cut_list.extend(items)

# 저장
with open(cut_json, "w", encoding="utf-8") as f:
    json.dump(cut_list, f, ensure_ascii=False, indent=2)

print(f"생성 완료: {cut_json} (총 {len(cut_list)}개)")


from pathlib import Path
import json

voice_dir = Path("D:/mix/white_list")
voice_json = voice_dir / "labeling.json"

with open(voice_json, "r", encoding="utf-8") as f:
    voice_meta = json.load(f)

voice_files = list(voice_dir.glob("*.wav"))

count = 0
for voice_path in voice_files:
    voice_stem = voice_path.stem
    # "audio"가 stem과 일치하는 데이터 찾기
    match = next((item for item in voice_meta if Path(item.get("audio", "")).stem == voice_stem), None)
    if match:
        count += 1

print(f'"audio" 값이 파일 이름(stem)과 일치하는 것의 수: {count}')


from pathlib import Path
import json

voice_dir = Path("D:/mix/white_list")
voice_json = voice_dir / "labeling.json"

with open(voice_json, "r", encoding="utf-8") as f:
    voice_meta = json.load(f)

# labeling.json에 등장하는 모든 audio(stem) 집합 만들기
audio_stems = set(Path(item.get("audio", "")).stem for item in voice_meta if "audio" in item)

voice_files = list(voice_dir.glob("*.wav"))

# labeling.json에 없는 wav의 개수와 목록
not_in_json = []
for voice_path in voice_files:
    if voice_path.stem not in audio_stems:
        not_in_json.append(voice_path.name)

print(f'총 {len(voice_files)}개 파일 중 labeling.json에 포함되지 않은 wav 개수: {len(not_in_json)}')
print(f'포함되지 않은 파일 목록: {not_in_json}')


from pathlib import Path
import json

voice_dir = Path("D:/mix/white_list")
voice_json = voice_dir / "labeling.json"
output_json = voice_dir / "cut_labeling.json"

# 폴더 내 실제 wav 파일 이름 집합 만들기
voice_files = set(p.name for p in voice_dir.glob("*.wav"))

# labeling.json 불러오기
with open(voice_json, "r", encoding="utf-8") as f:
    voice_meta = json.load(f)

# audio값이 실제 파일에 있는 딕셔너리만 선택
filtered = [item for item in voice_meta if "audio" in item and item["audio"] in voice_files]

# 저장
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)

print(f"cut_labeling.json 저장 완료 ({len(filtered)}개)")
