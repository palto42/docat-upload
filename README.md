# docat-upload

[![Release](https://img.shields.io/github/v/release/palto42/docat-upload)](https://img.shields.io/github/v/release/palto42/docat-upload)
[![Build status](https://img.shields.io/github/actions/workflow/status/palto42/docat-upload/main.yml?branch=main)](https://github.com/palto42/docat-upload/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/palto42/docat-upload/branch/main/graph/badge.svg)](https://codecov.io/gh/palto42/docat-upload)
[![Commit activity](https://img.shields.io/github/commit-activity/m/palto42/docat-upload)](https://img.shields.io/github/commit-activity/m/palto42/docat-upload)
[![License](https://img.shields.io/github/license/palto42/docat-upload)](https://img.shields.io/github/license/palto42/docat-upload)

Tool for uploading HTML documentation to a [docat](https://github.com/docat-org/docat) server, as an alternative to [docatl](https://github.com/docat-org/docatl).

- **Git repository**: <https://github.com/palto42/docat-upload/>
- **Documentation** <https://palto42.github.io/docat-upload/>

The tool packages a specified folder with HTML documentation content (e.g. created with mkdocs) and uploads it to the specified docat server.

Extra features:

- For Python documentation the script can extract the document version from the Python module with the same name as `project`.
- Limit the number of published version with `-max-versions`
  - The script will automatically delete older versions if the number of versions is exceeded
- Specify custom SSL certificate path if an in-house CA is used.
- Support insecure SSL for use with self signed certificates

## Usage

```text
usage: docat_upload [-h] -p PROJECT [-f FOLDER] [-r RELEASE] [-t TAG] -s SERVER [-a API_KEY] [-m NUM] [-d] [-V] [-i] [-c SSL_CERT]

options:
  -h, --help            show this help message and exit
  -p PROJECT, --project PROJECT
                        Project name
  -f FOLDER, --folder FOLDER
                        Documentation folder to be uploaded, e.g. `docs/_build/html`
  -r RELEASE, --release RELEASE
                        Release version for the upload, by default retrieved from the module.__version__
  -t TAG, --tag TAG     Tag this version, e.g. 'latest'
  -s SERVER, --server SERVER
                        URL of the docat server
  -a API_KEY, --api-key API_KEY
                        API key for docat server, required for delete and overwrite
  -m NUM, --max-versions NUM
                        Cut number of versions to max. NUM
  -d, --delete          Delete the specified version
  -V, --version         show program's version number and exit
  -i, --insecure        Don't check SSL cert
  -c SSL_CERT, --ssl-cert SSL_CERT
                        Path to SSL cert or cert bundle, e.g. /etc/ssl/certs/ca-certificates.crt
```

### `.env` settings

Instead of passing the options via CLI, they can be provided in an `.env` file.

```shell
DOCAT_PROJECT=docat_upload
DOCAT_SOURCE=docs/_build/html
DOCAT_SERVER=https://my.docat.server:8443/
DOCAT_API_KEY=abc123
DOCAT_MAX_VERSIONS=10
CERT_PATH=/etc/ssl/certs/ca-certificates.crt
```
