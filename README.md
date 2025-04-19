# RAG-知识库问答系统

本项目是一个基于 Langchain、FastAPI 和 MongoDB 构建的 RAG (Retrieval-Augmented Generation) 知识库问答系统。

## 技术栈

- Python: v3.10.6+
- FastAPI: v0.75.0+ // Web 框架
- Uvicorn: v2.1.3+ // ASGI 服务器
- PDM: v2.23.1+ // 包和依赖管理工具
- Langchain: v0.3.21+ // 语言模型框架
- Beanie: v1.29.0+ // MongoDB 异步 ORM
- ChromaDB: (通过 `langchain-chroma`) // 向量数据库，用于存储文档嵌入
- MongoDB: // 主数据库，用于存储知识库元数据、聊天记录等

## 主要功能

- **知识库管理**:
  - 支持创建、删除逻辑知识库。
  - 支持向指定知识库上传多个文件（PDF, TXT, DOCX 等，具体取决于 `DocumentChunker` 实现）。
  - 每个知识库对应一个 ChromaDB 集合，集合名称为知识库的 MongoDB `_id`。
  - 文件向量块及其元数据（来源文件 MD5、路径、知识库 ID 等）存储在对应的 ChromaDB 集合中。
  - 知识库元数据（标题、描述、文件列表等）存储在 MongoDB 的 `knowledgeBase` 集合中。
- **RAG 问答**:
  - 基于 Langchain 实现 RAG 流程。
  - 调用 LLM（通过 OneAPI 或其他配置的提供商）进行问答。
  - 支持基于整个知识库进行检索问答。
  - 支持通过元数据过滤（指定文件 MD5）实现对知识库中特定文件的检索问答。
- **聊天记录管理**:
  - 使用 `langchain-mongodb` 的 `MongoDBChatMessageHistory` 将聊天记录持久化存储在 MongoDB 的 `chatHistoy` 集合中，按 `session_id` 区分不同会话。
- **RESTful API**: 基于 FastAPI 提供接口。

## 运行项目

1. 需要部署 [One API](https://github.com/songquanpeng/one-api) 作为大模型网关
2. 在.env 文件中配置数据库连接信息、 MONGO_URI 等环境变量。
3. 在项目根目录下运行:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8081
```

4. 浏览器访问 API 文档： `http://localhost:8081/docs`。

## 项目结构

```
.env                # 环境变量配置 (例如 MONGO_URI, ONEAPI_BASE_URL)
.gitignore
pdm.lock
pyproject.toml      # PDM 项目配置文件和依赖
README.md           # 项目说明

chroma/             # ChromaDB 本地持久化数据存储目录
                    # (每个子目录对应一个知识库集合, 目录名为知识库 MongoDB _id)

src/
├── __init__.py
├── main.py             # FastAPI 应用入口
├── config/             # 配置相关
│   ├── __init__.py
│   └── Beanie.py       # Beanie 初始化配置
├── models/             # 数据模型 (Beanie Documents)
│   ├── __init__.py
│   ├── knowledgeBase.py # 知识库元数据模型
│   ├── chat_history.py  # (如果需要自定义聊天记录模型，否则使用 Langchain 默认)
│   └── user.py          # 用户模型 (示例)
│   └── ...             # 其他 Beanie 模型
├── router/             # FastAPI 路由
│   ├── __init__.py
│   ├── chatRouter.py    # 聊天相关接口
│   ├── knowledgeRouter.py # 知识库管理相关接口
│   └── userAuthRouter.py # 用户认证相关接口 (示例)
├── service/            # 业务逻辑服务
│   ├── __init__.py
│   ├── ChatSev.py       # 聊天服务逻辑 (RAG 链处理)
│   ├── knowledgeSev.py  # 知识库管理服务逻辑
│   └── userSev.py       # 用户服务逻辑 (示例)
├── utils/              # 工具类
│   ├── __init__.py
│   ├── DocumentChunker.py # 文档加载与分块逻辑
│   ├── embedding.py     # 获取 Embedding 模型的工具函数
│   ├── Knowledge.py     # 与 ChromaDB 交互的工具类
│   └── llm_modle.py     # 获取 LLM 实例的工具函数
└── ...

doc/
├── evLog.md            # 开发演进日志
└── ErrorLog.md         # 错误记录

tests/                  # 测试代码目录
```

## 环境依赖与安装

1.  **安装 PDM**: 如果尚未安装，请参照 PDM 官方文档安装。
2.  **安装项目依赖**: 在项目根目录下运行：
    ```bash
    pdm install
    ```
3.  **配置环境变量**: 创建 `.env` 文件，并根据需要配置以下变量 (示例):
    ```env
    MONGO_URI=mongodb://localhost:27017
    MONGO_DB_NAME=fastapi_rag
    MONGODB_COLLECTION_NAME_CHATHISTORY=chatHistoy
    # ONEAPI 相关配置 (如果使用)
    ONEAPI_BASE_URL=http://localhost:3000
    # 其他 API Keys 等...
    ```
4.  **启动外部服务**: 确保 MongoDB 服务正在运行。

## 相关项目-特此鸣谢

- [One API](https://github.com/songquanpeng/one-api)
