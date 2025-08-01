from fastapi import APIRouter, Depends, status, HTTPException

from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from slugify import slugify

from app.models import *
from app.backend.db_depends import get_db
from app.schemas import CreateProduct
from app.routers.auth import get_current_user

from typing import Annotated

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/")
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    products = await db.scalars(select(Product).where(Product.is_active == True))
    return products.all()


@router.post('/create')
async def create_product(
    db: Annotated[AsyncSession, Depends(get_db)], 
    create_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        await db.execute(insert(Product).values(
            name=create_product.name,
            slug=slugify(create_product.name),
            description=create_product.description,
            price=create_product.price,
            image_url=create_product.image_url,
            stock=create_product.stock,
            category_id=create_product.category,
            rating=0.0,
            supplier_id=get_user.get("id")
        ))
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    subcategories = await db.scalars(select(Category.id).where(Category.parent_id == category.id))

    array_category_id = [category.id, *subcategories.all()]
    products = await db.scalars(select(Product).where(
        Product.category_id.in_(array_category_id), 
        Product.is_active == True,
        Product.stock > 0
        ))
    return products.all()


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product"
        )
    return product


@router.put('/detail/{product_slug}')
async def update_product(
    db: Annotated[AsyncSession, Depends(get_db)], 
    product_slug: str, 
    update_product: CreateProduct,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product"
        )
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        if get_user.get("id") == product.supplier_id or get_user.get("is_admin"):
            await db.execute(update(Product).where(Product.slug == product_slug).values(
                name=update_product.name,
                slug=slugify(update_product.name),
                description=update_product.description,
                price=update_product.price,
                image_url=update_product.image_url,
                stock=update_product.stock,
                category_id=update_product.category,
                supplier_id=get_user.get("id")
            ))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product update is successful'
            }
        else:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )
        


@router.delete('/delete')
async def delete_product(
    db: Annotated[AsyncSession, Depends(get_db)], 
    product_id: int,
    get_user: Annotated[dict, Depends(get_current_user)],
):
    product = await db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product"
        )
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        if get_user.get("id") == product.supplier_id or get_user.get("is_admin"):
            await db.execute(delete(Product).where(Product.id == product_id))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'
            } 
        else:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )