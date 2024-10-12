#------------------------------------------------------------------------------
# Formatting for worksheets within workbooks
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# RGB values for cell fill colours

RGB_BLUE   = {"red": 0.81, "green": 0.89, "blue": 0.95}
RGB_YELLOW = {"red": 0.95, "green": 1.00, "blue": 0.80}
RGB_GREY   = {"red": 0.80, "green": 0.80, "blue": 0.80}

#------------------------------------------------------------------------------
# Formatting requests

def fmt_req_font(worksheet):
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
    
def fmt_req_autofilter(worksheet):
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

def fmt_req_autoresize(worksheet):
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
    
def fmt_hdr_bgcolor(worksheet, color):
    return {
        'repeatCell': {
            'range': {
                'sheetId': worksheet.id,
                'startRowIndex': 0,  # First row
                'endRowIndex': 1,    # Only apply to the first row
            },
            'cell': {
                'userEnteredFormat': {
                    'backgroundColor': color
                }
            },
            'fields': 'userEnteredFormat.backgroundColor'
        }
    }

def fmt_columns_bgcolor(worksheet, color, cfirst, clast, rfirst=1, rlast=-1):
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
                    'backgroundColor': color
                }
            },
            'fields': 'userEnteredFormat.backgroundColor'
        }
    }

# Format column(s) as decimal
def fmt_columns_decimal(worksheet, cfirst, clast, rfirst=1):
    return {
        'repeatCell': {
            'range': {
                'sheetId': worksheet.id,
                'startColumnIndex': cfirst,  # 0-indexed, e.g. K=10
                'endColumnIndex': clast,     # End is exclusive
                'startRowIndex': rfirst      # 0-index, 1=start after header row
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'NUMBER',        # Decimal format
                        'pattern': '#,##0.0###'  # Up to four decimal places
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }

# Format column(s) as percentage with 2 decimal places
def fmt_columns_percentage(worksheet, cfirst, clast, rfirst=1):
    return {
        'repeatCell': {
            'range': {
                'sheetId': worksheet.id,
                'startColumnIndex': cfirst,  # 0-indexed, e.g. N=13
                'endColumnIndex': clast,     # End is exclusive, so 14
                'startRowIndex': rfirst,     # 0-indexed, 1=Start after the header row
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'PERCENT',  # Percentage format
                        'pattern': '0.00%'  # Two decimal places
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }

# Format column(s) as local currency (£)
def fmt_columns_currency(worksheet, cfirst, clast, rfirst=1):
    return {
        'repeatCell': {
            'range': {
                'sheetId': worksheet.id,
                'startColumnIndex': cfirst,  # 0-indexed, e.g. N=13
                'endColumnIndex': clast,     # End is exclusive
                'startRowIndex': rfirst,     # Start after the header row
            },
            'cell': {
                'userEnteredFormat': {
                    'numberFormat': {
                        'type': 'CURRENCY',     # Currency format
                        'pattern': '£#,##0.00'  # GBP symbol with two decimal places
                    }
                }
            },
            'fields': 'userEnteredFormat.numberFormat'
        }
    }

# Format column(s) horizontal justification
def fmt_columns_hjustify(worksheet, cfirst, clast, justification, rfirst=1):
    return {
        'repeatCell': {
            'range': {
                'sheetId': worksheet.id,
                'startColumnIndex': cfirst,  # 0-indexed
                'endColumnIndex': clast,     # End is exclusive
                'startRowIndex': rfirst,     # Start after header row (0-indexed)
            },
            'cell': {
                'userEnteredFormat': {
                    'horizontalAlignment': justification
                }
            },
            'fields': 'userEnteredFormat.horizontalAlignment'
        }
    }
