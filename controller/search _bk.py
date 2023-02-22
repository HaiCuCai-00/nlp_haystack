import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pydantic
from config import (
    CONCURRENT_REQUEST_PER_WORKER,
    LOG_LEVEL,
    PIPELINE_YAML_PATH,
    QUERY_PIPELINE_NAME,
)
from fastapi import APIRouter, HTTPException
from haystack import Pipeline
from pydantic import BaseModel

from controller.utils import RequestLimiter

logging.getLogger("haystack").setLevel(LOG_LEVEL)
logger = logging.getLogger("haystack")

router = APIRouter()


class Request(BaseModel):
    query: str = pydantic.Field(
        default=None, example=None, description="query"
    )
    index: str =pydantic.Field(
        default=None, example=None, description="Index"
    )
    params: Optional[dict] = None


class Answer(BaseModel):
    answer: Optional[str]
    question: Optional[str]
    score: Optional[float] = None
    probability: Optional[float] = None
    context: Optional[str]
    offset_start: Optional[int]
    offset_end: Optional[int]
    offset_start_in_doc: Optional[int]
    offset_end_in_doc: Optional[int]
    document_id: Optional[str] = None
    meta: Optional[Dict[str, Any]]


class Document(BaseModel):
    text: Optional[str]
    question: Optional[str]
    score: Optional[float] = None
    id: Optional[str] = None
    meta: Optional[Dict[str, Any]]


class Response(BaseModel):
    query: str
    # answers: List[Answer]
    documents: List[Document]
    id: Optional[List[str]]


PIPELINE = Pipeline.load_from_yaml(
    Path(PIPELINE_YAML_PATH), pipeline_name=QUERY_PIPELINE_NAME
)
logger.info(f"Loaded pipeline nodes: {PIPELINE.graph.nodes.keys()}")
concurrency_limiter = RequestLimiter(CONCURRENT_REQUEST_PER_WORKER)


@router.get("/initialized")
def initialized():
    """
    This endpoint can be used during startup to understand if the
    server is ready to take any requests, or is still loading.

    The recommended approach is to call this endpoint with a short timeout,
    like 500ms, and in case of no reply, consider the server busy.
    """
    return True


@router.post("/query")
def query(request: Request):
    localtime = time.asctime( time.localtime(time.time()) )
    print("present time: ",localtime)
    if request.query == "":
        print("No query")
        return {"status": False , "msg": "query not be empty"}
    if request.index == "":
        print("No index")
        return {"status": False , "msg": "index not be empty"}
    try:
        with concurrency_limiter.run():
            result = _process_request(PIPELINE, request)
            return result
    except Exception as e:
        return {"status" : False , "msg": str(e)}

def _process_request(pipeline, request) -> Response:
    try: 

        start_time = time.time()

        params = request.params or {}
        
        params["filters"] = params.get("filters") or {}
        filters = {}
        if (
            "filters" in params
        ):  # put filter values into a list and remove filters with null value
            for key, values in params["filters"].items():
                if values is None:
                    continue
                if not isinstance(values, list):
                    values = [values]
                filters[key] = values
        params["filters"] = filters
        result = pipeline.run(query=request.query, params=params)

        # Convert document to dict
        result["documents"] = [document.to_dict() for document in result["documents"]]
        id_list = []
        for document in result["documents"]:
            if document["score"] is None:
                continue
            elif str(document["meta"]["index"]) == str(request.index):
                if document["score"] >= 0.6:
                #     # print(document["meta"]["index"])
                #     # print(type(document["meta"]["index"]))
                    id_list.append(document["meta"]["id"])
                #id_list.append(document["meta"]["_split_id"])

        result["id"] = list(set(id_list))
        result["_split_id"] = list(set(id_list))
        
        end_time = time.time()
        logger.info(
            {
                "request": request.dict(),
                "response": result,
                "time": f"{(end_time - start_time):.2f}",
            }
        )

        return result

    except Exception as e:
        return {"status": False , "msg": "not search"}
