#! /usr/bin/env python3

from typing import Any  # https://docs.python.org/3/library/typing.html
import os  # https://docs.python.org/3/library/os.html
import subprocess  # https://docs.python.org/3/library/subprocess.html
import re  # https://docs.python.org/3/library/re.html
import json  # https://docs.python.org/3/library/json.html
import xml.etree.ElementTree as ET  # https://docs.python.org/3/library/xml.etree.elementtree.html
from lxml import etree  # https://lxml.de/tutorial.html
import pandas as pd  # https://pandas.pydata.org/docs/user_guide/index.html#user-guide


def sf_cli_to_dict(command: str) -> dict:
    os.environ["SF_CONTENT_TYPE"] = "JSON"
    pattern_stdout: re.Pattern[str] = re.compile(pattern=patterns["ANSI"])
    shell: bool = False
    args: list[str] | str = command

    # sf data query commands should run in a shell and not be split into a list
    if command.startswith("sf data query"):
        shell: bool = True
    else:
        args = command.split(sep=" ")

    output: subprocess.CompletedProcess[bytes] = subprocess.run(
        args=args, shell=shell, stdout=subprocess.PIPE
    )

    # Dict from output of sf-cli command
    output_json: str = pattern_stdout.sub(repl="", string=output.stdout.decode())
    output_dict: Any = json.loads(s=output_json)
    return output_dict


def process_failures(failure: pd.Series) -> pd.Series:
    xml_path: str = failure["filePath"]
    error: str = failure["error"]
    find_pattern: re.Pattern[str] | None = None
    fix_function: function | None = None

    for pattern, obj in error_patterns.items():
        if pattern.search(string=error):
            find_pattern = obj["FIND"]
            fix_function = obj["ACTION"]
            continue

    parse_xml(xml_path=xml_path, find_pattern=find_pattern, fix_function=fix_error)
    return failure


def parse_xml(
    xml_path: str, find_pattern: re.Pattern[str] | None, fix_function: function | None
) -> None:
    tree: Any = etree.parse(source=xml_path, parser=None)
    for elem in tree.iter():
        elem_text: str = elem.text if elem.text else ""

        # Check if the element's text looks like an email address
        # match: re.Match[str] | None = error_pattern.search(string=elem_text)
        match = False

        if match:
            match_name: str = match.group("match_name")
            match_suffix: str = match.group("match_suffix")

            print("--- match ---")
            print(f"match_name: {match_name}")
            print(f"match_suffix: {match_suffix}")

            user: pd.DataFrame = users_df.loc[
                (users_df["Username_Name"] == match_name)
                & (users_df["Username_Suffix"] == match_suffix),
                :,
            ]

            username_new: str = users_df.loc[
                (users_df["Username_Name"] == match_name),
                "Username",
            ].values[0]
            print(f"username_new: {username_new}")

            email_new: str = users_df.loc[
                (users_df["Username_Name"] == match_name),
                "Email",
            ].values[0]
            print(f"email_new: {email_new}")

            print("--- elem ---")
            print(f"elem.attrib: {elem.attrib}")
            print(f"elem.tag: {elem.tag}")
            print(f"elem.text: {elem.text}")


def replace_invalid_users():
    pass


def replace_invalid_urls():
    pass


def add_missing_layout_fields():
    pass


# Top level domains to look for in usernames
tlds: list[str] = [
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "biz",
    "info",
]

# Suffixes to look for in usernames
envs: list[str] = [
    "dev",
    "qa",
    "uat",
    "prod",
]

# Relevant paths for this script
paths: dict[str, str] = {
    "script": os.path.dirname(p=os.path.abspath(path=__file__)),
    "metadata": os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)), "..", "..", "force-app"
        )
    ),
    "tmp": os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)), "..", "..", "tmp"
        )
    ),
}

