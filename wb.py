#-----------------------------------------------------------------------
# Main processing for the Google Sheets workbook
#-----------------------------------------------------------------------

import logging
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# Worksheets used as source information
WS_HL_DIVIDENDS     = "hl"             # Hargreaves Lansdown dividend information
WS_FE_DIVIDENDS     = "fe"             # FE Trustnet dividend information

# Worksheets created/updates
WS_SECURITY_INFO    = "Sec Info"       # "Security Information"
WS_POSITION_INCOME  = "Pos Income"     # "By Position"
WS_SEC_DIVIDENDS_HL = "By SecurityHL"
WS_SEC_DIVIDENDS_FE = "By SecurityFE"

# RGB values for cell fill colours
RGB_BLUE   = {"red": 0.81, "green": 0.89, "blue": 0.95}
RGB_YELLOW = {"red": 0.95, "green": 1.00, "blue": 0.80}
RGB_GREY   = {"red": 0.80, "green": 0.80, "blue": 0.80}

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
# Handling for dividend information taken from Hargreaves Lansdown
#-----------------------------------------------------------------------

class WsDividendsHL:
    def __init__(self, forever_income):
        self._forever_income = forever_income
        self._workbook = forever_income.workbook()
        self._wsname   = WS_SEC_DIVIDENDS_HL

        # Read 'hl' sheet into a DataFrame
        self._raw_df = self._forever_income.worksheet_to_df(WS_HL_DIVIDENDS)

        # Convert dividend information to generic format
        self._norm_df = self.normalise_divis()

        # Aggregate normalised data to get annual dividend information
        self._agg_df = self.aggregate_divis()

    def workbook(self):
        return self._workbook
    
    def wsname(self):
        return self._wsname
    
    def rawdata(self):
        return self._raw_df
    
    def normalised(self):
        return self._norm_df

    def aggregated(self):
        return self._agg_df
    
    def normalise_divis(self):
        df = self.rawdata()

        # Use str.extract() to split the 'value' column
        df[['Amount', 'Unit']] = df['Payment'].str.extract(r'([0-9\.]+)([a-zA-Z]+)')

        # Convert 'Amount' column to float
        df['Amount'] = df['Amount'].astype(float)

        # Convert date columns from DD/MM/YYYY to YYYYMMDD as strings
        df['ExDivDate'] = df['ExDivDate'].str.replace(r'(\d{2})/(\d{2})/(\d{4})', r'\3\2\1', regex=True)
        df['PaymentDate'] = df['PaymentDate'].str.replace(r'(\d{2})/(\d{2})/(\d{4})', r'\3\2\1', regex=True)

        # Drop 'Payment' column as it's no longer needed
        df = df.drop(columns=['Payment'])

        self._norm_df = df

        return df

    def aggregate_divis(self):   
        # Group by 'securityId' and aggregate
        aggregated_df = self.normalised().groupby('SecurityId').agg(
            Count=('Amount', 'size'),           # Count of rows per securityId
            AnnualDividend=('Amount', 'sum'),   # Sum of value per securityId
            Unit=('Unit', 'min'),               # Retain column Unit
            OldestExDiv=('ExDivDate', 'min')    # Oldest ex-div date per securityId
        ).reset_index()

        # Add a new column 'Freq' based on the 'Count' column
        count_to_freq = {1: 'A', 2: 'S', 4: 'Q', 12: 'M'}
        aggregated_df['Freq'] = aggregated_df['Count'].map(count_to_freq)

        # Reorder columns
        aggregated_df = aggregated_df[
            ['SecurityId','Freq','AnnualDividend','Unit','OldestExDiv']
        ]

        self._agg_df = aggregated_df

        return aggregated_df

    # Apply formatting to newly created/updated sheet
    def apply_formatting(self):
        # Retrieve worksheet details for formatting requests
        worksheet = self.workbook().worksheet(WS_HL_DIVIDENDS)

        requests = []
        # Step 1: Change font to Arial size 8
        requests.append(self._forever_income.fmt_req_font(worksheet))
        # Step 2: Turn on filters for the first row
        requests.append(self._forever_income.fmt_req_autofilter(worksheet))
        # Step 3: Auto resize all columns to fit their content
        requests.append(self._forever_income.fmt_req_autoreszie(worksheet))
        # Step 4: Grey fill colour for the header row
        requests.append(self._forever_income.fmt_hdr_bgcolour(worksheet, RGB_GREY))
        # Step 5: Blue fill colour for columns 'Annual Dividend' and 'Unit'
        requests.append(self._forever_income.fmt_columns_bgcolour(worksheet,RGB_BLUE,2,3))
        # Step 6: Yellow fill colour for column 'OldestExDiv'
        requests.append(self._forever_income.fmt_columns_bgcolour(worksheet,RGB_YELLOW,4,4))

        # Execute the requests
        response = self._forever_income.service().spreadsheets().batchUpdate(
                spreadsheetId=self._forever_income._spreadsheet_id, 
                body={'requests': requests}
            ).execute()
        
        logging.debug(f"service request response {response}")
        
    # Create or update the worksheet for HL dividends
    def refresh(self):
        self._forever_income.df_to_worksheet(self.aggregated(), self.wsname())
        self.apply_formatting()

    def __repr__(self):
        return self.rawdata()
    

#-----------------------------------------------------------------------
# Handling for dividend information taken from FE Trustnet
#-----------------------------------------------------------------------

