## 2025 年 4 月 14 日: 知识库架构重构：支持多文件和元数据过滤

- **实现功能**:
  - 重构知识库管理功能，支持在一个逻辑知识库（对应 MongoDB 中的 `KnowledgeBase` 文档）下上传和管理多个文件。
  - 使用 `KnowledgeBase` 文档的 `_id` 作为对应 ChromaDB 集合的名称。
  - 文件上传接口 (`POST /knowledgebases/{kb_id}/files/`) 改为接受 `UploadFile`。
  - 在文件向量化时，为每个文档块添加元数据，包括 `knowledge_base_id`, `source_file_path`, `source_file_md5`, `source_file_name`。
  - RAG 聊天接口 (`POST /chat/`) 支持通过 `knowledge_base_id` 选择知识库，并通过可选的 `filter_by_file_md5` 参数实现对特定文件的检索。
  - 移除了之前使用 JSON 文件或单独 MongoDB 集合存储文件路径到集合名映射的逻辑。
- **实现过程步骤**:
  1. 设计并确认新的架构方案，明确使用 `KnowledgeBase._id` 作为集合名，并通过元数据过滤实现细粒度检索。
  2. 重构 `src/utils/Knowledge.py`：
     - 添加 `add_file_to_knowledge_base` 方法处理文件向量化、元数据注入和 Chroma 存储（支持首次创建和后续添加）。
     - 修改 `get_retriever_for_knowledge_base` (原 `get_retrievers`) 以接受 `kb_id` 和 `filter_dict`。
     - 移除旧的基于文件路径映射的方法。
  3. 修改 `src/router/knowledgeRouter.py`：
     - 更新文件上传接口以使用 `UploadFile` 和 `Form`。
     - 调整接口路径和错误处理。
     - 实现删除知识库接口 (`DELETE /{kb_id}`)。
  4. 修改 `src/service/knowledgeSev.py`：
     - 实现 `process_uploaded_file` 函数处理文件上传、MD5 检查、调用 `Knowledge` 类和更新 MongoDB (`KnowledgeBase` 的 `filesList`)。
     - 实现 `delete_knowledge_base` 函数删除 MongoDB 文档和 Chroma 目录。
  5. 修改 `src/service/ChatSev.py`：
     - 更新 `invoke` 方法以接受 `knowledge_base_id` 和 `filter_by_file_md5`。
     - 根据参数动态构建 RAG 链或普通链，调用 `Knowledge.get_retriever_for_knowledge_base`。
     - 移除旧的 `get_chain` 方法。
  6. 修改 `src/router/chatRouter.py`：
     - 更新请求体模型 `ChatRequest` 和 `KnowledgeConfig`。
     - 更新聊天接口逻辑以匹配 `ChatSev.invoke` 的新参数。
- **重难点**:
  - 确保文件处理流程的健壮性，包括临时文件管理和异常处理。
  - 理解并正确使用 ChromaDB 的集合管理和元数据过滤功能（通过 LangChain 接口）。
  - 协调多个服务和工具类之间的数据流和依赖关系。
  - 确保操作的原子性（先更新 Chroma，再更新 MongoDB）。
  - 异步函数中调用同步库（如 ChromaDB 操作）的潜在性能影响（暂未优化）。
