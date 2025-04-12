# PRD

**针对 4.4. 会话管理 (Session Management)**

- **模型字段澄清:**

  - **`Session.username` 唯一性:** `Session` 模型中的 `username` 字段也被标记为 `Indexed(unique=True)`。这同样意味着一个用户只能有一个会话吗？根据 `get_session_list` 函数（可以获取用户的所有会话），这应该是不对的。请确认一个用户可以创建多个会话，如果是，我们需要移除 `Session.username` 的 `unique=True` 约束。[是，移除 `Session.username` 的 `unique=True` 约束。]
  - **`assistant_name` 缺失:** `sessionSev.create_session` 函数的实现和 `SessionCreate` 模型中提到了 `assistant_name`，但 `Session` 模型中并没有这个字段。是应该在 `Session` 模型中添加 `assistant_name` 字段，还是说创建会话时不需要传递或存储 `assistant_name`？[不需要,值需要 assistant_id 字段用于关联助手,并作查询条件]

- **FR-SESS-001: 创建新会话**

  - **基于助手:** 创建会话时，前端需要传递 `assistant_id`，这表示每个会话都必须关联一个助手。[是的]
  - **默认标题:** `SessionCreate` 模型中 `title` 的默认值是 "新会话"。这符合预期吗？[是的]

- **FR-SESS-002: 查看用户会话列表**

  - **分组与排序:** 调用 `GET /list?username={username}` 返回会话列表时，前端界面会如何展示？是按照助手分组显示，还是直接一个列表？当前的排序方式是按 `Session.date` 降序（`Session` 模型中没有 `date` 字段，`sessionSev.py` 的实现用的是 `Session.date`，但 `session.py` 模型里是 `created_at` 和 `updated_at`，这里代码和模型有不一致，应该按哪个字段排序？通常是按 `updated_at` 或 `created_at` 降序）。[前端界面会按照助手分组显示,具体分为助手列表和会话列表,它们分别位于两个选项卡中,点击助手进入对应的会话列表，会话列表按 `Session.updated_at` 降序排序,这是在修改模型后,sessinSev 没有更新,请以模型为准,更新 sessinSev.py]
  - **显示信息:** 列表中通常显示会话的哪些信息？`title`? 创建时间/更新时间? 关联的助手名称（如果模型添加了该字段）？[会话只显示 `title` 和 `updated_at` 字段,将用于计算会话最后活跃时间是几天前,不需要显示助手名称]

- **FR-SESS-003: 修改会话标题**

  - (这部分比较明确，根据 `session_id` 更新 `title` 字段。)

- **FR-SESS-004: 删除会话**

  - **确认:** 同删除助手，删除会话也会删除历史记录。在前端调用 `DELETE /{session_id}/delete` 之前，是否应该有二次确认提示？[是的,需要二次确认,该确认框可以二次封装 elementplus 的弹窗组件复用]
  - **关联数据处理:** PRD 需要记录：删除会话时，系统会调用 `ChatSev.clear_history` 清除该会话的聊天记录。

- **FR-SESS-005: 查看会话历史消息**
  - **API:** 目前的代码中似乎没有提供明确的 API 来获取单个会话的详细历史消息列表。这个功能是如何实现的？是包含在 RAG 问答流程中，还是需要一个单独的 API (例如 `GET /session/{session_id}/messages`)？[后者,需要单独的 API]
  - **分页:** 如果历史消息很多，是否需要分页加载？每次加载多少条？
  - **显示格式:** 聊天记录通常需要显示 quién (用户或 AI)、内容、时间戳等。

---

请根据你的理解和项目预期，逐一回答以上问题。你的回答将帮助我们把 PRD 的这两个功能部分描述得更清晰、准确。一次性回答所有问题也没关系，我会整理你的答案并更新到 PRD 描述中。
