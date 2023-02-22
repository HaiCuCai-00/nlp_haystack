"""
Pipelines allow putting together Components to build a graph.

In addition to the standard Haystack Components, custom user-defined Components
can be used in a Pipeline YAML configuration.

The classes for the Custom Components must be defined in this file.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import filetype
import fitz

from haystack.file_converter.base import BaseConverter

 
class CustomFileTypeClassifier(BaseConverter):
    """
    Route files in an Indexing Pipeline to corresponding file converters.
    """

    outgoing_edges = 8

    def _get_files_extension(self, file_paths: list) -> set:
        """
        Return the file extensions
        :param file_paths:
        :return: set
        """
        file_extensions = []
        for file_path in file_paths:
            file_extension = file_path.suffix.lstrip(".")
            if file_extension == "pdf":
                file_extension = (
                    "scanned_pdf" if self.check_scanned_pdf(file_path) else "pdf"
                )
            elif filetype.is_image(file_path):
                file_extension = "image"

            file_extensions.append(file_extension)

        return file_extensions

    def check_scanned_pdf(self, file_name: str) -> bool:
        """
        Calculate the percentage of document that is covered by (searchable) text.

        If the returned percentage of text is very low, the document is
        most likely a scanned PDF
        """
        total_page_area = 0.0
        total_text_area = 0.0

        doc = fitz.open(file_name)

        for _, page in enumerate(doc):
            total_page_area = total_page_area + abs(page.rect)
            text_area = 0.0
            for b in page.getTextBlocks():
                r = fitz.Rect(b[:4])  # rectangle where block text appears
                text_area = text_area + abs(r)
            total_text_area = total_text_area + text_area
        doc.close()
        text_perc = total_text_area / total_page_area
        if text_perc < 0.1:
            return True
        else:
            return False

    def run(self, file_paths: Union[Path, List[Path]]):  # type: ignore
        """
        Return the output based on file extension
        """
        if isinstance(file_paths, Path):
            file_paths = [file_paths]

        extension: set = self._get_files_extension(file_paths)
        if len(extension) > 1:
            raise ValueError(f"Multiple files types are not allowed at once.")

        output = {"file_paths": file_paths}
        ext: str = extension.pop()
        try:
            support_ext = ["txt", "pdf", "md", "docx", "html", "scanned_pdf", "image", "other"]
            if ext in support_ext:
                index = support_ext.index(ext) + 1
                return output, f"output_{index}"
            else:
                return output, "output_8"
        except ValueError:
            raise Exception(f"Files with an extension '{ext}' are not supported.")
