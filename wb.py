#-----------------------------------------------------------------------
# Main processing for the Google Sheets workbook
#-----------------------------------------------------------------------

import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from wbformat import fmt_req_font, fmt_req_autofilter
from wbformat import fmt_req_autoresize, fmt_hdr_bgcolor
from wbformat import fmt_columns_decimal, fmt_columns_percentage
from wbformat import fmt_columns_currency, fmt_columns_hjustify
from wbformat import RGB_GREY


# Worksheets used as source information
WS_HL_DIVIDENDS     = "hl"             # Hargreaves Lansdown dividend information
WS_FE_DIVIDENDS     = "fe"             # FE Trustnet dividend information
WS_OTHER_DIVIDENDS  = "other"          # Other dividend information

# Worksheets created/updates
WS_SECURITY_INFO    = "Sec Info"       # "Security Information"
WS_POSITION_INCOME  = "By Position"
WS_SEC_DIVIDENDS_HL = "By SecurityHL"  # Temporary
WS_SEC_DIVIDENDS_FE = "By SecurityFE"  # Temporary
WS_SEC_DIVIDENDS    = "By Security (new)"


#-----------------------------------------------------------------------
# Workshet Object for 'Security Info'
#-----------------------------------------------------------------------

class WsSecInfo:
    def __init__(self, forever_income, secu):
        self._forever_income = forever_income
        self._workbook       = forever_income.workbook()
        self._wsname         = WS_SECURITY_INFO
        self._secu           = secu
  
    def workbook(self):
        return self._workbook
    
    def wsname(self):
        return self._wsname
    
    def df(self):
        return self._df
    
    def create_security_info(self):
        # Column headings for Security Info sheet
        sec_info_cols = [
            'sname', 'lname', 'stype',
            'alias',
            'structure', 'sector', 
            'ISIN', 'SEDOL',
            'fund-class'
        ]
    
        # Ignore these columns from json security files
        entries_to_remove = [
            'info', 'divis','mdate',
            'fund-yield',
            'annual-income',
            'asset-allocation'
        ]

        # Read json files and create one row for each
        lst = []
        for sec in self._secu.securities():
            defn = self._secu.find_security(sec).data()
            for k in entries_to_remove:
                defn.pop(k, None)
            lst.append(defn)

        # Convert to dataframe with NaN replaced with None and all columns 'str'
        df = pd.DataFrame(lst)[sec_info_cols].astype(str).sort_values('sname')
        self._df = df.replace({'None':None, 'nan':None})

        return self._df
    
    def refresh(self):
        df = self.create_security_info()
        self._forever_income.df_to_worksheet(df, self.wsname())

    def __repr__(self):
        return self.df()


#-----------------------------------------------------------------------
# Handling for worksheet 'By Position'
#-----------------------------------------------------------------------

