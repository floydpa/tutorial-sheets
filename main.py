import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

scopes   = ["https://www.googleapis.com/auth/spreadsheets"]
creds    = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client   = gspread.authorize(creds)
sheet_id = "1-W8w2t3HXCG9zNy6RQ4w12zkCrX_jntvQ24xEinhxG4"
workbook = client.open_by_key(sheet_id)


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


def read_google_sheet_to_df(workbook, worksheet_name):
    """
    Reads a worksheet from a Google Spreadsheet into a Pandas DataFrame.
    
    Args:
        workbook: Handle for workbook opened by authorised client.
        worksheet_name (str): Name of the worksheet to read.
    
    Returns:
        pd.DataFrame: The worksheet data as a Pandas DataFrame.
    """

    # Get the worksheet by name
    worksheet = workbook.worksheet(worksheet_name)

    # Get all data from the worksheet
    data = worksheet.get_all_records()

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)

    return df

def add_values(workbook):
    values = [
        ["Name", "Price", "Quantity"],
        ["Basketball", 29.99, 1],
        ["Jeans", 39.99, 4],
        ["Soap", 7.99, 3],
    ]

    worksheet_list = map(lambda x: x.title, workbook.worksheets())
    new_worksheet_name = "Values"

    if new_worksheet_name in worksheet_list:
        sheet = workbook.worksheet(new_worksheet_name)
    else:
        sheet = workbook.add_worksheet(new_worksheet_name, rows=10, cols=10)

    sheet.clear()

    sheet.update(f"A1:C{len(values)}", values)

    sheet.update_cell(len(values) + 1, 2, "=sum(B2:B4)")
    sheet.update_cell(len(values) + 1, 3, "=sum(C2:C4)")

    sheet.format("A1:C1", {"textFormat": {"bold": True}})


# --- Test interface
# read_sample(workbook)

# --- Get contents of a worksheet into a dataframe
# worksheet_name = "By Security"
# df = read_google_sheet_to_df(workbook, worksheet_name)
# print(df)

# --- Append all worksheets into a single dataframe
# df = read_sheets(workbook)
# print(df)

# --- Add values to a worksheet
# add_values(workbook)
