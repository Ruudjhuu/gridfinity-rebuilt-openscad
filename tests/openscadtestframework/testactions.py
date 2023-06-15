from __future__ import annotations
from re import match
from typing import List
from abc import ABC, abstractmethod
from pathlib import Path
from .tests import Result


class TestActionFactory():
    REG = r"([A-z]+):(.*)"

    @staticmethod
    def create(line: str) -> TestAction:
        res = match(TestActionFactory.REG, line)
        if res:
            if res.group(1) == Assertion.identifier:
                return Assertion.create(res.group(2))
            if res.group(1) == Expect.identifier:
                return Expect.create(res.group(2))
            raise ValueError(f'Test action "{res.group(1)}" does not exist')
        raise ValueError(f"Could not parse test string: {line}")


class TestAction(ABC):
    identifier = "UNDEF"

    @staticmethod
    @abstractmethod
    def create(line: str) -> TestAction:
        raise NotImplementedError()

    @abstractmethod
    def run(self, run_result: Result) -> None:
        raise NotImplementedError()


class Assertion(TestAction):
    identifier = "ASSERT"
    REG = r".+"
    delimiter = ','

    def __init__(self, subs: List[SubAssertion]):
        self.subs = subs

    @staticmethod
    def create(line: str) -> Assertion:
        if match(Assertion.REG, line):
            items = line.split(Assertion.delimiter)

            subs: List[SubAssertion] = []
            for item in items:
                subs.append(SubAssertion.create(item))

            return Assertion(subs)
        raise ValueError(f"Could not parse: {line}")

    def run(self, run_result: Result) -> None:
        for sub in self.subs:
            sub.run(run_result)


class SubAssertion(TestAction):
    delimiter = "="
    regex = r"([^=]+)" + delimiter + r"(\d+(?:\.\d+)?)"

    def __init__(self, name: str, expectation: float):
        self.name = name
        self.expectation = expectation

    @staticmethod
    def create(line: str) -> SubAssertion:
        if match(SubAssertion.regex, line):
            items = line.split(SubAssertion.delimiter)
            return SubAssertion(items[0], float(items[1]))
        raise ValueError(f"Could not parse: {line}")

    def run(self, run_result: Result) -> None:
        poperty = getattr(run_result, self.name)
        if poperty != self.expectation:
            raise AssertionError(
                f'Expected: "{self.name}" == "{self.expectation}"\nActual: "{self.name}" == "{poperty}"')


class Expect(TestAction):
    identifier = "EXPECT"

    def __init__(self, file_path: Path):
        self.file_path = file_path

    @staticmethod
    def create(line: str) -> Expect:
        file_path = Path(line)
        if not file_path.exists():
            raise ValueError(f"File does not exists: {file_path}")
        return Expect(Path(line))

    def run(self, run_result: Result) -> None:
        run_result.compare_with_expected(path=self.file_path)
