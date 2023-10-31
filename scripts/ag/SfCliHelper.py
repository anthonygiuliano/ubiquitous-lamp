#! /usr/bin/env python3


from simple_salesforce import Salesforce  # https://pypi.org/project/simple-salesforce

# Formatting to SFDC date formatted_date = datetime.strptime(x, "%Y-%m-%d")
# Formatting to SFDC datetime formatted_datetime = datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%f%z")
import datetime  # https://docs.python.org/3/library/datetime.html
from collections import (
    namedtuple,
    OrderedDict,
)  # https://docs.python.org/3/library/collections.html
import argparse  # https://docs.python.org/3/library/argparse.html
import os  # https://docs.python.org/3/library/os.html
import subprocess  # https://docs.python.org/3/library/subprocess.html
import re  # https://docs.python.org/3/library/re.html
import json  # https://docs.python.org/3/library/json.html
from numpy import fix  # https://docs.python.org/3/library/json.html
import pandas as pd  # https://pandas.pydata.org/docs/user_guide/index.html#user-guide
from typing import Any, Callable  # https://docs.python.org/3/library/typing.html
from xml.etree.ElementTree import (
    ElementTree,
)  # https://docs.python.org/3/library/xml.etree.elementtree.html
from lxml import etree  # https://lxml.de

from SfImports import (
    SfErrors,
    SfPaths,
    SfPatterns,
    SfTlds,
)


