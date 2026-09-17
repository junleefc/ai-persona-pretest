# 데이터 출처

이 리포의 두 파일은 NVIDIA가 공개한 **Nemotron-Personas-Korea** 데이터셋(100만 명의 한국인 합성 페르소나)에서 만든 것입니다.

- `index.tsv.gz`: 100만 명 전체의 나이·성별·지역·직업·혼인·가구 형태와, 프로필 본문에서 뽑은 상황 태그 16종. 프로필 본문은 들어 있지 않습니다.
- `personas.jsonl`: 13,798명의 전체 프로필. 2,120개 직업이 모두 포함되도록 직업마다 최대 4명을 넣고, 연령대·성별·권역 층화 표본을 더했습니다. 일부 필드(스포츠·예술·여행·음식 페르소나, 병역, 전공)는 용량을 줄이려고 뺐습니다.

- 원본: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
- 제작: NVIDIA
- 라이선스: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- 모든 인물은 통계 데이터를 바탕으로 AI가 생성한 가상 인물입니다. 실존 인물이 아닙니다.

추출 방법은 `scripts/build_sample.py`에 있습니다.

원본을 부분 추출하고 일부 필드를 제외하는 변경을 했습니다. 이 파생물 역시 CC BY 4.0으로 배포합니다. 저장소의 코드와 문서는 MIT 라이선스입니다(LICENSE 참고).
