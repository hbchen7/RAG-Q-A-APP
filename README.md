# RAG-知识库问答系统

本项目是一个基于 Langchain、FastAPI、Chroma 和 MongoDB 构建的 RAG (Retrieval-Augmented Generation) 知识库问答系统。

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

## 运行项目

### docker 运行(推荐)

1. 确保安装了 docker 环境 ->[Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. 需要使用 docker 部署 [One API](https://github.com/songquanpeng/one-api) 作为大模型网关，在 docker-compose.yml 为每个服务添加`    - baota_net # 添加对共享外部网络的连接`,接着运行`docker compose up -d`
3. 在 fastapi 项目的.env 文件中配置你的数据库连接信息等环境变量。
4. 在项目根目录下依次运行:

```bash
docker network create baota_net
```

```bash
docker-compose up --build
```

5. 运行成功后，即可访问 API 文档： `http://localhost:8080/docs`。

### 本地运行

1. 确保安装了 Python 环境 (v3.10.6+)、安装 MongoDB 数据库 (v5.0+)
2. 需要使用 docker 部署 [One API](https://github.com/songquanpeng/one-api) 作为大模型网关，部署教程：
3. 安装 pdm: `pip install pdm`
4. 在项目根目录.env 文件中配置数据库连接信息、 MONGODB_URL 等环境变量。
5. 在项目根目录下依次运行:

```bash
pdm init # 初始化 PDM 项目，创建虚拟环境
```

```bash
pdm install # 安装项目依赖
```

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080 # 启动 FastAPI 应用
```

4. 浏览器访问 API 文档： `http://localhost:8080/docs`。

# 项目博客

- [langchain 项目如何实现流式输出经验分享](https://blog.csdn.net/m0_70647377/article/details/147422163)

# 关于作者

- ~~[个人网站]()~~:挖坑待填,敬请期待~
- [Github](https://github.com/hbchen7)
- [CSDN](https://blog.csdn.net/m0_70647377?spm=1000.2115.3001.5343)
- [BiliBili](https://space.bilibili.com/1608655290)

# 特此鸣谢

- [One API](https://github.com/songquanpeng/one-api)
- [langchain-API 文档](https://python.langchain.com/api_reference/)

# 特此鸣谢

- [One API](https://github.com/songquanpeng/one-api)
- [langchain-API 文档](https://python.langchain.com/api_reference/)
