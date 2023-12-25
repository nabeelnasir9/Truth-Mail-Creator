from pandas import read_excel, ExcelWriter, concat, DataFrame
from os.path import isfile, dirname
from os import makedirs


class DataHandlers:
    def __init__(self, file_name: str = "./created_accounts/credentials.xlsx"):
        self.__excel_file_name = file_name

    def __is_path_exists(self) -> None:
        directory = dirname(self.__excel_file_name)
        makedirs(directory, exist_ok=True)

    def create_excel_file(self, data: list[dict]) -> None:
        self.__is_path_exists()

        if isfile(self.__excel_file_name):
            old_data = read_excel(self.__excel_file_name, engine="openpyxl")
            merged_data = concat([DataFrame(old_data), DataFrame(data)], ignore_index=True)
            merged_data = merged_data.drop_duplicates()
        else:
            merged_data = DataFrame(data)

        writer = ExcelWriter(self.__excel_file_name, engine='xlsxwriter')
        merged_data.to_excel(writer, index=False, sheet_name="Scraping")
        writer.close()


