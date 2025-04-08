# ErrorLog

## Ruff 配置结构错误

### 问题背景

在配置 Ruff 代码检查工具时，VS Code 右下角提示 "Error while resolving settings from workspace"。

### 时间日期

2024-04-07

### 问题原因

Ruff 最新版本对配置结构进行了调整，一些配置字段的位置发生了变化。具体来说，`line-length` 等字段不再放在 `[tool.ruff.format]` 下，而是应该放在顶层的 `[tool.ruff]` 配置中。

### 解决方案

1. 将 `line-length` 配置移到 `[tool.ruff]` 下
2. 在 `[tool.ruff.format]` 下使用新的格式化选项：
   - `quote-style`
   - `indent-style`
   - `skip-magic-trailing-comma`
   - `line-ending`

### 经验教训

1. 在使用新版本的工具时，要注意查看最新的官方文档，因为配置结构可能会随版本更新而变化
2. 遇到配置错误时，要仔细阅读错误信息，通常会提供有用的提示
3. 保持项目文档的更新，记录这类配置变更，以便团队其他成员参考
