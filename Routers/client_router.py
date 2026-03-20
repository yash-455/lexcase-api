from fastapi import APIRouter, Request
from typing import Optional
from Models.client_model import ClientCreate, ClientUpdate, ClientResponse
from Controller.client_controller import add_client, get_clients, get_client, get_client_cases, update_client, delete_client

router = APIRouter(prefix="/clients", tags=["clients"])

# add new clients
@router.post("/add", response_model=ClientResponse, status_code=201)
async def create_client(client: ClientCreate, request: Request):
    user_id = request.state.user_id
    return await add_client(client, user_id)

# GET /clients?search=
@router.get("/get_all")
async def search_clients(request: Request, search: Optional[str] = None):
    user_id = request.state.user_id
    return await get_clients(search, user_id)


# GET /clients/{client_id}
@router.get("/get/{client_id}")
async def get_client_by_id(client_id: str):
    return await get_client(client_id)


# GET /clients/{client_id}/cases
@router.get("/get/{client_id}/cases")
async def get_cases_by_client(client_id: str):
    return await get_client_cases(client_id)


# PUT /clients/{client_id}
@router.put("/update/{client_id}")
async def update_client_by_id(client_id: str, update_data: ClientUpdate, request: Request):
    user_id = request.state.user_id
    return await update_client(client_id, update_data, user_id)


# DELETE /clients/{client_id}
@router.delete("/delete/{client_id}")
async def delete_client_by_id(client_id: str, request: Request):
    user_id = request.state.user_id
    return await delete_client(client_id, user_id)