class WsByPosition:
    def __init__(self, forever_income):
        self._forever_income = forever_income
        self._workbook       = forever_income.workbook()
        self._positions_list = []
        self._df = None

    def workbook(self):
        return self._workbook
    
    def positions_list(self):
        return self._positions_list
    
    def df(self):
        return self._df

    # Construct the base set of position information
    # This consists of 9 columns with sample imformation as follows:
    #   Who           Paul
    #   AccType       ISA
    #   Platform      II
    #   AccountId     P_ISA_II
    #   SecurityId    TMPL
    #   Name          Temple Bar Investment Trust plc
    #   Quantity      11,972
    #   Book Cost     £20,000
    #   Value (£)     £31,905

    def create_position_info(self, positions):
        self._positions_list = []
    
        for pos in positions:
            acc = pos.account()
            acc_id = "%s_%s_%s" % (acc.usercode(), pos.platform(), pos.account_type())
            p = {
                'Who':          pos.username(),
                'AccType':      pos.account_type(),
                'Platform':     pos.platform(),
                'AccountId':    acc_id,
                'SecurityId':   pos.sname(),
                'Name':         pos.lname(),
                'Quantity':     pos.quantity(),
                'BookCost':     pos.cost(),
                'Value':        pos.value(),
                'ValueDate':    pos.vdate()
            }
            
            logging.debug("position_info(p=%s)", p)
            self._positions_list.append(p)
    
        self._df = pd.DataFrame(self._positions_list).sort_values(
            ['Who','AccType','Platform','Value'],ascending=[True,True,True,False]
        ).reset_index(drop=True)

        # logging.debug("position_info(df.dtypes=%s)", self._df.dtypes)
        # print(df)

        return self._df

    # Apply formatting to newly created/updated sheet
    def apply_formatting(self):
        # Retrieve worksheet details for formatting requests
        worksheet = self.workbook().worksheet(WS_POSITION_INCOME)

        requests = []
        # Step 1: Change font to Arial size 8
        requests.append(fmt_req_font(worksheet))
        # Step 2: Turn on filters for the first row
        requests.append(fmt_req_autofilter(worksheet))
        # Step 3: Grey fill colour for the header row
        requests.append(fmt_hdr_bgcolor(worksheet, RGB_GREY))
        # Step 4: Format Quantity and Dividend as decimsl with up to 4dp, G=6, K=10     
        requests.append(fmt_columns_decimal(worksheet, 6, 7))
        requests.append(fmt_columns_decimal(worksheet, 10, 11))
        # Step 5: Format Yield as perentage with 2dp, M=12
        requests.append(fmt_columns_percentage(worksheet, 12, 13))
        # Step 6: Format BookCost, Value and Income as currency H=7,I=8,N=13
        requests.append(fmt_columns_currency(worksheet, 7, 9))
        requests.append(fmt_columns_currency(worksheet, 13, 14))
        # Step 7: Auto resize all columns to fit their content
        requests.append(fmt_req_autoresize(worksheet))
        # Step 8: Right justify J (9) and centre justify L (11)
        requests.append(fmt_columns_hjustify(worksheet, 9, 10, 'RIGHT'))
        requests.append(fmt_columns_hjustify(worksheet, 11, 12, 'CENTER'))
                        
        # Execute the requests
        response = self._forever_income.service().spreadsheets().batchUpdate(
                spreadsheetId=self._forever_income._spreadsheet_id, 
                body={'requests': requests}
            ).execute()
        
        logging.debug(f"service request response {response}")
        

    # Create or update the worksheet using a list of Position instances
    def refresh(self, positions):

        # Create a dataframe from the positions
        df = self.create_position_info(positions)

        # Use new df to add/update position income sheet
        # Allow 4 additional columns for formulas to be added later
        self._forever_income.df_to_worksheet(df, WS_POSITION_INCOME, 0, 4)

        # Add 4 columns of formulas with dividend & income information
        # Note that it's too slow to update one cell at a time
        #    sheet.update_cell(r, 11, f"=VLOOKUP($E{r},'By Security'!$A:$E,4,FALSE)")
        # Instead, construct a range of 4 columns and then add with a single update
        formulas = []
        formulas.append(['Dividend','Unit','Yield','Income'])
        for r in range(2,len(df)+2):
            divi = f"=VLOOKUP($E{r},'By Security'!$A:$E,4,FALSE)"
            unit = f"=VLOOKUP($E{r},'By Security'!$A:$E,5,FALSE)"
            yld  = f"=N{r}/I{r}"
            inc  = f'=IF(L{r}="p",G{r},I{r})*K{r}/100'
            row  = [divi,unit,yld,inc]
            formulas.append(row)

        # Update the range with formulas
        r = len(df)+1
        cell_range = f"K1:N{r}"
        # print(f"range={cell_range}")
        # print(formulas)
        sheet = self.workbook().worksheet(WS_POSITION_INCOME)
        sheet.update(cell_range, formulas, value_input_option='USER_ENTERED')

        # Make the headings bold for the 4 formula cooumns
        sheet.format("K1:N1", {"textFormat": {"bold": True}})

        # Apply other formatting to this sheet
        self.apply_formatting()


