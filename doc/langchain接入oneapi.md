（1）部署 OneAPI
Docker 快速启动：

bash
复制
docker run -d --name oneapi \
 -p 3000:3000 \
 -e SQLITE_DB_PATH=/data/oneapi.db \
 -v ~/oneapi/data:/data \
 justsong/oneapi
访问 http://localhost:3000（默认账号 root/123456）。

配置模型：
在 OneAPI 后台添加支持的模型（如 OpenAI、Claude、本地 LLaMA），填写对应 API Key。

（2）修改 LangChain 项目代码
假设你的原代码直接调用 OpenAI：

python
复制
from langchain.llms import OpenAI

llm = OpenAI(model="gpt-4", api_key="sk-xxx") # 直接依赖 OpenAI
改造为通过 OneAPI 调用：

python
复制
from langchain.llms import OpenAI

# 指向 OneAPI 的代理地址（替换原来的 OpenAI 基址）

ONEAPI_BASE_URL = "http://localhost:3000/v1" # OneAPI 的 OpenAI 兼容端点
ONEAPI_API_KEY = "oneapi-生成的密钥" # 在 OneAPI 后台创建

llm = OpenAI(
model="gpt-4", # 实际模型由 OneAPI 路由决定（可在后台配置映射）
api_key=ONEAPI_API_KEY,
base_url=ONEAPI_BASE_URL # 关键修改：将请求转发到 OneAPI
)
