from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession # 비동기처리
from sqlalchemy.ext.declarative import declarative_base

# 데이터베이스 접속

DATABASE_URL = "mysql+aiomysql://root:rkdtjgus**M7@localhost/real_capybara_everywhere"

# 비동기 처리 - 접속
engine = create_async_engine(DATABASE_URL, echo=True) # 엔진으로 db접속

# 비동기 처리 - 세션 생성
AsyncSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    class_=AsyncSession) 

Base = declarative_base()
