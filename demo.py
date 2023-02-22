import os
import uuid

from haystack.document_store import ElasticsearchDocumentStore
from haystack.file_converter.docx import DocxToTextConverter
from haystack.file_converter.pdf import PDFToTextConverter, PDFToTextOCRConverter
from haystack.file_converter.base import FileTypeClassifier
from haystack.pipeline import ExtractiveQAPipeline, DocumentSearchPipeline
from haystack.preprocessor.preprocessor import PreProcessor
from haystack.reader.transformers import TransformersReader
from haystack.retriever.sparse import ElasticsearchRetriever
from haystack.retriever.dense import DensePassageRetriever
from haystack.retriever import EmbeddingRetriever


db_dir = "../Data/Document_Database/"
docs = []
document_store = ElasticsearchDocumentStore(similarity="cosine", embedding_dim=384)
file_classification = FileTypeClassifier()
doc_converter = DocxToTextConverter(
    remove_numeric_tables=False, valid_languages=["en", "vi"]
)
pdf_converter = PDFToTextConverter(
    remove_numeric_tables=True, valid_languages=["en", "vi"]
)

processor = PreProcessor(
    clean_empty_lines=True,
    clean_whitespace=True,
    clean_header_footer=True,
    split_by="word",
    split_length=200,
    split_respect_sentence_boundary=True,
    language="english",
)

for file_name in os.listdir(db_dir):
    if file_name.endswith("pdf"):
        doc = pdf_converter.convert(
            file_path=os.path.join(db_dir, file_name),
            meta={"name": file_name, "id": uuid.uuid1().hex},
        )

    elif file_name.endswith("docx"):
        doc = doc_converter.convert(
            file_path=os.path.join(db_dir, file_name),
            meta={"name": file_name, "id": uuid.uuid1().hex},
        )

    print(doc)
    doc = processor.process(doc)
    docs.extend(doc)

document_store.write_documents(docs)
# retriever = ElasticsearchRetriever(document_store=document_store)
retriever = EmbeddingRetriever(document_store=document_store,
                               embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
# retriever = DensePassageRetriever(
#     document_store=document_store,
#     query_embedding_model="voidful/dpr-question_encoder-bert-base-multilingual",
#     passage_embedding_model="voidful/dpr-ctx_encoder-bert-base-multilingual",
#     max_seq_len_query=64,
#     max_seq_len_passage=256,
#     batch_size=16,
#     use_gpu=False,
#     embed_title=True,
#     use_fast_tokenizers=True,
# )
document_store.update_embeddings(retriever)

# reader = TransformersReader(
#     model_name_or_path="nguyenvulebinh/vi-mrc-large",
#     tokenizer="nguyenvulebinh/vi-mrc-large",
#     use_gpu=-1,
# )

# pipe = ExtractiveQAPipeline(reader, retriever)
pipe = DocumentSearchPipeline(retriever)
__import__("ipdb").set_trace()
prediction = pipe.run(
    query="tài liệu về tổ chức ?",
    params={"Retriever": {"top_k": 10}},
)
