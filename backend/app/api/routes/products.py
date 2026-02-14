from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.deps import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.asc()).all()


@router.post(
    "",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    p = Product(code=payload.code.strip(), name=payload.name)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"error": "conflict", "message": "product code must be unique"},
        )
    db.refresh(p)
    return p


@router.patch(
    "/{product_id}",
    response_model=ProductOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, detail={"error": "not_found", "message": "product not found"})

    if payload.code is not None:
        p.code = payload.code.strip()
    if payload.name is not None:
        p.name = payload.name

    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"error": "conflict", "message": "product code must be unique"},
        )
    db.refresh(p)
    return p


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin"))],
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, detail={"error": "not_found", "message": "product not found"})
    db.delete(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"error": "conflict", "message": "product is referenced and cannot be deleted"},
        )
    return None
