#!/usr/bin/env python3
"""check_anchors.py — doc link integrity guard for the spec/skills/docs tree.

The repo's thesis is "every claim is enforced by a command." Cross-document links are claims
too: "see spec/10 §3" only holds if that anchor still exists. This stdlib-only checker resolves
every intra-repo inline Markdown link and fails if a target file/dir is missing or an `#anchor`
does not match any heading in the target — so a renamed heading/file can't silently strand a link.

What it checks (intra-repo only; external http(s)/mailto links are ignored):
  - every relative inline link `](path)` resolves to an existing file (any extension) or, for a
    trailing-slash target, an existing directory;
  - any `#fragment` on a `.md` link matches the GitHub-generated slug of some heading there.
  Scope: inline-style `](...)` links only — reference-style `[id]: target` definitions,
  angle-bracket autolinks, and HTML `href=` anchors are NOT scanned.

Anchor slugs follow GitHub's algorithm (github-slugger): lowercase, drop every character that is
not a Unicode word char / hyphen / space, then turn each space into one hyphen (consecutive
symbols between spaces therefore yield consecutive hyphens, e.g. "A ↔ B" -> "a--b"; "(1:1, 전수)"
-> "11-전수"). Duplicate headings get `-1`, `-2`, ... suffixes, as GitHub does. Fenced code blocks
(``` and ~~~) are skipped for both heading extraction and link scanning, so illustrative snippets
don't create phantom anchors or phantom links.

Usage:
  python tools/check_anchors.py                 # scan the repo (cwd) recursively
  python tools/check_anchors.py spec skills      # scan only these roots
  python tools/check_anchors.py --list           # also print every checked link (verbose)

Exit code 0 = every intra-repo link (file + anchor) resolves. Exit code 1 = at least one broken
link, each printed as `file:line -> target#anchor  (reason)`. This is a gate, not a signal.
"""
import sys, os, re, argparse, glob

HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
# an optional Markdown link title:  ](path "title")  or  ](path 'title')
_TITLE = r'(?:\s+["\'][^"\']*["\'])?'
# inline link target with a fragment: ](  optional-path  #fragment  ["title"] )
LINK = re.compile(r'\]\(\s*([^)\s#]*)\s*#([^)\s]+?)' + _TITLE + r'\s*\)')
# inline link target without a fragment (for file-existence checks): ](path ["title"])
FILELINK = re.compile(r'\]\(\s*([^)\s#]+?)' + _TITLE + r'\s*\)')
FENCE = re.compile(r'^\s*(```|~~~)')


def gh_slug(text):
    """GitHub-slugger-compatible slug for a heading's rendered text."""
    t = text.strip().lower()
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)   # [label](url) -> label
    t = t.replace('`', '')                           # backticks are dropped anyway
    t = re.sub(r'[^\w\- ]', '', t, flags=re.UNICODE)  # keep word chars, hyphen, space
    return t.replace(' ', '-')                        # each space -> one hyphen (no collapse)


def headings_to_anchors(path):
    """Return the set of anchor slugs a Markdown file exposes (with GitHub dup suffixing)."""
    anchors, seen, in_fence, fence = set(), {}, False, None
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            f = FENCE.match(line)
            if f:
                if not in_fence:
                    in_fence, fence = True, f.group(1)
                elif line.strip().startswith(fence):
                    in_fence, fence = False, None
                continue
            if in_fence:
                continue
            m = HEADING.match(line)
            if not m:
                continue
            base = gh_slug(m.group(2))
            if base in seen:
                seen[base] += 1
                anchors.add(f'{base}-{seen[base]}')
            else:
                seen[base] = 0
                anchors.add(base)
    return anchors


def iter_links(path):
    """Yield (lineno, rawtarget, fragment_or_None) for inline links outside code fences."""
    in_fence, fence = False, None
    with open(path, encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            f = FENCE.match(line)
            if f:
                if not in_fence:
                    in_fence, fence = True, f.group(1)
                elif line.strip().startswith(fence):
                    in_fence, fence = False, None
                continue
            if in_fence:
                continue
            # strip inline code spans so `](#x)` inside backticks isn't treated as a link
            stripped = re.sub(r'`[^`]*`', '', line)
            for m in LINK.finditer(stripped):
                yield ln, m.group(1), m.group(2)
            for m in FILELINK.finditer(stripped):
                yield ln, m.group(1), None


def collect_md(roots):
    files = []
    for root in roots:
        if os.path.isfile(root) and root.endswith('.md'):
            files.append(root)
        else:
            files.extend(glob.glob(os.path.join(root, '**', '*.md'), recursive=True))
    return sorted(set(os.path.normpath(f) for f in files))


def main():
    ap = argparse.ArgumentParser(description='Check intra-repo Markdown link + anchor integrity.')
    ap.add_argument('roots', nargs='*', default=['.'],
                    help='files or directories to scan (default: current directory)')
    ap.add_argument('--list', action='store_true', help='print every checked anchor link')
    args = ap.parse_args()

    files = collect_md(args.roots)
    anchor_cache = {}

    def anchors_of(path):
        if path not in anchor_cache:
            anchor_cache[path] = headings_to_anchors(path)
        return anchor_cache[path]

    broken, checked = [], 0
    for f in files:
        base = os.path.dirname(f)
        for ln, target, frag in iter_links(f):
            # Resolve the link target file. Empty target => same file (pure #anchor link).
            if target == '':
                tgt = f
            elif target.startswith(('http://', 'https://', 'mailto:', '#')):
                if target.startswith('#'):
                    tgt, frag = f, target[1:]
                else:
                    continue  # external link — out of scope
            else:
                tgt = os.path.normpath(os.path.join(base, target))

            if frag is None:
                # file-existence check for EVERY relative (non-external) link target — not just a
                # hard-coded extension whitelist, so a renamed .toml/.sh/dir target can't slip past.
                if target and not target.startswith(('http://', 'https://', 'mailto:', '#')):
                    if target.endswith('/'):                       # directory link
                        if not os.path.isdir(tgt):
                            broken.append((f, ln, target, 'target directory missing'))
                    elif not os.path.exists(tgt):
                        broken.append((f, ln, target, 'target file missing'))
                continue

            # anchor check applies to .md targets we can read
            if not tgt.endswith('.md'):
                continue
            if not os.path.exists(tgt):
                broken.append((f, ln, f'{target}#{frag}', 'target file missing'))
                continue
            checked += 1
            if args.list:
                print(f'  {f}:{ln} -> {target or "(self)"}#{frag}')
            if frag not in anchors_of(tgt):
                broken.append((f, ln, f'{target or "(self)"}#{frag}', 'no matching heading'))

    for f, ln, link, why in broken:
        print(f'BROKEN {f}:{ln} -> {link}  ({why})')
    print(f'\n{len(files)} markdown files, {checked} anchor links checked, {len(broken)} broken.')
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main())
