"""pytest fixtures."""

from pathlib import Path

import pytest
from lxml import etree

TEST_DATA_DIR = Path(__file__).resolve().parent / 'data'


@pytest.fixture(autouse=True)
def logged_in_html():
    """Fixture providing the logged in HTML example"""
    return etree.parse(TEST_DATA_DIR / 'logged_in.html', etree.HTMLParser())


@pytest.fixture(autouse=True)
def logged_out_html():
    """Fixture providing the logged out HTML example"""
    return etree.parse(TEST_DATA_DIR / 'logged_out.html', etree.HTMLParser())


@pytest.fixture(autouse=True)
def captcha_error_html():
    """Fixture providing the logged out HTML example"""
    return etree.parse(TEST_DATA_DIR / 'captcha_error.html', etree.HTMLParser())
