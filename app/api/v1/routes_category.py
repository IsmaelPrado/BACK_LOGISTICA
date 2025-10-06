from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryListResponse,
    CategorySingleResponse
)
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categorías"])

@router.get("/", response_model=CategoryListResponse)
def list_categories(db: Session = Depends(get_db)):
    return category_service.get_all_categories(db)

@router.post("/", response_model=CategorySingleResponse)
def create_new_category(category: CategoryCreate, db: Session = Depends(get_db)):
    return category_service.create_category(db, category)

@router.put("/{category_id}", response_model=CategorySingleResponse)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    return category_service.update_category(db, category_id, data)

@router.delete("/{category_id}", response_model=CategorySingleResponse)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    return category_service.delete_category(db, category_id)
