#!/usr/bin/env python3
"""
report.json + templates/report.html -> REPORT.html

사용법:
  python3 fill_report.py report.json report-template.html REPORT.html

report.json 형식:
{
  "project_name": "가정통신문 정리 서비스",
  "date": "2026-09-13",
  "brief_file": "기획서.md",
  "page_file": "index.html",
  "yes_n": 3, "maybe_n": 2, "no_n": 2,
  "stop_section": "첫 화면",
  "stop_why": "안 누른 2명이 여기서 멈췄다. ...",
  "current_sentence": "index.html에 있는 문장 그대로",
  "proposed_sentence": "바꾼 문장",
  "form_note": "신청 항목 지적. 없으면 null",
  "near_insight": "근처 2명이 말해 주는 것",
  "personas": [
    {"name": "박선미", "age": 37, "sex": "여자", "district": "경기-용인시 수지구", "occupation": "정보 시스템 운영자",
     "kind": "target", "verdict": "yes", "stop": "없음",
     "a1": "...", "a2": "...", "a3": "...", "a4": "...", "a5": "...", "fix": "..."}
  ],
  "real_questions": ["...", "...", "..."],
  "sampling": {
    "source_short": "NVIDIA Nemotron-Personas-Korea 100만 명에서 검색",
    "source_line": "NVIDIA Nemotron-Personas-Korea. 통계청·대법원·건강보험공단 통계로 만든 가상 인물. CC BY 4.0",
    "matched_total": 43,
    "match_line": "30~55세 남성, 서울·경기·인천, 직업에 자재 또는 건설 + 영업",
    "fetched": 37,
    "fetch_line": "43명 중 무작위 40명 요청, 37명 수신",
    "pick_line": "타깃 5명은 지역·나이·가족이 겹치지 않게. 근처 2명은 나이 축, 직업 축을 하나씩 벗어나게",
    "conditions": [
      {"who": "수원 45세 레미콘 영업팀장", "cond": "30~55세, 남성, 서울·경기·인천, 직업에 자재/건설 + 영업", "result": "43명, 전원 건축자재 영업원"},
      {"who": "근처 1 (나이 축)", "cond": "같은 직업, 56~65세", "result": "16명 중 1명"},
      {"who": "근처 2 (직업 축)", "cond": "기계장비 영업, 같은 나이·지역", "result": "128명 중 1명"}
    ],
    "notes": ["직업명에 '레미콘'은 없어 건축자재 영업원으로 대체했다", "팀장인지, 팀원이 몇 명인지는 프로필에 없다"],
    "candidates": [
      {"name": "김종순", "age": 53, "sex": "남자", "district": "경기-수원시 영통구", "occupation": "건축자재 영업원", "family_type": "배우자·자녀와 거주", "picked": true}
    ]
  }
}
sampling.candidates에는 프로필을 받은 후보 전원(근처 후보 포함)을 넣고, 7명에 든 사람은 picked: true.
kind: target | near. verdict: yes | no | maybe. stop: 첫 화면 | 차이 | 무료 제안 | 신청 항목 | 없음
"""
import html, json, re, sys

KIND = {"target": "타깃", "near": "근처"}
VERDICT = {"yes": "누른다", "no": "안 누른다", "maybe": "모르겠다"}


def esc(v):
    return html.escape(str(v), quote=True)


