from __future__ import annotations

from flatsol.parse import readFile
from flatsol.types import Import, PureImport, AliasImport, SymImport, SrcFile

from fpy.composable.function import func
from fpy.composable.collections import mp1, to, or_
from fpy.experimental.do import do
from fpy.data.maybe import Just, Nothing, mapMaybe

from dataclasses import dataclass
from typing import TypeVar, List, Generic, Callable
from pathlib import Path
import os
import sys
import argparse

T = TypeVar("T")

INCLUDE_PATH = ("./node_modules/", "./")
FILES_SEEN = dict()
DEBUG = False


@dataclass
class Tree(Generic[T]):
    node: T
    children: List[Tree[T]]

    def to_dict(self):
        return {"file": self.node, "children": [c.to_dict() for c in self.children]}


def _getFileFromPath(name, path):
    global FILES_SEEN
    if DEBUG:
        print(f"Get File From Path: {name}, {path}", file=sys.stderr)
    if name in FILES_SEEN:
        if DEBUG:
            print("using cached", file=sys.stderr)
        return Just(FILES_SEEN[name])
    if not path.exists():
        return Nothing()
    with open(path) as fin:
        lines = list(fin)
        file = readFile(name, lines)
        FILES_SEEN[name] = file
        return Just(file)


def getLocalFile(name, base_path=None):
    if base_path is None:
        base_path = Path(".")
    path = (base_path / Path(name)).resolve()
    return _getFileFromPath(str(path), path)


def getFromInclPath(name):
    base_path = Path.cwd()
    files = mapMaybe(
        lambda x: _getFileFromPath(name, base_path / Path(x) / name), INCLUDE_PATH
    )
    if files:
        return Just(files[0])
    return Nothing()


def getFromURL(url):
    pass


def getImport(im: Import, seen=None, base_path=None):
    if seen is None:
        seen = set()
    if base_path is None:
        base_path = Path.cwd()
    if not isinstance(im, Import):
        return Nothing()
    if not isinstance(im, PureImport):
        # not yet implemented
        return Nothing()
    name = im.getname()
    if name.startswith("."):
        return getLocalFile(name, base_path=base_path)
    return or_(getFromInclPath, getFromURL)(name)


def buildTree(src, seen=None):
    if seen is None:
        seen = set()
    base_path = Path(src.filename).resolve().parent
    seen.add(src.filename)
    children = mapMaybe(func(getImport, seen=seen, base_path=base_path), src.imports)
    return Tree(src, mp1(func(buildTree, seen=None), children))


# A naive copy of topological sort from Haskell's Data.Graph
# Given the nature of file import dependency must be a connected graph
# We don't have to construct the dff


@func
def postorder(tree):
    return postorderF(tree.children) + [tree.node]


@func
def postorderF(forest):
    return sum(mp1(postorder, forest), start=[])


topSort = postorder ^ to(list)


def mkOutput(tree, compress=False):
    visited = set()
    content = []
    license = None
    for node in topSort(tree):
        if node.filename in visited:
            continue
        if DEBUG:
            print(f"appending: {node}", file=sys.stderr)
        visited.add(node.filename)
        content.append(f"// {node}\n")
        while node.body:
            line = node.body.pop(0)
            if "SPDX-License-Identifier:" in line:
                license = license or line
                continue
            if compress:
                if not line.strip():
                    continue
                if line.lstrip().startswith("/*"):
                    while not line.rstrip().endswith("*/"):
                        line = node.body.pop(0)
                    continue
                if line.lstrip().startswith("//"):
                    continue

            content.append(line)
    # to lift the license line to the top of the file
    if license:
        content.insert(0, license)
    return content


def main():
    global DEBUG
    argparser = argparse.ArgumentParser()
    argparser.add_argument("input_file", type=str, help="the input file")
    argparser.add_argument(
        "-x", "--compress", help="remove blank lines and comments", action="store_true"
    )
    argparser.add_argument("-V", "--verbose", action="store_true")
    argparser.add_argument(
        "-I",
        "--include",
        type=str,
        help="additional include paths, separate with colons",
    )
    argparser.add_argument(
        "-o",
        "--output",
        type=str,
        help="the output filename",
    )
    args = argparser.parse_args()
    DEBUG = args.verbose
    fin_name = args.input_file
    abspath = Path(fin_name).resolve()
    if DEBUG:
        print(f"Reading file: {abspath}", file=sys.stderr)
    with open(abspath) as fin:
        lines = list(fin)
        src = readFile(abspath, lines, keep_license=True)
        tree = buildTree(src)
        output = mkOutput(tree, compress=args.compress)
        if args.output is None:
            print("".join(output))
            return 0
        outputPath = Path(args.output).resolve()
        if DEBUG:
            print(f"Writing to: {outputPath}", file=sys.stderr)
        outputPath.write_text("".join(output))
    return 0
