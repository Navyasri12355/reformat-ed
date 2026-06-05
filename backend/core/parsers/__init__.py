"""
Document parsing module for NeuraCore.
Provides utilities to parse PDF, DOCX, and TXT files into curriculum atoms.
"""

from .document import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    strip_boilerplate,
    chunk_into_atoms,
    parse_document,
    SUPPORTED_TYPES,
    EXTENSION_FALLBACKS,
)

__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "extract_text_from_txt",
    "strip_boilerplate",
    "chunk_into_atoms",
    "parse_document",
    "SUPPORTED_TYPES",
    "EXTENSION_FALLBACKS",
]
