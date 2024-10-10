import pandas as pd

from wb import WbIncome
from hl import WsDividendsHL
from secinfo import WsSecInfo, WS_SECURITY_INFO, secinfo_dir


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


def add_rows(new_worksheet_name, workbook, rows):
    worksheet_list = map(lambda x: x.title, workbook.worksheets())
    if new_worksheet_name in worksheet_list:
        sheet = workbook.worksheet(new_worksheet_name)
    else:
        sheet = workbook.add_worksheet(new_worksheet_name, rows=10, cols=10)

    sheet.clear()

    sheet.update(f"A1:C{len(values)}", rows)

    sheet.update_cell(len(rows) + 1, 2, "=sum(B2:B4)")
    sheet.update_cell(len(rows) + 1, 3, "=sum(C2:C4)")

    sheet.format("A1:C1", {"textFormat": {"bold": True}})


def hl_add_by_security(workbook, df):
    
    # values without the column names
    values = df.values.tolist()
    # Insert list containing column headings
    hdr = list(df.columns.values)
    values.insert(0, hdr)

    worksheet_list = map(lambda x: x.title, workbook.worksheets())
    new_worksheet_name = "HL By Security"

    if new_worksheet_name in worksheet_list:
        sheet = workbook.worksheet(new_worksheet_name)
    else:
        sheet = workbook.add_worksheet(new_worksheet_name, rows=len(values), cols=len(hdr))

    sheet.clear()

    range = f"A1:{chr(ord('A')+len(hdr)-1)}{len(values)}"
    sheet.update(range, values)

    hrange = f"A1:{chr(ord('A')+len(hdr)-1)}1"
    sheet.format(hrange, {"textFormat": {"bold": True}})


# Open the main Google Sheets workbook
ForeverIncome = WbIncome()
workbook = ForeverIncome.workbook()

#------------------------------------------------------------------------------
# SecurityInfo - Create/Update Security Information sheet based on json files

if True:
    sec_info = WsSecInfo(ForeverIncome, secinfo_dir)
    ForeverIncome.df_to_worksheet(sec_info.df(), WS_SECURITY_INFO)

#------------------------------------------------------------------------------
# By SecurityHL - Create/Update sheet with aggregate dividends from 'hl'

if False:
    hl = WsDividendsHL(ForeverIncome)
    df = hl.aggregated()
    ForeverIncome.df_to_worksheet(df, "By SecurityHL")

#------------------------------------------------------------------------------

# --- Test interface
# read_sample(workbook)

# hl_add_by_security(workbook, df)

# --- Append all worksheets into a single dataframe
# df = read_sheets(workbook)
# print(df)

# --- Add values to a worksheet
# values = [
#     ["Name", "Price", "Quantity"],
#     ["Basketball", 29.99, 1],
#     ["Jeans", 39.99, 4],
#     ["Soap", 7.99, 3],
# ]
# add_rows("Values", workbook, values)


