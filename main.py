from fastapi import FastAPI
from Routers.auth_router import router as auth_router
from Routers.case_router import router as case_router
from Routers.user_router import router as user_router  
from Routers.client_router import router as client_router
from Routers.hearing_router import router as hearing_router
from Routers.doc_router import router as doc_router 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from Utils.jwt_handler import verify_access_token

app = FastAPI(title="LexCase API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(case_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(client_router, prefix="/api/v1")
app.include_router(hearing_router, prefix="/api/v1")
app.include_router(doc_router, prefix="/api/v1")

@app.middleware("http")
async def auth_middleware(request, call_next):

    # these routes don't need a token
    open_routes = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/change_password",
        "/api/v1/auth/forgot_password",
        "/api/v1/auth/reset_password",
    ]

    if request.url.path in open_routes:
        response = await call_next(request)
        return response

    # all other routes need a valid JWT token
    auth_header = request.headers.get("authorization")

    if auth_header is None:
        return JSONResponse(status_code=403, content={"error": "unauthorized"})

    try:
        token = auth_header.split(" ")[1]
    except IndexError:
        return JSONResponse(status_code=403, content={"error": "invalid authorization header format"})

    decode = verify_access_token(token)

    if decode is None:
        return JSONResponse(status_code=403, content={"error": "unauthorized"})

    request.state.user_id = decode.get("id")
    request.state.email = decode.get("email")

    response = await call_next(request)
    return response