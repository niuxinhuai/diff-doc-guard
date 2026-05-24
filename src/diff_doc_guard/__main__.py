import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

from . import __version__

DEFAULT_RULES = {
    "rules": [
        {
            "name": "API docs",
            "patterns": ["src/api/**", "api/**", "common/network/**", "**/service/**"],
            "docs": ["docs/API.md"],
            "reason": "API endpoint, enum, request, or response changes usually need documentation.",
        },
        {
            "name": "UI docs",
            "patterns": ["src/components/**", "components/**", "common/common_view/**"],
            "docs": ["docs/UI.md"],
            "reason": "Shared UI changes should be visible to downstream developers.",
        },
        {
            "name": "Operations docs",
            "patterns": ["scripts/**", "sh/**", "*.sh", "Dockerfile", "docker-compose.yml"],
            "docs": ["docs/BUILD_AND_RUN.md"],
            "reason": "Build, run, or release behavior changed.",
        },
    ]
}


def read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def load_rules(path, repo="."):
    if path and os.path.exists(path):
        return json.loads(read_file(path))
    discovered = os.path.join(repo, ".docguard.json")
    if os.path.exists(discovered):
        return json.loads(read_file(discovered))
    return DEFAULT_RULES


def init_rules_file(repo=".", force=False):
    path = os.path.join(repo, ".docguard.json")
    if os.path.exists(path) and not force:
        raise RuntimeError("%s already exists. Use --force to overwrite." % path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(DEFAULT_RULES, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def git_diff(repo, staged=False, base=None):
    try:
        if base:
            command = ["git", "-C", repo, "diff", "%s...HEAD" % base, "--", "."]
        elif staged:
            command = ["git", "-C", repo, "diff", "--cached", "--", "."]
        else:
            command = ["git", "-C", repo, "diff", "HEAD", "--", "."]
        return subprocess.check_output(command, stderr=subprocess.DEVNULL).decode("utf-8", "replace")
    except subprocess.CalledProcessError:
        return ""


def changed_files(diff_text):
    files = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:])
        elif line.startswith("diff --git "):
            match = re.search(r" b/(\S+)$", line)
            if match:
                files.append(match.group(1))
    seen = []
    for item in files:
        if item != "/dev/null" and item not in seen:
            seen.append(item)
    return seen


def matches(pattern, path):
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))


def evaluate(files, rules):
    hits = []
    for rule in rules.get("rules", []):
        matched = []
        for path in files:
            if any(matches(pattern, path) for pattern in rule.get("patterns", [])):
                matched.append(path)
        if matched:
            hits.append({
                "name": rule.get("name", "Unnamed rule"),
                "docs": rule.get("docs", []),
                "reason": rule.get("reason", ""),
                "files": matched,
            })
    return hits


def result_data(files, hits):
    return {
        "changed_files": files,
        "docs_to_check": hits,
        "needs_docs": bool(hits),
    }


def render(files, hits):
    output = ["# Documentation Sync Checklist", ""]
    if not files:
        output.extend(["No changed files were found in the provided diff.", ""])
        return "\n".join(output)
    output.append("## Changed Files")
    for path in files:
        output.append("- `%s`" % path)
    output.append("")
    if not hits:
        output.extend(["## Result", "", "No documentation rules matched. Still scan the PR for user-visible behavior changes.", ""])
        return "\n".join(output)
    output.append("## Docs To Check")
    for hit in hits:
        output.append("")
        output.append("### %s" % hit["name"])
        output.append("- Reason: %s" % hit["reason"])
        output.append("- Changed files: %s" % ", ".join("`%s`" % item for item in hit["files"]))
        output.append("- Candidate docs:")
        for doc in hit["docs"]:
            output.append("  - [ ] `%s`" % doc)
    output.append("")
    output.append("## PR Checklist")
    for hit in hits:
        for doc in hit["docs"]:
            output.append("- [ ] Checked whether `%s` needs an update." % doc)
    output.append("")
    return "\n".join(output)


def call_ai(diff_text, checklist, model=None, base_url=None):
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise RuntimeError("AI_API_KEY is not set")
    base_url = (base_url or os.getenv("AI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
    model = model or os.getenv("AI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only Markdown. Be concise."},
            {"role": "user", "content": "Improve this documentation sync checklist from the diff.\n\nDIFF:\n%s\n\nCHECKLIST:\n%s" % (diff_text[:12000], checklist[:6000])},
        ],
        "temperature": 0.1,
    }
    request = urllib.request.Request(
        base_url + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError("AI request failed: %s" % exc)
    return body["choices"][0]["message"]["content"].strip() + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate documentation sync reminders from git diff.")
    parser.add_argument("--repo", default=".", help="Git repository path")
    parser.add_argument("--diff", help="Read diff from file instead of git diff --cached")
    parser.add_argument("--staged", action="store_true", help="Inspect staged changes only")
    parser.add_argument("--base", help="Compare BASE...HEAD, useful in CI")
    parser.add_argument("--rules", help="JSON rule file")
    parser.add_argument("--init-rules", action="store_true", help="Create a starter .docguard.json in --repo")
    parser.add_argument("--force", action="store_true", help="Overwrite files created by --init-rules")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--exit-code", action="store_true", help="Exit with code 2 when docs may need updates")
    parser.add_argument("--ai", action="store_true", help="Use an OpenAI-compatible model to refine the checklist")
    parser.add_argument("--model", help="Override AI_MODEL for --ai")
    parser.add_argument("--base-url", help="Override AI_BASE_URL for --ai")
    parser.add_argument("--output", help="Write result to a file")
    parser.add_argument("--version", action="version", version="diff-doc-guard %s" % __version__)
    args = parser.parse_args(argv)

    if args.init_rules:
        path = init_rules_file(args.repo, args.force)
        sys.stdout.write("Created %s\n" % path)
        return 0

    diff_text = read_file(args.diff) if args.diff else git_diff(args.repo, args.staged, args.base)
    files = changed_files(diff_text)
    hits = evaluate(files, load_rules(args.rules, args.repo))
    if args.format == "json":
        checklist = json.dumps(result_data(files, hits), ensure_ascii=False, indent=2) + "\n"
    else:
        checklist = render(files, hits)
    result = call_ai(diff_text, checklist, args.model, args.base_url) if args.ai else checklist
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(result)
    else:
        sys.stdout.write(result)
    if args.exit_code and hits:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
