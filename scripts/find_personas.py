#!/usr/bin/env python3
"""
100만 명 색인(index.tsv.gz)에서 조건에 맞는 사람을 찾고, 전체 프로필을 HuggingFace /rows API로 받아 candidates.json에 저장한다.

사용법:
  python3 find_personas.py --age 30-55 --sex 남자 --occupation 자재,레미콘,시멘트 --region 경기,서울,인천 --n 24
  python3 find_personas.py --age 20-29 --tag 수험생 --n 24
  python3 find_personas.py --age 30-45 --family 자녀 --tag 육아,학부모 --region 서울,경기 --n 24
  python3 find_personas.py --age 55-70 --occupation 임업,산림,농업 --n 24

옵션 (모두 선택, 여러 값은 쉼표로 OR):
  --age 30-55        나이 범위
  --sex 남자|여자
  --region 경기,서울   province 또는 district에 포함되는 글자
  --occupation 영업,자재  occupation에 포함되는 글자 (OR)
  --occupation-all 영업   occupation에 반드시 포함 (AND, 여러 개면 모두)
  --tag 수험생,취업준비   상황 태그 (OR). 직업으로 안 잡히는 타깃을 찾을 때 쓴다
  --tag-all 육아,학부모   상황 태그 (AND, 모두 가진 사람만)
      쓸 수 있는 태그: 수험생 취업준비 창업준비 퇴사은퇴 육아 학부모 돌봄간병 건강관리
                      반려동물 재테크 귀농귀촌 프리랜서 1인가구 외국어유학 콘텐츠창작 결혼준비
  --marital 배우자있음|미혼 ...
  --family 자녀,혼자    family_type에 포함되는 글자 (OR)
  --n 24             전체 프로필을 받을 인원 (기본 24, 최대 100). 늘릴수록 오래 걸린다
  --seed 7           무작위 시드 (기본: 매번 다름)
  --index index.tsv.gz --out candidates.json

출력: 매칭 인원 수를 화면에, 후보 전체 프로필을 candidates.json에.
"""
import argparse, csv, gzip, json, os, random, sys, time, urllib.error, urllib.parse, urllib.request

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
    """HuggingFace에서 한 사람의 전체 프로필을 받는다. 429(요청 제한)는 길게 기다렸다 다시 시도한다."""
    url = f"{API}&offset={offset}&length=1"
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                d = json.load(resp)
            return d["rows"][0]["row"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep([6, 20, 45, 60][min(t, 3)])
            else:
                time.sleep(2 * (t + 1))
        except Exception:
            time.sleep(2 * (t + 1))
    return None


def from_local(hits, n, path="personas.jsonl"):
    """HuggingFace를 못 쓸 때. 같은 조건을 대체 파일에서 다시 건다."""
    if not os.path.exists(path):
        return []
    keys = {(r["age"], r["sex"], r["district"], r["occupation"]) for r in hits}
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if (r.get("age"), r.get("sex"), r.get("district"), r.get("occupation")) in keys:
                out.append(r)
    random.shuffle(out)
    return out[:n]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--age"); p.add_argument("--sex"); p.add_argument("--region")
    p.add_argument("--occupation"); p.add_argument("--occupation-all", dest="occ_all")
    p.add_argument("--marital"); p.add_argument("--family")
    p.add_argument("--tag"); p.add_argument("--tag-all", dest="tag_all")
    p.add_argument("--n", type=int, default=24); p.add_argument("--seed", type=int)
    p.add_argument("--index", default="index.tsv.gz"); p.add_argument("--out", default="candidates.json")
    a = p.parse_args()
    n = max(1, min(a.n, 100))
    lo, hi = (map(int, a.age.split("-")) if a.age else (0, 999))
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()] if s else None
    region, occ, occ_all, marital, family, tag, tag_all = map(
        split, [a.region, a.occupation, a.occ_all, a.marital, a.family, a.tag, a.tag_all])

    hits = []
    for r in load_index(a.index):
        if not (lo <= r["age"] <= hi): continue
        if a.sex and r["sex"] != a.sex: continue
        if region and not any_in(r["province"] + " " + r["district"], region): continue
        if occ and not any_in(r["occupation"], occ): continue
        if occ_all and not all(w in r["occupation"] for w in occ_all): continue
        if marital and not any_in(r["marital_status"], marital): continue
        if family and not any_in(r["family_type"], family): continue
        rtags = r.get("tags", "") or ""
        if tag and not any(t in rtags.split(",") for t in tag): continue
        if tag_all and not all(t in rtags.split(",") for t in tag_all): continue
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
            failed += 1
        else:
            full["row"] = r["row"]
            out.append(full)
        print(f"  받는 중 {i}/{len(picked)} (성공 {len(out)}, 실패 {failed})", end="\r", file=sys.stderr)
        time.sleep(0.35 + rng.random() * 0.3)   # 서버에 무리를 주지 않으려고 쉬어 간다
        if failed >= 8 and len(out) < 5:        # 계속 막히면 더 두드리지 않는다
            print("\n  요청이 계속 막혀 중단했습니다.", file=sys.stderr)
            break
    print(file=sys.stderr)

    if len(out) < min(10, n):
        local = from_local(hits, n)
        if local:
            print(f"HuggingFace에서 {len(out)}명만 받아, 대체 파일(personas.jsonl)에서 같은 조건으로 {len(local)}명을 찾았습니다.", file=sys.stderr)
            print("선별 메모에 '대체 파일 사용'이라고 적으세요.", file=sys.stderr)
            out = local
    if not out:
        sys.exit("프로필을 받지 못했습니다. 잠시 뒤 다시 실행하거나, personas.jsonl을 받아 같은 폴더에 두고 다시 실행하세요.")
    json.dump({"matched_total": len(hits), "fetched": len(out), "failed": failed, "candidates": out},
              open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"후보 {len(out)}명 저장: {a.out} (실패 {failed})", file=sys.stderr)
    for r in out[:40]:
        print(r["age"], r["sex"], r["district"], r["occupation"], "|", r["family_type"], "|", str(r["persona"])[:50])


if __name__ == "__main__":
    main()
