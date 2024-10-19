# -----------------------------------------------------------
# File:   tai.py
# Author: Austin Hyunwoo Kim  User ID: hkim929   Class: CPS 110
# Desc:   Text-Adventures Interpreter
# -----------------------------------------------------------
'''CpS 110 Program 5: Text Adventures

Completed by Austin Hyunwoo Kim (hkim929)
'''
import sys
import time
import random

class Phrase:
    """A pair of strings: .verb and .info

    .verb is the action to perform (always lowercase).
    .info is extra information the action may need.
    """
    def __init__(self, verb: str, info: str):
        self.verb = verb.lower()
        self.info = info

    def is_chapter(self, label: str) -> (bool):
        """Is this Phrase of the form "chapter <label>"?"""
        return self.verb == "chapter" and self.info == label

    def is_end(self) -> (bool):
        """Is this Phrase's verb "end"?"""
        return self.verb == "end"


class Line:
    """A list of one or more Phrase objects.
    """
    def __init__(self):
        self.line = []

    def add(self, p: Phrase):
        """Add a Phrase to the end of our list."""
        self.line.append(p)

    def length(self) -> (int):
        """Return the number of Phrases in our list."""
        return len(self.line)

    def get(self, i: int) -> (Phrase):
        """Return the <i>'th Phrase from our list.

        Precondition: <i> is a valid, 0-based index
        """
        return self.line[i]

    def is_chapter(self, label: str) -> (bool):
        """Does this Line begin with a Phrase of the form "chapter <label>"?"""
        return self.get(0).verb == "chapter" and self.get(0).info == label


class Script:
    """A list of Line objects comprising a TAIL script.
    """
    def __init__(self):
        self.script = []

    def add(self, line: Line):
        """Add <line> to the end of our list IF <line> is not empty."""
        self.script.append(line)

    def length(self) -> (int):
        """Return the number of Lines in this script."""
        return len(self.script)

    def get(self, i: int) -> (Line):
        """Return the <i>'th Line of the script.

        Precondition: <i> is a valid, 0-based index
        """
        return self.script[i]

    def find_chapter(self, label: str) -> (int):
        """Return the index of the Line containing the Phrase "chapter <label>".

        If no such Line can be found, raises a ValueError exception.
        """
        for idx in range(self.length()):
            if self.get(idx).is_chapter(label):
                return idx
        raise ValueError()

    def next_phrase(self, iline: int, iphrase: int) -> (int, int):
        """Return the line/phrase indices of the next phrase after <iline>/<iphrase>.

        Precondition:
            * <iline> is a valid, 0-based index into our list of Lines
            * <iphrase> is a valid, 0-based index into that Line's list of Phrases
        """
        if iphrase + 1 < self.get(iline).length():
            return (iline, iphrase + 1)
        elif iline + 1 < self.length():
            return (iline + 1, 0)

    def next_line(self, iline: int, iphrase: int) -> (int, int):
        """Return the line/phrase indices of the next line after <iline>/<iphrase>.

        Precondition:
            * <iline> is a valid, 0-based index into our list of Lines
            * <iphrase> is a valid, 0-based index into that Line's list of Phrases
        """
        if iline + 1 < self.length():
            return (iline + 1, iphrase * 0)

