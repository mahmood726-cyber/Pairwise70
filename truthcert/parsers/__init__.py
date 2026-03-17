"""Parser module with Parser Witness and Arbitration system."""

from .parser_witness import ParserWitness, ParserResult, ParserArbitrator
from .base_parser import BaseParser, TableData

__all__ = ["ParserWitness", "ParserResult", "ParserArbitrator", "BaseParser", "TableData"]
