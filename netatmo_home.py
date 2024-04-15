from dataclasses import dataclass
import logging
from typing import List

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


@dataclass
class NetatmoHome:
    """Holds all home information"""
    id: str
    name: str
    rooms: List[str]
