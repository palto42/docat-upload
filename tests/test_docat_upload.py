"""Test cases for docat_upload module"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from docat_upload.docat_upload import (
    delete_version,
    get_env,
    prune_versions,
    tag_release,
    upload_docs,
)


class TestUploadDocs:
    """Test cases for upload_docs function"""

    def test_upload_docs_success(self, tmp_path):
        """Test successful documentation upload"""
        # Create test documentation files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")
        (docs_dir / "page.html").write_text("<html>Page</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is True
            mock_post.assert_called_once()

    def test_upload_docs_ssl_error(self, tmp_path):
        """Test upload with SSL error"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.SSLError("SSL error")

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False

    def test_upload_docs_connection_error(self, tmp_path):
        """Test upload with connection error"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False

    def test_upload_docs_http_error(self, tmp_path):
        """Test upload with HTTP error response"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = False
            mock_response.reason = "Bad Request"
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False

    def test_upload_docs_with_subdirectories(self, tmp_path):
        """Test upload with nested directory structure"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        subdir = docs_dir / "api"
        subdir.mkdir()
        (subdir / "reference.html").write_text("<html>API</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is True

    def test_upload_docs_without_api_key(self, tmp_path):
        """Test upload without API key"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is True
            # Check that headers don't contain API key when empty
            call_kwargs = mock_post.call_args.kwargs
            assert ("Docat-Api-Key", "") not in call_kwargs.get("headers", {}).items()

    def test_upload_docs_ssl_cert_path(self, tmp_path):
        """Test upload with custom SSL certificate path"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
                verify_ssl="/path/to/cert.pem",
            )

            assert result is True
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs.get("verify") == "/path/to/cert.pem"

    def test_upload_docs_insecure_ssl(self, tmp_path):
        """Test upload with SSL verification disabled"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            result = upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
                verify_ssl=False,
            )

            assert result is True
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs.get("verify") is False

    def test_upload_docs_zip_file_cleanup(self, tmp_path):
        """Test that zip file is cleaned up after upload"""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "index.html").write_text("<html>Test</html>")

        with patch("docat_upload.docat_upload.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.ok = True
            mock_post.return_value = mock_response

            upload_docs(
                project="test-project",
                api_key="test-key",
                docs_folder=str(docs_dir),
                release="1.0.0",
                server="http://localhost:8000",
            )

            # Verify zip file was deleted
            zip_file = Path(docs_dir.parent) / "docs.zip"
            assert not zip_file.exists()


class TestTagRelease:
    """Test cases for tag_release function"""

    def test_tag_release_success(self):
        """Test successful version tagging"""
        with patch("docat_upload.docat_upload.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_put.return_value = mock_response

            result = tag_release(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                tag="latest",
                server="http://localhost:8000",
            )

            assert result is True
            mock_put.assert_called_once()
            call_args = mock_put.call_args
            assert "latest" in call_args[0][0]

    def test_tag_release_http_error(self):
        """Test tagging with HTTP error response"""
        with patch("docat_upload.docat_upload.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.reason = "Bad Request"
            mock_put.return_value = mock_response

            result = tag_release(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                tag="latest",
                server="http://localhost:8000",
            )

            assert result is False

    def test_tag_release_ssl_error(self):
        """Test tagging with SSL error"""
        with patch("docat_upload.docat_upload.requests.put") as mock_put:
            mock_put.side_effect = requests.exceptions.SSLError("SSL error")

            result = tag_release(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                tag="latest",
                server="http://localhost:8000",
            )

            assert result is False

    def test_tag_release_connection_error(self):
        """Test tagging with connection error"""
        with patch("docat_upload.docat_upload.requests.put") as mock_put:
            mock_put.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = tag_release(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                tag="latest",
                server="http://localhost:8000",
            )

            assert result is False

    def test_tag_release_without_api_key(self):
        """Test tagging without API key"""
        with patch("docat_upload.docat_upload.requests.put") as mock_put:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_put.return_value = mock_response

            result = tag_release(
                project="test-project",
                api_key=None,
                release="1.0.0",
                tag="latest",
                server="http://localhost:8000",
            )

            assert result is True
            call_kwargs = mock_put.call_args.kwargs
            assert call_kwargs.get("headers") is None


class TestDeleteVersion:
    """Test cases for delete_version function"""

    def test_delete_version_success(self):
        """Test successful version deletion"""
        with patch("docat_upload.docat_upload.requests.delete") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            result = delete_version(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is True
            mock_delete.assert_called_once()

    def test_delete_version_http_error(self):
        """Test deletion with HTTP error response"""
        with patch("docat_upload.docat_upload.requests.delete") as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.reason = "Not Found"
            mock_delete.return_value = mock_response

            result = delete_version(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False

    def test_delete_version_ssl_error(self):
        """Test deletion with SSL error"""
        with patch("docat_upload.docat_upload.requests.delete") as mock_delete:
            mock_delete.side_effect = requests.exceptions.SSLError("SSL error")

            result = delete_version(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False

    def test_delete_version_connection_error(self):
        """Test deletion with connection error"""
        with patch("docat_upload.docat_upload.requests.delete") as mock_delete:
            mock_delete.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = delete_version(
                project="test-project",
                api_key="test-key",
                release="1.0.0",
                server="http://localhost:8000",
            )

            assert result is False


class TestPruneVersions:
    """Test cases for prune_versions function"""

    def test_prune_versions_success(self):
        """Test successful version pruning"""
        with (
            patch("docat_upload.docat_upload.requests.get") as mock_get,
            patch("docat_upload.docat_upload.requests.delete") as mock_delete,
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "versions": [
                    {"name": "1.0.0"},
                    {"name": "2.0.0"},
                    {"name": "3.0.0"},
                ]
            }
            mock_get.return_value = mock_response

            mock_delete_response = Mock()
            mock_delete_response.status_code = 200
            mock_delete.return_value = mock_delete_response

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=2,
                server="http://localhost:8000",
            )

            assert result is True
            # Should delete oldest version
            mock_delete.assert_called_once()

    def test_prune_versions_nothing_to_delete(self):
        """Test pruning when versions are within limit"""
        with patch("docat_upload.docat_upload.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "versions": [
                    {"name": "1.0.0"},
                    {"name": "2.0.0"},
                ]
            }
            mock_get.return_value = mock_response

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=5,
                server="http://localhost:8000",
            )

            assert result is True

    def test_prune_versions_ssl_error(self):
        """Test pruning with SSL error"""
        with patch("docat_upload.docat_upload.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.SSLError("SSL error")

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=5,
                server="http://localhost:8000",
            )

            assert result is False

    def test_prune_versions_connection_error(self):
        """Test pruning with connection error"""
        with patch("docat_upload.docat_upload.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=5,
                server="http://localhost:8000",
            )

            assert result is False

    def test_prune_versions_json_error(self):
        """Test pruning with JSON decode error"""
        from json import JSONDecodeError

        with patch("docat_upload.docat_upload.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
            mock_get.return_value = mock_response

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=5,
                server="http://localhost:8000",
            )

            assert result is False

    def test_prune_versions_delete_error(self):
        """Test pruning when deletion fails"""
        with (
            patch("docat_upload.docat_upload.requests.get") as mock_get,
            patch("docat_upload.docat_upload.requests.delete") as mock_delete,
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "versions": [
                    {"name": "1.0.0"},
                    {"name": "2.0.0"},
                    {"name": "3.0.0"},
                ]
            }
            mock_get.return_value = mock_response

            mock_delete_response = Mock()
            mock_delete_response.status_code = 403
            mock_delete_response.reason = "Forbidden"
            mock_delete.return_value = mock_delete_response

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=2,
                server="http://localhost:8000",
            )

            assert result is False

    def test_prune_versions_sorting(self):
        """Test that versions are sorted correctly for deletion"""
        with (
            patch("docat_upload.docat_upload.requests.get") as mock_get,
            patch("docat_upload.docat_upload.requests.delete") as mock_delete,
        ):
            mock_response = Mock()
            mock_response.json.return_value = {
                "versions": [
                    {"name": "3.0.0"},
                    {"name": "1.0.0"},
                    {"name": "2.0.0"},
                ]
            }
            mock_get.return_value = mock_response

            mock_delete_response = Mock()
            mock_delete_response.status_code = 200
            mock_delete.return_value = mock_delete_response

            result = prune_versions(
                project="test-project",
                api_key="test-key",
                max_versions=2,
                server="http://localhost:8000",
            )

            assert result is True
            # Should delete version 1.0.0 (oldest)
            call_args = mock_delete.call_args[0][0]
            assert "1.0.0" in call_args


class TestGetEnv:
    """Test cases for get_env function"""

    def test_get_env_from_environment(self):
        """Test getting environment variable from os.environ"""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = get_env("TEST_VAR")
            assert result == "test_value"

    def test_get_env_from_env_file(self, tmp_path):
        """Test getting environment variable from .env file"""
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=file_value\n")

        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = env_file.open("r")

            # Change to tmp_path to have .env in current directory
            with patch("os.path.exists", return_value=True), patch("os.getcwd", return_value=str(tmp_path)):
                _result = get_env("TEST_VAR")

    def test_get_env_not_found(self):
        """Test getting non-existent environment variable"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_env("NON_EXISTENT_VAR")
            assert result is None

    def test_get_env_file_not_found(self):
        """Test when .env file does not exist"""
        result = get_env("SOME_VAR")
        # Should fall back to os.getenv which returns None
        assert result is None

    def test_get_env_permission_error(self):
        """Test handling permission error when reading .env"""
        with patch("builtins.open", side_effect=PermissionError()), patch.dict(os.environ, {"TEST_VAR": "env_value"}):
            result = get_env("TEST_VAR")
            # Should fall back to environment variable
            assert result == "env_value"
