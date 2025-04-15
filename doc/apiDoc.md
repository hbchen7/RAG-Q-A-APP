# OneAPI API 文档

本文档描述了[One API](https://github.com/songquanpeng/one-api) 开源项目的 API 接口（部分）。

## 用户管理 (User Management)

### 1. 用户注册 (User Registration)

- **接口路径:** `/api/user/register`
- **请求方法:** `POST`
- **控制器函数:** `controller.Register`
- **认证:**
  - 无需认证。
  - 可能受以下中间件限制：
    - `middleware.CriticalRateLimit()`: 限制接口调用频率。
    - `middleware.TurnstileCheck()`: 如果启用了 Turnstile 人机验证，则需要通过验证。
- **功能:** 创建一个新的用户账户。
- **请求体:**
  ```json
  {
    "username": "newuser",
    "password": "password123",
    "email": "user@example.com", // 如果开启了邮箱验证则必须
    "verification_code": "123456", // 如果开启了邮箱验证则必须
    "aff_code": "invite_code" // 可选，邀请码
  }
  ```
- **说明:**
  - 此接口的可用性取决于管理员是否在后台设置中开启了“新用户注册” (`config.RegisterEnabled`) 和“密码注册” (`config.PasswordRegisterEnabled`)。
  - 如果管理员开启了“邮箱验证” (`config.EmailVerificationEnabled`)，请求体中必须包含 `email` 和 `verification_code` 字段，且验证码需有效。
  - `aff_code` 是邀请者的邀请码，如果提供，新用户将与邀请者关联。

### 2. 用户登录 (User Login)

- **接口路径:** `/api/user/login`
- **请求方法:** `POST`
- **控制器函数:** `controller.Login`
- **认证:**
  - 无需认证。
  - 可能受以下中间件限制：
    - `middleware.CriticalRateLimit()`: 限制接口调用频率。
- **功能:** 验证用户凭据并创建用户会话。
- **请求体:**
  ```json
  {
    "username": "existinguser",
    "password": "password123"
  }
  ```
- **说明:**
  - 此接口的可用性取决于管理员是否在后台设置中开启了“密码登录” (`config.PasswordLoginEnabled`)。
  - 登录成功后，服务器会设置 Session Cookie，用于后续请求的用户认证。
  - 响应中会包含用户的基本信息（ID、用户名、显示名称、角色、状态）。

### 3. 获取当前用户信息 (Get Self Information)

- **接口路径:** `/api/user/self`
- **请求方法:** `GET`
- **控制器函数:** `controller.GetSelf`
- **认证:**
  - 需要用户认证 (`middleware.UserAuth()`)。
- **功能:** 获取当前登录用户的完整信息，包括额度。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": {
      "id": 1,
      "username": "user1",
      "display_name": "User One",
      "role": 1, // 角色 (e.g., 1: 普通用户, 10: 管理员)
      "status": 1, // 状态 (e.g., 1: Enabled, 2: Disabled)
      "email": "user@example.com",
      "quota": 1000000, // 总配额
      "used_quota": 250000, // 已用额度
      "remain_quota": 750000 // 剩余额度 (计算得出: quota - used_quota)
    }
  }
  ```
- **代码位置:**
  - 路由定义: `router/api-router.go` (约第 36 行: `selfRoute.GET("/self", controller.GetSelf)`)
  - 控制器实现: `controller/user.go` (约第 248 行: `GetSelf` 函数)

## 令牌管理 (Token Management)

### 4. 获取用户令牌列表 (Get User Tokens)

- **接口路径:** `/api/token/`
- **请求方法:** `GET`
- **控制器函数:** `controller.GetAllTokens`
- **认证:**
  - 需要用户认证 (`middleware.UserAuth()`)。
  - 用户需先登录，并在请求头中携带有效的认证信息（Session Cookie 或 Bearer Token）。
- **功能:** 查询并返回当前登录用户创建的所有令牌。
- **查询参数:**
  - `p` (可选): 页码，用于分页，从 0 开始。每页项目数量由 `config.ItemsPerPage` 配置。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": [
      {
        "id": 1,
        "user_id": 5,
        "name": "My First Token",
        "key": "sk-abc...", // 令牌 Key (部分隐藏)
        "status": 1, // 令牌状态 (1: Enabled, 2: Disabled, 3: Expired, 4: Exhausted)
        "remain_quota": 500000, // 剩余额度
        "unlimited_quota": false, // 是否无限额度
        "created_time": 1678886400, // 创建时间 (Unix Timestamp)
        "accessed_time": 1678887000, // 最近访问时间 (Unix Timestamp)
        "expired_time": -1 // 过期时间 (-1: 永不过期)
      },
      {
        "id": 2,
        "user_id": 5,
        "name": "Another Token",
        "key": "sk-def..."
        // ... 其他令牌信息
      }
      // ... 更多令牌
    ]
  }
  ```

