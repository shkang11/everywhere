from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # 비동기처리
from sqlalchemy.ext.declarative import declarative_base
from mysqlpw import pw # 깃허브에 올릴거라서 내 비번은 mysqlpw.py에 pw변수에 넣어 가져옴
                        # 그리고 mysql.pw는 .gitignore에 추가하여 깃에서 추적안하게함
# 데이터베이스 접속

DATABASE_URL = f"mysql+aiomysql://root:{pw}@localhost/real_capybara_everywhere"

# 비동기 처리 - 접속
engine = create_async_engine(DATABASE_URL, echo=True) # 엔진으로 db접속

# 비동기 처리 - 세션 생성
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession) 

Base = declarative_base()
