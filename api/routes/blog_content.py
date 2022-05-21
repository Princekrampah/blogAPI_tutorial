from email.policy import HTTP
from json import JSONDecoder
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from datetime import datetime
from typing import List

from ..schemas import BlogContent, BlogContentResponse, db
from .. import oath2


router = APIRouter(
    prefix="/blog",
    tags=["Blog Content"]
)

# TODO: CRUD

@router.post("", response_description="Create blog content", response_model=BlogContentResponse)
async def create_blog(blog_content: BlogContent, current_user = Depends(oath2.get_current_user)):
    
    try:
        blog_content = jsonable_encoder(blog_content)

        # add additional information
        blog_content["auther_name"] = current_user["name"]
        blog_content["auther_id"] = current_user["_id"]
        blog_content["created_at"] = str(datetime.utcnow())

        new_blog_content = await db["blogPost"].insert_one(blog_content)

        create_blog_post = await db["blogPost"].find_one({"_id": new_blog_content.inserted_id})

        return create_blog_post

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("", response_description="Get blog content", response_model=List[BlogContentResponse])
async def get_blogs(limit: int = 4, orderby: str = "created_at"):

    try:
        blog_posts = await db["blogPost"].find({"$query": {}, "$orderby": {orderby: -1}}).to_list(limit)
        return blog_posts
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{id}", response_description="Get blog content", response_model=BlogContentResponse)
async def get_blogs(id: str):

    try:
        blog_posts = await db["blogPost"].find_one({"_id": id})

        if blog_posts is None:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog with this id not found"
        )

        return blog_posts
        
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{id}", response_description="Update blog content", response_model=BlogContentResponse)
async def update_blog(id: str, blog_content: BlogContent, current_user=Depends(oath2.get_current_user)):

    if blog_post := await db["blogPost"].find_one({"_id": id}):
        if blog_post["auther_id"] == current_user["_id"]:

            try:
                blog_content = {k: v for k, v in blog_content.dict().items() if v is not None}

                if len(blog_content) >= 1:
                    update_result = await db["blogPost"].update_one({"_id": id}, {"$set": blog_content})

                    if update_result.modified_count == 1:
                        if (updated_blog_post := await db["blogPost"].find_one({"_id": id})) is not None:
                            return updated_blog_post

                    if (existing_post := await db["blogPost"].find_one({"_id": id})) is not None:
                        return existing_post

                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Blog content not found"
                    )

            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not the auther of this blog post"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog content not found"
            )


@router.delete("/{id}", response_description="Delete blog post")
async def delete_blog_post(id: str, current_user=Depends(oath2.get_current_user)):

    if blog_post := await db["blogPost"].find_one({"_id": id}):

        if blog_post["auther_id"] == current_user["_id"]:

            try:
                delete_result = await db["blogPost"].delete_one({"_id": id})

                if delete_result.deleted_count == 1:
                    return HTTPException(status_code=status.HTTP_204_NO_CONTENT)

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )
            except Exception as e:
                print(e)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You are not the auther of this blog post"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog content not found"
        )