from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

app = FastAPI(
    title="Debug API",
    description="Logs all incoming requests with headers, parameters, and body",
    version="1.0.0",
)


class ProductList(BaseModel):
    urls: List[str]


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    headers = dict(request.headers)
    headers["bypass-tunnel-reminder"] = "1"
    response = await call_next(request)

    return response


@app.post("/order")
async def create_order(request: Request, data: ProductList):
    headers = dict(request.headers)
    query_params = dict(request.query_params)

    print(f"Headers: {headers}")
    print(f"Received JSON: {data.dict()}")
    print(f"Query Params: {query_params}")

    return {
        "status": "OK",
        "headers": headers,
        "query_params": query_params,
        "body": data.dict(),
    }
