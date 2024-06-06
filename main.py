from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from database import Base, engine
from controllers import router
from contextlib import asynccontextmanager

# 비동기 처리 <- 기존: Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # 애플리케이션 시작 시 실행될 로직
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) #db에 테이블없으면 테이블 생성
    yield
    # 애플리케이션 종료 시 실행될 로직(필요할 경우)

# FastAPI 애플리케이션 초기화
# Swagger UI와 Redoc 도 비활성화 한다.
app = FastAPI(lifespan=app_lifespan, docs_url=None, redoc_url=None) # FastAPI객체 만들기, 비동기처리: lifespan에 함수명넣기
app.add_middleware(SessionMiddleware, secret_key="your-secret-key") #객체에 세션미들웨어추가    
app.include_router(router) # controllers.py에 APIRouter로 정의한 라우터를 fastapi객체인 app에 등록
templates = Jinja2Templates(directory="templates")

@app.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse('loginSignUp.html', {"request": request})
