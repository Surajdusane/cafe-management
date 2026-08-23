from pydantic import BaseModel, ConfigDict


class PublicCafeBranding(BaseModel):
    """Cafe identity shown on the public menu. Deliberately excludes billing internals."""

    name: str
    address: str | None
    phone: str | None
    email: str | None
    logo_url: str | None
    currency: str


class PublicMenuItem(BaseModel):
    """A menu item as seen by customers: only display fields, no ids or timestamps."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None
    price: float
    image_url: str | None
    is_vegetarian: bool
    is_popular: bool
    is_available: bool


class PublicCategory(BaseModel):
    """An active category with its items, as rendered in one menu section."""

    name: str
    description: str | None
    items: list[PublicMenuItem]
