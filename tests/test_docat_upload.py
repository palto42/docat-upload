from docat_upload.docat_upload import main

__author__ = "Matthias Homann"
__copyright__ = "Matthias Homann"
__license__ = "GPL-3.0-or-later"


def test_main(capsys):
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts against stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main()
    captured = capsys.readouterr()
    assert "The 7-th Fibonacci number is 13" in captured.out
