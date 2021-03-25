from dataclasses import dataclass
from typing import List
from abc import ABCMeta, abstractmethod

"""
data ImportSym = Plain string | Alias string string

data Import = Pure string
            | Alias string string
            | Sym string [ImportSym]
"""


class Import(metaclass=ABCMeta):
    @abstractmethod
    def getname(self):
        raise NotImplementedError


@dataclass
class PureImport(Import):
    filename: str

    def getname(self):
        return self.filename


@dataclass
class AliasImport(Import):
    filename: str
    alias: str

    def getname(self):
        return self.filename


class Sym:
    pass


@dataclass
class PlainSym(Sym):
    name: str


@dataclass
class AliasSym(Sym):
    name: str
    alias: str


@dataclass
class SymImport(Import):
    filename: str
    syms: List[Sym]

    def getname(self):
        return self.filename


@dataclass
class SrcFile:
    filename: str
    imports: List[Import]
    body: List[str]

    def __hash__(self):
        return hash(hash(self.filename) + hash("".join(self.body)))

    def __repr__(self):
        return self.filename
