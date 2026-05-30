"""Helper script to upload documentation to a `docat` server"""

import argparse
import importlib
import logging
import os
import re
from importlib.metadata import version
from json import JSONDecodeError
from pathlib import Path
from zipfile import ZipFile

import requests
import urllib3
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def configure_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output.

    Parameters
    ----------
    verbose : bool
        Whether to enable debug-level logging.
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)s: %(message)s")
    logger.debug("Logging configured; verbose=%s", verbose)


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
    logger.debug("Preparing documentation archive for folder %s", folder)

    file_count = 0
    with ZipFile(zip_file, "w") as zipper:
        for file_path in folder.glob("**/*"):
            if file_path.is_file():
                zipper.write(file_path, file_path.relative_to(folder))
                file_count += 1
    logger.debug("Created zip archive %s containing %d files", zip_file, file_count)

    logger.info("Upload documentation for %s v%s", project, release)
    post_url = f"{server}/api/{project}/{release}"
    headers = {"Docat-Api-Key": api_key} if api_key else {}
    logger.debug("Sending upload request to %s with headers=%s verify_ssl=%s", post_url, headers, verify_ssl)
    try:
        response = requests.post(
            post_url,
            files={"file": zip_file.open("rb")},
            timeout=60,
            headers=headers,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        logger.error("SSL error during upload: %s", e)  # noqa: TRY400
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error during upload: %s", e)  # noqa: TRY400
        return False

    zip_file.unlink()
    logger.debug("Deleted temporary zip archive %s", zip_file)

    if not response.ok:
        logger.error("Failed to upload documentation: %s", response.reason)
        return False

    logger.info("Documentation version %s for %s uploaded successfully", release, project)
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
    tag_url = f"{server}/api/{project}/{release}/tags/{tag}"
    logger.debug("Tagging release %s at %s", release, tag_url)
    try:
        response = requests.put(
            tag_url,
            timeout=60,
            headers={"Docat-Api-Key": api_key} if api_key else None,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        logger.error("SSL error during tagging: %s", e)  # noqa: TRY400
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error during tagging: %s", e)  # noqa: TRY400
        return False
    logger.debug("Tag request returned status code %s", response.status_code)
    if response.status_code == 201:
        logger.info("Tagged %s version %s as '%s'", project, release, tag)
    else:
        logger.error("Failed to tag version %s of project %s: %s", release, project, response.reason)
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
    project_url = f"{server}/api/projects/{project}"
    logger.debug("Fetching project versions from %s", project_url)
    try:
        response = requests.get(
            project_url,
            timeout=60,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        logger.error("SSL error during version pruning: %s", e)  # noqa: TRY400
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error during version pruning: %s", e)  # noqa: TRY400
        return False
    try:
        project_data = response.json()
    except JSONDecodeError:
        logger.exception("Failed to decode project version data for %s", project)
        return False
    versions = project_data["versions"]
    version_names = [version_info["name"] for version_info in versions]
    logger.debug("Received versions for project %s: %s", project, version_names)
    sorted_versions = sorted(versions, key=lambda x: tuple(map(int, x["name"].split("."))))
    if len(versions) <= max_versions:
        logger.info("Nothing to delete, only %d available", len(versions))
        return True
    delete_urls = [f"{server}/api/{project}/{doc_version['name']}" for doc_version in sorted_versions[:-max_versions]]
    logger.debug("Pruning versions: %s", delete_urls)
    for doc_version in sorted_versions[:-max_versions]:
        delete_url = f"{server}/api/{project}/{doc_version['name']}"
        logger.debug("Deleting version %s via %s", doc_version["name"], delete_url)
        response = requests.delete(
            delete_url,
            headers={"Docat-Api-Key": api_key} if api_key else None,
            timeout=60,
            verify=verify_ssl,
        )
        if response.status_code == 200:
            logger.info("Deleted version %s of project %s", doc_version["name"], project)
        else:
            logger.error(
                "Failed to delete version %s of project %s: %s",
                doc_version["name"],
                project,
                response.reason,
            )
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
    delete_url = f"{server}/api/{project}/{release}"
    logger.debug("Deleting version %s for project %s at %s", release, project, delete_url)
    try:
        response = requests.delete(
            delete_url,
            headers={"Docat-Api-Key": api_key} if api_key else None,
            timeout=60,
            verify=verify_ssl,
        )
    except requests.exceptions.SSLError as e:
        logger.error("SSL error during deletion: %s", e)  # noqa: TRY400
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error during deletion: %s", e)  # noqa: TRY400
        return False
    if response.status_code == 200:
        logger.info("Deleted %s version %s.", project, release)
        return True
    logger.error("Failed to delete version %s of project %s: %s", release, project, response.reason)
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
        logger.debug("No .env file found when reading %s", env_key)
    except PermissionError:
        logger.warning("No permission to read '.env' file.")
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
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose output",
        action="store_true",
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
    configure_logging(args.verbose)
    logger.debug("Parsed command line arguments: %s", args)

    if not args.insecure:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    verify_ssl = args.ssl_cert if args.ssl_cert else args.insecure

    if args.release is None:
        module = importlib.import_module(args.project)
        try:
            args.release = module.__version__
        except AttributeError:
            args.release = "unknown"
    logger.debug("Using release version %s", args.release)

    if not re.match(r"^((0|[1-9]\d*)\.?)*$", args.release):
        logger.info("Skip upload of un-released version '%s'", args.release)
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
