import json
import logging
import os
import shutil
import uuid
import time
from pathlib import Path
import pathlib
from typing import Any, Dict, List, Optional

import ocrmypdf
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from haystack.pipeline import Pipeline
from pydantic import BaseModel

from config import (
    FILE_STATIC_PATH,
    FILE_UPLOAD_PATH,
    INDEXING_PIPELINE_NAME,
    PIPELINE_YAML_PATH,
)
from controller.utils import as_form
from pipeline import custom_component

logger = logging.getLogger(__name__)
router = APIRouter()
file_classification = custom_component.CustomFileTypeClassifier()

try:
    _, pipeline_config, definitions = Pipeline._read_yaml(
        path=Path(PIPELINE_YAML_PATH),
        pipeline_name=INDEXING_PIPELINE_NAME,
        overwrite_with_env_variables=True,
    )
    # Since each instance of FAISSDocumentStore creates an in-memory FAISS index, the Indexing & Query Pipelines would
    # end up with different indices. The check below prevents creation of Indexing Pipelines with FAISSDocumentStore.
    is_faiss_present = False
    for node in pipeline_config["nodes"]:
        if definitions[node["name"]]["type"] == "FAISSDocumentStore":
            is_faiss_present = True
            break
    if is_faiss_present:
        logger.warning(
            "Indexing Pipeline with FAISSDocumentStore is not supported with the REST APIs."
        )
        INDEXING_PIPELINE = None
    else:
        INDEXING_PIPELINE = Pipeline.load_from_yaml(
            Path(PIPELINE_YAML_PATH), pipeline_name=INDEXING_PIPELINE_NAME
        )
        PDF_NODE = INDEXING_PIPELINE.get_node("PDFFileConverter")
except KeyError:
    INDEXING_PIPELINE = None
    logger.warning(
        "Indexing Pipeline not found in the YAML configuration. File Upload API will not be available."
    )


os.makedirs(FILE_UPLOAD_PATH, exist_ok=True)  # create directory for uploading files


@as_form
class FileUploadParams(BaseModel):
    # clean_numeric_tables: Optional[bool] = None
    clean_whitespace: Optional[bool] = None
    clean_empty_lines: Optional[bool] = None
    clean_header_footer: Optional[bool] = None
    valid_languages: Optional[List[str]] = None
    split_by: Optional[str] = None
    split_length: Optional[int] = None
    split_overlap: Optional[int] = None
    split_respect_sentence_boundary: Optional[bool] = None
  


class Document(BaseModel):
    text: Optional[str]
    meta: Optional[Dict[str, Any]]


class Response(BaseModel):
    url: Optional[List]
    documents: List[Document]


@router.post("/file-upload")
def file_upload(
    file: UploadFile=File(...),
    meta: Optional[str] = Form("null"),  # JSON serialized string
    params: FileUploadParams = Depends(FileUploadParams.as_form),):

    localtime = time.asctime( time.localtime(time.time()) )
    print("present time: ",localtime)
    meta = json.loads(meta) or {}
    type_file = (".doc",".pdf",".docx",".txt",".xml",".html")
    try:
        if (file.filename == ""):
            print("wrong file")
            return {"status": False , "msg": "no file to upload"}
        elif pathlib.Path(file.filename).suffix not in type_file:
            print("wrong file format")
            return {"status": False , "msg": "wrong file format"}
        elif meta["index"] == "":
            print("No index")
            return {"status": False , "msg": "index not be empty"}
        elif meta["id"] == "":
            print("No id")
            return {"status": False , "msg": "id not be empty"}
        elif not INDEXING_PIPELINE:
            raise HTTPException(
                status_code=501, detail="Indexing Pipeline is not configured."
            )
    except :
        return {"status": False , "msg": "Fail to upload file"}

    return_pdf = False
    file_paths: list = []
    file_metas: list = []
    urls = []

    
    # print("1 ",meta)
    # print(f'This is params:  {params}')
    # print(meta)
    try:
        file_id = uuid.uuid4().hex
        file_path = Path(FILE_UPLOAD_PATH) / f"{file_id}_{file.filename}"
            
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_type = file_classification.run(file_path)

        print(f'This is file_type:  {file_type}')
        

        if file_type[1] == "output_2" or file_type[1] == "output_6":

            file_out = (
                Path(FILE_STATIC_PATH)
                / f"{file_id}_{file.filename.replace(' ', '')}"
            )
            url = f"/static/{file_id}_{file.filename.replace(' ', '')}"
            ocrmypdf.ocr(
                input_file=file_path,
                output_file=file_out,
                language=["vie", "eng"],
                deskew=True,
                rotate_pages=True,
                jobs=4,
                skip_text=True,
            )
            file_path = file_out
            urls.append(url)
            return_pdf = True
        file_paths.append(file_path)
        meta["name"] = file.filename
        file_metas.append(meta)
    finally:
        file.file.close()
    
    test=INDEXING_PIPELINE.run(
        file_paths=file_paths,
        meta=file_metas,
        params=params.dict(),
    )
    # print(test)
    if return_pdf:
        result = PDF_NODE.run(file_paths)[0]
        result["url"] = urls
        return result
    else:
        return {"status": True, "msg": "Upload successfully"}
