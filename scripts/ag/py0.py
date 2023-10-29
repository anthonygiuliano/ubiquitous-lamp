#! /usr/bin/env python3

from typing import Any  # https://docs.python.org/3/library/typing.html
import os
from os.path import join, dirname  # https://docs.python.org/3/library/os.html
from dotenv import load_dotenv  # https://pypi.org/project/python-dotenv/
import subprocess  # https://docs.python.org/3/library/subprocess.html
import re
import json  # https://docs.python.org/3/library/json.html
import xml.etree.ElementTree as ET  # https://docs.python.org/3/library/xml.etree.elementtree.html
import pandas as pd  # https://pandas.pydata.org/docs/user_guide/index.html#user-guide
from simple_salesforce import (
    Salesforce,
)  # https://simple-salesforce.readthedocs.io/en/latest/

###### <Psuedocode>
# Get target environment variables
# Find nodes with values that look like email addresses or usernames
# Get the files containing those nodes from the target org
# Inspect the corresponding nodes in the metadata from the target org
# If the first part of the username matches the first part of the node value, then replace the source node value with the target node value
# Else replace the source node value based on user mapping
# Either
# Get target users
# Split target users on @
# Split element[1] on .
# Create list of dicts
# TargetUsers = [username: {name, domain, tld, suffix}]
# Search force-app/main/default/*.xml nodes for targetUsers
# Potentially filter for nodes 'assignedTo', 'notifyTo'
# Replace node values with corresponding targetUsers
# Or
# Get specified map of source users to target users from environment variables
# Save files
# Commit changes
# Proceed with workflow

###### </Psuedocode>

# Get access token from sf-cli
sf_stdout: subprocess.CompletedProcess[bytes] = subprocess.run(
    args=["sf", "org", "display", "user", "--json"], stdout=subprocess.PIPE
)

# Regex pattern to cleanup output
## '\x1b\[.*?m' matches ANSI escape sequences
## '\n' matches newlines
pattern_stdout: re.Pattern[str] = re.compile(pattern=r"\x1b\[.*?m|\n")

sf_json: str = pattern_stdout.sub(repl="", string=sf_stdout.stdout.decode())
sf_dict: dict = json.loads(s=sf_json)["result"]

# Authenticate to target org using access token
sf: Salesforce = Salesforce(
    instance_url=sf_dict["instanceUrl"], session_id=sf_dict["accessToken"]
)

# Get users from target org
users = sf.query(query="SELECT Id, FirstName, LastName, Email, Username FROM User")[
    "records"
]

# Drop 'attributes' key from each user dict
[user.pop("attributes", None) for user in users]

# Create pd.DataFrame from users
users_df: pd.DataFrame = pd.DataFrame(data=users)

# Split username on @ and expand into new columns
users_df[["Username_Name", "Username_Domain"]] = users_df["Username"].str.split(
    pat="@", expand=True
)

# Split the Username_Domain column on '.' and expand into new columns with dynamic names
split_cols: pd.DataFrame = users_df["Username_Domain"].str.split(pat=".", expand=True)
split_cols.columns = [f"Username_Domain_{i}" for i in range(len(split_cols.columns))]
users_df = pd.concat([users_df, split_cols], axis=1)

# Get the absolute path to the directory containing the script
script_dir: str = os.path.dirname(p=os.path.abspath(path=__file__))

# Construct the absolute path to the force-app directory
metadata_dir: str = os.path.abspath(
    path=os.path.join(script_dir, "..", "..", "force-app")
)

# Iterate recursively over the directory tree and find all XML files
xml_paths: list[Any] = []
for root_path, dirs, files in os.walk(top=metadata_dir):
    for file in files:
        if file.endswith(".xml"):
            xml_paths.append(os.path.join(root_path, file))

# Regex pattern to match email addresses in xml nodes
pattern_email: re.Pattern[str] = re.compile(
    pattern=r"(?P<username_name>[^@]+)@[^@]+\.[^@]+"
)

# Process each XML file
for xml_path in xml_paths:
    # Parse the XML file
    tree: ET.ElementTree = ET.parse(source=xml_path)
    root: ET.Element = tree.getroot()

    # Recursively process each element in the XML file
    for elem in root.iter():
        elem_text: str = elem.text if elem.text else ""
        # Check if the element's text looks like an email address
        match: re.Match[str] | None = re.match(pattern=pattern_email, string=elem_text)
        if match:
            username_name: str = match.group("username_name")
            username_new: str = users_df.loc[
                users_df["Username_Name"] == username_name, "Username"
            ].values[0]
            email_new: str = users_df.loc[
                users_df["Username_Name"] == username_name, "Email"
            ].values[0]
            xml_basename: str = os.path.basename(p=xml_path)
            print("------------------")
            print(f"username_name: {username_name}")
            print(f"username_new: {username_new}")
            print(f"email_new: {email_new}")
            print(f"user_current: {elem.text}")
            print("---------")
            print(f"xml_basename: {xml_basename}")
            print(f"root.tag: {root.tag}")
            print(f"elem.attrib: {elem.attrib}")
            print(f"elem.tag: {elem.tag}")

            # Determine if the value is an email address or a username
            #! TODO
            # Replace the username with the new username
            elem.text = elem_text.replace(username_name, username_new)

            # Write the updated XML file to disk
            tree.write(file_or_filename=xml_path)
