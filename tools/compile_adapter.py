#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compile_adapter.py — deterministic runtime-adapter assembly (reference compiler, S10).

> **EN:** The agent_compiler skill (skills/10-agent-compiler.md) describes a 7-step, read-only
> assembly of a person's *confirmed, scoped* instance records into the eight-section runtime
> adapter — the Personal Agent that runs a task. This module makes that assembly EXECUTABLE
> instead of prose: given a subject's instance packs, it (1) keeps only runtime-active records
> (review_status ∈ {confirmed, narrowed}, Gate G3), (2) drops self_reported (draft-only,
> decision C) and superseded (drift_history) records, (3) optionally scope-filters to a task,
> (4) routes each record into its canonical section(s) via the S10 §4 pack→section map,
> (5) lays the boundary_authority layer on top (or the default-safe-policy floor when empty),
> and (6) logs every pack with no active record as a coverage gap (naming the section(s) that
> pack would feed) — never inventing a rule for a gap (G1).
> It assembles records; it does not create or edit them (read-only, like the hand-authored
> examples/logotekton/runtime-adapter.md it reproduces).

HONEST SCOPE: this is the deterministic *assembly* the compiler contract promises — the analog of
tools/pab_merge.py (the merge actuator) and tools/context_select.py (the selection predicate). The
live host runtime (tools/pab.py compile branch) is still a STUB; what is real here is the tested,
reproducible section-membership + gap + boundary math. Sections 8 (output_validator) and the whole
adapter response_policy are *derived* views over the active slices — this tool reports which packs
feed them, it does not fabricate concrete checks.

Usage:
  python tools/compile_adapter.py examples/logotekton                 # human summary
  python tools/compile_adapter.py examples/logotekton --json          # structured adapter (JSON)
  python tools/compile_adapter.py examples/logotekton --task review   # scope-filter to a task tag
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import convergence_report as cr   # loader (collect/load_structured) + CANONICAL_PACKS  # noqa: E402
import context_select as cs       # scope_overlap predicate  # noqa: E402

# 런타임 활성 상태 (G3) — 컴파일 두 번째 잠금장치.
ACTIVE_STATUS = {"confirmed", "narrowed"}

# 팩 → 8섹션 라우팅 (skills/10-agent-compiler.md §4 표). evaluation_cases·drift_history 는
# 섹션에 컴파일되지 않는다(평가 입력 / 폐기 선별용).
PACK_SECTIONS = {
    "user.identity_roles": (1,),
    "user.persona_core": (1, 3),
    "user.communication_style": (2, 8),
    "user.artifact_policy": (4,),
    "user.decision_policy": (3,),
    "user.tacit_heuristics": (5,),
    "user.red_flags": (5,),
    "user.workflow_playbooks": (6,),
    "user.domain_overlays": (2, 5),
    "user.tool_stack": (6,),
    "user.boundary_authority": (7,),
    # memory_project_graph 는 섹션 1·6 에 *프로젝트 맥락 피연산자*로 합류한다(페르소나가 아님) —
    # 어댑터는 이를 persona 와 섞지 않는 별도 하위블록으로 둔다(skills/10 §4 섹션1 경계, 전이성).
    "user.memory_project_graph": (1, 6),
}

SECTION_NAMES = {
    1: "identity_role",
    2: "active_patterns",
    3: "decision_policy",
    4: "artifact_policy",
    5: "heuristics_red_flags",
    6: "workflow",
    7: "boundary_rules",
    8: "output_validator",
}

# 섹션 8(출력 검증기)에 입력을 주는 팩 (communication_style·boundary_authority·artifact_policy).
SECTION8_INPUT_PACKS = ("user.communication_style", "user.boundary_authority", "user.artifact_policy")


def _as_id_set(value):
    """supersedes 값(리스트/문자열/None)을 id 집합으로."""
    out = set()
    if isinstance(value, list):
        out |= {str(v).strip() for v in value if v is not None and str(v).strip()}
    elif value is not None and str(value).strip():
        out.add(str(value).strip())
    return out


def collect_superseded(pack_records, drift_records):
    """폐기된(=대체된) 레코드 id 집합. drift_history 의 supersedes + 레코드 자체 supersedes 필드.

    skill 10 §3 주의: `narrowed` 상태만으로 활성 여부를 판정하면 안 되고, supersedes 의 *대상*은
    제외해야 한다(폐기된 옛 버전을 끌고 오지 않도록).
    """
    ids = set()
    for d in drift_records:
        ids |= _as_id_set(d.get("supersedes"))
    for recs in pack_records.values():
        for r in recs:
            if isinstance(r, dict):
                ids |= _as_id_set(r.get("supersedes"))
    return ids


def _is_self_reported(rec):
    return str(rec.get("reliability", "behavioral")).strip().lower() == "self_reported"


