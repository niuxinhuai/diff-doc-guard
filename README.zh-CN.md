# Diff Doc Guard

[English](README.md)

根据 git diff 生成文档同步检查清单。

Diff Doc Guard 适合有“接口变化必须更新 API 文档”“公共组件变化必须更新 UI 文档”等规则的团队。它本地优先、依赖少，也适合放进 CI。

## 功能

- 用可配置规则匹配变更文件和候选文档
- 支持工作区变更、暂存区变更、diff 文件、`BASE...HEAD` 对比
- 支持 Markdown 和 JSON 输出
- 支持 `--exit-code`，在可能需要同步文档时返回失败码
- 可选 AI 润色，兼容 OpenAI-compatible 接口

## 安装

```bash
python3 -m pip install -e .
```

## 使用

```bash
diff-doc-guard --repo .
diff-doc-guard --staged
diff-doc-guard --base origin/main
diff-doc-guard --rules examples/docguard.json --diff examples/sample.diff
diff-doc-guard --format json
diff-doc-guard --exit-code
```

## 规则文件

```json
{
  "rules": [
    {
      "name": "API inventory",
      "patterns": ["src/api/**", "common/network/**"],
      "docs": ["docs/API.md"],
      "reason": "接口变化需要同步 API 文档"
    }
  ]
}
```

## AI 润色

```bash
export AI_API_KEY="your-key"
diff-doc-guard --repo . --ai
```

## 开发

```bash
python3 -m pip install -e .
python3 -m unittest discover -s tests
```

## License

MIT
