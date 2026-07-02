#!/usr/bin/env python3
"""bootstrap_plan.py — deterministic repo → OpenCrab ingest plan (skill 17 bootstrap).

Reads a checkout of this repo and emits the EXACT provisioning plan that skill
17 (skills/17-bootstrap.md) executes against OpenCrab: which projects to ensure,
which builder packs to ingest from which source files, and which empty
personal.<subject>.* shells to prepare. The plan is pure repo-tree arithmetic —
no network, no OpenCrab access — so it can be locked by tests and re-run by
anyone to verify a bootstrap did neither more nor less than the repo prescribes.

Mapping contract (MUST stay in sync with skills/17-bootstrap.md §Stage 2):
  skills/NN-<name>.md                  -> skill.pab.<name_snake>.v0.1
  spec/NN-<name>.md                    -> pa.<name_snake>.v0.1
  templates/user.<pack>.template.yaml
    (+ schemas/user.<pack>.schema.json) -> personal.<pack>.template.v0.1
  schemas/{record.base,candidate,trigger}.schema.json -> pa.shared_schemas.v0.1 (one pack)

Usage:
  python tools/bootstrap_plan.py .                 # plan for this checkout
  python tools/bootstrap_plan.py . --subject you   # also name the 14 personal shells
                                                   #  (grammar ^[a-z0-9_]+$; else exit 2 + hint)
  python tools/bootstrap_plan.py . --json          # machine-readable plan

Exit 0 = plan produced. Exit 2 = repo root missing/not a PAB checkout (sibling
tools' CLI contract). This is a *plan*, not an actuator: it never writes.
"""
import sys, os, re, json, argparse, glob

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

SHARED_SCHEMAS = ("record.base.schema.json", "candidate.schema.json", "trigger.schema.json")
PROJECTS = (
    ("personal agent builder skills", "builder_apparatus"),
    ("personal agent evidence", "personal_agent_evidence_archive"),
    ("personal agent", "personal_agent_canonical"),
)


def _snake(md_name):
    """skills/15-tacit-knowledge-mining.md -> tacit_knowledge_mining"""
    stem = re.sub(r"^\d+-", "", os.path.splitext(os.path.basename(md_name))[0])
    return stem.replace("-", "_")


def build_plan(root, subject=None):
    """Return the deterministic plan dict for a repo checkout at `root`."""
    skills = sorted(glob.glob(os.path.join(root, "skills", "[0-9]*.md")))
    specs = sorted(glob.glob(os.path.join(root, "spec", "[0-9]*.md")))
    templates = sorted(glob.glob(os.path.join(root, "templates", "user.*.template.yaml")))

    builder = []
    for f in skills:
        builder.append({"pack": f"skill.pab.{_snake(f)}.v0.1", "source": [os.path.relpath(f, root)]})
    for f in specs:
        builder.append({"pack": f"pa.{_snake(f)}.v0.1", "source": [os.path.relpath(f, root)]})
    for f in templates:
        pack = os.path.basename(f).replace("user.", "", 1).replace(".template.yaml", "")
        schema = os.path.join(root, "schemas", f"user.{pack}.schema.json")
        src = [os.path.relpath(f, root)]
        if os.path.isfile(schema):
            src.append(os.path.relpath(schema, root))
        builder.append({"pack": f"personal.{pack}.template.v0.1", "source": src})
    shared = [os.path.join("schemas", s) for s in SHARED_SCHEMAS
              if os.path.isfile(os.path.join(root, "schemas", s))]
    if shared:
        builder.append({"pack": "pa.shared_schemas.v0.1", "source": shared})

    shells = [f"personal.{'<subject>' if not subject else subject}.{p['pack'].split('.')[1]}.v0.1"
              for p in builder if p["pack"].startswith("personal.") and p["pack"].endswith(".template.v0.1")]

    return {
        "projects": [{"name": n, "role": r} for n, r in PROJECTS],
        "builder_packs": builder,
        "personal_shells": shells,
        "counts": {
            "skills": len(skills), "specs": len(specs), "templates": len(templates),
            "builder_packs": len(builder), "personal_shells": len(shells),
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Deterministic repo -> OpenCrab bootstrap plan (skill 17).")
    ap.add_argument("root", nargs="?", default=".", help="repo checkout root (default: cwd)")
    ap.add_argument("--subject", default=None, help="owner handle for the 14 personal shells")
    ap.add_argument("--json", action="store_true", help="emit the plan as JSON")
    args = ap.parse_args()

    root = args.root
    if not os.path.isdir(os.path.join(root, "skills")) or not os.path.isdir(os.path.join(root, "spec")):
        sys.stderr.write(f"[error] PAB 체크아웃이 아닙니다 (skills/·spec/ 없음): {root}\n")
        return 2
    if args.subject is not None and not re.fullmatch(r"[a-z0-9_]+", args.subject):
        # subject 는 레코드 id 문법 <subject>.<recordkind>.NNN 의 첫 토큰 — 소유자가 고른
        # 닉네임을 조용히 변형하지 않고, 정규화 *제안*과 함께 거부한다 (skill 17 Stage 0).
        hint = re.sub(r"[^a-z0-9_]+", "_", args.subject.lower()).strip("_")
        sys.stderr.write(f"[error] subject 는 ^[a-z0-9_]+$ 여야 합니다: {args.subject!r}"
                         + (f" — 제안: {hint!r}\n" if hint else "\n"))
        return 2

    plan = build_plan(root, args.subject)
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    c = plan["counts"]
    print("=" * 60)
    print("BOOTSTRAP PLAN  (skills/17-bootstrap.md · repo -> OpenCrab)")
    print("=" * 60)
    print("Stage 1 · projects (ensure, idempotent):")
    for p in plan["projects"]:
        print(f"  - {p['name']}   [{p['role']}]")
    print(f"\nStage 2 · builder packs to ingest ({c['builder_packs']}):")
    for item in plan["builder_packs"]:
        print(f"  - {item['pack']}  <-  {', '.join(item['source'])}")
    print(f"\nStage 3 · personal shells ({c['personal_shells']}, EMPTY — no records):")
    for s in plan["personal_shells"]:
        print(f"  - {s}")
    print("\nStage 4 · activation mode: ASK THE OWNER (A command / B ambient / C manual; default A)")
    print("-" * 60)
    print(f"totals: skills {c['skills']} + specs {c['specs']} + templates {c['templates']}"
          f" + shared 1 = {c['builder_packs']} builder packs; {c['personal_shells']} shells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
