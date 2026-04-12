"""Helper script to upload documentation to a `docat` server"""

import argparse
import importlib
import os
import re
from importlib.metadata import version
from json import JSONDecodeError
from pathlib import Path
from zipfile import ZipFile

import requests
import urllib3
from dotenv import dotenv_values

__version__ = version("docat_upload")


def upload_docs(
    project: str,
    api_key: str,
    docs_folder: str,
    release: str,
    server: str,
    verify_ssl: str | bool = True,
) -> bool:
    """Upload documentation to the docat server.

    Parameters
    ----------
    project : str
        Name of the project on the docat server
    api_key : str | None
        API key of the project
    docs_folder : str
        Path to the html documentation folder
    release : str
        Project version to be uploaded
    server : str
        Dcat server URL
    verify_ssl : str | bool, optional
        Verify SSL (True), path to SSL certificates (str), or accept insecure SSL (False), by default True

    Returns
    -------
    bool
        True = successful
    """
    folder = Path(docs_folder)
    zip_file = folder.parent / Path("docs.zip")

    # create a ZipFile object
    zipper = ZipFile(zip_file, "w")
    # iterate over the folder and its subfolders
    for file_path in folder.glob("**/*"):
        # check if the path is a file (not a directory)
        if file_path.is_file():
            # write the file to the zip file with its relative path
            zipper.write(file_path, file_path.relative_to(folder))
    # close the zip file
    zipper.close()

    print(f"Upload documentation for {project} v{release}")
    try:
        # Send the POST request to the API with the file attached
        response = requests.post(
            f"{server}/api/{project}/{release}",
            files={"file": zip_file.open("rb")},
            timeout=60,
            headers={"Docat-Api-Key": api_key} if api_key else {},
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False

    # Delete zip file
    zip_file.unlink()

    # check the status code of the response
    if not response.ok:
        print(f"Failed to upload documentation: {response.reason}")
        return False

    print(f"Documentation version {release} for {project} uploaded successfully")
    return True


def tag_release(
    project: str, api_key: str | None, release: str, tag: str, server: str, verify_ssl: str | bool = True
) -> bool:
    """Add a version tag to an existing document.

    Parameters
    ----------
    project : str
        Name of the project on the docat server
    api_key : str | None
        API key of the project
    release : str
        Project version to be tagged
    tag : str
        Name of the tah
    server : str
        Dcat server URL
    verify_ssl : str | bool, optional
        Verify SSL (True), path to certs or accept insecure SSL (False), by default True

    Returns
    -------
    bool
        True = successful
    """
    try:
        response = requests.put(
            f"{server}/api/{project}/{release}/tags/{tag}",
            timeout=60,
            headers={"Docat-Api-Key": api_key} if api_key else None,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    if response.status_code == 201:
        print(f"Tagged {project} version {release} of  as '{tag}'")
    else:
        print(f"Failed to tag version {release} of project {project}: {response.reason}")
        return False
    return True


def prune_versions(
    project: str, api_key: str | None, max_versions: int, server: str, verify_ssl: str | bool = True
) -> bool:
    """_summary_

    Parameters
    ----------
    project : str
        Name of the project on the docat server
    api_key : str | None
        API key of the project
    max_versions : int
        Maximum number of versions to keep
    server : str
        Dcat server URL
    verify_ssl : str | bool, optional
        Verify SSL (True), path to certs or accept insecure SSL (False), by default True

    Returns
    -------
    bool
        True = successful
    """
    try:
        response = requests.get(
            f"{server}/api/projects/{project}",
            timeout=60,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    try:
        project_data = response.json()
    except JSONDecodeError:
        print(f"Failed to fetch versions for project {project}")
        return False
    versions = project_data["versions"]
    sorted_versions = sorted(versions, key=lambda x: tuple(map(int, x["name"].split("."))))
    if len(versions) <= max_versions:
        print(f"Nothing to delete, only {len(versions)} available")
        return True
    for doc_version in sorted_versions[:-max_versions]:
        response = requests.delete(
            f"{server}api/{project}/{doc_version['name']}",
            headers={"Docat-Api-Key": api_key} if api_key else None,
            timeout=60,
            verify=verify_ssl,
        )
        if response.status_code == 200:
            print(f"Deleted version {doc_version['name']} of project {project}")
        else:
            print(f"Failed to delete version {doc_version['name']} of project {project}: {response.reason}")
            return False
    return True


def delete_version(project: str, api_key: str | None, release: str, server: str, verify_ssl: str | bool = True) -> bool:
    """_summary_

    Parameters
    ----------
    project : str
        Name of the project on the docat server
    api_key : str | None
        API key of the project
    release : str
        Project version to be deleted
    server : str
        Dcat server URL
    verify_ssl : str | bool, optional
        Verify SSL (True), path to certs or accept insecure SSL (False), by default True

    Returns
    -------
    bool
        True = successful
    """
    try:
        response = requests.delete(
            f"{server}api/{project}/{release}",
            headers={"Docat-Api-Key": api_key} if api_key else None,
            timeout=60,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return False
    if response.status_code == 200:
        print(f"Deleted {project} version {release}.")
        return True
    print(f"Failed to delete version {release} of project {project}: {response.reason}")
    return False


def get_env(env_key: str) -> str | None:
    """Get environment variable from .env file or environment

    Parameters
    ----------
    env_key : str
        Name of the environment variable

    Returns
    -------
    str | None
        Value of the variable or None if not defined.
    """
    try:
        with open(".env", encoding="utf-8") as file:
            for line in file:
                if line.startswith(f"{env_key}="):
                    try:
                        return re.split(r"=|\s", line)[1]
                    except IndexError:
                        return None
    except FileNotFoundError:
        pass
    except PermissionError:
        print("WARNING: No permission to read '.env' file.")
    return os.getenv(env_key)


def get_args() -> argparse.Namespace:
    """Parse CLI arguments

    Returns
    -------
    argparse.Namespace
        Parsed CLI arguments
    """

    def greater_zero(value):
        """Check that the argument is greater than 0"""
        int_value = int(value)
        if int_value < 0:
            raise argparse.ArgumentTypeError(f"{value} is an invalid positive int value")  # noqa: TRY003
        return int_value

    config = dotenv_values(".env")

    # create parser
    parser = argparse.ArgumentParser()

    # add arguments to the parser
    parser.add_argument(
        "-p",
        "--project",
        help="Project name",
        type=str,
        required=True,
        default=config.get("DOCAT_PROJECT"),
    )
    parser.add_argument(
        "-f",
        "--folder",
        help="Documentation folder to be uploaded, e.g. `docs/_build/html`",
        type=str,
        default=config.get("DOCAT_SOURCE"),
    )
    parser.add_argument(
        "-r",
        "--release",
        help="Release version for the upload, by default retrieved from the module.__version__",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--tag",
        help="Tag this version, e.g. 'latest'",
        type=str,
    )
    parser.add_argument(
        "-s",
        "--server",
        help="URL of the docat server",
        type=str,
        required=config.get("DOCAT_SERVER") is None,
        default=config.get("DOCAT_SERVER"),
    )
    parser.add_argument(
        "-a",
        "--api-key",
        help="API key for docat server, required for delete and overwrite",
        type=str,
        default=config.get("DOCAT_API_KEY"),
    )
    parser.add_argument(
        "-m",
        "--max-versions",
        metavar="NUM",
        help="Cut number of versions to max. NUM",
        type=greater_zero,
        default=config.get("DOCAT_MAX_VERSIONS"),
    )
    parser.add_argument(
        "-d",
        "--delete",
        help="Delete the specified version",
        action="store_true",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"docat_upload {__version__}",
    )
    parser.add_argument(
        "-i",
        "--insecure",
        help="Don't check SSL cert",
        action="store_false",
    )
    parser.add_argument(
        "-c",
        "--ssl-cert",
        help="Path to SSL cert or cert bundle, e.g. /etc/ssl/certs/ca-certificates.crt",
        type=str,
        default=config.get("CERT_PATH"),
    )
    args = parser.parse_args()

    if (args.delete or args.max_versions) and not args.api_key:
        parser.error(
            "No API key provided as argument, environment variable 'DOCAT_API_KEY' or in '.env' file, but required when --max-versions is used"
        )

    return args


def main():
    """Package documents and upload them to docat server"""
    args = get_args()

    if not args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    verify_ssl = args.ssl_cert if args.ssl_cert else args.insecure

    if args.release is None:
        module = importlib.import_module(args.project)
        try:
            args.release = module.__version__
        except AttributeError:
            args.release = "unknown"
    # Check if new release should be published
    if not re.match(r"^((0|[1-9]\d*)\.?)*$", args.release):
        print(f"Skip upload of un-released version '{args.release}'")
        return

    if args.delete:
        return (
            0
            if delete_version(
                project=args.project,
                api_key=args.api_key,
                release=args.release,
                server=args.server,
                verify_ssl=verify_ssl,
            )
            else 1
        )

    if args.folder:
        upload_docs(
            project=args.project,
            api_key=args.api_key,
            docs_folder=args.folder,
            release=args.release,
            server=args.server,
            verify_ssl=verify_ssl,
        )

    if args.tag:
        tag_release(
            project=args.project,
            api_key=args.api_key,
            release=args.release,
            tag=args.tag,
            server=args.server,
            verify_ssl=verify_ssl,
        )

    if args.max_versions:
        prune_versions(
            project=args.project,
            api_key=args.api_key,
            max_versions=args.max_versions,
            server=args.server,
            verify_ssl=verify_ssl,
        )


if __name__ == "__main__":
    main()
