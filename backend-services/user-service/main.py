
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="GateFlow User Service",
    version="1.0.0"
)


users = [
    {
        "id": 1,
        "name": "Rohit",
        "role": "Developer"
    },
    {
        "id": 2,
        "name": "Alex",
        "role": "Administrator"
    },
    {
        "id": 3,
        "name": "Sam",
        "role": "Engineer"
    }
]


@app.get("/")
async def root():
    return {
        "service": "user-service",
        "status": "running"
    }


@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "service": "user-service"
    }


@app.get("/users")
async def get_users():

    return {
        "service": "user-service",
        "message": "Request successfully routed through GateFlow",
        "total": len(users),
        "users": users
    }


@app.get("/users/{user_id}")
async def get_user(user_id: int):

    user = next(
        (u for u in users if u["id"] == user_id),
        None
    )

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
