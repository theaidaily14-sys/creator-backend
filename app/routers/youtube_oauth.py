from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from urllib.parse import urlencode
import httpx
from cryptography.fernet import Fernet
from datetime import datetime, timezone

from app.config import settings
from app.deps import get_db, get_current_user
from app import models

router = APIRouter(prefix="/oauth/youtube", tags=["youtube-oauth"])

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "openid",
    "email",
    "profile",
]

def fernet() -> Fernet:
    return Fernet(settings.TOKEN_ENCRYPTION_KEY)

@router.get("/connect")
def connect(
    user: models.User = Depends(get_current_user),
):
    state = f"user:{user.id}"
    redirect_uri = settings.BASE_URL + settings.GOOGLE_REDIRECT_PATH

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"auth_url": url}

@router.get("/callback")
async def callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    if not state.startswith("user:"):
        raise HTTPException(status_code=400, detail="Invalid state")
    user_id = int(state.split("user:")[1])
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    redirect_uri = settings.BASE_URL + settings.GOOGLE_REDIRECT_PATH

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(token_url, data=data)
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Token exchange failed")
        token_json = token_resp.json()

        access_token = token_json.get("access_token", "")
        refresh_token = token_json.get("refresh_token", "")
        expires_in = token_json.get("expires_in", 0)

        if not access_token:
            raise HTTPException(status_code=400, detail="No access token returned")

        yt_url = "https://www.googleapis.com/youtube/v3/channels"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"part": "snippet", "mine": "true"}

        yt_resp = await client.get(yt_url, headers=headers, params=params)
        if yt_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch channel info")
        yt = yt_resp.json()

    items = yt.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No channel found on this account")

    ch0 = items[0]
    platform_channel_id = ch0["id"]
    title = ch0["snippet"]["title"]
    channel_url = f"https://www.youtube.com/channel/{platform_channel_id}"

    f = fernet()
    access_enc = f.encrypt(access_token.encode()).decode()
    refresh_enc = f.encrypt(refresh_token.encode()).decode() if refresh_token else ""

    expiry = datetime.now(timezone.utc).timestamp() + float(expires_in or 0)
    token_expiry_iso = datetime.fromtimestamp(expiry, tz=timezone.utc).isoformat()

    existing = (
        db.query(models.Channel)
        .filter(
            models.Channel.platform == "youtube",
            models.Channel.platform_channel_id == platform_channel_id,
        )
        .first()
    )
    if existing:
        if existing.user_id != user.id:
            raise HTTPException(status_code=409, detail="Channel already linked to another user")
        existing.channel_title = title
        existing.channel_url = channel_url
        existing.access_token_enc = access_enc
        existing.refresh_token_enc = refresh_enc
        existing.token_expiry_iso = token_expiry_iso
    else:
        ch = models.Channel(
            user_id=user.id,
            platform="youtube",
            platform_channel_id=platform_channel_id,
            channel_title=title,
            channel_url=channel_url,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            token_expiry_iso=token_expiry_iso,
        )
        db.add(ch)

    db.commit()
    return {"ok": True, "message": "YouTube channel linked. You can close this window."}