def is_runtime_active(rec, superseded_ids):
    """이 레코드가 어댑터에 컴파일될 수 있는가.

    (1) review_status ∈ {confirmed, narrowed} (G3), (2) self_reported 아님(draft-only, 결정 C),
    (3) 다른 레코드에 의해 폐기되지 않음(supersedes 대상 아님).
    """
    if not isinstance(rec, dict):
        return False
    if str(rec.get("review_status", "")).strip().lower() not in ACTIVE_STATUS:
        return False
    if _is_self_reported(rec):
        return False
    if str(rec.get("id", "")).strip() in superseded_ids:
        return False
    return True


def _ref(rec, pack):
    return {
        "id": rec.get("id"),
        "pack": pack,
        "statement": rec.get("statement"),
        "scope": rec.get("scope"),
    }


def compile_adapter(pack_records, drift_records, task_tags=None):
    """확정·비폐기·behavioral 슬라이스를 8섹션 어댑터로 결정론적으로 조립한다.

    task_tags 가 주어지면 scope_overlap 으로 작업류에 닿는 레코드만 켠다(작업별 활성화). None 이면
    전체 활성 슬라이스(한 작업류 스냅샷). 반환은 직렬화 가능한 dict.
    """
    superseded = collect_superseded(pack_records, drift_records)

    active_by_pack = {}
    for pack in PACK_SECTIONS:
        recs = pack_records.get(pack, []) or []
        active = [
            r for r in recs
            if is_runtime_active(r, superseded)
            # scope 소스 해석을 context_select 와 일치시킨다(`scope` 없으면 `applies_in`) — applies_in 은
            # 런타임 컨텍스트 스위치(spec/01 §, skills/06)이므로 scope 만 보면 applies_in-스코프 레코드가
            # 모든 작업류에 새어든다. 두 결정론 도구가 runtime-active 집합에서 갈라지면 안 된다. (it.15)
            and (task_tags is None
                 or cs.scope_overlap(r.get("scope") or r.get("applies_in"), task_tags))
        ]
        # 결정론: (id, statement) 전순서로 정렬 (동일 입력 → 동일 어댑터).
        # id 만으로는 동일-id 레코드(예: 충돌/중복)에서 안정정렬이 입력순서에 의존 — statement 를
        # 보조키로 더해 입력순서와 무관한 전순서를 보장한다(적대적 검증 it.14).
        active_by_pack[pack] = sorted(
            active, key=lambda r: (str(r.get("id", "")), str(r.get("statement", "")))
        )

    sections = {n: [] for n in range(1, 9)}
    # 섹션 1 경계(전이성): memory_project_graph 는 섹션 1 에 *피연산자*로 들어오지만
    # 페르소나(identity_roles·persona_core)와 섞이지 않는 별도 하위블록(project_context)으로
    # 적재한다 — skills/10 §4. (섹션 6 합류는 정상: 워크플로의 프로젝트 단계.)
    project_context = []
    for pack, secs in PACK_SECTIONS.items():
        for r in active_by_pack[pack]:
            for s in secs:
                if s == 1 and pack == "user.memory_project_graph":
                    project_context.append(_ref(r, pack))
                else:
                    sections[s].append(_ref(r, pack))

    # 경계 레이어: 확인된 BoundaryRule 이 있으면 인스턴스 경계, 없으면 기본 안전 정책 하한.
    boundary_active = active_by_pack.get("user.boundary_authority", [])
    boundary_source = "instance" if boundary_active else "default_safe_policy"

    # 섹션 8(출력 검증기)은 파생 뷰 — 어떤 입력 팩이 활성인지 보고(체크를 발명하지 않음).
    section8_inputs = [p for p in SECTION8_INPUT_PACKS if active_by_pack.get(p)]
    if boundary_source == "default_safe_policy":
        section8_inputs = section8_inputs + ["default_safe_policy"]

    # 갭 로그: 컴파일 대상 12팩 중 활성 레코드 0개인 팩. `feeds_sections` 는 그 팩이 *기여하는*
    # 섹션 번호다 — 그 섹션이 통째로 비었다는 뜻이 아니라(다른 팩이 채울 수 있다), 이 팩의 몫이
    # 비었다는 뜻이다(팩 단위 커버리지 갭).
    gap_log = [
        {"pack": pack, "feeds_sections": list(secs)}
        for pack, secs in PACK_SECTIONS.items()
        if not active_by_pack[pack]
    ]

    active_packs = [p for p in PACK_SECTIONS if active_by_pack[p]]
    provenance = {
        SECTION_NAMES[s]: sorted({str(ref["id"]) for ref in sections[s]})
        for s in range(1, 9) if sections[s]
    }

    return {
        "task_tags": list(task_tags) if isinstance(task_tags, (list, tuple, set)) else task_tags,
        "sections": {SECTION_NAMES[s]: sections[s] for s in range(1, 9)},
        # 섹션 1 의 project_context 하위블록 (페르소나와 분리; 프로젝트 종료 시 교체 대상).
        "project_context": project_context,
        "boundary_source": boundary_source,
        "section8_inputs": section8_inputs,
        "response_policy_inputs": [
            p for p in ("user.communication_style", "user.boundary_authority")
            if active_by_pack.get(p)
        ] or ["default_safe_policy"],
        "gap_log": gap_log,
        "coverage": {
            "active_packs": active_packs,
            "n_active_packs": len(active_packs),
            "n_compile_packs": len(PACK_SECTIONS),
            "n_gaps": len(gap_log),
        },
        "provenance": provenance,
        "superseded_excluded": sorted(superseded),
    }


