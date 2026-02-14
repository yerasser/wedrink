from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.deps import get_db
from app.models.product import Product
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeItemIn, RecipeItemOut

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/{product_id}", response_model=list[RecipeItemOut])
def get_recipes(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail={"error": "not_found", "message": "product not found"})

    return db.query(Recipe).filter(Recipe.product_id == product_id).all()


@router.put(
    "/{product_id}",
    response_model=list[RecipeItemOut],
    dependencies=[Depends(require_role("admin"))],
)
def put_recipes(product_id: int, items: list[RecipeItemIn], db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, detail={"error": "not_found", "message": "product not found"})

    with db.begin():
        db.query(Recipe).filter(Recipe.product_id == product_id).delete()

        rows = []
        for it in items:
            rows.append(
                Recipe(
                    product_id=product_id,
                    ingredient_id=it.ingredient_id,
                    qty=it.qty,
                )
            )
        db.add_all(rows)

    return db.query(Recipe).filter(Recipe.product_id == product_id).all()
