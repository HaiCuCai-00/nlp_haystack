from fastapi import APIRouter

# from controller import feedback, file_upload, search
from controller import file_upload, search

router = APIRouter()

router.include_router(search.router, tags=["search"])
# router.include_router(feedback.router, tags=["feedback"])
router.include_router(file_upload.router, tags=["file-upload"])
