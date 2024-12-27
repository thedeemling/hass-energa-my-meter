"""Scrapping logic to get the data from the Energa website"""
from datetime import datetime
from urllib import parse

from custom_components.energa_my_meter.energa.data import EnergaMeterReading


class EnergaWebsiteScrapper:
    """Class with static members containing XPath logic that gathers the data from the Energa HTMLs"""

    @staticmethod
    def get_text_value_by_xpath(html, xpath: str) -> str:
        """Returns normalized value string if xpath expression was found correctly"""
        result_raw = html.xpath(xpath)
        return None if not result_raw or len(result_raw) == 0 else ''.join(result_raw).strip()

    @staticmethod
    def get_detail_info(html, detail_name: str) -> str:
        """Helper method to get a specific detail from the details part of the website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="{detail_name}"]/../../text()').format(
            detail_name=detail_name
        )
        return EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def parse_as_number(text: str) -> int:
        """Converts string to int if string is not null"""
        return None if not text else int(text)

    @staticmethod
    def parse_as_float(text: str) -> float:
        """Converts string to float if string is not null"""
        return None if not text else float(text.replace(',', '.'))

    @staticmethod
    def parse_as_date(text: str) -> datetime:
        """Converts string to date object of specific format if string is not null"""
        return None if not text else datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")

    @staticmethod
    def get_energy_used(html) -> float:
        """Returns the value of the energy used from Energa HTML website"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[1]/td[@class="last"]/span/text()'
        result_str = EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaWebsiteScrapper.parse_as_float(result_str)

    @staticmethod
    def get_energy_used_last_update(html) -> datetime:
        """Returns the last time the value of the energy was updated by Energa"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[1]/td[@class="first"]/div[2]/text()'
        result_str = EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaWebsiteScrapper.parse_as_date(result_str)

    @staticmethod
    def get_energy_produced(html) -> float:
        """Returns the value of the energy produced from Energa HTML website"""
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr[3]/td[@class="last"]/span/text()'
        result_str = EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaWebsiteScrapper.parse_as_float(result_str)

    @staticmethod
    def get_ppe_number(html) -> int:
        """Returns the number of the PPE from Energa HTML website"""
        number_str = EnergaWebsiteScrapper.get_detail_info(html, 'Numer PPE')
        return EnergaWebsiteScrapper.parse_as_number(number_str)

    @staticmethod
    def get_seller(html) -> str:
        """Returns the name of the seller from Energa HTML website"""
        return EnergaWebsiteScrapper.get_detail_info(html, 'Sprzedawca')

    @staticmethod
    def get_client_type(html) -> str:
        """Returns the client type from Energa HTML website"""
        return EnergaWebsiteScrapper.get_detail_info(html, 'Typ')

    @staticmethod
    def get_contract_period(html) -> str:
        """Returns the users contract period from Energa HTML website"""
        return EnergaWebsiteScrapper.get_detail_info(html, 'Okres umowy')

    @staticmethod
    def get_tariff(html) -> str:
        """Returns the name of meter's currently associated tariff from Energa HTML website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="Taryfa"]/../../span/text()')
        return EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def get_ppe_address(html) -> str:
        """Returns the address of the PPE from Energa HTML website"""
        xpath = ('//div[@id="content"]//div[@id="left"]/div[@class="detailsInfo"]/'
                 + 'div/span/b[text()="Adres PPE"]/../../div/text()')
        return EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def get_meter_id(html, meter_number: int) -> int:
        """
        Returns the internal meters ID used on Energa HTML website.
        This ID is normally hidden for the user and is only used in internal website calls
        """
        xpath = ('//form[@name="meterSelectForm"]/select[@name="meterSelectF"]'
                 + f'/option[contains(text(), "{meter_number}")]/@value')
        number_str = EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)
        return EnergaWebsiteScrapper.parse_as_number(number_str)

    @staticmethod
    def get_meter_name(html) -> str:
        """
        Returns the name of the user's meter from Energa HTML website.
        If the user didn't change it, it will contain the meter number.
        """
        xpath = '//div[@id="content"]//div[@id="left"]//div[text()="Licznik"]/../b/text()'
        return EnergaWebsiteScrapper.get_text_value_by_xpath(html, xpath)

    @staticmethod
    def get_meters(html):
        """Returns the list of the user's meters from Energa HTML website"""
        result = []

        meter_details_rows = html.xpath('.//div[@id="content"]/table/tbody/tr')

        for meter_row in meter_details_rows:
            meter_info = meter_row.xpath('.//div[@title="Edytuj"]/img')
            more_info_link = EnergaWebsiteScrapper.get_text_value_by_xpath(meter_row, './/div//a/@href')

            if meter_info and more_info_link and len(meter_info) > 0:
                meter_detail = {
                    'ppe': meter_info[0].attrib.get('ppe'),
                    'meter_name': meter_info[0].attrib.get('metername'),
                    'meter_number': meter_info[0].attrib.get('metersn'),
                    'meter_id': parse.parse_qs(parse.urlparse(more_info_link).query).get('mpc', [None])[0]
                }
                result.append(meter_detail)

        return result

    @staticmethod
    def is_captcha_shown(html) -> bool:
        """Returns true if the user is required to fill captcha"""
        captcha_image = html.xpath('//img[@name="captcha"]')
        return captcha_image is not None and len(captcha_image) > 0

    @staticmethod
    def is_error_shown(html) -> str | None:
        """Returns true if the user is required to fill captcha"""
        error_details = html.xpath('//div[@id="errorDetails"]')
        return error_details is not None and len(error_details) > 0

    @staticmethod
    def is_logged_in(html) -> bool:
        """Returns true if the user is logged in"""
        login_form = html.xpath('//form[@id="loginForm"]')
        return login_form is None or len(login_form) == 0

    @staticmethod
    def get_xrf_token(html) -> str:
        """Returns generated by the server anti-xsrf token"""
        return html.xpath('string(//input[@name="_antixsrf"]/@value)')

    @staticmethod
    def get_meter_readings(html) -> [EnergaMeterReading]:
        """Returns all found meter readings found on the website"""
        result: [EnergaMeterReading] = []
        xpath = '//div[@id="content"]//div[@id="right"]/table//tr'
        for meter_row in html.xpath(xpath):
            m_name = EnergaWebsiteScrapper.get_text_value_by_xpath(meter_row, '(.//td[@class="first"]/div)[1]/text()')
            m_reading_date = EnergaWebsiteScrapper.get_text_value_by_xpath(
                meter_row,
                '(.//td[@class="first"]/div)[2]/text()'
            )
            m_reading = EnergaWebsiteScrapper.get_text_value_by_xpath(meter_row, './/td[@class="last"]/span/text()')

            if m_name and m_reading:
                result.append(
                    EnergaMeterReading(m_name, m_reading_date,EnergaWebsiteScrapper.parse_as_float(m_reading))
                )

        return result
