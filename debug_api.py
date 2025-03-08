from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Debug API",
    description="Logs all incoming requests with headers, parameters, and body",
    version="1.0.0",
)


class ProductList(BaseModel):
    urls: List[str]


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    request.headers.__dict__["_dict"]["bypass-tunnel-reminder"] = "1"

    response = await call_next(request)

    logger.info(f"Final headers in response: {dict(response.headers)}")

    return response


@app.post("/order")
async def create_order(request: Request, data: ProductList):
    headers = dict(request.headers)
    logger.info(f"Headers: {headers}")

    logger.info(f"Received JSON: {data.dict()}")

    query_params = dict(request.query_params)
    logger.info(f"Query Params: {query_params}")

    return {
        "status": "OK",
        "headers": headers,
        "query_params": query_params,
        "body": data.dict(),
    }
