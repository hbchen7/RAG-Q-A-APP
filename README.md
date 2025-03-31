#

# 技术栈

- Python 3.10.6
- FastAPI // web 框架
- unicorn // web 服务框架

# 项目结构

- main.py // 项目入口文件
- src // 项目主目录
- tests // 测试用例目录
- requirements.txt // 项目依赖文件
- Dockerfile // 项目打包文件

# 运行项目指导

```
## 安装依赖
pdm install -r requirements.txt
```

```
## 运行项目
uvicorn main:app --reload
```