def grouping(l, n):
    """Grouping by n count list"""
    for i in range(0, len(l), n):
        group = []
        for j in range(len(l) // 2):
            group.append(l[i+2*j:i+n+2*j])
        return group

def load_script(stream) -> (Script):
    """Return the Script created by parsing the contents of the file <stream>."""
    script = Script()
    lines = [line.strip() for line in stream.readlines()]
    while True:
        if "" in lines:
            lines.remove("")
        else:
            break

    for line in lines:
        if line[0] == "#":
            lines.remove(line)

    for idx in range(len(lines)):
        if lines[idx][0] != '>':
            lines[idx] = lines[idx].split(" ")
            lines[idx] = grouping(lines[idx], 2)
        else:
            lines[idx] = [[lines[idx][0], lines[idx][1:]]]

    for i in range(len(lines)):
        line = Line()
        for j in range(len(lines[i])):
            if lines[i][j][0] == ">":
                phrase = Phrase('println', lines[i][j][1])
            else:
                phrase = Phrase(lines[i][j][0], lines[i][j][1].replace("+", " "))
            line.add(phrase)
        script.add(line)
    return script

class Interpreter:
    """The logic and context required to interpret a TAIL script.

    Keeps a copy of the script being interpreted, along
    with all "state" required to keep track of where we
    are in the script, etc.

    Interpreters keep track of the current location in
    the TAIL script with a "bookmark": a pair of integers,
    one telling us the current LINE of the script,
    the other telling us the current PHRASE within that LINE.

    Each .step() call will
        * get the Phrase indicated by the "bookmark"
        * interpret that Phrase
        * and, depending on the Phrase, advance the "bookmark" to
            - the next phrase in that line, or
            - the next line, or
            - another line altogether (i.e., a "chapter" line)
    """
    def __init__(self, s: Script):
        self.terp = s
        self.bookmark = [0, 0]
        self.truedict = {}
        self.lastinp = ""
        self.visitrecord = []
        self.lastgoto = ""

    def _advance_phrase(self):
        """Move the "bookmark" forward to the next phrase.

        If there IS no next phrase (i.e., we were at the last
        phrase in the line), advance to the beginning of the
        next line instead.
        """
        if self.bookmark[1] + 1 < self.terp.get(self.bookmark[0]).length():
            self.bookmark = [self.bookmark[0], self.bookmark[1] + 1]
        else:
            self._advance_line()

    def _advance_line(self):
        """Move the "bookmark" forward to the beginning of the next line."""
        if self.bookmark[0] + 1 < self.terp.length():
            self.bookmark = [self.bookmark[0] + 1, 0]

    def _skip_to_line(self, iline: int):
        """Move the "bookmark" to the beginning of line <iline>."""
        self.bookmark = [iline, 0]

    def next_phrase(self) -> (Phrase):
        """Get whatever Phrase the "bookmark" is pointing at."""
        return self.terp.get(self.bookmark[0]).get(self.bookmark[1])

    def step(self):
        """Get the current Phrase, "interpret" it, and advance the "bookmark" appropriately."""
        phrase = self.terp.get(self.bookmark[0]).get(self.bookmark[1])
        verb = phrase.verb
        info = phrase.info
        flag = True
        if verb == "println":
            print(info.replace("$", self.lastgoto).replace("$", self.lastgoto))
        elif verb == "print":
            print(info.replace("$", self.lastgoto), end="")
        elif verb == "goto":
            for i in range(script.length()):
                if script.get(i).get(0).is_chapter(info.replace("$", self.lastgoto)):
                    self.lastgoto = info.replace("$", self.lastgoto)
                    self._skip_to_line(i)
                    flag = False
        elif verb == "prompt":
            print(info.replace("$", self.lastgoto), end="")
            self.lastinp = input().lower()
        elif verb == "on":
            if self.lastinp.find(info.replace("$", self.lastgoto).lower()) == -1:
                self._advance_line()
                flag = False
        elif verb == "set":
            self.truedict.update({info.replace("$", self.lastgoto): True})
        elif verb == "clear":
            if info.replace("$", self.lastgoto) in self.truedict:
                del self.truedict[info.replace("$", self.lastgoto)]
        elif verb == "if":
            if info.replace("$", self.lastgoto) not in self.truedict:
                self._advance_line()
                flag = False
        elif verb == "unless":
            if info.replace("$", self.lastgoto) in self.truedict:
                self._advance_line()
                flag = False
        elif verb == "match":
            if self.lastinp.startswith(info.replace("$", self.lastgoto).lower()):
                self.lastinp = self.lastinp.replace(info.replace("$", self.lastgoto).lower(), "")
            else:
                self._advance_line()
                flag = False
        elif verb == "visit":
            for i in range(script.length()):
                if script.get(i).get(0).is_chapter(info.replace("$", self.lastgoto)):
                    self.visitrecord.append(self.bookmark[0] + 1)
                    self._skip_to_line(i)
                    flag = False
        elif verb == "return":
            self._skip_to_line(self.visitrecord[len(self.visitrecord) - 1])
            del self.visitrecord[len(self.visitrecord) - 1]
            flag = False
        elif verb == "wait":
            """Usage: wait second

            Wait for second second.
            """
            time.sleep(int(info))
        elif verb == "chance":
            """Usage: chance percentage

            It has a percentage chance of continuing to the next phrase
            and a (100 - percentage) chance of skipping to the next line.
            """
            if random.random() > int(info)/100:
                self._advance_line()
                flag = False

        elif verb == "time":
            """Usage: time start
               Usage: time end
               Usage: time show

               It check how much time you spend during start to end. And show seconds.
            """
            if info == "start":
                self.stime = time.time()
            elif info == "end":
                self.etime = time.time()
            elif info == "show":
                print(round((self.etime - self.stime)), "sec")
        if flag:
            self._advance_phrase()
    def run(self):
        """Repeatedly step until an "end" Phrase is encountered."""
        while not self.next_phrase().is_end():
            self.step()

if __name__ == "__main__":
    try:
        file = sys.argv[1]
        with open(file) as fobj:
            script = load_script(fobj)
        terp = Interpreter(script)
        terp.run()
    except IndexError:
        print("Usage: python3 tai.py filename", file=sys.stderr)
    except FileNotFoundError:
        print("Cannot read file", file=sys.stderr)
