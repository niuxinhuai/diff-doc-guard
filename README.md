# Diff Doc Guard

根据 `git diff` 判断哪些文档可能需要同步，生成可贴到 PR 的文档检查清单。

它适合有“代码变更必须同步文档”约定的团队。默认走本地规则，配置 API Key 后可以让模型补充变更说明和遗漏风险。

## 快速开始

```bash
python3 -m diff_doc_guard --repo .
```

使用自定义规则：

```bash
python3 -m diff_doc_guard --rules examples/docguard.json --diff examples/sample.diff
```

启用 AI 增强：

```bash
export AI_API_KEY="your-key"
python3 -m diff_doc_guard --repo . --ai
```

## 规则格式

```json
{
  "rules": [
    {
      "name": "API inventory",
      "patterns": ["src/api/**", "common/network/**"],
      "docs": ["docs/API.md"],
      "reason": "接口枚举或请求模型变化需要同步 API 文档"
    }
  ]
}
```

## License

MIT
