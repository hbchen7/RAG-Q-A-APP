#

# 技术栈

- Python v3.10.6
- FastAPI v0.75.0 // web 框架
- unicorn v2.1.3// web 服务框架
- pdm v2.23.1 // 包管理工具
- chroma v0.2.0// 向量数据库
- Beanie v1.29.0 // MongoDB ORM

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

# 相关项目-特此鸣谢

- [One API](https://github.com/songquanpeng/one-api)
