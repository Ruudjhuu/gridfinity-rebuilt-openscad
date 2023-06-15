from argparse import ArgumentParser
from pathlib import Path
from typing import List
from .utestparser import UTestSuite

FILE_REGEX = r"*.scad"

if __name__ == '__main__':
    parser = ArgumentParser(
        prog="openscadtestframework",
        description='Test opescad testcases'
    )

    parser.add_argument("filename", nargs='?')
    parser.add_argument("-d", "--directory",
                        help="Directory containing scad test files")

    args = parser.parse_args()

    file_list: List[Path] = []

    if args.filename:
        file_path = Path(args.filename)
        if not file_path.is_file():
            raise ValueError(f"{file_path} is not a file")
        file_list = [file_path]
    elif args.directory:
        directory = Path(args.directory)
        if not directory.is_dir():
            raise ValueError(f"{directory} is not a directory")
        for file in directory.iterdir():
            if file.is_file() and file.match(FILE_REGEX):
                file_list.append(file)
    else:
        raise ValueError("Directory or filename should be given")

    errors = 0
    for file in file_list:
        errors += UTestSuite(file).run()

    if errors:
        exit(1)
