from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from starlette import status

from app.routers.auth import get_current_user
from app.models.users import User
from app.backend.db_depends import get_db


router = APIRouter(prefix='/permission', tags=['permission'])


@router.patch('/')
async def supplier_permission(
    db: Annotated[AsyncSession, Depends(get_db)], 
    get_user: Annotated[dict, Depends(get_current_user)],
    user_id: int
):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.is_supplier:
            await db.execute(update(User).where(User.id == user_id).values(is_supplier=False, is_customer=True))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is no longer supplier'
            }
        else:
            await db.execute(update(User).where(User.id == user_id).values(is_supplier=True, is_customer=False))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is now supplier'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
        )
    

@router.patch('/change/active')
async def is_active_change(
    db: Annotated[AsyncSession, Depends(get_db)], 
    get_user: Annotated[dict, Depends(get_current_user)],
    user_id: int
):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can't deactivate yourself"
            )
        if user.is_active:
            await db.execute(update(User).where(User.id == user_id).values(is_active=False))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is deactivate'
            }
        else:
            await db.execute(update(User).where(User.id == user_id).values(is_active=True))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is activated'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
        )
    

@router.delete('/delete')
async def delete_user(
    db: Annotated[AsyncSession, Depends(get_db)], 
    get_user: Annotated[dict, Depends(get_current_user)],
    user_id: int
):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return {
                'status_code': status.HTTP_200_OK,
                'detail': f'User {user_id} deleted'
            } 
    
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
        ) 