## 模型与渠道管理 (Model & Channel Management)

### 5. 获取模型列表 (Get Models)

- **接口路径:** `/api/models`
- **请求方法:** `GET`
- **认证:**
  - 需要用户认证 (`middleware.UserAuth()`)。
- **功能:** 获取当前 OneAPI 系统中所有可用的模型列表（按渠道分组）。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": {
      "1": ["gpt-3.5-turbo", "gpt-4", "gpt-4-32k"], // 渠道类型 1 (如 OpenAI) 对应的模型
      "2": ["claude-2", "claude-instant-1"], // 渠道类型 2 (如 Anthropic) 对应的模型
      "3": ["gemini-pro", "gemini-pro-vision"] // 渠道类型 3 (如 Google) 对应的模型
      // ... 其他渠道类型的模型列表
    }
  }
  ```
- **说明:**
  - 响应 `data` 是一个对象，键是渠道 _类型_ ID（整数），值是该渠道类型支持的模型名称数组。
  - 此接口返回的是系统 _当前版本支持的所有_ 模型类型，按其 _默认_ 关联的渠道类型进行分组。这 _不_ 代表管理员实际配置的可用渠道或用户实际可用的模型。

### 6. 获取渠道列表 (Get Channels)

- **接口路径:** `/api/channel/`
- **请求方法:** `GET`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 获取管理员在 OneAPI 系统中配置的所有渠道列表。
- **查询参数:**
  - `p` (可选): 页码，用于分页，从 0 开始。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": [
      {
        "id": 1,
        "name": "OpenAI Channel 1",
        "type": 1, // 渠道类型 (e.g., 1: OpenAI, 2: Anthropic, 3: Google PaLM2/Gemini)
        "key": "sk-xxx...", // API Key (部分隐藏)
        "models": "gpt-3.5-turbo,gpt-4", // 该渠道支持的模型列表 (逗号分隔)
        "status": 1, // 状态 (1: Enabled, 2: Disabled)
        "group": "default", // 所属分组
        "priority": 0, // 优先级
        "weight": 0, // 权重
        "created_time": 1234567890, // 创建时间 (Unix Timestamp)
        "base_url": "https://api.openai.com/v1", // 基础 URL
        "other": "{}" // 其他配置 (JSON 字符串)
        // ... 其他渠道信息
      }
      // ... 其他渠道
    ]
  }
  ```
- **说明:** 返回管理员实际配置的渠道详细信息。

### 7. 添加渠道 (Add Channel)

