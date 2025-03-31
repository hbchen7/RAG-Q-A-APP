# 使用多阶段构建
FROM python:3.10-slim-bullseye as builder

# 设置工作目录
WORKDIR /app

# 首先只复制依赖相关文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
