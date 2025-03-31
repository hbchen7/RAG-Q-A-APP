from fastapi import APIRouter
from fastapi import File
fileRouter = APIRouter()

@fileRouter.post('/upload',summary="上传文件")
async def upload_file(file: bytes =File(...)):
    print(file)



