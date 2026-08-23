from sqlalchemy.orm import Session

from app.models.cafe_setting import CafeSetting

SETTINGS_ID = 1


def get_or_create_settings(db: Session) -> CafeSetting:
    settings = db.get(CafeSetting, SETTINGS_ID)
    if settings is None:
        settings = CafeSetting(id=SETTINGS_ID)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_settings(db: Session, payload) -> CafeSetting:
    settings = get_or_create_settings(db)
    for field, value in payload.model_dump().items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings
