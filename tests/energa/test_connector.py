from unittest.mock import patch

import pytest
from custom_components.energa_my_meter import EnergaWebsiteLoadingError
from custom_components.energa_my_meter.energa.connector import EnergaWebsiteConnector
from custom_components.energa_my_meter.energa.errors import EnergaMyMeterCaptchaRequirementError, \
    EnergaMyMeterAuthorizationError
from mechanize import Browser


class TestEnergaWebsiteConnector:
    """Tests the connection management to Energa logic"""
    @patch(target='mechanize.Browser', autospec=Browser)
    def test_authenticate_when_energa_returns_an_empty_response_should_raise_an_error(self, browser_mock):
        browser_mock.open.return_value = None
        username = 'username'
        password = 'passsword'
        connector = EnergaWebsiteConnector()
        with pytest.raises(EnergaWebsiteLoadingError):
            connector.authenticate(username, password, browser_mock)

    @patch(target='mechanize.Browser', autospec=Browser)
    @patch(
        target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.is_captcha_shown',
        return_value=True
    )
    def test_authenticate_when_energa_returns_captcha_response_should_raise_an_error(
            self,
            browser_mock,
            _captcha_shown_mock
    ):
        browser_mock.open.return_value.read.return_value = '<html><body><p>Some response</p></body></html>'
        username = 'username'
        password = 'passsword'
        connector = EnergaWebsiteConnector()
        with pytest.raises(EnergaMyMeterCaptchaRequirementError):
            connector.authenticate(username, password, browser_mock)

    @patch(target='mechanize.Browser', autospec=Browser)
    @patch(
        target='custom_components.energa_my_meter.energa.scrapper.EnergaWebsiteScrapper.is_logged_in',
        return_value=False
    )
    def test_authenticate_when_energa_did_not_log_in_the_user_should_raise_an_error(
            self,
            browser_mock,
            _is_logged_in_mock
    ):
        browser_mock.open.return_value.read.return_value = '<html><body><p>Some response</p></body></html>'
        username = 'username'
        password = 'passsword'
        connector = EnergaWebsiteConnector()
        with pytest.raises(EnergaMyMeterAuthorizationError):
            connector.authenticate(username, password, browser_mock)

    @patch(target='mechanize.Browser', autospec=Browser)
    def test_authenticate_when_energa_correctly_logs_in_the_user_should_not_raise_any_errors(
            self,
            browser_mock
    ):
        browser_mock.open.return_value.read.return_value = '<html><body><p>Some response</p></body></html>'
        username = 'username'
        password = 'passsword'
        connector = EnergaWebsiteConnector()
        response = connector.authenticate(username, password, browser_mock)
        assert response is not None
