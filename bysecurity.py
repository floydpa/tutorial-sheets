#------------------------------------------------------------------------------
# Create/Update the 'By Security' income sheet
#------------------------------------------------------------------------------

import logging
import pandas as pd

#------------------------------------------------------------------------------
# Worksheets names

# Base worksheet class
from wb import Ws
# Source dividend information
from wb import WS_HL_DIVIDENDS, WS_FE_DIVIDENDS, WS_OTHER_DIVIDENDS
# Sheets created/updated
from wb import WS_SEC_DIVIDENDS_HL, WS_SEC_DIVIDENDS_FE, WS_SEC_DIVIDENDS

from wbformat import fmt_req_font, fmt_req_autofilter
from wbformat import fmt_req_autoresize, fmt_hdr_bgcolor
from wbformat import fmt_columns_bgcolor
from wbformat import RGB_GREY, RGB_BLUE, RGB_YELLOW


# Apply formatting to newly created/updated sheet
def apply_formatting(forever_income, worksheet_name):
    # Retrieve worksheet details for formatting requests
    workbook  = forever_income.workbook()
    worksheet = workbook.worksheet(worksheet_name)

    requests = []
    # Step 1: Change font to Arial size 8
    requests.append(fmt_req_font(worksheet))
    # Step 2: Turn on filters for the first row
    requests.append(fmt_req_autofilter(worksheet))
    # Step 3: Auto resize all columns to fit their content
    requests.append(fmt_req_autoresize(worksheet))
    # Step 4: Grey fill colour for the header row
    requests.append(fmt_hdr_bgcolor(worksheet, RGB_GREY))
    # Step 5: Blue fill colour for columns 'Annual Dividend' and 'Unit'
    requests.append(fmt_columns_bgcolor(worksheet,RGB_BLUE,2,3))
    # Step 6: Yellow fill colour for column 'OldestExDiv'
    requests.append(fmt_columns_bgcolor(worksheet,RGB_YELLOW,4,4))

    # Execute the requests
    response = forever_income.service().spreadsheets().batchUpdate(
            spreadsheetId=forever_income.spreadsheet_id(),
            body={'requests': requests}
        ).execute()
        
    logging.debug(f"service request response {response}")

    return response


#-----------------------------------------------------------------------
# Handling for dividend information taken from Hargreaves Lansdown
#-----------------------------------------------------------------------

class WsDividendsHL(Ws):
    def __init__(self, wbDestination, wbSource):
        # Initialise based on workbook where sheet will be created
        Ws.__init__(self, wbDestination, WS_SEC_DIVIDENDS_HL)
        # Read 'hl' sheet from the source workbook
        self._raw_df = wbSource.worksheet_to_df(WS_HL_DIVIDENDS)
        # Convert dividend information to generic format
        self._norm_df = self.normalise_divis()
        # Aggregate normalised data to get annual dividend information
        self._agg_df = self.aggregate_divis()
    
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
        aggregated_df = self.normalised().groupby(['SecurityId','Name']).agg(
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
            ['SecurityId','Name','Freq','AnnualDividend','Unit','OldestExDiv']
        ]

        self._agg_df = aggregated_df

        return aggregated_df
        
    def refresh(self):
        # Create or update the worksheet for HL dividends
        self.wbinstance().df_to_worksheet(self.aggregated(), self.wsname())
        apply_formatting(self.wbinstance(), self.wsname())

    def __repr__(self):
        return self.rawdata()
    

#-----------------------------------------------------------------------
# Handling for dividend information taken from FE Trustnet
#-----------------------------------------------------------------------

class WsDividendsFE(Ws):
    def __init__(self, wbDestination, wbSource):
        # Initialise based on workbook where sheet will be created
        Ws.__init__(self, wbDestination, WS_SEC_DIVIDENDS_FE)
        # Read 'hl' sheet from the source workbook
        self._raw_df = wbSource.worksheet_to_df(WS_FE_DIVIDENDS)
        # Convert dividend information to generic format
        self._norm_df = self.normalise_divis()
        # Aggregate normalised data to get annual dividend information
        self._agg_df = self.aggregate_divis()
    
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
        # Some dividends (e.g. RL) are expressed in pence, so scale up
        df['Amount'] = df['Amount'] * df['Scale']
        # Convert to dividend in pence (from pounds)
        df['Amount'] = df['Amount'] * 100
        # Set Unit as pence
        df['Unit'] = 'p'
        # Convert date columns from DD.MM.YYYY to YYYYMMDD as strings
        df['ExDivDate'] = df['ExDivDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)
        df['PaymentDate'] = df['PaymentDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)

        # Drop columns no longer needed
        df = df.drop(columns=['DividendType','DividendAmount','Scale','TaxIndicator'])
    
        self._norm_df = df

        return df

    def aggregate_divis(self):   
        # Group by 'securityId' and aggregate
        aggregated_df = self.normalised().groupby(['SecurityId','Name']).agg(
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
            ['SecurityId','Name','Freq','AnnualDividend','Unit','OldestExDiv']
        ]

        self._agg_df = aggregated_df

        return aggregated_df
        
    def refresh(self):
        # Create or update the worksheet for FE dividends
        self.wbinstance().df_to_worksheet(self.aggregated(), self.wsname())
        apply_formatting(self.wbinstance(), self.wsname())

    def __repr__(self):
        return self.rawdata()
    

#-----------------------------------------------------------------------
# Create worksheet containing security aggregated dividend information
#-----------------------------------------------------------------------

class WsDividendsBySecurity(Ws):
    def __init__(self, wbDestination, wbSource):
        # Initialise based on workbook where sheet will be created
        Ws.__init__(self, wbDestination, WS_SEC_DIVIDENDS)

        # Get dividends from 'hl' sheet
        hl = WsDividendsHL(wbDestination, wbSource)

        # Get dividends from 'fe' sheet
        fe = WsDividendsFE(wbDestination, wbSource)

        # Get other dividends (already aggregated)
        other = wbSource.worksheet_to_df(WS_OTHER_DIVIDENDS)

        # Aggregate normalised data to get annual dividend information
        self._df = pd.concat([hl.aggregated(), fe.aggregated(), other], 
                  ignore_index=True).sort_values(by='SecurityId')

    def aggregated(self):
        return self._df

    def refresh(self):
        # Create or update the worksheet for FE dividends
        self.wbinstance().df_to_worksheet(self.aggregated(), self.wsname())
        apply_formatting(self.wbinstance(), self.wsname())

    def __repr__(self):
        return self.aggregated()