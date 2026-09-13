#!/usr/bin/env python3
"""원본 parquet(100만 명) -> index.tsv.gz (행번호, 나이, 성별, 시도, 시군구, 직업, 혼인, 가구형태). 제작자용."""
import glob, gzip, os, pandas as pd
files = sorted(glob.glob(os.path.expanduser("~/.cache/huggingface/hub/datasets--nvidia--Nemotron-Personas-Korea/snapshots/*/data/train-*.parquet")))
cols = ["age", "sex", "province", "district", "occupation", "marital_status", "family_type"]
df = pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)
assert len(df) == 1_000_000
with gzip.open("index.tsv.gz", "wt", encoding="utf-8", compresslevel=9) as f:
    f.write("row\t" + "\t".join(cols) + "\n")
    for i, r in enumerate(df.itertuples(index=False)):
        f.write(str(i) + "\t" + "\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in r) + "\n")
print("index.tsv.gz", round(os.path.getsize("index.tsv.gz") / 1e6, 1), "MB")
