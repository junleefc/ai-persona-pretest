#!/usr/bin/env python3
"""
report.json + templates/report.html -> REPORT.html

사용법:
  python3 fill_report.py report.json report-template.html REPORT.html

report.json 형식:
{
  "project_name": "가정통신문 정리 서비스",
  "run_info": "Claude Opus 5로 6분 걸림",
  "date": "2026-09-13",
  "brief_file": "기획서.md",
  "page_file": "index.html",
  "yes_n": 3, "maybe_n": 2, "no_n": 2,
  "stop_section": "첫 화면",
  "stop_basis": "신청하지 않았거나 망설인 핵심 타깃 3명이 읽다가 멈춘 지점",
  "stop_counts": {"첫 화면": 1, "차이": 2, "무료 제안": 0, "신청 항목": 1},
  "stop_why": "안 누른 2명이 여기서 멈췄다. ...",
  "current_sentence": "index.html에 있는 문장 그대로",
  "proposed_sentence": "바꾼 문장",
  "form_note": "신청 항목 지적. 없으면 null",
  "near_insight": "인접 세그먼트 2명의 반응으로 본 타깃 범위 판단",
  "personas": [
    {"name": "박선미", "age": 37, "sex": "여자", "district": "경기-용인시 수지구", "occupation": "정보 시스템 운영자",
     "kind": "target", "verdict": "yes", "stop": "없음",
     "a1": "...", "a2": "...", "a3": "...", "a4": "...", "a5": "...", "fix": "..."}
  ],
  "real_questions": ["...", "...", "..."],
  "panel_title": "선택. 7명이 내 타깃이 아닐 때만 쓴다",
  "panel_note": "선택. 위와 같을 때 맨 위에 띄울 경고 문장. 없으면 null",
  "sampling": {
    "source_short": "NVIDIA Nemotron-Personas-Korea 100만 명에서 검색",
    "source_line": "NVIDIA Nemotron-Personas-Korea. 통계청·대법원·건강보험공단 통계로 만든 가상 인물. CC BY 4.0",
    "matched_total": 43,
    "match_line": "30~55세 남성, 서울·경기·인천, 직업에 자재 또는 건설 + 영업",
    "fetched": 37,
    "fetch_line": "43명 중 무작위 40명 요청, 37명 수신",
    "pick_line": "핵심 타깃 5명은 지역·연령·가족이 겹치지 않게. 인접 세그먼트 2명은 연령 축과 직업 축을 하나씩 벗어나게",
    "conditions": [
      {"who": "수원 45세 레미콘 영업팀장", "cond": "30~55세, 남성, 서울·경기·인천, 직업에 자재/건설 + 영업", "result": "43명, 전원 건축자재 영업원"},
      {"who": "인접 세그먼트 1 (연령 축)", "cond": "같은 직업, 56~65세", "result": "16명 중 1명"},
      {"who": "인접 세그먼트 2 (직업 축)", "cond": "기계장비 영업, 같은 연령·지역", "result": "128명 중 1명"}
    ],
    "notes": ["직업명에 '레미콘'은 없어 건축자재 영업원으로 대체했다", "팀장인지, 팀원이 몇 명인지는 프로필에 없다"],
    "candidates": [
      {"name": "김종순", "age": 53, "sex": "남자", "district": "경기-수원시 영통구", "occupation": "건축자재 영업원", "family_type": "배우자·자녀와 거주", "picked": true}
    ]
  }
}
sampling.candidates에는 프로필을 받은 후보 전원(인접 세그먼트 후보 포함)을 넣고, 7명에 든 사람은 picked: true.
kind: target(핵심 타깃) | near(인접 세그먼트). verdict: yes | no | maybe. stop: 첫 화면 | 차이 | 무료 제안 | 신청 항목 | 없음
"""
import html, json, re, sys

