from platform import system as system_platform
from threading import active_count
from psutil import Process
from os.path import isfile
from os import system


class PPrints:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

    def __init__(self):
        self._process = Process()
        self._log_file = "logs.txt"

    @staticmethod
    def clean_terminal():
        if system_platform().lower() == "windows":
            system("cls")
        else:
            system("clear")
        return system_platform()

    def pretty_print(self, current_site: str,
                     status: str,
                     mode: str,
                     proxy: str,
                     proxy_country: str,
                     proxy_validation: str,
                     proxies_count: str,
                     logs: bool = False):
        memory_info = self._process.memory_info()
        current_memory_usage = memory_info.rss / 1024 / 1024  # Convert bytes to megabytes

        print(f"{self.GREEN}Platform: {self.clean_terminal()}\n"
              f"{self.BLUE}Current_Site: {current_site}\n"
              f"{self.GREEN}Status: {status}\n"
              f"{self.BLUE}Proxy: {proxy}\n"
              f"{self.CYAN}Proxy_Country: {proxy_country}\n"
              f"{self.WARNING}Validation: {proxy_validation}\n"
              f"{self.GREEN}Total:Current: {proxies_count}\n"
              f"{self.BLUE}Mode: {mode}\n"
              f"{self.GREEN}OutPutFile: Excel\n"
              f"{self.BLUE}LaunchedDrivers: {active_count()}\n"
              f"{self.RED}MemoryUsageByScript: {current_memory_usage: .2f}MB\n"
              f"{self.RED}Warning: Don't open the output file while script is running\n{self.RESET}")
        if logs:
            log_msg = f"Current_Site: {current_site}\n" \
                      f"Status: {status}\n\n"
            if isfile(self._log_file):
                file_obj = open(self._log_file, "a")
                file_obj.write(log_msg)
                file_obj.close()
            else:
                file_obj = open(self._log_file, "w")
                file_obj.write(log_msg)
                file_obj.close()
