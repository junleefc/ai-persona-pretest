#!/usr/bin/env python3
"""
원본 parquet(100만 명) -> index.tsv.gz
컬럼: 행번호, 나이, 성별, 시도, 시군구, 직업, 혼인, 가구형태, 상황태그

상황태그는 직업으로 안 잡히는 타깃(수험생, 취업준비, 육아 등)을 찾기 위해
프로필 본문에서 정규식으로 뽑아 둔 것이다. 제작자용 스크립트.
"""
import glob, gzip, os, sys
import pandas as pd

TAGS = {
    "수험생": "수험|고시|시험 준비|시험을 준비|공무원 시험|자격증 취득|편입",
    "취업준비": "취업 준비|취업준비|구직|이직 준비|재취업",
    "창업준비": "창업을 준비|창업 준비|창업을 꿈|자기 사업|1인 기업|개업을 준비",
    "퇴사은퇴": "퇴사|은퇴|명예퇴직|정년|제2의 인생|인생 2막",
    "육아": "육아|아이를 키우|자녀를 키우|어린이집|유치원|초등학생 자녀",
    "학부모": "학부모|입시|학원|자녀의 교육|사교육",
    "돌봄간병": "간병|부모님을 돌보|요양|치매",
    "건강관리": "다이어트|체중|당뇨|고혈압|건강 관리|재활",
    "반려동물": "반려견|반려묘|반려동물|강아지|고양이를 키",
    "재테크": "재테크|투자|주식|부동산|내 집 마련|저축",
    "귀농귀촌": "귀농|귀촌|농사|텃밭|농장",
    "프리랜서": "프리랜서|외주|1인 사업|자영업|가게를 운영",
    "1인가구": "혼자 살|1인 가구|자취",
    "외국어유학": "외국어|영어 공부|유학|어학연수|토익",
    "콘텐츠창작": "블로그|유튜브|인스타그램|콘텐츠 제작|글을 쓰",
    "결혼준비": "결혼을 준비|신혼|예비 부부",
}

BASE = ["age", "sex", "province", "district", "occupation", "marital_status", "family_type"]
TEXT = ["persona", "professional_persona", "family_persona",
        "career_goals_and_ambitions", "hobbies_and_interests", "skills_and_expertise"]

files = sorted(glob.glob(os.path.expanduser(
    "~/.cache/huggingface/hub/datasets--nvidia--Nemotron-Personas-Korea/snapshots/*/data/train-*.parquet")))
df = pd.concat([pd.read_parquet(f, columns=BASE + TEXT) for f in files], ignore_index=True)
assert len(df) == 1_000_000, len(df)

blob = df[TEXT[0]].fillna("")
for c in TEXT[1:]:
    blob = blob + " " + df[c].fillna("")
hit = {k: blob.str.contains(p, regex=True) for k, p in TAGS.items()}
tags = pd.DataFrame(hit).apply(lambda r: ",".join([k for k, v in r.items() if v]), axis=1)
for k in TAGS:
    print(k, int(hit[k].sum()), file=sys.stderr)

out = df[BASE].copy()
out["tags"] = tags
with gzip.open("index.tsv.gz", "wt", encoding="utf-8", compresslevel=9) as f:
    f.write("row\t" + "\t".join(out.columns) + "\n")
    for i, r in enumerate(out.itertuples(index=False)):
        f.write(str(i) + "\t" + "\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")
print("index.tsv.gz", round(os.path.getsize("index.tsv.gz") / 1e6, 1), "MB", file=sys.stderr)
