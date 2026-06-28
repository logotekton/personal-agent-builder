<!--
EN: PR checklist for Personal Agent Builder (spec v0.3). Every PR must respect the four
pack classes, the six quality gates, the canonical 14-pack / 14-candidate vocabulary, and
pass tools/validate_packs.py. Keep changes scoped; fill every section below.
한국어 우선 — 영어가 편하면 영어로 적어도 됩니다.
-->

## 변경 요약 (What & Why)

<!-- 무엇을, 왜 바꿨는지 2~4문장. 관련 이슈가 있으면 `Closes #NN`. -->



## 어떤 팩 클래스에 영향 (Affected pack class)

<!-- 이 PR이 건드리는 항목에 [x]. 클래스는 절대 섞지 마세요 (게이트 G6). -->

- [ ] **skill pack** (`skill.pab.*`) — 빌더 방법론 / `skills/`, `spec/02-builder-pipeline.md`
- [ ] **template pack** (`user.*.template` / schema) — 14개 팩 스키마 / `schemas/`, `spec/03-pack-catalog.md`
- [ ] **instance pack** (`personal.<subject>.*`) — 승인된 레코드 데이터 / `examples/`
- [ ] **adapter pack** (`*.runtime_adapter`) — 컴파일된 런타임
- [ ] governance / spec / tooling / docs (위 4클래스 외)

영향받는 팩(정식 이름) 또는 스킬:

## 6개 게이트 준수 확인 (Quality gates — [`spec/01-kernel-schema.md`](../spec/01-kernel-schema.md) §2)

- [ ] **G1** 증거 없는 주장 없음 — 모든 레코드/예제가 ≥1 `evidence_refs`
- [ ] **G2** 스코프 없는 규칙 없음 — 모든 레코드에 비어있지 않은 `scope`
- [ ] **G3** pending 런타임 활성화 없음 — `confirmed`/`narrowed`/편집된 항목만 활성
- [ ] **G4** 행동 언어만 — 추측된 심리가 아니라 관찰된 행동으로 기술
- [ ] **G5** 승격 전 프라이버시 — `sensitive`/`restricted` 항목은 BoundaryRule 먼저
- [ ] **G6** 템플릿/인스턴스 분리 — 템플릿에 라이브 레코드 없음
- [ ] N/A — 이 PR은 레코드/스키마를 건드리지 않음

## 정식 이름 사용 확인 (Canonical naming — [`spec/08-naming-and-ids.md`](../spec/08-naming-and-ids.md))

- [ ] 14개 팩 정식 이름만 사용 (`user.identity_roles` … `user.drift_history`)
- [ ] 14개 candidate type 정식 이름만 사용 (`IdentityRoleCandidate` … `DriftRecordCandidate`)
- [ ] 폐기 코드명(`pa.t03`, `t06`, `x12`, `.ba` 등)은 "구 코드명" 주석으로만 등장
- [ ] 통합 베이스 레코드 필드 사용 — `statement`/`confidence` (폐기 `claim`/`score` 아님)

## validate_packs.py 통과 (Validation)

- [ ] `python tools/validate_packs.py` 로컬 통과 (또는 N/A: 검증 대상 파일 변경 없음)

```text
# 실행 결과 붙여넣기 (paste output)
```

## 관련 spec 링크 (Related spec)

<!-- 이 변경의 근거가 되는 spec/스키마 문서를 링크하세요 (상대 경로). -->

- [ ] [`spec/00-overview.md`](../spec/00-overview.md)
- [ ] [`spec/01-kernel-schema.md`](../spec/01-kernel-schema.md)
- [ ] [`spec/02-builder-pipeline.md`](../spec/02-builder-pipeline.md)
- [ ] [`spec/03-pack-catalog.md`](../spec/03-pack-catalog.md)
- [ ] [`spec/04-privacy-boundary.md`](../spec/04-privacy-boundary.md)
- [ ] [`spec/05-evaluation-drift.md`](../spec/05-evaluation-drift.md)
- [ ] [`spec/06-convergence-model.md`](../spec/06-convergence-model.md)
- [ ] 기타:

---

기여 가이드: [`CONTRIBUTING.md`](../CONTRIBUTING.md) · 거버넌스: [`GOVERNANCE.md`](../GOVERNANCE.md)
