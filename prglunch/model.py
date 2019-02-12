from typing import *
from dataclasses import dataclass


@dataclass
class Restaurant:
    name: str
    menu: List['MenuItem']


@dataclass
class MenuItem:
    name: str
    price: int
