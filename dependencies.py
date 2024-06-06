from passlib.context import CryptContext
from database import AsyncSessionLocal # 비동기

# dependencies.py 에 있는것은 main.py나 컨트롤러파일들에 넣어도되는데
# 아래와 같은 것들을 여러 api그룹들에서 쓴다고 생각하면 공통적인 코드를 그룹마다
# 넣어야하기에 공통적으로 쓰는 코드를 dependencies.py 파일로 따로 뺴놓은것

## 인크립션 선언부분
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 패스워드 해싱하는 함수
def get_password_hash(password):
    return pwd_context.hash(password)


# 패스워드 검증하는 함수
            ## 사용자가 입력하는 pw, 데이터베이스에 변환(해시)돼서 들어간 pw
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 비동기 처리
# 세션 리턴 - 비동기
# 데이터베이스 API 사용시 해당 get_db()호출하여 세션을 만들어서 db작업가능
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        await session.commit()
       #await session.close()  원래는 세션을 닫아줘야하지만 with문으로 열었기에 자동으로 닫아주니까 안써준다.