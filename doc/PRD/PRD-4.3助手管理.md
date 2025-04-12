**针对 4.3. 助手管理 (Assistant Management)**

- **FR-ASST-001: 创建助手**

  - **必填/可选字段:** 代码中 `AssistantRequest` 模型定义了 `title`, `username`, `prompt` 的默认值，`knowledge_Id` 是可选的 (`None`)。在 API 调用时，`username` 是必须由前端提供的吗？还是说可以默认为 'root'？[是，将由前端 pinia 中的 authStore.user.username 提供。] `title` 和 `prompt` 是否允许用户在创建时不提供而使用默认值？[允许，将使用默认值。]
  - **默认值确认:** 确认一下 `title` 的默认值是 "新助手"，`prompt` 的默认值是 "你是一个 AI 助手，请根据用户的问题给出回答。" 这是否符合预期？[是]
  - **约束:** `Assistant` 模型中 `username` 字段被标记为 `Indexed(unique=True)`。这意味着一个用户只能拥有一个助手吗？这似乎与能够获取“助手列表”(`get_assistant_list`) 的功能有些矛盾。请确认一下这里的业务逻辑，一个用户是否应该能创建多个助手？如果是，我们需要移除 `username` 字段的 `unique=True` 约束。[是,请移除 `username` 字段的 `unique=True` 约束。]
  - **`session_id` 字段:** `Assistant` 模型中有一个 `session_id: Optional[str]` 字段。但一个助手通常会关联多个会话。这个字段的用途是什么？是否是早期设计的遗留，可以移除？[是,可以移除。]

- **FR-ASST-002: 查看用户拥有的助手列表**

  - **显示信息:** 调用 `GET /assistant?username={username}` 返回助手列表时，前端界面上通常会显示哪些信息？是只显示 `title`，还是会显示 `title` 和部分 `prompt` 或关联的 `knowledge_Id`？[显示全部信息。]
  - **排序:** 当前代码是按 `created_at` 降序排序，这个排序方式符合需求吗？[希望新创建的助手排在前面，所以希望按 `created_at` 升序排序。]

- **FR-ASST-003: 编辑助手**

  - **允许修改字段:** 代码 `update_assistant` 服务函数目前只更新 `title`, `prompt`, `knowledge_Id`。确认这是所有允许用户编辑的字段吗？（`username` 和 `created_at` 不可编辑）。[是的,源代码正确的]

- **FR-ASST-004: 删除助手**
  - **确认:** 删除助手是一个破坏性操作，尤其因为它会删除关联的会话。在前端界面调用 `DELETE /assistant?assistant_id={...}` 之前，是否应该有明确的二次确认提示框？（例如：“确定要删除助手 [助手名称] 及其所有会话记录吗？”）[是的,前端需要有二次确认提示,弹出确认框]
  - **关联数据处理:** PRD 中需要明确记录：删除助手时，系统会自动查找并删除所有与该助手 `assistant_id` 相关联的 `Session` 文档，并调用 `ChatSev.clear_history` 清除这些会话的聊天记录。这一点与代码实现一致。[是的]
