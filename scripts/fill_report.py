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
  "real_questions": ["...", "...", "..."]
}
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
