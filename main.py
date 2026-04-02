from fastapi import FastAPI
from Routers.auth_router import router as auth_router
from Routers.case_router import router as case_router
from Routers.user_router import router as user_router  
from Routers.client_router import router as client_router
from Routers.hearing_router import router as hearing_router
from Routers.doc_router import router as doc_router 
from Routers.query_router import router as query_router
from Routers.chat_router import router as chat_router
from Routers.conversation_router import router as conversation_router
from Routers.dashboard_router import router as dashboard_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from Utils.jwt_handler import verify_access_token

app = FastAPI(title="LexCase API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(case_router)
app.include_router(user_router)
app.include_router(client_router)
app.include_router(hearing_router)
app.include_router(doc_router)
app.include_router(query_router)
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(dashboard_router)

@app.middleware("http")
async def auth_middleware(request, call_next):

    # these routes don't need a token
    open_routes = [
        "/auth/login",
        "/auth/register",
        "/auth/verify_registration",
        "/auth/change_password",
        "/auth/forgot_password",
        "/auth/reset_password",
    ]

    if request.url.path in open_routes or request.method == "OPTIONS":
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