from fastapi import FastAPI
from app.routers.category import router as router_category

app = FastAPI()
app.include_router(router_category)


@app.get("/")
async def welcome() -> dict:
    return {"message": "My e-commerce app"}