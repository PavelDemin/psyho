import config
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class gsheets:
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    def __init__(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(config.CLIENT_SECRET, self.scope)
        self.gc = gspread.authorize(credentials)
        self.sh = self.gc.open(config.spreadsheet_name)

    def read_sheet(self, number_sheet: int):
        worksheet = self.sh.get_worksheet(number_sheet)
        return worksheet

    def get_list_worksheets(self):
        return self.sh.worksheets()

    def get_values_from_row(self, number_sheet: int = 0, row_num: int = 1) -> list:
        values_list = self.read_sheet(number_sheet).row_values(row_num)
        return values_list

    def get_all_values_from_worksheet(self, number_sheet: int = 0) -> list:
        list_of_lists = self.read_sheet(number_sheet).get_all_values()
        return list_of_lists