class WbIncome:
    def __init__(self):
        scopes   = ["https://www.googleapis.com/auth/spreadsheets"]
        creds    = Credentials.from_service_account_file("credentials.json", scopes=scopes)
        client   = gspread.authorize(creds)
        sheet_id = "1-W8w2t3HXCG9zNy6RQ4w12zkCrX_jntvQ24xEinhxG4"

        self._workbook = client.open_by_key(sheet_id)

        # Parameters needed for batch requests
        self._spreadsheet_id = sheet_id
        self._service = build('sheets', 'v4', credentials=creds)

    def workbook(self):
        return self._workbook
    
    def service(self):
        return self._service
    
    def spreadsheet_id(self):
        return self._spreadsheet_id
    
    def worksheet(self, worksheet_name):
        if worksheet_name in self.worksheet_list():
            sheet = self.workbook().worksheet(worksheet_name)
        else:
            sheet = None
        return sheet

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
    
    def df_to_worksheet(self, df, worksheet_name, add_rows=0, add_cols=0):
        # Convert DataFrame to list of lists
        values = df.values.tolist()

        # Insert list containing column headings
        hdr = list(df.columns.values)
        values.insert(0, hdr)

        if worksheet_name in self.worksheet_list():
            sheet = self.workbook().worksheet(worksheet_name)
        else:
            sheet = self.workbook().add_worksheet(worksheet_name, rows=len(values)+add_rows, cols=len(hdr)+add_cols)

        sheet.clear()

        range = f"A1:{chr(ord('A')+len(hdr)-1)}{len(values)}"
        sheet.update(range, values)

        hrange = f"A1:{chr(ord('A')+len(hdr)-1)}1"
        sheet.format(hrange, {"textFormat": {"bold": True}})


    def get_fillcolour(self, range_name='Sheet1!A1'):
        # Retrieve cell format data
        result = self.service().spreadsheets().get(
            spreadsheetId=self._spreadsheet_id, 
            ranges=range_name, 
            fields='sheets(data(rowData(values(userEnteredFormat))))'
        ).execute()

        # Extract the background color (RGB) from the response
        cell_data = result['sheets'][0]['data'][0]['rowData'][0]['values'][0]['userEnteredFormat']

        # Check if the backgroundColor field exists
        if 'backgroundColor' in cell_data:
            background_color = cell_data['backgroundColor']
            red = background_color.get('red', 1)   # Default to 1 if color is white
            green = background_color.get('green', 1)
            blue = background_color.get('blue', 1)

            return {red, green, blue}
        else:
            return None
        

    def __repr__(self):
        s = "WORKBOOK:"
        for ws in self.worksheet_list():
            s += "\n  Sheet(%s)"%(ws)
        return s
    

if __name__ == '__main__':
    ForeverIncome = WbIncome()
    # print(ForeverIncome)

    # Get contents of 'hl' worksheet as a DataFrame
    df = ForeverIncome.worksheet_to_df("hl")
    print(df)

    def read_sample(workbook):
        worksheet_list = map(lambda x: x.title, workbook.worksheets())
        for ws_name in worksheet_list:
            print(ws_name)

        values_list = workbook.sheet1.row_values(1)
        print(values_list)


    def read_sheets(workbook):
        # Create a list to hold the values
        values = []
    
        # Get all worksheets
        for ws in workbook.worksheets():
            # Append the values of the worksheet to values
            values.extend(ws.get_all_values())
    
        # create df from values
        df = pd.DataFrame(values)
    
        return df

    #------------------------------------------------------------------------------

    # --- Test interface
    # read_sample(workbook)

    # --- Append all worksheets into a single dataframe
    # df = read_sheets(workbook)
    # print(df)


        