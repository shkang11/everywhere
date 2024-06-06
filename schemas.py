from pydantic import BaseModel
from typing import Optional

# 파이덴틱 모델들 (클라이언트에서 데이터 받아오기위한 모델들)

# 회원가입 시 데이터 검증
class UserCreate(BaseModel):
    username: str
    email: str
    password: str # 해시 전 패스워드를 받습니다.

# 회원 로그인 시 데이터 검증
class UserLogin(BaseModel):
    username: str
    password: str # 해시 전 패스워드를 받습니다.

class FreeCreate(BaseModel):
    title: str
    content: str

class FreeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None