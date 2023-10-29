import re
import os
from typing import Any, Callable, Literal
from enum import Enum
from xml.etree.ElementTree import (
    ElementTree,
)  # https://docs.python.org/3/library/xml.etree.elementtree.html
import pandas as pd  # https://pandas.pydata.org/docs/user_guide/index.html#user-guide


class SfEnum(Enum):
    @classmethod
    def values(cls) -> list[Any]:
        return [member.value for member in cls]

    @classmethod
    def names(cls) -> list[str]:
        return [member.name for member in cls]

    @classmethod
    def get(cls, enum: str | Enum) -> Any:
        if isinstance(enum, str) and enum.upper() in cls.names():
            return getattr(cls, enum.upper())
        elif (
            isinstance(enum, Enum)
            and issubclass(enum.__class__, Enum)
            and enum.name in cls.names()
        ):
            return getattr(cls, enum.name)
        else:
            raise TypeError(f"Invalid enum: {enum}")


class SfTlds(SfEnum):
    COM = "com"
    ORG = "org"
    NET = "net"
    EDU = "edu"
    GOV = "gov"
    BIZ = "biz"
    INFO = "info"


class SfEnvs(SfEnum):
    DEV = "dev"
    QA = "qa"
    UAT = "uat"
    PROD = "prod"


class SfPaths(SfEnum):
    SCRIPT = os.path.dirname(p=os.path.abspath(path=__file__))
    METADATA = os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)), "..", "..", "force-app"
        )
    )
    TMP = os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)), "..", "..", "tmp"
        )
    )
    DEPLOY_CONCISE = os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)),
            "..",
            "..",
            "tmp",
            "deploy-concise.json",
        )
    )
    QUERY_USERS = os.path.abspath(
        path=os.path.join(
            os.path.dirname(p=os.path.abspath(path=__file__)),
            "..",
            "..",
            "tmp",
            "query-users.json",
        )
    )


class SfCommands(SfEnum):
    DEPLOY = f"sf project deploy start --source-dir {SfPaths.METADATA.value} --test-level RunLocalTests --dry-run --concise"
    USERS = "sf data query --query 'SELECT Id, FirstName, LastName, Email, Username FROM User'"


class SfFindPatterns(SfEnum):
    ANSI = re.compile(pattern=r"\x1b\[.*?m|\n")
    EMAIL = re.compile(
        pattern=r"\b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@]+\.(?P<match_suffix>[A-Za-z]+)\b"
    )
    INSTANCE_URL = re.compile(
        pattern=r"https://(www\.)?(?P<instance>[^/]+)\.my\.salesforce\.com"
    )
    ERROR_NO_USER_FOUND = re.compile(
        pattern=r"no User named \b(?P<match_name>[A-Za-z0-9._%+-]+)(?P<match_domain>@[^@])+\.(?P<match_suffix>[A-Za-z]+)\b found"
    )
    ERROR_DEFAULT_CERTIFICATE = re.compile(
        pattern=r"\bThe default certificate cannot be selected as the Request Signing Certificate\b"
    )
    ERROR_REQUIRED_LAYOUT_FIELD = re.compile(
        pattern=r"\bLayout must contain an item for required layout field: (?P<match_field>[A-Za-z0-9._%+-])+"
    )


class SfFixPatterns(SfEnum):
    ERROR_NO_USER_FOUND = re.compile(
        pattern=r"\b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@]+\.(?P<match_suffix>[A-Za-z]+)\b"
    )
    ERROR_DEFAULT_CERTIFICATE = re.compile(
        pattern=r"https://(www\.)?(?P<instance>[^/]+)\.my\.salesforce\.com"
    )
    ERROR_REQUIRED_LAYOUT_FIELD = re.compile(pattern=r"TODO FIND END OF PAGE LAYOUT")


class SfFixFunctions(SfEnum):
    ERROR_NO_USER_FOUND = lambda: None
    ERROR_DEFAULT_CERTIFICATE = lambda: None
    ERROR_REQUIRED_LAYOUT_FIELD = lambda: None

    def fix_no_user_found(
        self, xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
    ) -> None:
        elem: ElementTree = ElementTree(file=xml_path)
        match_name: str = match_groups["match_name"]
        match_suffix: str = match_groups["match_suffix"]

        user: pd.DataFrame = users_df.loc[
            (users_df["Username_Name"] == match_name)
            & (users_df["Username_Suffix"] == match_suffix),
            :,
        ]

        if user.empty:
            user = users_df.loc[
                (users_df["Username_Name"] == match_name),
                :,
            ]

        username_new: str = str(
            object=user.loc[
                0,
                "Username",
            ]
        )

        print(f"--- replace_invalid_users: username_new ---")
        print(f"username_new: {username_new}")

        email_new: str = str(
            object=user.loc[
                0,
                "Email",
            ]
        )

        print(f"--- replace_invalid_users: email_new ---")
        print(f"email_new: {email_new}")

    def fix_default_certificate(
        self, xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
    ) -> None:
        pass

    def fix_required_layout_field(
        self, xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
    ) -> None:
        pass


def main() -> None:
    print("yes main")
    for value in SfPaths.values():
        print(f"value: {value}")
    pass


if __name__ == "__main__":
    print("no main")
    for value in SfPaths.values():
        print(f"value: {value}")
