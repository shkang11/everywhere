from fastapi import APIRouter, Request, Depends, HTTPException
from schemas import UserCreate, UserLogin, FreeCreate, FreeUpdate, QuestionCreate, QuestionUpdate, ShareCreate, ShareUpdate 
from models import User, Free, Question, Share
from dependencies import get_db, get_password_hash, verify_password
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import Base, engine
from fastapi.responses import RedirectResponse

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


## 우리동네 자유게시판 글쓰기 - 비동기 처리
@router.post("/frees/")
async def create_free(request: Request, free: FreeCreate, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    
    # 세션에는 username이 있는데 db에 username이 없는 경우(해킹당한?경우)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_free = Free(user_id=user.id, username=username, title=free.title, content=free.content)
    db.add(new_free) # 여기는 db를 직접 쓰는 부분이 아니라 await안씀
    await db.commit()
    await db.refresh(new_free)
    return new_free

## 우리동네 자유게시판 글조회 - 비동기 처리
@router.get("/frees/")
async def list_frees(request: Request, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #result = await db.execute(select(Free).where(Free.user_id==user.id))
    result = await db.execute(select(Free))
    frees = result.scalars().all()
    return templates.TemplateResponse("frees.html", {"request": request, "frees": frees, "username": username})

## 우리동네 자유게시판 글 수정 - 비동기 처리
@router.put("/frees/{free_id}")
async def update_free(request: Request, free_id: int, free: FreeUpdate, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Free).where(Free.user_id==user.id, free_id==Free.id))
    db_free = result.scalars().first()
    if db_free is None:
        return {"error": "Writing not found"}
   
    if free.title is not None:
        db_free.title = free.title 
    if free.content is not None:
        db_free.content = free.content
    
    await db.commit()
    await db.refresh(db_free) 
    return db_free
  
## 우리동네 자유 게시판 글 삭제 - 비동기 처리
@router.delete("/frees/{free_id}")
async def delete_free(request: Request, free_id: int, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Free).where(Free.user_id==user.id, free_id==Free.id))
    db_free = result.scalars().first()
    if db_free is None:
        return {"error": "Writing not found"}
   
    await db.delete(db_free)
    await db.commit()
    return {"message": "Writing deleted"}

## 주민에게 질문해요 게시판 글쓰기 - 비동기 처리
@router.post("/questions/")
async def create_question(request: Request, question: QuestionCreate, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    
    # 세션에는 username이 있는데 db에 username이 없는 경우(해킹당한?경우)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_question = Question(user_id=user.id, username=username, title=question.title, content=question.content)
    db.add(new_question) # 여기는 db를 직접 쓰는 부분이 아니라 await안씀
    await db.commit()
    await db.refresh(new_question)
    return new_question

## 주민에게 질문해요 게시판 글조회 - 비동기 처리
@router.get("/questions/")
async def list_questions(request: Request, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #result = await db.execute(select(Question).where(Question.user_id==user.id))
    result = await db.execute(select(Question))
    questions = result.scalars().all()
    return templates.TemplateResponse("questions.html", {"request": request, "questions": questions, "username": username})

## 주민에게 질문해요 글 수정 - 비동기 처리
@router.put("/questions/{question_id}")
async def update_question(request: Request, question_id: int, question: QuestionUpdate, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Question).where(Question.user_id==user.id, question_id==Question.id))
    db_question = result.scalars().first()
    if db_question is None:
        return {"error": "Writing not found"}
   
    if question.title is not None:
        db_question.title = question.title 
    if question.content is not None:
        db_question.content = question.content
    
    await db.commit()
    await db.refresh(db_question) 
    return db_question
  
## 주민에게 질문해요 게시판 글 삭제 - 비동기 처리
@router.delete("/questions/{question_id}")
async def delete_question(request: Request, question_id: int, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Question).where(Question.user_id==user.id, question_id==Question.id))
    db_question = result.scalars().first()
    if db_question is None:
        return {"error": "Writing not found"}
   
    await db.delete(db_question)
    await db.commit()
    return {"message": "Writing deleted"}

## 우리동네 나눔해요 글쓰기 - 비동기 처리
@router.post("/shares/")
async def create_share(request: Request, share: ShareCreate, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    
    # 세션에는 username이 있는데 db에 username이 없는 경우(해킹당한?경우)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    new_share = Share(user_id=user.id, username=username, title=share.title, content=share.content)
    db.add(new_share) # 여기는 db를 직접 쓰는 부분이 아니라 await안씀
    await db.commit()
    await db.refresh(new_share)
    return new_share

## 우리동네 나눔해요 글조회 - 비동기 처리
@router.get("/shares/")
async def list_shares(request: Request, db: AsyncSession = Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    #result = await db.execute(select(Share).where(Share.user_id==user.id))
    result = await db.execute(select(Share))
    shares = result.scalars().all()
    return templates.TemplateResponse("shares.html", {"request": request, "shares": shares, "username": username})

## 우리동네 나눔해요 글 수정 - 비동기 처리
@router.put("/shares/{share_id}")
async def update_share(request: Request, share_id: int, share: ShareUpdate, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Share).where(Share.user_id==user.id, share_id==Share.id))
    db_share = result.scalars().first()
    if db_share is None:
        return {"error": "Writing not found"}
   
    if share.title is not None:
        db_share.title = share.title 
    if share.content is not None:
        db_share.content = share.content
    
    await db.commit()
    await db.refresh(db_share) 
    return db_share
  
## 우리동네 나눔해요 글 삭제 - 비동기 처리
@router.delete("/shares/{share_id}")
async def delete_share(request: Request, share_id: int, db: AsyncSession=Depends(get_db)):
    username = request.session.get("username") # 쿠키에서 가져온 username
    if username is None:
        raise HTTPException(status_code=401, detail="Not authorized")
    result = await db.execute(select(User).where(User.username==username))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(select(Share).where(Share.user_id==user.id, share_id==Share.id))
    db_share = result.scalars().first()
    if db_share is None:
        return {"error": "Writing not found"}
   
    await db.delete(db_share)
    await db.commit()
    return {"message": "Writing deleted"}

# 홈화면 조회
@router.get("/home")
async def list_boards(request: Request):
    username = request.session.get("username")
    if username is None:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/about")
async def about():
    return {"message": "이것은 동네별 커뮤니티 에브리웨어 소개 페이지입니다."}