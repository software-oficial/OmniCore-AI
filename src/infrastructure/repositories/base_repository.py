from sqlalchemy.orm import Session


class BaseRepository:
    """
    Base Repository for multi-tenant isolation.
    Uses explicit business_id passed during instantiation to ensure thread safety.
    """

    def __init__(self, session: Session, business_id: str):
        self.session = session
        self.business_id = business_id

    @property
    def app_id(self) -> str:
        return self.business_id