KIND = {"target": "핵심 타깃", "near": "인접 세그먼트"}
COLOR = {"yes": "#0E6E66", "no": "#A8221B", "maybe": "#9A6410"}
ORDER = {"no": 0, "maybe": 1, "yes": 2}
SECTIONS = ["첫 화면", "차이", "무료 제안", "신청 항목"]
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
    ordered = sorted(ps, key=lambda p: (ORDER.get(p["verdict"], 3), 0 if p["kind"] == "target" else 1))
    for p in ordered:
        c = card_tpl
        vals = {
            "VERDICT": p["verdict"], "KIND": p["kind"],
            "ICON_COLOR": COLOR.get(p["verdict"], "#69727A"),
            "NAME": p["name"],
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
        stop = (p.get("stop") or "").strip()
        tag = "" if (p["verdict"] == "yes" or stop in ("", "없음")) else f'<span class="stopped">{esc(stop)}에서 멈춤</span><br>'
        c = c.replace("{{STOPPED_TAG}}", tag)
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
        "PICK_LINE": sp.get("pick_line", "핵심 타깃 5명, 인접 세그먼트 2명"),
        "CAND_N": str(len(cands)),
    }
    for k, v in top_samp.items():
        tpl = tpl.replace("{{" + k + "}}", esc(v))

    # 결론 픽토그램 (순서는 누른다 → 모르겠다 → 안 누른다)
    icon_order = sorted(ps, key=lambda p: ({"yes": 0, "maybe": 1, "no": 2}.get(p["verdict"], 3), p["name"]))
    mi = re.search(r"<!-- ICON START -->(.*?)<!-- ICON END -->", tpl, re.S)
    icons = []
    for p in icon_order:
        b = mi.group(1)
        for k, v in {"ICON_COLOR": COLOR.get(p["verdict"], "#69727A"),
                     "ICON_NAME": p["name"], "ICON_AGE": p["age"]}.items():
            b = b.replace("{{" + k + "}}", esc(v))
        icons.append(b)
    tpl = tpl[: mi.start()] + "\n".join(icons) + tpl[mi.end():]

    # 어디서 멈췄나 막대
    counts = d.get("stop_counts") or {}
    top = d.get("stop_section")
    mx = max([int(counts.get(k, 0)) for k in SECTIONS] + [1])
    ms = re.search(r"<!-- STOP START -->(.*?)<!-- STOP END -->", tpl, re.S)
    bars = []
    for name in SECTIONS:
        n = int(counts.get(name, 0))
        b = ms.group(1)
        cls = "hot" if name == top else ("zero" if n == 0 else "")
        for k, v in {"ST_CLASS": cls, "ST_NAME": name,
                     "ST_PCT": round(n / mx * 100), "ST_N": n}.items():
            b = b.replace("{{" + k + "}}", esc(v))
        bars.append(b)
    tpl = tpl[: ms.start()] + "\n".join(bars) + tpl[ms.end():]

    # 패널 경고 배너: 없으면 통째로 제거
    pn = d.get("panel_note")
    if pn:
        tpl = tpl.replace("{{PANEL_TITLE}}", esc(d.get("panel_title", "이 결과는 페이지 문제가 아닙니다")))
        tpl = tpl.replace("{{PANEL_NOTE}}", esc(pn))
        tpl = tpl.replace("<!-- PANEL START -->", "").replace("<!-- PANEL END -->", "")
    else:
        tpl = re.sub(r"\s*<!-- PANEL START -->.*?<!-- PANEL END -->\s*", "\n", tpl, flags=re.S)

    # 신청 항목 콜아웃: 없으면 통째로 제거
    if d.get("form_note"):
        tpl = tpl.replace("<!-- FORM START -->", "").replace("<!-- FORM END -->", "")
    else:
        tpl = re.sub(r"\s*<!-- FORM START -->.*?<!-- FORM END -->\s*", "\n", tpl, flags=re.S)

    qs = d["real_questions"]
    top = {
        "PROJECT_NAME": d["project_name"], "DATE": d["date"],
        "BRIEF_FILE": d["brief_file"], "PAGE_FILE": d["page_file"],
        "RUN_INFO": d.get("run_info") or "가상 인물 7명 인터뷰",
        "YES_N": yes, "MAYBE_N": maybe, "NO_N": no,
        "STOP_SECTION": d["stop_section"], "STOP_BASIS": d.get("stop_basis") or "", "STOP_WHY": d["stop_why"],
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
