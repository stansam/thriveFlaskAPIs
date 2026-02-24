from typing import TypeVar, Generic, Type, Optional, List, Any
from app.extensions import db
from app.repository.base.utils import handle_db_exceptions

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """
    Generic Base Repository that provides standard database CRUD operations.
    Should be inherited by domain-specific repositories.
    """

    def __init__(self, model_class: Type[ModelType]):
        self.model = model_class

    @handle_db_exceptions
    def get_by_id(self, id: str) -> Optional[ModelType]:
        """Fetch a single record by its primary key ID."""
        return self.model.query.get(id)

    @handle_db_exceptions
    def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """Fetch all records with optional pagination."""
        return self.model.query.limit(limit).offset(offset).all()

    @handle_db_exceptions
    def create(self, data: dict, commit: bool = True) -> ModelType:
        """Instantiate and optionally persist a new record."""
        obj = self.model(**data)
        db.session.add(obj)
        if commit:
            db.session.commit()
        return obj

    @handle_db_exceptions
    def update(self, db_obj: ModelType, data: dict, commit: bool = True) -> ModelType:
        """Update fields on an existing database record."""
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        if commit:
            db.session.commit()
        return db_obj

    @handle_db_exceptions
    def delete(self, db_obj: ModelType, commit: bool = True) -> bool:
        """Delete an existing database record."""
        db.session.delete(db_obj)
        if commit:
            db.session.commit()
        return True
