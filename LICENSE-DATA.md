# 데이터 출처

`personas.jsonl`은 NVIDIA가 공개한 **Nemotron-Personas-Korea** 데이터셋(100만 명의 한국인 합성 페르소나)에서 10,000명(원본의 1%)을 연령대·성별·권역으로 층화 추출한 것입니다. 필드 일부(스포츠·예술·여행·음식 페르소나, 병역, 전공 등)는 용량을 줄이기 위해 뺐습니다.

- 원본: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
- 제작: NVIDIA
- 라이선스: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- 모든 인물은 통계 데이터를 바탕으로 AI가 생성한 가상 인물입니다. 실존 인물이 아닙니다.

추출 방법은 `scripts/build_sample.py`에 있습니다.
