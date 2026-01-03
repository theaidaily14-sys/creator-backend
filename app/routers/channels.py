from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.deps import get_db, get_current_user
from app import models
from app.schemas import ChannelsListOut

router = APIRouter(prefix="/channels", tags=["channels"])

@router.get("", response_model=ChannelsListOut)
def list_channels(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    channels = db.query(models.Channel).filter(models.Channel.user_id == user.id).all()
    return {"channels": channels}

@router.delete("/{channel_id}")
def unlink_channel(
    channel_id: int,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ch = db.get(models.Channel, channel_id)
    if not ch or ch.user_id != user.id:
        raise HTTPException(status_code=404, detail="Channel not found")
    db.delete(ch)
    db.commit()
    return {"ok": True}
