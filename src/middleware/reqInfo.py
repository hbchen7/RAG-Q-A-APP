from fastapi import Request


async def request_info_middleware(request: Request, call_next):
    print(f"请求方法: {request.method}, 路径: {request.url.path}")
    response = await call_next(request)
    return response
