from datetime import date
from decimal import Decimal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.policy import check_claim


class Claim(BaseModel):
    employee: str
    merchant: str
    category: str
    amount: Decimal = Field(allow_inf_nan=False)  # NaN and Infinity are malformed input: HTTP 422
    expense_date: date
    has_receipt: bool


class CheckRequest(BaseModel):
    claim: Claim
    history: list[Claim] = []


app = FastAPI(title="Expense claim policy check")


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # FastAPI's default 422 echoes the bad input back, and NaN cannot be encoded as JSON,
    # which turned a clean 422 into a 500. Return location and message only.
    detail = [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/claims/check")
def check(req: CheckRequest):
    return check_claim(
        req.claim.model_dump(),
        [h.model_dump() for h in req.history],
        date.today(),
    )
