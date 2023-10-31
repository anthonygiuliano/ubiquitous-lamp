#! /usr/bin/env python3


from simple_salesforce import Salesforce  # https://pypi.org/project/simple-salesforce

# Formatting to SFDC date formatted_date = datetime.strptime(x, "%Y-%m-%d")
# Formatting to SFDC datetime formatted_datetime = datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f%z")
import datetime
from collections import OrderedDict
import argparse
import os  # https://docs.python.org/3/library/os.html
import subprocess  # https://docs.python.org/3/library/subprocess.html
import re  # https://docs.python.org/3/library/re.html
import json
from numpy import fix  # https://docs.python.org/3/library/json.html
import pandas as pd  # https://pandas.pydata.org/docs/user_guide/index.html#user-guide
from typing import Any, Callable  # https://docs.python.org/3/library/typing.html
from xml.etree.ElementTree import (
    ElementTree,
)  # https://docs.python.org/3/library/xml.etree.elementtree.html
from lxml import etree

from SfImports import (
    SfCommands,
    SfEnvs,
    SfFindPatterns,
    SfFixes,
    SfErrors,
    SfPaths,
    SfTlds,
)


class SfCli:
    def __init__(
        self, command: str = "", shell: bool = False, debug: bool = False
    ) -> None:
        self.command: str = (
            getattr(SfCommands, command).value
            if command in SfCommands.values()
            else command
        )
        self.args: list[str] = self.command.split(sep=" ")
        self.shell: bool = shell
        self.debug: bool = debug
        self.output: subprocess.CompletedProcess[bytes]
        self.json: str
        self.dict: dict = {}
        self.df: pd.DataFrame

        if self.debug:
            self.sim()
        else:
            self.run()

    def sim(self) -> None:
        # Open the file and load the JSON data
        with open(file=SfPaths.DEPLOY_CONCISE.value, mode="r") as f:
            self.dict = json.load(fp=f)
        self._to_df()

    def run(self) -> None:
        # Ensure json response
        os.environ["SF_CONTENT_TYPE"] = "JSON"

        # sf data query commands should run in a shell and not be split into a list
        sf_command: str | list[str]
        if self.command.startswith("sf data query"):
            sf_command = self.command
            self.shell = True
        else:
            sf_command = self.args
            self.args = self.command.split(sep=" ")

        self.output = subprocess.run(
            args=sf_command, shell=self.shell, stdout=subprocess.PIPE
        )
        self._to_dict()
        self._to_df()
        return None

    def _to_dict(self) -> None:
        # Dict from output of sf-cli command
        self.json = re.sub(
            pattern=SfFindPatterns.ANSI.value,
            repl="",
            string=self.output.stdout.decode(),
        )
        self.dict = json.loads(s=self.json)
        return None

    def _to_df(self) -> None:
        status: int = self.dict["status"]
        result: dict[str, Any] = self.dict["result"] if "result" in self.dict else {}
        attributes: dict[str, Any] = (
            result["attributes"] if "attributes" in result else {}
        )

        if "records" in result and status == 1:
            self.df = pd.DataFrame.from_dict(data=result["records"], orient="columns")
            self._process_users() if attributes["type"] == "User" else None
        elif "files" in result and status == 0:
            self.df = pd.DataFrame.from_dict(data=result["files"], orient="columns")
            self._process_failures()
        return None

    def _process_users(self) -> None:
        # Split username on @ and expand into new columns
        self.df[["Username_Name", "Username_Domain"]] = self.df["Username"].str.split(
            pat="@", expand=True
        )

        # Create new column for username tld, i.e. com, org, etc.
        # Uses the intersection of the tlds list and the result of splitting on . in order to handle
        # cases where usernames have a suffix like .prod, .uat, etc.
        self.df["Username_Tld"] = (
            self.df["Username_Domain"]
            .str.split(pat=".")
            .apply(func=lambda strs: next(iter(set(strs) & set(SfTlds.values())), None))
        )

        # Create new column for username suffix, i.e. everything between @ and .com, .org, etc.
        self.df["Username_Suffix"] = self.df.apply(
            f=lambda row: row["Username_Domain"].split(sep=f".{row['Username_Tld']}")[
                0
            ],
            axis=1,
        )

    def _process_failures(self) -> None:
        self.df["fixPattern"] = None
        self.df["fixFunction"] = None
        self.df["matchGroups"] = None
        self.df.apply(f=self._get_fixes, axis=1)

    def _get_fixes(self, row: pd.Series) -> pd.Series:
        error: str = row["error"]
        for fix_pattern in SfErrors:
            match: re.Match[str] | None = re.search(
                pattern=fix_pattern.value, string=error
            )
            if match:
                row["fixPattern"] = fix_pattern
                row["fixFunction"] = SfFixes.get(enum=fix_pattern)
                row["matchGroups"] = match.groupdict()
                self._apply_fixes(row=row)
        return row

    def _apply_fixes(self, row: pd.Series) -> pd.Series:
        fix_function: Callable = row["fixFunction"]
        fix_function(xml_path=row["filePath"], match_groups=row["matchGroups"])
        return row

    def _parse_xml(
        self, xml_path: str, fix_pattern: re.Pattern[str], fix_function: Callable
    ) -> None:
        tree: ElementTree = etree.parse(source=xml_path, parser=None)
        for elem in tree.iter():
            elem_text: str = elem.text if elem.text else ""

            # Check if the element's text matches the find pattern
            match: re.Match[str] | None = fix_pattern.search(string=elem_text)

            if match:
                match_groups: dict[str, str] = match.groupdict()
                fix_function(elem=elem, match_groups=match_groups)
                continue


def main(arg1: str, arg2: str) -> None:
    print(f"arg1: {arg1}")
    print(f"arg2: {arg2}")
    # fake_deploy = SfCli(command="deploy", debug=True)
    # deploy_df: pd.DataFrame = fake_deploy.df
    # get_users = SfCli(command=SfCommands.USERS.value)
    # users_df: pd.DataFrame = get_users.df
    pass


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="py.py description"
    )
    parser.add_argument(
        "-a",
        "--arg1",
        type=str,
        help="arg1 help",
        default="arg1 default",
    )
    parser.add_argument(
        "-b",
        "--arg2",
        type=str,
        help="arg2 help",
        default="arg2 default",
    )
    args: argparse.Namespace = parser.parse_args()
    main(arg1=args.arg1, arg2=args.arg2)
