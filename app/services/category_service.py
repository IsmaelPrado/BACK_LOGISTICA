from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.core.responses import ResponseCode
from app.schemas.api_response import APIResponse
from fastapi import HTTPException, status

def get_all_categories(db: Session):
    categories = db.query(Category).all()
    return APIResponse.from_enum(ResponseCode.SUCCESS, data=categories)

def create_category(db: Session, category: CategoryCreate):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría ya existe"
        )
    new_category = Category(**category.dict())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return APIResponse.from_enum(ResponseCode.SUCCESS, data=new_category, detail="Categoría creada correctamente")

def update_category(db: Session, category_id: int, data: CategoryUpdate):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    category.name = data.name
    db.commit()
    db.refresh(category)
    return APIResponse.from_enum(ResponseCode.SUCCESS, data=category, detail="Categoría actualizada correctamente")

def delete_category(db: Session, category_id: int):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    db.delete(category)
    db.commit()
    return APIResponse.from_enum(ResponseCode.SUCCESS, detail="Categoría eliminada correctamente")
