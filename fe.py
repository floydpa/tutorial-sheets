#-------------------------------------------------------------------------
# Processing of FE Trustnet dividend information on 'fe' worksheet
#-------------------------------------------------------------------------

import pandas as pd


def normalised(df):
    # Convert 'Amount' column to float
    df['Amount'] = df['DividendAmount'].astype(float)

    # Set Unit as pence
    df['Unit'] = 'p'

    # Convert date columns from DD.MM.YYYY to YYYYMMDD as strings
    df['ExDivDate'] = df['ExDivDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)
    df['PaymentDate'] = df['PaymentDate'].str.replace(r'(\d{2})\.(\d{2})\.(\d{4})', r'\3\2\1', regex=True)

    # Drop columns no longer needed
    df = df.drop(columns=['DividendType','DividendAmount','TaxIndicator'])
    
    return df


def aggregated(df):   
    # Group by 'securityId' and aggregate
    aggregated_df = df.groupby('SecurityId').agg(
        Count=('Amount', 'size'),           # Count of rows per securityId
        AnnualDividend=('Amount', 'sum'),   # Sum of value per securityId
        Unit=('Unit', 'min'),               # Retain column Unit
        OldestExDiv=('ExDivDate', 'min')    # Oldest ex-div date per securityId
    ).reset_index()

    # Add a new column 'Freq' based on the 'Count' column
    count_to_freq = {1: 'A', 2: 'S', 4: 'Q', 12: 'M'}
    aggregated_df['Freq'] = aggregated_df['Count'].map(count_to_freq)

    # Reorder columns
    aggregated_df = aggregated_df[['SecurityId','Freq','AnnualDividend','Unit','OldestExDiv']]

    return aggregated_df


class WsDividendsFE:
    def __init__(self, workbook):
        self._workbook = workbook
        self._wsname   = "fe"

        # Read 'hl' sheet into a DataFrame
        self._raw_df = workbook.worksheet_to_df(self.wsname())

        # Convert dividend information to generic format
        self._norm_df = normalised(self._raw_df)

        # Aggregate normalised data to get annual dividend information
        self._agg_df = aggregated(self._norm_df)


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

    def __repr__(self):
        return self.rawdata()
    

if __name__ == '__main__':

    from wb import WbIncome
    
    # Open Google Sheets workbook
    ForeverIncome = WbIncome()

    # Get 'hl' worksheet
    fe = WsDividendsFE(ForeverIncome)

    # Show raw data
    print(fe.rawdata())

    # Show normalised data
    print(fe.normalised())

    # Show aggregated data
    print(fe.aggregated())
    
