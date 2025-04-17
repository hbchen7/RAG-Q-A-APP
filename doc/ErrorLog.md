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

## OneAPI 无法连接 MySQL 数据库 (Docker 网络问题)

- **时间:** 2025-04-17 (根据日志推断)
- **问题背景:** 使用宝塔面板 Docker 功能分别部署 OneAPI 和 MySQL 8.2.0 容器。OneAPI 容器启动时报错，无法连接到 MySQL。
- **错误日志:**
  ```
  oneapi-1 | [FATAL] 2025/04/17 - 08:45:11 | model/main.go:115 [InitDB] failed to initialize database: dial tcp 172.18.0.2:3306: connect: no route to host
  ```
- **问题原因:** OneAPI 容器 (`oneapi-1`) 与 MySQL 容器 (IP `172.18.0.2`) 不在同一个可以相互通信的 Docker 网络中，或者 OneAPI 配置的数据库地址不正确。`no route to host` 表明网络层面上无法找到目标主机。仅在宿主机防火墙开放端口不足以保证容器间通信。
- **解决方案:**
  1.  **(推荐)** 使用 Docker Compose 定义和管理 OneAPI 和 MySQL 服务，确保它们在同一个 Compose 自动创建的网络中，并在 OneAPI 配置中使用 MySQL 的**服务名**作为主机地址。
  2.  手动创建自定义 Docker 网络，并将两个容器都连接到该网络，同样在 OneAPI 配置中使用 MySQL 的**容器名**作为主机地址。
  3.  检查并修正 OneAPI 的数据库连接配置（通常是环境变量），确保指向正确的、可访问的 MySQL 容器地址（最好是容器名/服务名）。
- **经验教训:** Docker 容器间通信依赖于正确的 Docker 网络配置。默认情况下，单独创建的容器可能不在同一网络，导致无法直接通过 IP 或名称访问。使用 Docker Compose 或自定义网络是解决容器间通信的标准做法。配置连接时应优先使用服务名/容器名，而不是容易变动的 IP 地址。
