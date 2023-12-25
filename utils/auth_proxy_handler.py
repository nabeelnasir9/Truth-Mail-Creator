from requests.exceptions import RequestException
from os.path import normpath, join, isfile
from tempfile import mkdtemp
from shutil import rmtree
from requests import get


class ProxyExtension:
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]},
        "minimum_chrome_version": "76.0.0"
    }
    """

    background_js = """
    var config = {
        mode: "fixed_servers",
        rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: %d
            },
            bypassList: ["localhost"]
        }
    };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        { urls: ["<all_urls>"] },
        ['blocking']
    );
    """

    def __init__(self, host, port, user, password):
        self._dir = normpath(mkdtemp())

        manifest_file = join(self._dir, "manifest.json")
        with open(manifest_file, mode="w") as f:
            f.write(self.manifest_json)

        background_js = self.background_js % (host, port, user, password)
        background_file = join(self._dir, "background.js")
        with open(background_file, mode="w") as f:
            f.write(background_js)

    @property
    def directory(self):
        return self._dir

    def __del__(self):
        rmtree(self._dir)


class ProxyFunctions:
    def __init__(self, proxies_url: str):
        self._proxy_url = proxies_url

    def load_proxies(self) -> any([list, None]):
        if "http" in self._proxy_url:
            return self._load_proxies_from_url()
        return self._load_proxies_from_file()

    def _load_proxies_from_file(self) -> any([list, None]):
        if isfile(self._proxy_url):
            open_file = open(file=self._proxy_url, mode="r")
            file_content = open_file.readline()
            open_file.close()
            clean_proxies = [proxy.strip() for proxy in file_content]
            return clean_proxies
        return None

    def _load_proxies_from_url(self) -> any([list, None]):
        response = get(url=self._proxy_url)
        if response.status_code == 200:
            decoded_content = response.content.decode().strip()
            split_proxies = decoded_content.split("\n")
            clean_proxies = [proxy.strip() for proxy in split_proxies]
            return clean_proxies
        return None

    @staticmethod
    def unpack_single_proxy(proxy: str) -> tuple:
        proxy_host, proxy_port, proxy_user, proxy_pass = proxy.split(":")
        proxy_tuple = (proxy_host, int(proxy_port), proxy_user, proxy_pass)
        return proxy_tuple


class ProxyCheckers:
    TEST_ADDR = 'https://api.my-ip.io/ip'

    def __init__(self, proxy: str):
        self._proxy_host, self._proxy_port, self._proxy_user, self._proxy_pass = proxy.split(":")

    def check_proxy_validation(self) -> dict:
        proxy_url = f'http://{self._proxy_user}:{self._proxy_pass}@{self._proxy_host}:{self._proxy_port}'
        target_url = self.TEST_ADDR
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }

        try:
            response = get(target_url, proxies=proxies, timeout=10)
            if response.ok:
                ip_api_url = f'http://ip-api.com/json/{self._proxy_host}'
                ip_info = get(ip_api_url).json()
                country = ip_info.get('country')
                return {
                    'country': country,
                    'proxy': self._proxy_host,
                    'status': 'Valid',
                    'response_code': response.status_code
                }
            else:
                return {
                    'proxy': self._proxy_host,
                    'status': 'Invalid',
                    'response_code': response.status_code
                }
        except RequestException:
            return {
                'proxy': self._proxy_host,
                'status': 'Error',
                'response_code': None
            }

