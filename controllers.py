from fastapi import APIRouter, Request, Depends, HTTPException
from schemas import UserCreate, UserLogin, WritingCreate, WritingUpdate
from models import User, Writing
from dependencies import get_db, get_password_hash, verify_password
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import Base, engine

# API 들 나열 - 컨트롤러의 핵심

router = APIRouter() # APIRouter로 정의한 라우터
templates = Jinja2Templates(directory='templates')

# 회원 가입 - db처리관련 부분은 모두 await처리로 비동기 처리
@router.post("/signup")                     # 비동기 세션을 받도록 AsyncSession으로 변경
async def signup(signup_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username==signup_data.username))
    # 먼저 username이 이미 존재하는지 확인
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail= "이미 동일 사용자 이름이 가입되어 있습니다.")
    

    hashed_password = get_password_hash(signup_data.password)
    new_user = User(username=signup_data.username, email=signup_data.email, hashed_password=hashed_password)
    db.add(new_user)
    try:
        await db.commit()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="회원가입이 실패했습니다. 기입한 내용을 확인해보세요.")

    await db.refresh(new_user)
    return {"message": "회원가입을 성공했습니다."}

# 비동기 처리 - db쓰는 부분은 await처리로 속도를 높임
# 로그인 (세션의 관리를 위해 Request를 인자로 넣어놓음) -> 로그인하면 클라이언트에 쿠키값 저장
# 그래서 그다음 부터 요청시 해당 쿠키값과 함께 보내진다
@router.post("/login")
async def login(request: Request, signin_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username==signin_data.username))
    user = result.scalars().first()
    if user and verify_password(signin_data.password, user.hashed_password):
        request.session["username"] = user.username
        return {"message": "로그인을 성공했습니다."}
    else:
        raise HTTPException(status_code=401, detail="로그인을 실패했습니다.")
                            ## 401은 인증이 안됐을때 오류코드

# 로그 아웃 (세션 처리를 위해 인자에 Request가 있음)
# 로그아웃 요청할 때도 역시 동일 쿠키값이 전송된다. 이 쿠키값을 기반으로 특정
# 세션을 알아내고 그 세션에 있는 유저 네임을 삭제함으로 해당 아이디는 로그아웃된다.
@router.post("/logout")
async def logout(request: Request):
    request.session.pop("username", None)
    return {"message": "로그아웃이 성공했습니다."}


## 글쓰기 - 비동기 처리
@router.post("/writings/")
async def create_writing(request: Request, writing: WritingCreate, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    
    # 세션에는 username이 있는데 db에 username이 없는 경우(해킹당한?경우)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_writing = Writing(user_id=user.id, title=writing.title, content=writing.content)
    db.add(new_writing) # 여기는 db를 직접 쓰는 부분이 아니라 await안씀
    await db.commit()
    await db.refresh(new_writing)
    return new_writing

## 글조회 - 비동기 처리
@router.get("/writings/")
async def list_writings(request: Request, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Writing).where(Writing.user_id==user.id))
    writings = result.scalars().all()
    return templates.TemplateResponse("writings.html", {"request": request, "writings": writings, "username": username})

## 글 수정 - 비동기 처리
@router.put("/writings/{writing_id}")
async def update_writing(request: Request, writing_id: int, writing: WritingUpdate, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Writing).where(Writing.user_id==user.id, writing_id==Writing.id))
    db_writing = result.scalars().first()
    if db_writing is None:
        return {"error": "Writing not found"}
   
    if writing.title is not None:
        db_writing.title = writing.title 
    if writing.content is not None:
        db_writing.content = writing.content
    
    await db.commit()
    await db.refresh(db_writing) 
    return db_writing
  
## 글 삭제 - 비동기 처리
@router.delete("/writings/{writing_id}")
async def delete_writing(request: Request, writing_id: int, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Writing).where(Writing.user_id==user.id, writing_id==Writing.id))
    db_writing = result.scalars().first()
    if db_writing is None:
        return {"error": "Writing not found"}
   
    await db.delete(db_writing)
    await db.commit()
    return {"message": "Writing deleted"}

@router.get("/about")
async def about():
    return {"message": "이것은 동네별 커뮤니티 에브리웨어 소개 페이지입니다."}