"""
doc-report: Professional Report Document Generator
Converts Markdown to styled Word documents (.docx)
"""

__version__ = "1.0.0"
__author__ = "Frentis"

from .agent import DocReportAgent
from .generator import DocxGenerator
from .parser import MarkdownParser

__all__ = ["DocReportAgent", "DocxGenerator", "MarkdownParser"]
