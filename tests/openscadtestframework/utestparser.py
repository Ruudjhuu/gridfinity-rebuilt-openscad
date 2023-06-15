from __future__ import annotations
from pathlib import Path
from re import match, search
from typing import List
from tempfile import TemporaryDirectory
import shutil
import os
from .testactions import TestActionFactory, TestAction
from .os import OS
from .tests import STLResult


COMMENT_CHAR = "//"
TEST_CHAR = "///"
CALL_MATCH = r".?\(.*\)\s*;"


class ParseError(ValueError):
    def __init__(self, context: ParseContext, message: str = "Parse error"):
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        return str(super()) + ":\n" + str(self.context)


class ParseContext():
    def __init__(self, path: Path, line_nr: int, content: str):
        self.path = path
        self.line_nr = line_nr
        self.content = content

    def __str__(self) -> str:
        return "file: " + str(self.path) + "\nline: " + str(self.line_nr) + "\ncontent: " + self.content


class UTestSuite():
    def __init__(self, file_path: Path):
        self.file_path = file_path.resolve()
        self.tmp_dir = TemporaryDirectory()
        self.tmp_file = Path(self.tmp_dir.name).joinpath(file_path.name)
        shutil.copy(self.file_path, self.tmp_file)
        self.testcases = UTestSuitParser().parse(self.tmp_file)

    def run(self) -> int:
        print(f"Running TestSuite: {self.file_path.name}")
        self.replace_include_with_relative_path()
        errors = 0
        for case in self.testcases:
            errors += case.run()

        print(
            f"\nNOK: total errors: {errors}" if errors else "\nResut: OK")

        return errors

    def replace_include_with_relative_path(self) -> None:
        tmp_pwd = Path.cwd()
        os.chdir(self.file_path.parent)

        output: str = ""
        with self.tmp_file.open("r") as f:
            for line in f.readlines():
                res = match(r"include\s*<([^>]*)>", line)
                if res:
                    output += line.replace(res.group(1),
                                           str(Path(res.group(1)).resolve()))
                else:
                    output += line
        with self.tmp_file.open("w") as f:
            f.write(output)

        os.chdir(tmp_pwd)


class UTestCase():
    default_args: list[str] = ["--enable",
                               "fast-csg", "--enable", "predictible-output"]
    output_arg = "-o"

    def __init__(self, file_path: Path, line_nr: int, actions: List[TestAction]):
        self.file_path = file_path
        self.out_file = file_path.parent.joinpath("out.stl")
        self.line_nr = line_nr
        self.actions = actions
        self.errors = 0

    def run(self) -> int:
        print(f"{self.file_path.name}:{self.line_nr} ... ", end="")
        self.isolate_line()
        self.run_openscad()
        self.remove_isolation()
        result = STLResult(self.out_file)
        for action in self.actions:
            try:
                action.run(result)
            except AssertionError as excp:
                self.errors += 1
                print(f"\n{excp}")
                break

        print("NOK" if self.errors else "OK")
        return self.errors

    def isolate_line(self) -> None:
        output: str = ""
        with self.file_path.open("r") as f:
            for num, line in enumerate(f, 1):
                if num == self.line_nr:
                    output += "!" + line
                else:
                    output += line
        with self.file_path.open("w") as f:
            f.write(output)

    def remove_isolation(self) -> None:
        output: str = ""
        with self.file_path.open("r") as f:
            for num, line in enumerate(f, 1):
                if num == self.line_nr:
                    output += line[1:]
                else:
                    output += line
        with self.file_path.open("w") as f:
            f.write(output)

    def run_openscad(self) -> None:
        cmd: List[str] = self.default_args + [self.output_arg, str(
            self.out_file), str(self.file_path)]
        result = OS.execute_openscad(cmd)
        if result.return_code:
            raise OSError(
                f"OpenScad failed with:\n{result.stdout}\n{result.stderr}")


class UTestSuitParser():

    def parse(self, file_path: Path) -> List[UTestCase]:
        cases: List[UTestCase] = []
        with file_path.open() as f:
            for num, line in enumerate(f, 1):
                if search(CALL_MATCH, line):
                    if search(TEST_CHAR, line):
                        line = "".join(line.split(TEST_CHAR)[1].split())
                        cases.append(UTestCase(file_path, num,
                                     [TestActionFactory.create(line)]))
        return cases