class SfCliHelper:
    SCRIPT_DIR: str = os.path.dirname(p=os.path.abspath(path=__file__))
    ENV: dict[str, str] = {}
    SF: Salesforce
    DR_FILE: str = ""
    DR_DF: pd.DataFrame = pd.DataFrame()
    USERS_DF: pd.DataFrame = pd.DataFrame()
    ERRORS: list = []

    def __init__(self, deploy_results_file: str) -> None:
        cls = self.__class__
        cls.ENV = cls.get_env()
        cls.SF = Salesforce(
            session_id=cls.ENV["accessToken"],
            instance_url=cls.ENV["instanceUrl"],
        )
        cls.DR_FILE = deploy_results_file
        cls.DR_DF = cls.get_deploy_results()
        cls.USERS_DF = cls.get_users()
        cls.process_dr()
        return None

    @classmethod
    def process_dr(cls) -> None:
        for index, row in cls.DR_DF.iterrows():
            xml_path: str = row["filePath"] if "filePath" in row else ""
            match_groups: dict[str, str] = row["matchGroups"]
            fix_pattern: re.Pattern[str] = row["fixPattern"]
            fix_function: Callable[[str, dict[str, str]], pd.DataFrame] = row[
                "fixFunction"
            ]
            # fix_function(xml_path=xml_path, match_groups=match_groups)
        return None

    @classmethod
    def fix_no_user_found(cls, xml_path: str, match_groups: dict[str, str]) -> None:
        elem: ElementTree = ElementTree(file=xml_path)
        match_name: str = (
            match_groups["match_name"] if "match_name" in match_groups else ""
        )
        match_suffix: str = (
            match_groups["match_suffix"] if "match_suffix" in match_groups else ""
        )
        user: pd.Series = cls.get_matching_user(
            match_name=match_name, match_suffix=match_suffix
        )
        username: str = str(
            object=user.loc[
                0,
                "Username",
            ]
        )
        email: str = str(
            object=user.loc[
                0,
                "Email",
            ]
        )
        print(f"--- fix_no_user_found: username={username} ---")
        print(f"--- fix_no_user_found: email={email} ---")
        return None

    @classmethod
    def get_matching_user(cls, match_name: str, match_suffix: str) -> pd.Series:
        # Get user from users_df based on match_name and match_suffix
        users: pd.DataFrame = cls.USERS_DF.loc[
            (cls.USERS_DF["Username_Name"] == match_name)
            & (cls.USERS_DF["Username_Suffix"] == match_suffix),
            :,
        ]

        # If no user found, try again with just match_name
        if users.empty:
            users = cls.USERS_DF.loc[
                (cls.USERS_DF["Username_Name"] == match_name),
                :,
            ]

        # If still no user found, raise error
        if users.empty:
            raise ValueError(f"No user found for {match_name}")
        # If multiple users found, raise error
        elif users.shape[0] > 1:
            raise ValueError(f"Multiple users found for {match_name}")

        return users.iloc[0]

    @classmethod
    def get_deploy_results(cls) -> pd.DataFrame:
        deploy_results_dict: dict[str, dict] = {}
        deploy_results: pd.DataFrame = pd.DataFrame()
        if not os.path.isfile(path=cls.DR_FILE):
            raise ValueError(f"Invalid path specified: {cls.DR_FILE}")

        with open(file=cls.DR_FILE, mode="r") as f:
            deploy_results_dict = json.load(fp=f)

        if "result" in deploy_results_dict and "files" in deploy_results_dict["result"]:
            deploy_results_dict = deploy_results_dict["result"]["files"]
            deploy_results = pd.DataFrame.from_records(data=deploy_results_dict)
            deploy_results["fixPattern"] = None
            deploy_results["fixFunction"] = None
            deploy_results["matchGroups"] = None
            deploy_results.apply(cls.get_fixes, axis=1)

        return deploy_results

    @classmethod
    def get_fixes(cls, row: pd.Series) -> pd.Series:
        error: str = row["error"]
        for fix in SfErrors.values():
            match: re.Match[str] | None = re.search(
                pattern=fix["ID"].value, string=error
            )
            if match:
                row["fixPattern"] = fix["FIX"].value
                row["fixFunction"] = fix["FN"]
                row["matchGroups"] = match.groupdict()
                break
        return row

    @classmethod
    def _apply_fixes(cls, row: pd.Series) -> pd.Series:
        fix_function: Callable = row["fixFunction"]
        fix_function(
            xml_path=row["filePath"],
            match_groups=row["matchGroups"],
            users_df=cls.USERS_DF,
        )
        return row

    @classmethod
    def get_users(cls) -> pd.DataFrame:
        users: pd.DataFrame = pd.DataFrame()
        result: OrderedDict | None = cls.SF.query(
            query="SELECT Id, FirstName, LastName, Email, Username FROM User"
        )
        if result and "records" in result:
            users = pd.DataFrame.from_dict(data=result["records"], orient="columns")
            users[["Username_Name", "Username_Domain"]] = users["Username"].str.split(
                pat="@", expand=True
            )

            # Create new column for username tld, i.e. com, org, etc.
            # Uses the intersection of the tlds list and the result of splitting on . in order to handle
            # cases where usernames have a suffix like .prod, .uat, etc.
            users["Username_Tld"] = (
                users["Username_Domain"]
                .str.split(pat=".")
                .apply(lambda strs: next(iter(set(strs) & set(SfTlds.values())), None))
            )

            # Create new column for username suffix, i.e. everything between @ and .com, .org, etc.
            users["Username_Suffix"] = users.apply(
                lambda row: row["Username_Domain"].split(sep=f".{row['Username_Tld']}")[
                    0
                ],
                axis=1,
            )
        return users

    @classmethod
    def get_env(cls) -> dict[str, str]:
        # Get access token from sf-cli
        sf_stdout: subprocess.CompletedProcess[bytes] = subprocess.run(
            args=["sf", "org", "display", "user", "--json"], stdout=subprocess.PIPE
        )
        sf_json: str = re.sub(
            pattern=SfPatterns.ANSI.value, repl="", string=sf_stdout.stdout.decode()
        )
        if "result" in sf_json:
            sf_env: dict[str, str] = json.loads(s=sf_json)["result"]
        else:
            raise ValueError("No result in sf_json")
        return sf_env


def main(deploy_results_file: str) -> None:
    print(f"deploy_results_file: {deploy_results_file}")
    # fake_deploy = SfCli(command="deploy", debug=True)
    # deploy_df: pd.DataFrame = fake_deploy.df
    # get_users = SfCli(command=SfCommands.USERS.value)
    # users_df: pd.DataFrame = get_users.df
    sf_cli_helper: SfCliHelper = SfCliHelper(
        deploy_results_file=SfPaths.DEPLOY_CONCISE.value
    )
    pass


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="SfCliHelper description"
    )
    parser.add_argument(
        "-r",
        "--results",
        type=str,
        help="File containing the deployment results to fix",
        default=SfPaths.DEPLOY_CONCISE.value,
    )
    args: argparse.Namespace = parser.parse_args()
    main(deploy_results_file=args.results)
    # main(arg1=args.arg1, arg2=args.arg2)