def load(path):
    """(pack_records, drift_records) 를 디렉터리 *또는* 단일 인스턴스 파일에서 로드.

    디렉터리면 cr.collect(모든 파일). 단일 파일이면 그 파일만 — revolution 의 .pre 픽스처처럼 *한
    스냅샷*을 같은 폴더의 후보 파일과 섞지 않고 컴파일할 때 쓴다(T0 재현 검증).
    """
    if os.path.isdir(path):
        pack_records, _ev, drift_records, _n = cr.collect(path)
        return pack_records, drift_records
    value = cr.load_structured(path)
    pack_records = {p: [] for p in cr.CANONICAL_PACKS}
    drift_records = []
    if value is not None:
        for pack_hint, rec in cr._iter_records_from_value(value):
            pack = pack_hint or cr._infer_pack_for_record(rec)
            if pack is None:
                continue
            pack_records.setdefault(pack, []).append(rec)
            if pack == "user.drift_history":
                drift_records.append(rec)
    return pack_records, drift_records


def render_summary(adapter, directory):
    lines = []
    lines.append("=" * 72)
    lines.append("Personal Agent — 컴파일된 런타임 어댑터 (reference compiler, S10)")
    lines.append(f"입력: {directory}  ·  작업 태그: {adapter['task_tags'] or '(전체 활성 슬라이스)'}")
    lines.append("정의: skills/10-agent-compiler.md §3·§4 · G3 + reliability(C) + supersession")
    lines.append("=" * 72)
    cov = adapter["coverage"]
    lines.append(f"활성 팩: {cov['n_active_packs']} / {cov['n_compile_packs']} (컴파일 대상)  ·  "
                 f"갭: {cov['n_gaps']}  ·  경계: {adapter['boundary_source']}")
    if adapter["superseded_excluded"]:
        lines.append(f"폐기 제외(supersedes): {', '.join(adapter['superseded_excluded'])}")
    lines.append("")
    lines.append("[섹션별 활성 레코드]")
    for s in range(1, 9):
        name = SECTION_NAMES[s]
        refs = adapter["sections"][name]
        if refs:
            ids = ", ".join(str(r["id"]) for r in refs)
            lines.append(f"  {s}. {name:<20} {len(refs)}개: {ids}")
        else:
            extra = " (기본 안전 정책)" if s == 7 and adapter["boundary_source"] == "default_safe_policy" else ""
            lines.append(f"  {s}. {name:<20} (공백 — 갭){extra}")
    pc = adapter.get("project_context") or []
    if pc:
        ids = ", ".join(str(r["id"]) for r in pc)
        lines.append(f"  1+ project_context     {len(pc)}개: {ids}  (페르소나 아님 — 프로젝트 맥락)")
    lines.append("")
    lines.append("[갭 로그] 빈/저커버리지 슬롯 — 다음 채굴 라운드 신호 (추측으로 메우지 않음, G1)")
    if adapter["gap_log"]:
        for g in adapter["gap_log"]:
            secs = "·".join(str(x) for x in g["feeds_sections"])
            lines.append(f"  - {g['pack']:<28} → 섹션 {secs} 기여 없음")
    else:
        lines.append("  (갭 없음)")
    lines.append("=" * 72)
    return "\n".join(lines)


def build_arg_parser():
    import argparse
    p = argparse.ArgumentParser(
        description="확정 인스턴스 레코드를 8섹션 런타임 어댑터로 결정론적으로 컴파일한다 (참조 컴파일러).",
    )
    p.add_argument("directory", help="인스턴스 팩 디렉터리 (예: examples/logotekton)")
    p.add_argument("--task", default=None,
                   help="작업 스코프 태그 (예: 'review' 또는 'context.task.code') — 주면 스코프 매칭 필터")
    p.add_argument("--json", action="store_true", help="구조화된 어댑터를 JSON 으로 출력")
    return p


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    # 존재하지 않거나 읽을 수 없는 입력에서 *조용히 성공*하지 않는다 — 그래야 문서-커맨드 가드
    # (check_commands)의 exit-0 판정이 "예제가 실제로 해석된다"를 진짜로 증명한다(적대적 검증 it.10).
    if not os.path.exists(args.directory):
        print(f"error: 입력 경로가 없습니다: {args.directory}", file=sys.stderr)
        return 2
    pack_records, drift_records = load(args.directory)
    if not any(pack_records.get(p) for p in pack_records):
        print(f"error: {args.directory} 에서 레코드를 하나도 로드하지 못했습니다 "
              "(빈/파싱불가 입력 — 컴파일할 대상 없음)", file=sys.stderr)
        return 1
    adapter = compile_adapter(pack_records, drift_records, task_tags=args.task)
    if args.json:
        print(json.dumps(adapter, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_summary(adapter, args.directory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
