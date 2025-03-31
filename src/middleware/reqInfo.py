from fastapi import  Request
from main import app

  # 打印请求信息
@app.middleware("http")
async def startup( request: Request, next):

  print(f"URL: {request.url}")
  # 打印IP地址
  print(f"IP: {request.client.host}")
  # 打印请求方法
  response = await next(request)
  return response  