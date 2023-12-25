from selenium.common import WebDriverException, TimeoutException, NoSuchElementException
from utils.auth_proxy_handler import ProxyExtension, ProxyFunctions, ProxyCheckers
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver
from undetected_chromedriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from utils.data_handler import DataHandlers
from random import choice, choices, uniform
from utils.smspool_api import smspool
from utils.pprints import PPrints
import chromedriver_autoinstaller
from psutil import process_iter
from os import path, makedirs
from time import sleep, time
import pyautogui
import requests
import string
import base64


class AdvanceAutomator(object):
    """
    Class for automating the account creation process on ProtonMail and Truth Social.

    Args:
        proxy_url (str): The URL of the proxy server.
        guru_api_key (str): API key for the captcha solving service.
        smspool_api_key (str): API key for the SMS service.
        enable_proxies (bool, optional): Enable or disable the use of proxies. Defaults to True.
        headless (bool, optional): Run the browser in headless mode. Defaults to False.
        verbose (bool, optional): Enable verbose logging. Defaults to True.
        estimated_wait (int, optional): Maximum wait time for WebDriverWait. Defaults to 60.
        default_password (str, optional): Default password for account creation. Defaults to "Zaws12345@".
        temp_folder (str, optional): Temporary folder path. Defaults to "temp".

    Attributes:
        __proton_signup_url (str): URL for ProtonMail signup.
        __guru_req_api_endpoint (str): Captcha solving API endpoint.
        __guru_status_api_endpoint (str): Captcha solving status API endpoint.
        __truth_verify_endpoint (str): URL for Truth Social verification.
        __css_skip_proton_pricing (str): CSS selector for skipping ProtonMail pricing page.
        ... (Other CSS selectors for various elements)

    Methods:
        __init__: Initializes the AdvanceAutomator instance.
        __validate_directories: Creates necessary directories.
        __pprint_override: Customized pretty print for logging.
        __create_patched_browser: Creates and configures a patched WebDriver instance.
        __kill_chromedriver: Kills all running chromedriver processes.
        __human_like_interaction: Introduces human-like delays.
        __handle_proton_signup_page: Handles the ProtonMail signup page.
        __solve_captcha_using_api: Solves captcha using an external API.
        __handle_proton_caption_solution: Handles the ProtonMail captcha solution.
        __handle_proton_welcome_process: Handles the welcome process on ProtonMail.
        __handle_truth_startup_process: Handles the startup process on Truth Social.
        __get_truth_verification_message: Retrieves the verification message for Truth Social.
        __handle_truth_phone_number_verification_process: Handles phone number verification for Truth Social.
        __handle_cloudflare_bypassing: Bypasses Cloudflare security on Truth Social.
        __finalize_truth_account: Creates a final username for Truth Social account.
        automate: Main method to execute the entire account creation process.
    """

    # Fixed Sites
    __proton_signup_url: str = "https://account.proton.me/mail/signup"
    __guru_req_api_endpoint: str = "http://api.captcha.guru/in.php"
    __guru_status_api_endpoint: str = "http://api.captcha.guru/res.php"
    __truth_verify_endpoint: str = "https://truthsocial.com/verify"

    # css locators
    __css_skip_proton_pricing: str = 'div[class="sign-layout-main-content"] > div > button'
    __css_captcha_submit_button: str = 'div[class="challenge-canvas"] + div > button'
    __css_proton_cards_next_button: str = 'div[class*="two-content"] > footer > button'
    __css_proton_close_popup_button: str = 'div[class*="two-content"] > button'
    __css_proton_choose_name_button: str = 'form[name="accountForm"] > button'
    __css_proton_recovery_ph_number_skip: str = 'form[name="recoveryForm"] > button + button'
    __css_proton_recovery_ph_number_confirm_skip: str = 'div[class*="modal-two-footer"] > div > button'

    __css_truth_date_picker: str = 'select[data-testid="datepicker-year"]'
    __css_truth_startup_form_button: str = 'form[data-testid="form"] > div[class="text-center"] > button'
    __css_truth_first_verification_box: str = 'input[aria-label="Please enter verification code. Digit 1"]'
    __css_truth_submit_username_button: str = 'form[data-testid="form"] > div[class*="text-center"] > button'
    __css_truth_switch_to_last_card: str = 'main > div[class*="justify-center"] > div:nth-child(2) > button'
    __css_truth_finalize_button: str = 'div[data-testid="card-body"] > div:nth-child(2) > div > button'

    def __init__(self,
                 proxy_url: str,
                 guru_api_key: str,
                 smspool_api_key: str,
                 enable_proxies: bool = True,
                 headless: bool = False,
                 verbose: bool = True,
                 estimated_wait: int = 60,
                 default_password: str = "Zaws12345@",
                 temp_folder: str = "temp",
                 pace: float = 0.2,
                 max_retries: int = 2,
                 captcha_verification_image: str = "./additional_files/verification_area.png"
                 ) -> None:
        """
        Initializes the AdvanceAutomator instance.

        Args:
            proxy_url (str): The URL of the proxy server.
            guru_api_key (str): API key for the captcha solving service.
            smspool_api_key (str): API key for the SMS service.
            enable_proxies (bool, optional): Enable or disable the use of proxies. Defaults to True.
            headless (bool, optional): Run the browser in headless mode. Defaults to False.
            verbose (bool, optional): Enable verbose logging. Defaults to True.
            estimated_wait (int, optional): Maximum wait time for WebDriverWait. Defaults to 60.
            default_password (str, optional): Default password for account creation. Defaults to "Zaws12345@".
            temp_folder (str, optional): Temporary folder path. Defaults to "temp".

        Returns:
            None

        """
        self.__pace: float = pace
        self.__captcha_verification_image: str = path.abspath(captcha_verification_image)
        self.__max_retries: int = max_retries
        self.__proxies_handlers: ProxyFunctions = ProxyFunctions(proxies_url=proxy_url)
        self.__pprints: PPrints = PPrints()
        self.__enable_proxies: bool = enable_proxies
        self.__headless: bool = headless
        self.__driver_mode: str = "Headless" if headless else "Windowed"
        self.__verbose: bool = verbose
        self.__proxy_index: int = 0
        self.__proxies: list = list()
        self.__total_proxies: int = 0
        self.__proxy_details: dict = {}
        self.__wait: any([WebDriverWait, None]) = None
        self.__action: any([ActionChains, None]) = None
        self.__default_password: str = default_password
        self.__estimated_time: int = estimated_wait
        self.__temp_folder: str = path.abspath(temp_folder)
        self.__captcha_ss_path: str = path.join(self.__temp_folder, 'captcha.png')
        self.__guru_api_key: str = guru_api_key
        self.__smspool_api_key: str = smspool_api_key
        self.__data_handlers: DataHandlers = DataHandlers()
        self.__validate_directories()

    def __validate_directories(self):
        """
        Creates necessary directories.

        Returns:
            None
        """

        makedirs(name=self.__temp_folder, exist_ok=True)

    def __pprint_override(self, current_site: str, status: str, logs: bool = False) -> None:
        """
        Customized pretty print for logging.

        Args:
            current_site (str): Current website being processed.
            status (str): Status message.
            logs (bool, optional): Include additional logs. Defaults to False.

        Returns:
            None
        """

        if self.__verbose:
            if self.__enable_proxies:
                try:
                    country = self.__proxy_details["country"]
                except KeyError:
                    country = "UNKNOWN"
                try:
                    proxy = self.__proxy_details['proxy']
                except KeyError:
                    proxy = "Not yet Known"
                try:
                    proxy_validation = self.__proxy_details['status']
                except KeyError:
                    proxy_validation = "Not yet Known"
            else:
                country = "Proxies are disable"
                proxy = "Proxies are disable"
                proxy_validation = "Proxies are disable"

            proxies_count = f"{self.__total_proxies}:{self.__proxy_index}"

            self.__pprints.pretty_print(current_site=current_site,
                                        status=status,
                                        proxy=proxy,
                                        proxies_count=proxies_count,
                                        proxy_country=country,
                                        proxy_validation=proxy_validation,
                                        mode=self.__driver_mode,
                                        logs=logs)

    def __create_patched_browser(self) -> WebDriver:
        """
        Creates and configures a patched WebDriver instance.

        Returns:
            WebDriver: The configured WebDriver instance.
        """

        retries = 0
        while retries < self.__max_retries:
            if self.__enable_proxies:
                if self.__total_proxies <= 0:
                    proxies_list = self.__proxies_handlers.load_proxies()
                    if not proxies_list:
                        self.__pprint_override(
                            current_site="Proton",
                            status=f"ERROR (create_patched_browser) Unable to load proxies", logs=True
                        )
                    else:
                        self.__proxies = proxies_list
                        self.__total_proxies = len(self.__proxies)

                if self.__proxy_index >= self.__total_proxies - 1:
                    self.__proxy_index = 0

                proxy_checker = ProxyCheckers(proxy=self.__proxies[self.__proxy_index])
                proxy_checker_status = proxy_checker.check_proxy_validation()
                while (proxy_checker_status["status"] == "Invalid" or proxy_checker_status["status"] == "Error") \
                        and self.__total_proxies > 0:
                    self.__proxies.pop(self.__proxy_index)
                    self.__total_proxies = len(self.__proxies)
                    self.__proxy_index += 1
                    if self.__proxy_index >= self.__total_proxies - 1:
                        self.__proxy_index = 0
                        proxies_list = self.__proxies_handlers.load_proxies()
                        if proxies_list:
                            self.__proxies = proxies_list
                            self.__total_proxies = len(self.__proxies)
                        break
                self.__proxy_details = proxy_checker_status
            try:
                options = ChromeOptions()
                options.add_argument('--disable-popup-blocking')
                options.add_argument("--window-size=1920,1080")
                if self.__enable_proxies:
                    proxy = self.__proxies_handlers.unpack_single_proxy(self.__proxies[self.__proxy_index])
                    self.__proxy_index += 1
                    proxy_extension = ProxyExtension(*proxy)
                    options.add_argument(f"--load-extension={proxy_extension.directory}")

                version_main = int(chromedriver_autoinstaller.get_chrome_version().split(".")[0])
                if self.__headless:
                    driver = Chrome(options=options, enable_logging=False, version_main=version_main, headless=True)
                else:
                    driver = Chrome(options=options, enable_logging=False, version_main=version_main, headless=False)
            except WebDriverException:
                retries += 1
                continue
            self.__wait = WebDriverWait(driver, self.__estimated_time)
            self.__action = ActionChains(driver)
            driver.delete_all_cookies()
            # driver.execute_script(script='document.body.style.zoom = "100%"')
            return driver

    @staticmethod
    def __kill_chromedriver():
        """
        Kills all running chromedriver processes.

        Returns:
            None
        """

        for proc in process_iter(['pid', 'name']):
            if "chromedriver" in proc.name():
                proc.kill()

    @staticmethod
    def __human_like_interaction():
        """
        Introduces human-like delays.

        Returns:
            None
        """

        delay_time = uniform(2, 4)
        sleep(delay_time)

    def __handle_proton_signup_page(self, driver: WebDriver) -> str:
        """
        Handles the ProtonMail signup page.

        Args:
            driver (WebDriver): The WebDriver instance.

        Returns:
            str: The created ProtonMail email.
        """

        iframe = self.__wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'iframe[title="Username"]')))
        driver.switch_to.frame(iframe)
        first_char = choice(string.ascii_lowercase)
        remaining_chars = ''.join(choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=9))
        email = f"{first_char}{remaining_chars}"
        self.__wait.until(EC.element_to_be_clickable((By.ID, "email"))).click()
        actions = ActionChains(driver=driver)
        for digit in email:
            actions.send_keys(digit)
            actions.perform()
            sleep(self.__pace)
        driver.switch_to.default_content()
        self.__wait.until(EC.visibility_of_element_located((By.ID, "password"))).click()
        actions = ActionChains(driver=driver)
        for digit in self.__default_password:
            actions.send_keys(digit)
            actions.perform()
            sleep(self.__pace)
        self.__wait.until(EC.visibility_of_element_located((By.ID, "repeat-password"))).click()
        actions = ActionChains(driver=driver)
        for digit in self.__default_password:
            actions.send_keys(digit)
            actions.perform()
            sleep(self.__pace)
        self.__human_like_interaction()
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'form[name="accountForm"] > button'))).click()
        driver.switch_to.default_content()
        return email

    def __solve_captcha_using_api(self) -> tuple[int, int]:
        """
        Solves captcha using an external API.

        Returns:
            tuple[int, int]: Captcha coordinates (x, y).
        """

        image_content = base64.b64encode(open(file=self.__captcha_ss_path, mode="rb").read()).decode()
        payload = {
            'textinstructions': 'Select all images with slider',
            'click': 'geetest',
            'key': self.__guru_api_key,
            'method': 'base64',
            'body': image_content
        }
        response = requests.post(url=self.__guru_req_api_endpoint, data=payload)
        captcha_id = response.text.split('|')[1].strip()
        sleep(2)
        response = requests.get(f"{self.__guru_status_api_endpoint}?key={self.__guru_api_key}&id={captcha_id}").content
        while response == "b'CAPCHA_NOT_READY'":
            sleep(3)
            response = requests.get(
                f"{self.__guru_status_api_endpoint}?key={self.__guru_api_key}&id={captcha_id}"
            ).content

        coordinates = response.decode("utf-8").split("|")[1].replace('coordinates:', '').strip().split(',')
        coordinate_x, coordinate_y, coordinate_z = (
            int(coordinates[0].replace("x=", "").strip()),
            int(coordinates[1].replace("y=", "").strip()),
            int(coordinates[2].replace("w=", "").strip())
        )
        return coordinate_x, coordinate_y

    def __handle_proton_caption_solution(self, driver: WebDriver) -> None:
        """
        Handles the ProtonMail captcha solution.

        Args:
            driver (WebDriver): The WebDriver instance.

        Returns:
            None
        """

        captcha_outer_frame = self.__wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'iframe[title="Captcha"]'))
        )
        driver.switch_to.frame(captcha_outer_frame)
        captcha_image_frame = self.__wait.until(EC.visibility_of_element_located((By.NAME, "pcaptcha")))
        driver.switch_to.frame(captcha_image_frame)
        self.__wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "challenge-canvas")))
        sleep(10)
        canvas = self.__wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "challenge-canvas")))
        pyautogui.moveTo(x=500, y=500)
        canvas.screenshot(self.__captcha_ss_path)

        # solve the captcha
        coordinate_x, coordinate_y = self.__solve_captcha_using_api()
        pyautogui.click(801, 600)
        pyautogui.moveTo(801, 500)
        pyautogui.mouseDown()
        pyautogui.move(coordinate_x - 5, coordinate_y - 37, duration=1)
        pyautogui.mouseUp()
        sleep(3)
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_captcha_submit_button))).click()
        driver.switch_to.default_content()

    def __unsolved_captcha_handler(self, driver: WebDriver):
        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[id="label_1"][data-testid="tab-header-Email-button"]')
        )).click()
        sleep(1)
        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[id="label_0"][data-testid="tab-header-CAPTCHA-button"]')
        )).click()
        self.__handle_proton_caption_solution(driver=driver)

    def __handle_proton_welcome_process(self, driver: WebDriver) -> None:
        """
        Handles the welcome process on ProtonMail.

        Returns:
            None
        """
        while True:
            try:
                self.__wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_proton_choose_name_button))).click()
                break
            except TimeoutException:
                self.__unsolved_captcha_handler(driver=driver)

        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, self.__css_proton_recovery_ph_number_skip))
        ).click()
        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, self.__css_proton_recovery_ph_number_confirm_skip))
        ).click()
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_proton_cards_next_button))).click()
        sleep(.5)
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_proton_cards_next_button))).click()
        sleep(.5)
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_proton_cards_next_button))).click()
        sleep(.5)
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_proton_close_popup_button))).click()

    def __handle_truth_startup_process(self, email: str, driver: WebDriver) -> bool:
        """
        Handles the startup process on Truth Social.

        Args:
            email (str): ProtonMail email used for Truth Social.
        """

        try:
            self.__wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, self.__css_truth_date_picker)))
        except TimeoutException:
            return False
        year_drop_down = Select(self.__wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, self.__css_truth_date_picker)))
        )
        year_drop_down.select_by_value('1996')
        self.__human_like_interaction()
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_truth_startup_form_button))).click()
        self.__wait.until(EC.visibility_of_element_located((By.NAME, 'email'))).click()
        for digit in f"{email}@proton.me":
            self.__action.send_keys(digit)
            self.__action.perform()
            sleep(self.__pace)
        self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_truth_startup_form_button))).click()
        # wait for the verification email
        try:
            driver.find_element(By.CSS_SELECTOR, self.__css_truth_startup_form_button).click()
        except NoSuchElementException:
            ...
        sleep(15)
        return True

    def __get_truth_verification_message(self, driver: WebDriver, truth_handle: any) -> None:
        """
        Retrieves the verification message for Truth Social.

        Args:
            driver (WebDriver): The WebDriver instance.
            truth_handle: Handle for the Truth Social window.

        Returns:
            None
        """
        while True:
            driver.refresh()
            sleep(5)
            current_messages = driver.find_elements(
                By.CSS_SELECTOR, 'div[data-shortcut-target="item-container-wrapper"]'
            )
            found_message = False
            for message in current_messages:
                if 'truth' in message.text.lower():
                    message.click()
                    found_message = True
                    break
            if found_message:
                break
        message_content_iframe = self.__wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'iframe[title="Email content"]'))
        )
        driver.switch_to.frame(message_content_iframe)
        anchor_tags_in_message = driver.find_elements(By.TAG_NAME, 'a')
        links = [tag.get_attribute('href') for tag in anchor_tags_in_message]
        for link in links:
            if 'verify' in link:
                driver.close()
                driver.switch_to.window(truth_handle)
                sleep(1)
                driver.get(link)
                break
        driver.switch_to.default_content()

    def __handle_truth_phone_number_verification_process(self, driver: WebDriver) -> bool:
        """
        Handles phone number verification for Truth Social.
        Args:
            driver (WebDriver): The WebDriver instance.
        """

        code: str = ""
        total_retries = 0
        while total_retries <= self.__max_retries:
            sms = smspool(apikey=self.__smspool_api_key)
            purchased_message = sms.purchase_sms(service="Truth Social")
            phone_number, order_id = purchased_message['number'], purchased_message['order_id']
            ph_editor = self.__wait.until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div[class="PhoneInputCountry"] + input'))
            )
            ph_editor.clear()
            ph_editor.click()
            for digit in str(phone_number):
                self.__action.send_keys(digit)
                self.__action.perform()
                sleep(0.5)
            try:
                self.__wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'form[data-testid="form"] > div[class="text-center"] > button'))
                ).click()
            except TimeoutException:
                ...
            sleep(2)
            start_time = time()
            max_duration = 3 * 60  # 3 minutes
            force_break = False
            while True:
                elapsed_time = time() - start_time
                if elapsed_time >= max_duration:
                    force_break = True
                    break
                message = sms.check_sms(order_id)
                if 'sms' in message:
                    code = message['sms']
                    break
            total_retries += 1
            if force_break:
                driver.back()
            else:
                break

        if total_retries >= self.__max_retries and code != "":
            return False

        verification_input = self.__wait.until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, self.__css_truth_first_verification_box))
        )
        verification_input.click()
        actions = ActionChains(driver=driver)
        for digit in str(code):
            actions.send_keys(digit)
            actions.perform()
            sleep(self.__pace)

        return True

    def __handle_cloudflare_bypassing(self, driver: WebDriver) -> bool:
        """
        Bypasses Cloudflare security on Truth Social.
        Args:
            driver (WebDriver): The WebDriver instance.
        Returns:
            bool
        """
        sleep(20)
        driver.execute_script(f'''window.open("{self.__truth_verify_endpoint}","_blank");''')
        sleep(5)
        driver.switch_to.window(window_name=driver.window_handles[0])
        driver.close()
        sleep(2)
        driver.switch_to.window(window_name=driver.window_handles[-1])
        try:
            WebDriverWait(driver=driver, timeout=10).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div[id="cf-turnstile"] > iframe'))
            )
            pyautogui.moveTo(x=500, y=500)
            sleep(3)
            cords = pyautogui.locateCenterOnScreen(image=self.__captcha_verification_image,
                                                   grayscale=True, minSearchTime=2.5)
            if cords:
                pyautogui.click(cords)
        except TimeoutException:
            ...
        sleep(2)
        try:
            WebDriverWait(driver=driver, timeout=10).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'div[id="cf-turnstile"] > iframe'))
            )
            return False
        except TimeoutException:
            ...
        driver.switch_to.default_content()
        return True

    def __finalize_truth_account(self) -> str:
        """
        Creates a final username for a Truth Social account.
        Returns:
            str: The finalized Truth Social username.
        """

        first_char = choice(string.ascii_lowercase)
        remaining_chars = ''.join(choice(string.ascii_lowercase + string.digits) for _ in range(9))
        username = f"{first_char}{remaining_chars}"
        self.__wait.until(EC.visibility_of_element_located((By.NAME, 'username'))).send_keys(username)
        self.__wait.until(EC.visibility_of_element_located((By.NAME, 'password'))).send_keys(self.__default_password)
        sleep(1)
        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, self.__css_truth_submit_username_button))
        ).click()
        self.__wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, self.__css_truth_switch_to_last_card))
        )[-1].click()
        self.__wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, self.__css_truth_finalize_button))
        ).click()
        return username

    def automate(self):
        """
        Main method to execute the entire account creation process.
        Returns:
            None
        """

        while True:
            self.__pprint_override(current_site="Proton", status="Creating patched driver")
            driver: WebDriver = self.__create_patched_browser()
            proton_handle = driver.current_window_handle
            try:
                self.__pprint_override(current_site="Proton", status=f"loading url: {self.__proton_signup_url}")
                driver.get(self.__proton_signup_url)
                self.__pprint_override(current_site="Proton", status="Handling email creation process")
                proton_email: str = self.__handle_proton_signup_page(driver=driver)
                self.__human_like_interaction()
                self.__pprint_override(current_site="Proton", status="Handling captcha section")
                self.__wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, self.__css_skip_proton_pricing))).click()
                self.__handle_proton_caption_solution(driver=driver)
                self.__pprint_override(current_site="Proton", status="Handling welcome messages")
                self.__handle_proton_welcome_process(driver=driver)

                # create a truth account created
                self.__pprint_override(current_site="Truth", status="Switching to truth")
                driver.execute_script(f"window.open('{self.__truth_verify_endpoint}','_blank')")
                truth_site_handle = driver.window_handles[-1]
                driver.switch_to.window(truth_site_handle)
                if not self.__handle_truth_startup_process(email=proton_email, driver=driver):
                    driver.quit()
                    continue
                self.__pprint_override(current_site="Truth", status="Verifying email")
                driver.switch_to.window(proton_handle)
                self.__get_truth_verification_message(driver=driver, truth_handle=truth_site_handle)
                self.__pprint_override(current_site="Truth", status="Verifying phone number")
                if not self.__handle_truth_phone_number_verification_process(driver=driver):
                    driver.quit()
                    continue
                self.__pprint_override(current_site="Truth", status="Bypassing cloud flare security (will take time)")
                if not self.__handle_cloudflare_bypassing(driver=driver):
                    self.__pprint_override(current_site="Truth", status="Unable to solve cloud flare security")
                    driver.quit()
                    continue
                self.__pprint_override(current_site="Truth", status="Creating username and finalizing account")
                truth_username = self.__finalize_truth_account()
                temp_data = [
                    {
                        "email": f"{proton_email}@proton.me",
                        "password": self.__default_password,
                        "truth_username": f"@{truth_username}",
                        "truth_password": self.__default_password}
                ]
                self.__data_handlers.create_excel_file(data=temp_data)
                driver.quit()
            except KeyboardInterrupt:
                print("[---] Closing program please wait")
                driver.quit()
                self.__kill_chromedriver()
                break
