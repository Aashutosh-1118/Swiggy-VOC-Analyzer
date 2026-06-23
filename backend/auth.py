import os
from fastapi import Header, HTTPException

API_KEY = os.getenv("API_KEY")


def verify_api_key(x_api_key: str = Header(...)):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfigured: no API_KEY set")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True