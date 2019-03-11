class SymbolTable(object):
    def __init__(self):
        self.classTable = {}
        self.subroutineTable = {}
        self.count = {"static": 0,
                      "field": 0,
                      "argument": 0,
                      "local": 0}

    def define(self, name, type, kind):
        index = self.count[kind]
        self.count[kind] += 1
        if kind in {"static", "field"}:
            self.classTable[name] = {"type": type,
                                     "kind": kind,
                                     "index": index}
        elif kind in {"argument", "local"}:
            self.subroutineTable[name] = {"type": type,
                                          "kind": kind,
                                          "index": index}

    def resetSubroutineTable(self):
        self.subroutineTable = {}
        self.count["argument"] = self.count["local"] = 0

    def varCount(self, kind):
        return self.count[kind]

    def kindOf(self, name):
        if name in self.subroutineTable:
            return self.subroutineTable[name]["kind"]
        elif name in self.classTable:
            return self.classTable[name]["kind"]
        else:
            return None

    def typeOf(self, name):
        if name in self.subroutineTable:
            return self.subroutineTable[name]["type"]
        elif name in self.classTable:
            return self.classTable[name]["type"]
        else:
            return None

    def indexOf(self, name):
        if name in self.subroutineTable:
            return self.subroutineTable[name]["index"]
        elif name in self.classTable:
            return self.classTable[name]["index"]
        else:
            return None
