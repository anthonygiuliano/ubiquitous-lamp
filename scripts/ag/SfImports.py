import re  # https://docs.python.org/3/library/re.html
import os  # https://docs.python.org/3/library/os.html
from typing import Any  # https://docs.python.org/3/library/typing.html
from enum import Enum  # https://docs.python.org/3/library/enum.html
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


class SfPatterns(SfEnum):
    ANSI = re.compile(pattern=r"\x1b\[.*?m|\n")
    NO_USER_FOUND_ID = re.compile(
        pattern=r"no User named \b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@])+\.(?P<match_suffix>[A-Za-z]+)\b found"
    )
    NO_USER_FOUND_NO_MATCH = re.compile(
        pattern=r"no User named \b[A-Za-z0-9._%+-]+@[^@]+\.[A-Za-z]+\b found"
    )
    NO_USER_FOUND_FIX = re.compile(
        pattern=r"\b(?P<match_name>[A-Za-z0-9._%+-]+)@[^@]+\.(?P<match_suffix>[A-Za-z]+)\b"
    )
    DEFAULT_CERTIFICATE_ID = re.compile(
        pattern=r"\bThe default certificate cannot be selected as the Request Signing Certificate\b"
    )
    DEFAULT_CERTIFICATE_FIX = re.compile(
        pattern=r"https://(www\.)?(?P<instance>[^/]+)\.my\.salesforce\.com"
    )
    REQUIRED_LAYOUT_FIELD_ID = re.compile(
        pattern=r"\bLayout must contain an item for required layout field: (?P<match_field>[A-Za-z0-9._%+-])+"
    )
    REQUIRED_LAYOUT_FIELD_FIX = re.compile(pattern=r"# TODO FIND END OF PAGE LAYOUT")


class SfFixes:
    @staticmethod
    def NO_USER_FOUND_FN(
        xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
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

        # TODO: Modify xml in place
        return None

    @staticmethod
    def DEFAULT_CERTIFICATE_FN(
        xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
    ) -> None:
        # TODO
        return None

    @staticmethod
    def REQUIRED_LAYOUT_FIELD_FN(
        xml_path: str, match_groups: dict[str, str], users_df: pd.DataFrame
    ) -> None:
        # TODO
        return None


class SfErrors(SfEnum):
    NO_USER_FOUND = {
        "ID": SfPatterns.NO_USER_FOUND_ID,
        "FIX": SfPatterns.NO_USER_FOUND_FIX,
        "FN": SfFixes.NO_USER_FOUND_FN,
    }
    DEFAULT_CERTIFICATE = {
        "ID": SfPatterns.DEFAULT_CERTIFICATE_ID,
        "FIX": SfPatterns.DEFAULT_CERTIFICATE_FIX,
        "FN": SfFixes.DEFAULT_CERTIFICATE_FN,
    }
    REQUIRED_LAYOUT_FIELD = {
        "ID": SfPatterns.REQUIRED_LAYOUT_FIELD_ID,
        "FIX": SfPatterns.REQUIRED_LAYOUT_FIELD_FIX,
        "FN": SfFixes.REQUIRED_LAYOUT_FIELD_FN,
    }


def main() -> None:
    print("MAIN")
    pass


if __name__ == "__main__":
    pass