- **接口路径:** `/api/channel/`
- **请求方法:** `POST`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 添加一个新的渠道到 OneAPI 系统。
- **请求体:**
  ```json
  {
    "name": "My New Channel",
    "type": 1, // 渠道类型 (必填)
    "key": "sk-xxx\nsk-yyy", // API 密钥 (必填，支持多行，每行一个 Key)
    "base_url": "", // 覆盖默认 Base URL (可选)
    "other": "", // 其他配置 (可选, JSON 字符串)
    "models": "gpt-3.5-turbo,gpt-4", // 支持的模型列表 (逗号分隔, 必填)
    "group": "default", // 所属分组 (默认 'default')
    "status": 1, // 状态 (1: Enabled, 2: Disabled, 默认 1)
    "priority": 0 // 优先级 (可选, 整数, 值越大优先级越高)
    // 可能还有其他字段，如 weight, headers 等，取决于 OneAPI 版本和配置
  }
  ```
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": ""
  }
  ```
- **说明:**
  - `key` 字段支持多行文本，每行一个密钥，系统会自动为每个密钥创建一个渠道记录。
  - 具体的必填和可选字段可能因 OneAPI 版本和渠道类型而异。

### 8. 删除渠道 (Delete Channel)

- **接口路径:** `/api/channel/{id}`
- **请求方法:** `DELETE`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 删除指定 ID 的渠道。
- **路径参数:**
  - `id` (必填): 要删除的渠道 ID。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": ""
  }
  ```

### 9. 更新渠道 (Update Channel)

- **接口路径:** `/api/channel/`
- **请求方法:** `PUT`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 更新指定渠道的信息。
- **请求体:**
  ```json
  {
    "id": 1, // 要更新的渠道 ID (必填)
    "name": "OpenAI Channel Updated",
    "type": 1,
    "key": "sk-new-key",
    "base_url": "https://api.openai.com/v1",
    "other": "{}",
    "models": "gpt-3.5-turbo,gpt-4,gpt-4-32k",
    "group": "premium",
    "status": 1,
    "priority": 10
    // 提供需要更新的字段及其新值
  }
  ```
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": {
      "id": 1,
      "name": "OpenAI Channel Updated",
      "type": 1,
      "key": "sk-new...", // Key 可能部分隐藏
      "models": "gpt-3.5-turbo,gpt-4,gpt-4-32k",
      "status": 1,
      "created_time": 1234567890
      // ... 其他更新后的渠道信息
    }
  }
  ```
- **说明:** 请求体中必须包含 `id` 字段，其他字段为可选，仅提供需要修改的字段即可。

### 10. 删除已禁用的渠道 (Delete Disabled Channels)

- **接口路径:** `/api/channel/disabled`
- **请求方法:** `DELETE`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 批量删除所有状态为“已禁用” (status=2) 的渠道。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "",
    "data": 2 // 实际删除的渠道数量
  }
  ```

### 11. 测试指定渠道 (Test Channel)

- **接口路径:** `/api/channel/test/{id}`
- **请求方法:** `GET`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 测试指定 ID 的渠道的连通性和可用性。
- **路径参数:**
  - `id` (必填): 要测试的渠道 ID。
- **响应示例 (成功):**
  ```json
  {
    "success": true,
    "message": "", // 成功时通常为空
    "time": 0.532 // 测试耗时（秒）
  }
  ```
- **响应示例 (失败):**
  ```json
  {
    "success": false,
    "message": "连接失败: 超时或认证错误", // 具体的错误信息
    "time": 5.1 // 测试耗时（秒）
  }
  ```
- **说明:** 系统会尝试使用该渠道配置向其 `base_url` 发送一个简单的测试请求（通常是获取模型列表或余额）。

### 12. 测试所有渠道 (Test All Channels)

- **接口路径:** `/api/channel/test`
- **请求方法:** `GET`
- **认证:**
  - 需要管理员认证 (`middleware.AdminAuth()`)。
- **功能:** 触发对所有已配置渠道的后台异步测试。
- **查询参数:**
  - `scope` (可选): 测试范围。如果未指定或为 "all"，则测试所有渠道。可以指定特定渠道 ID (e.g., `?scope=1,3,5`) 或分组名称 (e.g., `?scope=group:default`) 来测试特定范围。
- **响应示例 (请求已接受):**
  ```json
  {
    "success": true,
    "message": "" // 通常表示测试任务已启动
  }
  ```
- **说明:**
  - 此接口仅用于 _启动_ 后台测试任务，不会立即返回测试结果。
  - 测试过程是异步的。测试结果（成功、失败、耗时）通常会在管理界面的渠道列表中更新。
  - 根据系统配置（如“出错时自动禁用”），测试失败的渠道可能会被自动禁用。
