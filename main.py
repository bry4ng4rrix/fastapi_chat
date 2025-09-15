from fastapi import FastAPI 
from database import create_db_and_tables , get_session
from routers.user import router as users_router
from routers.message import router as messages_router
from routers.auth import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/user")
app.include_router(messages_router, prefix="/message")
## create database
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000 ,reload=True)