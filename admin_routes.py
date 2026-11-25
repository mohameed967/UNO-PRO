import os,hmac
from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from database import store
router=APIRouter()
class Login(BaseModel):
    username:str
    password:str
class Ban(BaseModel):
    banned:bool
def auth(req):
    if not req.session.get("admin"): raise HTTPException(401,"سجّل الدخول أولاً")
    return req.session["admin"]
@router.get("/admin")
async def page(): return FileResponse("admin/dashboard.html")
@router.post("/admin/api/login")
async def login(x:Login,req:Request):
    u=os.getenv("ADMIN_USERNAME","owner"); p=os.getenv("ADMIN_PASSWORD","")
    if not p: raise HTTPException(503,"اضبط ADMIN_PASSWORD في متغيرات البيئة")
    if not(hmac.compare_digest(x.username,u) and hmac.compare_digest(x.password,p)): raise HTTPException(401,"بيانات الدخول غير صحيحة")
    req.session.clear(); req.session["admin"]=u; store.log_action(u,"login")
    return {"ok":True}
@router.post("/admin/api/logout")
async def logout(req:Request): req.session.clear(); return {"ok":True}
@router.get("/admin/api/me")
async def me(req:Request): return {"username":auth(req)}
@router.get("/admin/api/stats")
async def stats(req:Request): auth(req); return store.stats()
@router.get("/admin/api/users")
async def users(req:Request,q:str=""): auth(req); return store.list_users(q[:80])
@router.post("/admin/api/users/{uid}/ban")
async def ban(uid:str,x:Ban,req:Request):
    actor=auth(req)
    if not store.set_banned(uid,x.banned): raise HTTPException(404,"المستخدم غير موجود")
    store.log_action(actor,"ban" if x.banned else "unban",uid); return {"ok":True}
@router.get("/admin/api/admins")
async def admins(req:Request): auth(req); return store.list_admins()
@router.get("/admin/api/logs")
async def logs(req:Request): auth(req); return store.logs()
