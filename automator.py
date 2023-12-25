from utils.create_accounts import AdvanceAutomator


class TruthAutomator(object):
    def __init__(self,
                 guru_api_key: str,
                 smspool_api_key: str,
                 proxy_url: str = "",  # you must provide if proxies are enable
                 default_password: str = "Zaws12345@",
                 temp_folder: str = "temp",
                 estimated_wait: int = 60,
                 enable_proxies: bool = False,
                 headless: bool = False,
                 verbose: bool = True,
                 pace: float = 0.2,
                 max_retries: int = 2,
                 captcha_verification_image: str = "./additional_files/verification_area.png"
                 ):

        self.__proxy_url: str = proxy_url
        self.__guru_api_key: str = guru_api_key
        self.__smspool_api_key: str = smspool_api_key
        self.__default_password: str = default_password
        self.__temp_folder: str = temp_folder
        self.__estimated_time: int = estimated_wait
        self.__enable_proxies: bool = enable_proxies
        self.__headless: bool = headless
        self.__verbose: bool = verbose
        self.__pace: float = pace
        self.__captcha_verification_image: str = captcha_verification_image
        self.__max_retries: int = max_retries

    def run_script(self):
        automator_instance: AdvanceAutomator = AdvanceAutomator(
            proxy_url=self.__proxy_url,
            guru_api_key=self.__guru_api_key,
            smspool_api_key=self.__smspool_api_key,
            default_password=self.__default_password,
            temp_folder=self.__temp_folder,
            enable_proxies=self.__enable_proxies,
            estimated_wait=self.__estimated_time,
            headless=self.__headless,
            verbose=self.__verbose,
            pace=self.__pace,
            captcha_verification_image=self.__captcha_verification_image,
            max_retries=self.__max_retries
        )
        automator_instance.automate()


if __name__ == '__main__':
    obj = TruthAutomator(
        proxy_url="https://proxy.webshare.io/api/v2/proxy/list/download/abzdbmqijjevfvivbocnvxmcryctiiygndlogpgp/US/any/username/backbone/-/",
        guru_api_key="2babe0556554608b0e60954b2ffed352",
        smspool_api_key="LDlRg2NHm7FnMqoiDhV2q2SMgC6Nm48U",
        enable_proxies=True,
        estimated_wait=40
    )
    obj.run_script()
