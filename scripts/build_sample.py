#!/usr/bin/env python3
"""
원본 parquet(100만 명) -> personas.jsonl (대체용 표본). 제작자용.

두 가지를 합친다.
1) 직업 커버: 2,120개 직업마다 최대 4명. 방송작가, 임업 종사자처럼 드문 직업이 사라지지 않게 한다.
2) 인구 비례: 연령대(6) x 성별(2) x 권역(5)로 나눠 원본 비율대로 6,000명, 각 칸 최소 30명.
겹치는 사람은 한 번만 넣는다.
"""
import glob, json, os, sys
import pandas as pd

SNAP = os.path.expanduser("~/.cache/huggingface/hub/datasets--nvidia--Nemotron-Personas-Korea/snapshots/*/data/train-*.parquet")
PER_OCC = 4
N_DEMO = 6000
MIN_PER_CELL = 30
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
df = pd.concat([pd.read_parquet(f, columns=KEEP) for f in files], ignore_index=True)
print("원본", len(df), file=sys.stderr)

# 1) 직업 커버
idx = []
for _, g in df.groupby("occupation", dropna=True, observed=True):
    idx.extend(g.sample(n=min(PER_OCC, len(g)), random_state=SEED).index.tolist())
occ = df.loc[idx]
print("직업 커버", len(occ), "명 /", df["occupation"].nunique(), "직업", file=sys.stderr)

# 2) 인구 비례
d = df.copy()
d["_cell"] = d["age"].map(age_band) + "|" + d["sex"].astype(str) + "|" + d["province"].map(region_of)
counts = d["_cell"].value_counts()
alloc = (counts / counts.sum() * N_DEMO).round().astype(int).clip(lower=MIN_PER_CELL)
parts = [d[d["_cell"] == cell].sample(n=min(n, int((d["_cell"] == cell).sum())), random_state=SEED)
         for cell, n in alloc.items()]
demo = pd.concat(parts).drop(columns=["_cell"])
print("인구 비례", len(demo), file=sys.stderr)

out = pd.concat([occ, demo]).drop_duplicates(subset=["uuid"]).sample(frac=1, random_state=SEED).reset_index(drop=True)
print("합계", len(out), file=sys.stderr)
print(out["occupation"].nunique(), "직업 포함", file=sys.stderr)

with open("personas.jsonl", "w", encoding="utf-8") as f:
    for rec in out.to_dict(orient="records"):
        rec["age"] = int(rec["age"])
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("saved personas.jsonl", os.path.getsize("personas.jsonl") // 1024 // 1024, "MB", file=sys.stderr)