error_patterns: dict[re.Pattern[str], dict[str, Any]] = {
    re.compile(
        pattern=r"no User named \b(?P<match_name>[A-Za-z0-9._%+-]+)(?P<match_domain>@[^@])+\.(?P<match_suffix>[A-Za-z]+)\b found"
    ): {
        "FIND": re.compile(
            pattern=r"\b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@]+\.(?P<match_suffix>[A-Za-z]+)\b"
        ),
        "ACTION": replace_invalid_users,
    },
    re.compile(
        pattern=r"\bThe default certificate cannot be selected as the Request Signing Certificate\b"
    ): {
        "FIND": re.compile(
            pattern=r"https://(www\.)?(?P<instance>[^/]+)\.my\.salesforce\.com"
        ),
        "ACTION": replace_invalid_urls,  # TODO: replace with instance url from org
    },
    re.compile(
        pattern=r"\bLayout must contain an item for required layout field: (?P<match_field>[A-Za-z0-9._%+-])+"
    ): {
        "FIND": None,  # TODO: find end of page layout xml
        "ACTION": add_missing_layout_fields,
    },
}

# Regex patterns
patterns: dict[str, re.Pattern[str]] = {
    "ANSI": re.compile(pattern=r"\x1b\[.*?m|\n"),
    "EMAIL": re.compile(
        pattern=r"\b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@]+\.(?P<match_suffix>[A-Za-z]+)\b"
    ),
    "INSTANCE_URL": re.compile(
        pattern=r"https://(www\.)?(?P<instance>[^/]+)\.my\.salesforce\.com"
    ),
    "REQUIRED_LAYOUT_FIELD": re.compile(
        pattern=r"\b(?P<match_field>[A-Za-z0-9._%+-])+\b"
    ),
}

# Deployment errors and their corresponding patterns
errors: dict[re.Pattern[str], re.Pattern[str]] = {
    re.compile(pattern=r"no User named [^@]+@[^@]+\.[^@]+ found"): patterns["EMAIL"],
    re.compile(
        pattern=r"\bThe default certificate cannot be selected as the Request Signing Certificate\b"
    ): patterns["INSTANCE_URL"],
    re.compile(
        pattern=r"\bLayout must contain an item for required layout field: (?P<match_field>[A-Za-z0-9._%+-])+"
    ): patterns["REQUIRED_LAYOUT_FIELD"],
}

sf_deploy_result: dict = sf_cli_to_dict(
    command=f"sf project deploy start --source-dir {paths['metadata']} --test-level RunLocalTests --dry-run --concise"
)["result"]

sf_deploy_failures: dict = sf_deploy_result["files"]
failures_df: pd.DataFrame = pd.DataFrame.from_dict(
    data=sf_deploy_failures, orient="columns"
)

sf_query_users_result: dict = sf_cli_to_dict(
    command="sf data query --query 'SELECT Id, FirstName, LastName, Email, Username FROM User'"
)["result"]
users_df: pd.DataFrame = pd.DataFrame.from_dict(
    data=sf_query_users_result["records"], orient="columns"
)

# Authenticate to target org using access token
# sf: Salesforce = Salesforce(
#     instance_url=sf_org_result["instanceUrl"],
#     session_id=sf_org_result["accessToken"],
# )

# # Get users from target org
# users = sf.query(query="SELECT Id, FirstName, LastName, Email, Username FROM User")[
#     "records"
# ]

# Create pd.DataFrame from users
# users_df: pd.DataFrame = pd.DataFrame(data=users)

# Split username on @ and expand into new columns
users_df[["Username_Name", "Username_Domain"]] = users_df["Username"].str.split(
    pat="@", expand=True
)

# Create new column for username tld, i.e. com, org, etc.
# Uses the intersection of the tlds list and the result of splitting on . in order to handle
# cases where usernames have a suffix like .prod, .uat, etc.
users_df["Username_Tld"] = (
    users_df["Username_Domain"]
    .str.split(pat=".")
    .apply(func=lambda strs: next(iter(set(strs) & set(tlds)), None))
)

# Create new column for username suffix, i.e. everything between @ and .com, .org, etc.
users_df["Username_Suffix"] = users_df.apply(
    func=lambda row: row["Username_Domain"].split(sep=f".{row['Username_Tld']}")[0],
    axis=1,
)

failures_df.apply(func=process_failures, axis=1)

pass
# Iterate recursively over the directory tree and find all XML files
# xml_paths: list[str] = []
# for root_path, dirs, files in os.walk(top=paths["metadata"]):
#     if paths["metadata"] in root_path:
#         for file in files:
#             if file.endswith(".xml"):
#                 xml_paths.append(path.join(root_path, file))
