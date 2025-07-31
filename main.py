import uvicorn
from fastapi import FastAPI
from app.routers.category import router as router_category
from app.routers.products import router as router_products
from app.routers.auth import router as router_auth
from app.routers.permission import router as router_permission

app = FastAPI()
app.include_router(router_category)
app.include_router(router_products)
app.include_router(router_auth)
app.include_router(router_permission)


@app.get("/")
async def welcome() -> dict:
    return {"message": "My e-commerce app"}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)