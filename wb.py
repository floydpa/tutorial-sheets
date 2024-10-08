#-----------------------------------------------------------------------
# Main processing for the Google Sheets workbook
#-----------------------------------------------------------------------

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

class WbIncome:
    def __init__(self):
        scopes   = ["https://www.googleapis.com/auth/spreadsheets"]
        creds    = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client   = gspread.authorize(creds)
        sheet_id = "1-W8w2t3HXCG9zNy6RQ4w12zkCrX_jntvQ24xEinhxG4"

        self._workbook = client.open_by_key(sheet_id)

    def workbook(self):
        return self._workbook
    
    def worksheet_list(self):
        ws_list = []
        for ws_name in map(lambda x: x.title, self._workbook.worksheets()):
            ws_list.append(ws_name)
        return ws_list
    
    def worksheet_to_df(self, worksheet_name):
        # Get the worksheet by name
        worksheet = self.workbook().worksheet(worksheet_name)
        
        # Get all data from the worksheet and convert to DataFrame
        df = pd.DataFrame(worksheet.get_all_records())

        return df

    def __repr__(self):
        s = "WORKBOOK:"
        for ws in self.worksheet_list():
            s += "\n  Sheet(%s)"%(ws)
        return s
    

if __name__ == '__main__':
    ForeverIncome = WbIncome()
    # print(ForeverIncome)

    df = ForeverIncome.worksheet_to_df("hl")
    print(df)


        