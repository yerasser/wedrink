from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.deps import get_db
from app.models import Inventory
from app.models.ingredient import Ingredient
from app.schemas.ingredient import IngredientCreate, IngredientOut, IngredientUpdate

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientOut])
def list_ingredients(db: Session = Depends(get_db)):
    return db.query(Ingredient).order_by(Ingredient.id.asc()).all()


@router.post(
    "",
    response_model=IngredientOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_ingredient(payload: IngredientCreate, db: Session = Depends(get_db)):
    ing = Ingredient(name=payload.name.strip())
    inv = Inventory(ingredient_id=ing.id)
    db.add(ing)
    db.add(inv)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "conflict", "message": "ingredient name must be unique"},
        )
    db.refresh(ing)
    return ing


@router.patch(
    "/{ingredient_id}",
    response_model=IngredientOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_ingredient(ingredient_id: int, payload: IngredientUpdate, db: Session = Depends(get_db)):
    ing = db.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "ingredient not found"})

    if payload.name is not None:
        ing.name = payload.name.strip()

    db.add(ing)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "conflict", "message": "ingredient name must be unique"},
        )
    db.refresh(ing)
    return ing


@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    ing = db.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "ingredient not found"})

    db.delete(ing)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "conflict", "message": "ingredient is referenced and cannot be deleted"},
        )
    return None
