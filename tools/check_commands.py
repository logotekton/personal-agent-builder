#!/usr/bin/env python3
"""check_commands.py — documented-command integrity guard.

A command printed in a doc is a promise that it RUNS; this guard keeps that promise executable. It
scans every Markdown file for fenced shell blocks, extracts each invocation of this repo's tools /
test suite, and runs it, failing if any exits nonzero. So a renamed flag or a changed CLI signature
(e.g. the two-file convergence_report form that silently broke) can't survive in the docs.

SCOPE NOTE — this verifies *runnability* (exit 0), not the *figures* a doc prints. The numeric
results (coverage 0.07, merge_rate 0.095, 42 PASS, ...) are locked separately by the test suite
(tests/test_tools.py), which asserts the exact tool output. A doc comment like `# merge_rate 0.095`
is NOT compared against stdout here; if you change a locked number, a test breaks, not this guard.

Scope — it runs only SAFE, READ-ONLY invocations of THIS REPO'S TOOLS (whose CLI could drift) and
reports the rest as skipped:
  - runs:  python tools/<validate_packs|convergence_report|dedup_check|check_anchors|
           context_select|compile_adapter|pab_merge>.py <args>.
  - skips: anything with a placeholder (<...>, "당신", path/to, ...), a write/side-effect flag
           (--apply, --out, output redirection >), a transient /tmp/ path (an output of a prior
           --apply step, absent in a clean checkout), the test suite itself (unittest /
           test_tools.py, to avoid recursion when this guard is in turn exercised by that suite),
           and `python -c` env/config one-liners (which may rely on version-specific stdlib like
           tomllib and are not a tool CLI). Both ``` and ~~~ fences are scanned. Backslash
           line-continuations are joined before running.

Usage:
  python tools/check_commands.py                 # scan the repo (cwd) recursively
  python tools/check_commands.py --list          # print every command and its disposition

Exit 0 = every runnable documented command succeeded. Exit 1 = at least one failed (each printed
as `FAIL exit=N: <cmd>  (<file>)`). This is a gate, not a signal.
"""
import sys, os, re, glob, subprocess, argparse, shlex

TOOL_INVOCATION = re.compile(r'^\s*(python3?|python3? -m)\s+\S')
FENCE = re.compile(r'^\s*(```|~~~)')
PLACEHOLDER = ('<', '당신', 'path/to', '...', '--subject')
SIDE_EFFECT = ('--apply', '--out', '>', '|')
# transient scratch paths — outputs of prior --apply steps, absent in a clean checkout
TRANSIENT = ('/tmp/',)
# self-referential / covered directly by CI's own test step — skip to avoid recursion
RECURSIVE = ('unittest', 'test_tools.py')
# only these repo tools are auto-run; anything else is skipped as out-of-scope
RUNNABLE_TOOLS = ('validate_packs.py', 'convergence_report.py', 'dedup_check.py',
                  'check_anchors.py', 'check_schemas.py', 'check_triggers.py',
                  'context_select.py', 'compile_adapter.py', 'pab_merge.py')


def fenced_blocks(path):
    """Yield the line-lists of fenced code blocks (both ``` and ~~~ fences)."""
    in_fence, fence, buf = False, None, []
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            m = FENCE.match(line)
            if m:
                if not in_fence:
                    in_fence, fence = True, m.group(1)
                    continue
                elif line.strip().startswith(fence):   # matching closing fence
                    in_fence, fence = False, None
                    yield buf
                    buf = []
                    continue
                # a different fence delimiter inside an open block → treat as content
            if in_fence:
                buf.append(line.rstrip('\n'))
    if buf:
        yield buf


def commands_in(block):
    """Join backslash-continuations and return whole python commands found in a fenced block."""
    out, acc = [], ''
    for ln in block:
        if acc:
            acc += ' ' + ln.strip()
        else:
            # 명령 시작 줄에서만 셸 프롬프트 마커($ 또는 >)를 떼고 매칭한다 — '$ python tools/…' 처럼
            # 프롬프트가 붙은 호출이 추출조차 안 돼 실행성이 검증되지 않던 가짜 음성을 막는다(적대적 검증 it.19).
            # 연속줄(redirect ' > out' 등)에는 적용하지 않는다.
            start = re.sub(r'^\s*[$>]\s+', '', ln)
            if TOOL_INVOCATION.match(start):
                acc = start.strip()
            else:
                continue
        if acc.rstrip().endswith('\\'):
            acc = acc.rstrip()[:-1].strip()
        else:
            out.append(re.sub(r'\s+#.*$', '', acc).strip())
            acc = ''
    if acc:
        out.append(re.sub(r'\s+#.*$', '', acc).strip())
    return out


def classify(cmd):
    """Return 'run', or a 'skip:<reason>' disposition for a command string."""
    if any(p in cmd for p in PLACEHOLDER):
        return 'skip:placeholder'
    if any(s in cmd for s in SIDE_EFFECT):
        return 'skip:side-effect'
    if any(t in cmd for t in TRANSIENT):
        return 'skip:transient-path'
    if any(r in cmd for r in RECURSIVE):
        return 'skip:test-suite'
    if cmd.startswith(('python -c', 'python3 -c')):
        # env/config one-liners (e.g. `import tomllib`) — may need version-specific stdlib; not a tool CLI
        return 'skip:env-check'
    if any(t in cmd for t in RUNNABLE_TOOLS):
        return 'run'
    return 'skip:out-of-scope'


def main():
    ap = argparse.ArgumentParser(description='Run every safe documented command and check it succeeds.')
    ap.add_argument('roots', nargs='*', default=['.'], help='dirs/files to scan (default: cwd)')
    ap.add_argument('--list', action='store_true', help='print every command and its disposition')
    args = ap.parse_args()

    files = []
    for root in args.roots:
        if os.path.isfile(root) and root.endswith('.md'):
            files.append(root)
        else:
            files.extend(glob.glob(os.path.join(root, '**', '*.md'), recursive=True))
    files = sorted(set(os.path.normpath(f) for f in files))

    seen = {}   # cmd -> file (first occurrence, for reporting)
    for f in files:
        for blk in fenced_blocks(f):
            for cmd in commands_in(blk):
                seen.setdefault(cmd, f)

    ran = skipped = broken = 0
    failures = []
    for cmd in sorted(seen):
        disp = classify(cmd)
        if disp != 'run':
            skipped += 1
            if args.list:
                print(f'SKIP ({disp.split(":", 1)[1]}): {cmd}')
            continue
        # normalize `python ` -> `python3 ` for the runner
        runnable = re.sub(r'^python(?= )', 'python3', cmd)
        try:
            r = subprocess.run(runnable, shell=True, capture_output=True, text=True, timeout=180)
            ok = r.returncode == 0
        except Exception as e:  # noqa: BLE001 — surface any launch failure as a break
            ok, r = False, type('R', (), {'returncode': -1, 'stderr': str(e)})()
        ran += 1
        if args.list:
            print(f'{"OK  " if ok else "FAIL"} exit={r.returncode}: {cmd}')
        if not ok:
            broken += 1
            failures.append((cmd, seen[cmd], r.returncode))

    for cmd, f, code in failures:
        print(f'FAIL exit={code}: {cmd}  ({f})')
    print(f'\n{len(files)} markdown files; {ran} commands run, {skipped} skipped, {broken} broken.')
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main())
