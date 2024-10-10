#-------------------------------------------------------------------------
# Process json security file definitions to create a worksheet
#-------------------------------------------------------------------------

import logging
import os
import pandas as pd

from SecurityClasses import SecurityUniverse

from wb import WbIncome

# Column headings for Security Info sheet
sec_info_cols = [
    'sname', 'lname', 'stype',
    'alias',
    'structure', 'sector', 
    'ISIN', 'SEDOL',
    'fund-class'
]

# Ignore these columns from json security files
entries_to_remove = ('info', 'divis','mdate',
                     'fund-yield',
                     'annual-income',
                     'asset-allocation')

# Worksheet name
WS_SECURITY_INFO = "Sec Info"

# Directory holding json security files
secinfo_dir = os.getenv('HOME') + '/SecurityInfo'


class WsSecInfo:
    def __init__(self, obj, secinfo_dir):
        self._obj      = obj
        self._workbook = obj.workbook()
        self._wsname   = WS_SECURITY_INFO

        secu = SecurityUniverse(secinfo_dir)

        # Read json files and create one row for each
        lst = []
        for sec in secu.securities():
            defn = secu.find_security(sec).data()
            for k in entries_to_remove:
                defn.pop(k, None)
            lst.append(defn)

        # Convert to dataframe with NaN replaced with None and all columns 'str'
        df = pd.DataFrame(lst)[sec_info_cols].astype(str).sort_values('sname')
        self._df = df.replace({'None':None, 'nan':None})
        
    def workbook(self):
        return self._workbook
    
    def wsname(self):
        return self._wsname
    
    def df(self):
        return self._df

    def add_worksheet(self):
        # Convert DataFrame to list of lists
        values = self.df().values.tolist()

        # Insert list containing column headings
        hdr = list(self.df().columns.values)
        values.insert(0, hdr)

        worksheet_list = map(lambda x: x.title, self.workbook().worksheets())
        new_worksheet_name = self.wsname()

        if new_worksheet_name in worksheet_list:
            sheet = self.workbook().worksheet(new_worksheet_name)
        else:
            sheet = self.workbook().add_worksheet(new_worksheet_name, rows=len(values), cols=len(hdr))

        sheet.clear()

        range = f"A1:{chr(ord('A')+len(hdr)-1)}{len(values)}"
        sheet.update(range, values)

        hrange = f"A1:{chr(ord('A')+len(hdr)-1)}1"
        sheet.format(hrange, {"textFormat": {"bold": True}})

    def __repr__(self):
        return self.df()
    

if __name__ == '__main__':

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    # Open Google Sheets workbook
    ForeverIncome = WbIncome()

    # Consume json security information files and create worksheet
    sec_info = WsSecInfo(ForeverIncome, secinfo_dir)

    print(sec_info.df())

    sec_info.add_worksheet()

  