def main(json_path, tpl_path, out_path):
    d = json.load(open(json_path, encoding="utf-8"))
    tpl = open(tpl_path, encoding="utf-8").read()

    ps = d["personas"]
    if len(ps) != 7:
        sys.exit(f"personas는 7명이어야 합니다. 지금 {len(ps)}명")
    yes = sum(p["verdict"] == "yes" for p in ps)
    maybe = sum(p["verdict"] == "maybe" for p in ps)
    no = sum(p["verdict"] == "no" for p in ps)

    # 카드 블록
    m = re.search(r"<!-- CARD START -->(.*?)<!-- CARD END -->", tpl, re.S)
    card_tpl = m.group(1)
    cards = []
    for p in ps:
        c = card_tpl
        vals = {
            "VERDICT": p["verdict"], "KIND": p["kind"],
            "INITIAL": str(p["name"])[:1], "NAME": p["name"],
            "AGE": p["age"], "SEX": p["sex"],
            "DISTRICT": str(p["district"]).replace("-", " "),
            "OCCUPATION": p["occupation"],
            "KIND_LABEL": KIND[p["kind"]], "VERDICT_LABEL": VERDICT[p["verdict"]],
            "STOP": p.get("stop") or ("없음" if p["verdict"] == "yes" else ""),
            "A1": p["a1"], "A2": p["a2"], "A3": p["a3"], "A4": p["a4"], "A5": p["a5"],
            "FIX_QUOTE": p["fix"],
        }
        for k, v in vals.items():
            c = c.replace("{{" + k + "}}", esc(v))
        cards.append(c)
    tpl = tpl[: m.start()] + "\n".join(cards) + tpl[m.end():]

    # 추출 깔때기
    sp = d.get("sampling") or {}
    def block(tag, items, render):
        nonlocal tpl
        mm = re.search(rf"<!-- {tag} START -->(.*?)<!-- {tag} END -->", tpl, re.S)
        body = "\n".join(render(mm.group(1), it) for it in items)
        tpl = tpl[: mm.start()] + body + tpl[mm.end():]
    def sub(s_, vals):
        for k, v in vals.items():
            s_ = s_.replace("{{" + k + "}}", esc(v))
        return s_
    block("COND", sp.get("conditions", []), lambda b, c: sub(b, {"C_WHO": c["who"], "C_COND": c["cond"], "C_RESULT": c["result"]}))
    block("NOTE", sp.get("notes", []), lambda b, n: sub(b, {"NOTE": n}))
    cands = sp.get("candidates", [])
    block("CAND", cands, lambda b, c: sub(b, {
        "CAND_CLASS": "picked" if c.get("picked") else "", "CAND_NAME": c.get("name", ""), "CAND_AGE": c.get("age", ""),
        "CAND_SEX": c.get("sex", ""), "CAND_DISTRICT": str(c.get("district", "")).replace("-", " "),
        "CAND_OCC": c.get("occupation", ""), "CAND_FAMILY": c.get("family_type", "")}))
    if not cands:
        tpl = re.sub(r'\s*<details class="cands">.*?</details>\s*', "\n", tpl, flags=re.S)
    top_samp = {
        "SOURCE_SHORT": sp.get("source_short", "NVIDIA Nemotron-Personas-Korea 100만 명에서 검색"),
        "SOURCE_LINE": sp.get("source_line", "NVIDIA Nemotron-Personas-Korea. 공공 통계로 만든 가상 인물. CC BY 4.0"),
        "MATCHED_N": f"{int(sp.get('matched_total', 0)):,}", "MATCH_LINE": sp.get("match_line", ""),
        "FETCHED_N": f"{int(sp.get('fetched', 0)):,}", "FETCH_LINE": sp.get("fetch_line", ""),
        "PICK_LINE": sp.get("pick_line", "타깃 5명, 근처 2명"),
        "CAND_N": str(len(cands)),
    }
    for k, v in top_samp.items():
        tpl = tpl.replace("{{" + k + "}}", esc(v))

    # 신청 항목 콜아웃: 없으면 통째로 제거
    if not d.get("form_note"):
        tpl = re.sub(r'\s*<div class="callout" id="form">.*?</div>\s*', "\n", tpl, flags=re.S)

    qs = d["real_questions"]
    top = {
        "PROJECT_NAME": d["project_name"], "DATE": d["date"],
        "BRIEF_FILE": d["brief_file"], "PAGE_FILE": d["page_file"],
        "YES_N": yes, "MAYBE_N": maybe, "NO_N": no,
        "STOP_SECTION": d["stop_section"], "STOP_WHY": d["stop_why"],
        "CURRENT_SENTENCE": d["current_sentence"], "PROPOSED_SENTENCE": d["proposed_sentence"],
        "FORM_NOTE": d.get("form_note") or "", "NEAR_INSIGHT": d["near_insight"],
        "REAL_Q1": qs[0], "REAL_Q2": qs[1], "REAL_Q3": qs[2],
    }
    for k, v in top.items():
        tpl = tpl.replace("{{" + k + "}}", esc(v))

    left = re.findall(r"{{[A-Z_0-9]+}}", tpl)
    if left:
        sys.exit(f"채워지지 않은 자리: {sorted(set(left))}")
    open(out_path, "w", encoding="utf-8").write(tpl)
    print(f"saved {out_path} · 누른다 {yes} 모르겠다 {maybe} 안 누른다 {no}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
