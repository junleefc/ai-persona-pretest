#!/usr/bin/env python3
"""
100만 명 색인(index.tsv.gz)에서 조건에 맞는 사람을 찾고, 전체 프로필을 HuggingFace /rows API로 받아 candidates.json에 저장한다.

사용법:
  python3 find_personas.py --age 30-55 --sex 남자 --occupation 자재,레미콘,시멘트 --region 경기,서울,인천 --n 40
  python3 find_personas.py --age 30-45 --family 자녀 --region 서울,경기 --n 40
  python3 find_personas.py --age 55-70 --occupation 임업,산림,농업 --n 40

옵션 (모두 선택, 여러 값은 쉼표로 OR):
  --age 30-55        나이 범위
  --sex 남자|여자
  --region 경기,서울   province 또는 district에 포함되는 글자
  --occupation 영업,자재  occupation에 포함되는 글자 (OR)
  --occupation-all 영업   occupation에 반드시 포함 (AND, 여러 개면 모두)
  --marital 배우자있음|미혼 ...
  --family 자녀,혼자    family_type에 포함되는 글자 (OR)
  --n 40             전체 프로필을 받을 인원 (기본 40, 최대 100)
  --seed 7           무작위 시드 (기본: 매번 다름)
  --index index.tsv.gz --out candidates.json

출력: 매칭 인원 수를 화면에, 후보 전체 프로필을 candidates.json에.
"""
import argparse, csv, gzip, json, random, sys, time, urllib.parse, urllib.request

API = "https://datasets-server.huggingface.co/rows?dataset=nvidia%2FNemotron-Personas-Korea&config=default&split=train"


def load_index(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        rd = csv.DictReader(f, delimiter="\t")
        for r in rd:
            r["row"] = int(r["row"]); r["age"] = int(r["age"])
            yield r


def any_in(val, words):
    return any(w in val for w in words)


def fetch_row(offset, tries=4):
    url = f"{API}&offset={offset}&length=1"
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                d = json.load(resp)
            return d["rows"][0]["row"]
        except Exception as e:
            time.sleep(2 * (t + 1))
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--age"); p.add_argument("--sex"); p.add_argument("--region")
    p.add_argument("--occupation"); p.add_argument("--occupation-all", dest="occ_all")
    p.add_argument("--marital"); p.add_argument("--family")
    p.add_argument("--n", type=int, default=40); p.add_argument("--seed", type=int)
    p.add_argument("--index", default="index.tsv.gz"); p.add_argument("--out", default="candidates.json")
    a = p.parse_args()
    n = max(1, min(a.n, 100))
    lo, hi = (map(int, a.age.split("-")) if a.age else (0, 999))
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()] if s else None
    region, occ, occ_all, marital, family = map(split, [a.region, a.occupation, a.occ_all, a.marital, a.family])

    hits = []
    for r in load_index(a.index):
        if not (lo <= r["age"] <= hi): continue
        if a.sex and r["sex"] != a.sex: continue
        if region and not any_in(r["province"] + " " + r["district"], region): continue
        if occ and not any_in(r["occupation"], occ): continue
        if occ_all and not all(w in r["occupation"] for w in occ_all): continue
        if marital and not any_in(r["marital_status"], marital): continue
        if family and not any_in(r["family_type"], family): continue
        hits.append(r)

    print(f"100만 명 중 조건 매칭 {len(hits)}명", file=sys.stderr)
    if not hits:
        sys.exit("조건에 맞는 사람이 없습니다. 조건을 넓히세요.")
    rng = random.Random(a.seed)
    rng.shuffle(hits)
    picked = hits[:n]

    out, failed = [], 0
    for i, r in enumerate(picked, 1):
        full = fetch_row(r["row"])
        if full is None:
            failed += 1; continue
        full["row"] = r["row"]
        out.append(full)
        print(f"  받는 중 {i}/{len(picked)}", end="\r", file=sys.stderr)
    print(file=sys.stderr)
    if not out:
        sys.exit("HuggingFace /rows API에서 프로필을 받지 못했습니다. 네트워크를 확인하거나 대체 파일(personas.jsonl)을 쓰세요.")
    json.dump({"matched_total": len(hits), "fetched": len(out), "failed": failed, "candidates": out},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"후보 {len(out)}명 저장: {a.out} (실패 {failed})", file=sys.stderr)
    for r in out[:40]:
        print(r["age"], r["sex"], r["district"], r["occupation"], "|", r["family_type"], "|", str(r["persona"])[:50])


if __name__ == "__main__":
    main()
