#!/usr/bin/env python3
"""
NVIDIA Nemotron-Personas-Korea 원본(100만 명)에서 10,000명(100만 명의 1%)을 층화 추출해 personas.jsonl로 저장한다.
제작자용 스크립트. 참가자는 실행하지 않는다.

층화 기준: 연령대(6) x 성별(2) x 권역(5). 각 셀에 원본 비율만큼 배정하되 최소 50명 보장.
"""
import glob, json, os, sys
import pandas as pd

SNAP = os.path.expanduser("~/.cache/huggingface/hub/datasets--nvidia--Nemotron-Personas-Korea/snapshots/*/data/train-*.parquet")
N_TOTAL = 10000
MIN_PER_CELL = 50
SEED = 7

KEEP = ["uuid", "age", "sex", "province", "district", "occupation", "education_level",
        "marital_status", "family_type", "housing_type",
        "persona", "professional_persona", "family_persona",
        "skills_and_expertise", "hobbies_and_interests", "career_goals_and_ambitions"]

REGION = {
    "수도권": ["서울", "경기", "인천"],
    "영남": ["부산", "대구", "울산", "경남", "경북", "경상"],
    "호남": ["광주", "전남", "전북", "전라"],
    "충청": ["대전", "세종", "충남", "충북", "충청"],
    "강원제주": ["강원", "제주"],
}

def region_of(p):
    for k, vs in REGION.items():
        if any(v in str(p) for v in vs):
            return k
    return "기타"

def age_band(a):
    if a < 30: return "19-29"
    if a < 40: return "30-39"
    if a < 50: return "40-49"
    if a < 60: return "50-59"
    if a < 70: return "60-69"
    return "70+"

files = sorted(glob.glob(SNAP))
if not files:
    sys.exit("parquet not found")
frames = [pd.read_parquet(f, columns=KEEP) for f in files]
df = pd.concat(frames, ignore_index=True)
print("원본", len(df), file=sys.stderr)

df["_band"] = df["age"].map(age_band)
df["_region"] = df["province"].map(region_of)
df["_cell"] = df["_band"] + "|" + df["sex"].astype(str) + "|" + df["_region"]

counts = df["_cell"].value_counts()
alloc = (counts / counts.sum() * N_TOTAL).round().astype(int).clip(lower=MIN_PER_CELL)
# 합계를 N_TOTAL에 맞춤 (가장 큰 셀에서 조정)
diff = N_TOTAL - alloc.sum()
alloc[alloc.idxmax()] += diff

parts = []
for cell, n in alloc.items():
    sub = df[df["_cell"] == cell]
    parts.append(sub.sample(n=min(n, len(sub)), random_state=SEED))
out = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)

print("추출", len(out), file=sys.stderr)
print(out["_band"].value_counts().sort_index().to_string(), file=sys.stderr)
print(out["sex"].value_counts().to_string(), file=sys.stderr)
print(out["_region"].value_counts().to_string(), file=sys.stderr)

out = out.drop(columns=["_band", "_region", "_cell"])
with open("personas.jsonl", "w", encoding="utf-8") as f:
    for rec in out.to_dict(orient="records"):
        rec = {k: (int(v) if k == "age" else v) for k, v in rec.items()}
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("saved personas.jsonl", os.path.getsize("personas.jsonl") // 1024, "KB", file=sys.stderr)
