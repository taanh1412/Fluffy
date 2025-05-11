from typing import Tuple, Optional, List

class FileResponse:
    def __init__(self, file_hash: str, file_name: str, data: Optional[bytes] = None):
        self.file_hash = file_hash
        self.file_name = file_name
        self.data = data

class SearchResult:
    def __init__(self, file_hash: str, file_name: str):
        self.file_hash = file_hash
        self.file_name = file_name