class WsDividendsFE:
    def __init__(self, forever_income):
        self._forever_income = forever_income
        self._workbook = forever_income.workbook()
        self._wsname   = WS_SEC_DIVIDENDS_FE

        # Read 'hl' sheet into a DataFrame
        self._raw_df = self._forever_income.worksheet_to_df(WS_FE_DIVIDENDS)

        # Convert dividend information to generic format
        self._norm_df = self.normalise_divis()

        # Aggregate normalised data to get annual dividend information
        self._agg_df = self.aggregate_divis()


    def workbook(self):
        return self._workbook
    
    def wsname(self):
        return self._wsname
    
    def rawdata(self):
        return self._raw_df
    
    def normalised(self):
        return self._norm_df

    def aggregated(self):
        return self._agg_df

    def normalise_divis(self):
        df = self.rawdata()
        # Convert 'Amount' column to float
        df['Amount'] = df['DividendAmount'].astype(float)

        # Set Unit as pence
        df['Unit'] = 'p'

        # Convert date columns from DD.MM.YYYY to YYYYMMDD as strings
        df['ExDivDate'] = df['ExDivDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)
        df['PaymentDate'] = df['PaymentDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)

        # Drop columns no longer needed
        df = df.drop(columns=['DividendType','DividendAmount','TaxIndicator'])
    
        self._norm_df = df

        return df

    def aggregate_divis(self):   
        # Group by 'securityId' and aggregate
        aggregated_df = self.normalised().groupby('SecurityId').agg(
            Count=('Amount', 'size'),           # Count of rows per securityId
            AnnualDividend=('Amount', 'sum'),   # Sum of value per securityId
            Unit=('Unit', 'min'),               # Retain column Unit
            OldestExDiv=('ExDivDate', 'min')    # Oldest ex-div date per securityId
        ).reset_index()

        # Add a new column 'Freq' based on the 'Count' column
        count_to_freq = {1: 'A', 2: 'S', 4: 'Q', 12: 'M'}
        aggregated_df['Freq'] = aggregated_df['Count'].map(count_to_freq)

        # Reorder columns
        aggregated_df = aggregated_df[
            ['SecurityId','Freq','AnnualDividend','Unit','OldestExDiv']
        ]

        self._agg_df = aggregated_df

        return aggregated_df

    # Apply formatting to newly created/updated sheet
    def apply_formatting(self):
        # Retrieve worksheet details for formatting requests
        worksheet = self.workbook().worksheet(WS_FE_DIVIDENDS)

        requests = []
        # Step 1: Change font to Arial size 8
        requests.append(self._forever_income.fmt_req_font(worksheet))
        # Step 2: Turn on filters for the first row
        requests.append(self._forever_income.fmt_req_autofilter(worksheet))
        # Step 3: Auto resize all columns to fit their content
        requests.append(self._forever_income.fmt_req_autoreszie(worksheet))
        # Step 4: Grey fill colour for the header row
        requests.append(self._forever_income.fmt_hdr_bgcolour(worksheet, RGB_GREY))
        # Step 5: Blue fill colour for columns 'Annual Dividend' and 'Unit'
        requests.append(self._forever_income.fmt_columns_bgcolour(worksheet,RGB_BLUE,2,3))
        # Step 6: Yellow fill colour for column 'OldestExDiv'
        requests.append(self._forever_income.fmt_columns_bgcolour(worksheet,RGB_YELLOW,4,4))

        # Execute the requests
        response = self._forever_income.service().spreadsheets().batchUpdate(
                spreadsheetId=self._forever_income._spreadsheet_id, 
                body={'requests': requests}
            ).execute()
        
        logging.debug(f"service request response {response}")
        
    # Create or update the worksheet for HL dividends
    def refresh(self):
        self._forever_income.df_to_worksheet(self.aggregated(), self.wsname())
        self.apply_formatting()

    def __repr__(self):
        return self.rawdata()


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
        requests.append(self._forever_income.fmt_req_font(worksheet))
        # Step 2: Turn on filters for the first row
        requests.append(self._forever_income.fmt_req_autofilter(worksheet))
        # Step 3: Auto resize all columns to fit their content
        requests.append(self._forever_income.fmt_req_autoreszie(worksheet))
        # Step 4: Grey fill colour for the header row
        requests.append(self._forever_income.fmt_hdr_bgcolour(worksheet, RGB_GREY))

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

    def fmt_req_font(self, worksheet):
        return {
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'fontFamily': 'Arial',
                            'fontSize': 8
                            }
                        }
                    },
                'fields': 'userEnteredFormat.textFormat'
            }
        } 
    
    def fmt_req_autofilter(self, worksheet):
        return {
            'setBasicFilter': {
                'filter': {
                    'range': {
                        'sheetId': worksheet.id,
                        'startRowIndex': 0,  # First row
                        'endRowIndex': 1,    # Filter only on the first row
                    }
                }
            }
        }       

    def fmt_req_autoreszie(self,worksheet):
        return {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': worksheet.id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,  # First column (A)
                    'endIndex': worksheet.col_count  # Resize up to the last column
                }
            }
        }               
    
    def fmt_hdr_bgcolour(self, worksheet, colour):
        return {
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex': 0,  # First row
                    'endRowIndex': 1,    # Only apply to the first row
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': colour
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        }

    def fmt_columns_bgcolour(self, worksheet, colour, cfirst, clast, rfirst=1, rlast=-1):
        if rlast < 0:
            # Get the last row number
            all_values = worksheet.get_all_values()
            rlast = len(all_values)  # This gives the last row with data

        return {
            'repeatCell': {
                'range': {
                    'sheetId': worksheet.id,
                    'startRowIndex':    rfirst,  # 0-indexed
                    'endRowIndex':      rlast,   # 0-indexed
                    'startColumnIndex': cfirst,  # 0-indexed, e.g. D = 3
                    'endColumnIndex':   clast+1, # 0-indexed, but end is exclusive
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': colour
                    }
                },
                'fields': 'userEnteredFormat.backgroundColor'
            }
        }

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


        