from fpy.parsec.parsec import parser, one, pseq, many1, many, neg, ptrans, c2s, pmaybe
from fpy.data.either import fromLeft, fromRight, either, Left, Right
from fpy.composable.collections import or_, and_, of_, trans0, apply
from fpy.utils.placeholder import __
from fpy.experimental.do import do
from fpy.debug.debug import trace

from flatsol.types import (
    Import,
    PureImport,
    AliasImport,
    Sym,
    PlainSym,
    AliasSym,
    SymImport,
    SrcFile,
)

filename = ptrans(
    one(__ == '"') >> many1(neg(__ == '"')) << one(__ == '"'),
    trans0(c2s),
)
symbolname = ptrans(
    one(or_(lambda x: x.isalpha(), of_("_")))
    + many(one(or_(lambda x: x.isalnum(), of_("_")))),
    trans0(c2s),
)
spc1 = many1(one(__ == " "))
spc = many(one(__ == " "))


@parser
@do(Right)
def parse_pure_import(s):
    pure_import = pseq("import") >> spc1 >> filename << spc << one(__ == ";")
    fname, rest < -pure_import(s)
    return PureImport(fname)


@parser
@do(Right)
def parse_alias_import_star(s):
    alias_import_star = (
        pseq("import")
        >> spc1
        >> one(__ == "*")
        >> spc1
        >> pseq("as")
        >> spc1
        >> symbolname
    )
    from_file = spc1 >> pseq("from") >> spc1 >> filename << spc << one(__ == ";")
    sym, rest < -alias_import_star(s)
    fname, _ < -from_file(rest)
    return AliasImport(fname, sym)


@parser
@do(Right)
def parse_alias_import_as(s):
    from_file = pseq("import") >> spc1 >> filename << spc << pseq("as")
    symname = spc1 >> symbolname << spc << one(__ == ";")
    fname, rest < -from_file(s)
    sym, _ < -symname(rest)
    return AliasImport(fname, sym)


parse_alias_import = parse_alias_import_as | parse_alias_import_star


@parser
@do(Right)
def parse_sym_import(s):
    sym, rest < -symbolname(s)
    alias, rest < -(pmaybe(spc1 >> pseq("as") >> spc1 >> symbolname))(rest)
    if alias:
        return [AliasSym(sym, alias)], rest
    return [PlainSym(sym)], rest


parse_sym_lst = parse_sym_import + many(
    spc >> one(__ == ",") >> spc >> parse_sym_import
)


@parser
@do(Right)
def parse_sym_lst_import(s):
    symlst, rest < -(
        pseq("import")
        >> spc
        >> one(__ == "{")
        >> spc
        >> parse_sym_lst
        << spc
        << one(__ == "}")
    )(s)
    fname, _ < -(spc >> pseq("from") >> spc1 >> filename << spc << one(__ == ";"))(rest)
    return SymImport(fname, symlst)


parse_import = parse_pure_import | parse_alias_import | parse_sym_lst_import


def readFile(name, lines, keep_license=False):
    body = []
    imports = []
    for line in lines:
        if "SPDX-License-Identifier:" in line:
            if keep_license:
                body.append(line)
            continue

        if line.strip().startswith("import"):
            im = (spc >> parse_import)(line)
            if im:
                imports.append(fromRight(None, im))
                body.append("// " + line)
                continue
            print("cannot parse import: ", line)
            body.append(line)
            continue
        body.append(line)
    return SrcFile(str(name), imports, body)


if __name__ == "__main__":
    test = """import   "test.sol"; """
    res = parse_import(test)
    print(res)
    test = """import * as foo from "foobar.sol" ; """
    res = parse_import(test)
    print(res)
    test = """import "foobar.sol" as foobar; """
    res = parse_import(test)
    print(res)
    test = """import {symbol1 as alias, symbol2} from "filename"; """
    res = parse_import(test)
    print(res)
