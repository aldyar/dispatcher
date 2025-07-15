from fastapi import FastAPI
from router.lead_router import router
import uvicorn
from database.models import async_main

app = FastAPI(
    title="Lead API",
    version="1.0.0"
)

app.include_router(router)


@app.on_event("startup")
async def on_startup():
    await async_main() 


if __name__ == '__main__':
    uvicorn.run('main:app',host ='0.0.0.0',port = 5001)