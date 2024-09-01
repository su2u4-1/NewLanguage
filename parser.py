import os.path
from typing import Literal, Iterable

TokenType = Literal["string", "integer", "symbol", "keyword", "float", "char", "identifier", "filename"]
Label = Literal["filename", "class", "subroutine", "var_s", "argument_list", "statements", "let_S", "do_S", "if_S", "while_S", "for_S", "return_S", "break_S", "continue_S", "expression", "term"]
tokentype = ("string", "integer", "symbol", "keyword", "float", "char", "identifier")
Symbol = ("{", "}", "[", "]", "(", ")", "=", ";", ",", ".", "~", "+", "-", "*", "/", "|", "&", "==", "!=", ">=", "<=", ">", "<")
Number = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")
atoZ = ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z")
Keyword = ("class", "var", "attr", "constructor", "function", "method", "void", "pass", "let", "do", "if", "if else", "else", "while", "return", "for", "break", "continue", "false", "true", "none", "self", "int", "bool", "char", "str", "list", "float")


class Token:
    def __init__(self, type: TokenType, content: str, location: tuple[int, int] = (-1, -1)) -> None:
        self.content = content
        self.type = type
        self.line = location[0]
        self.index = location[1]

    def __str__(self) -> str:
        return f"<{self.type}> {self.content} [{self.line}, {self.index}]"

    def __eq__(self, value: object) -> bool:
        if type(value) == Token:
            return self.type == value.type and self.content == value.content
        elif type(value) == Tokens:
            if self.type == value.type:
                for i in value.content:
                    if i == self.content:
                        return True
        return False


class Tokens:
    def __init__(self, type: TokenType, content: Iterable[str]) -> None:
        self.content = content
        self.type = type

    def __eq__(self, value: object) -> bool:
        if type(value) == Token:
            if self.type == value.type:
                for i in self.content:
                    if i == value.content:
                        return True
        return False


def read_from_path(path: str) -> list[str]:
    path = os.path.abspath(path)
    file: list[str] = []
    if os.path.isdir(path):
        for f in os.listdir(path):
            if os.path.isfile(f):
                file.append(f)
    elif os.path.isfile(path):
        file.append(path)
    source: list[str] = []
    for i in file:
        if i.endswith(".nj"):
            with open(i, "r") as f:
                source.append("//" + i.split("\\")[-1])
                source += f.readlines()
    return source


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.length = len(tokens)
        self.code: list[Token] = []
        self.error: list[tuple[str, tuple[int, int]]] = []
        self.var_g = {}
        self.var_l = {}
        self.var_i = {"attr": 0, "global": 0, "local": 0}

    def get(self) -> Token:
        self.index += 1
        if self.index >= self.length:
            exit()
        return self.tokens[self.index - 1]

    def peek(self) -> Token:
        return self.tokens[self.index - 1]

    def main(self) -> list[Token]:
        while True:
            now = self.get()
            if now == Token("keyword", "class"):
                self.compileClass()
            elif self.index >= self.length:
                break
            else:
                self.error.append(("missing keyword 'class'", (now.line, now.index)))
        return self.code

    def compileClass(self) -> None:
        now = self.get()
        if now.type != Token("symbol", "{"):
            self.error.append(("missing symbol '{'", (now.line, now.index)))
        now = self.get()
        while now == Tokens("keyword", ("constructor", "function", "method", "var", "attr")):
            if now == Tokens("keyword", ("constructor", "function", "method")):
                self.compileSubroutine()
            elif now == Tokens("keyword", ("var", "attr")):
                self.compileVar(_global=True)
        now = self.get()
        if now != Token("symbol", "}"):
            self.error.append(("missing symbol '}'", (now.line, now.index)))

    def compileVar(self, _global: bool = False) -> None:
        now = self.peek()
        if now == Token("keyword", "var"):
            if _global:
                kind = "global"
            else:
                kind = "local"
        else:
            kind = "attr"
        now = self.get()
        if now != Tokens("keyword", ("int", "bool", "char", "str", "list", "float")) and now.type != "index":
            pass

    def compileSubroutine(self) -> None:
        pass


def lexer(source: list[str]) -> list[Token]:
    tokens: list[Token] = []
    content = ""
    state = ""
    location = (-1, -1)
    for i, line in enumerate(source):
        if line.startswith("//"):
            tokens.append(Token("filename", line[2:], (-1, -1)))
            continue
        for j, char in enumerate(line):
            if state == "commant":
                if char == "`":
                    state = ""
                continue
            elif state == "string":
                content += char
                if char == '"':
                    tokens.append(Token("string", content, location))
                    content = ""
                    state = ""
                continue
            elif state == "neg":
                if char in Number:
                    content += char
                    state = "int"
                    continue
                else:
                    tokens.append(Token("symbol", content, location))
                    content = ""
                    state = ""
            elif state == "identifier":
                if char in atoZ or char == "_" or char in Number:
                    content += char
                    continue
                elif content in Keyword:
                    tokens.append(Token("keyword", content, location))
                else:
                    tokens.append(Token("identifier", content, location))
                content = ""
                state = ""
            elif state == "int":
                if char in Number:
                    if content == "-0":
                        tokens.append(Token("symbol", "-", location))
                        tokens.append(Token("integer", "0", (i + 1, j + 1)))
                        content = ""
                        state = ""
                    elif char == "0":
                        tokens.append(Token("integer", "0", (i + 1, j + 1)))
                        content = ""
                        state = ""
                    else:
                        content += char
                        continue
                elif char == ".":
                    content += char
                    state = "float"
                    continue
                else:
                    tokens.append(Token("integer", content, location))
                    content = ""
                    state = ""
            elif state == "float":
                if char in Number:
                    content += char
                    continue
                else:
                    tokens.append(Token("float", content, location))
                    content = ""
                    state = ""

            if char == '"':
                state = "string"
                content = char
                location = (i + 1, j + 1)
            elif char == "#":
                break
            elif char == "`":
                state = "commant"
            elif char == "-":
                state = "neg"
                content = char
                location = (i + 1, j + 1)
            elif char in Symbol:
                tokens.append(Token("symbol", char, (i + 1, j + 1)))
            elif char in Number:
                state = "int"
                content = char
                location = (i + 1, j + 1)
            elif char in atoZ or char == "_":
                state = "identifier"
                content = char
                location = (i + 1, j + 1)
    if state != "":
        print("error:", state)
        print("location:", location)
        exit()
    return tokens


if __name__ == "__main__":
    path = input("file(s) path: ")
    source = read_from_path(path)
    tokens = lexer(source)
    parser = Parser(tokens)
    xmlcode = parser.main()
