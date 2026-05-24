# Diff Doc Guard

[中文文档](README.zh-CN.md)

Generate documentation sync checklists from git diffs.

Diff Doc Guard helps teams enforce rules like "API changes must update API docs" without building a heavy review bot. It is local-first, dependency-light, and works in CI.

## Features

- Matches changed files against configurable documentation rules.
- Supports working-tree, staged, explicit diff file, and `BASE...HEAD` comparisons.
- Supports Markdown and JSON output.
- Can return a failing exit code when documentation may need updates.
- Optional AI polishing through an OpenAI-compatible endpoint.

## Install

```bash
python3 -m pip install -e .
```

## Usage

```bash
diff-doc-guard --repo .
diff-doc-guard --staged
diff-doc-guard --base origin/main
diff-doc-guard --rules examples/docguard.json --diff examples/sample.diff
diff-doc-guard --format json
diff-doc-guard --exit-code
```

## Rule File

```json
{
  "rules": [
    {
      "name": "API inventory",
      "patterns": ["src/api/**", "common/network/**"],
      "docs": ["docs/API.md"],
      "reason": "API changes should update API documentation"
    }
  ]
}
```

## AI Polishing

```bash
export AI_API_KEY="your-key"
diff-doc-guard --repo . --ai
```

## Development

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests
```

## License

MIT
