from imp import reload
import logging

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from config import FILE_STATIC_PATH, ROOT_PATH
from controller.errors.http_error import http_error_handler
from controller.router import router as api_router

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p")
logger = logging.getLogger(__name__)
logging.getLogger("elasticsearch").setLevel(logging.WARNING)
logging.getLogger("haystack").setLevel(logging.INFO)


def get_application() -> FastAPI:
    application = FastAPI(
        title="Search Engine API", debug=True, version="0.1", root_path=ROOT_PATH
    )

    # This middleware enables allow all cross-domain requests to the API from a browser. For production
    # deployments, it could be made more restrictive.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_exception_handler(HTTPException, http_error_handler)

    application.include_router(api_router)

    application.mount("/static", StaticFiles(directory=FILE_STATIC_PATH))

    return application


app = get_application()

logger.info("Open http://127.0.0.1:8005/docs to see Swagger API Documentation.")
logger.info(
    """
    Or just try it out directly: curl --request POST --url 'http://127.0.0.1:8005/query' -H "Content-Type: application/json"  --data '{"query": "Did Albus Dumbledore die?"}'
    """
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=2628)
