import logging
import os
from datetime import datetime, timedelta
import calendar
import json, shutil

from SecurityClasses import SecurityUniverse
from PortfolioClasses import UserPortfolioGroup
from AccountClasses import AccountGroup
from PlatformClasses import AJB,II,AV
from PlatformClasses import GSM, FSB, CSB, NW, NSI

from wb import GspreadAuth, WbIncome, WbSecMaster
from wb import WsSecInfo, WsSecUrls, WsByPosition
from bysecurity import WsDividendsHL, WsDividendsFE
from bysecurity import WsDividendsBySecurity, WsEstimatedIncome

# Worksheets used as source information
from wb import WS_SECURITY_INFO, WS_SECURITY_URLS

#---------------------------------------------------------
# Directories holding the configuration files
secinfo_dir = os.getenv('HOME') + '/SecurityInfo'
accinfo_dir = os.getenv('HOME') + '/AccountInfo'

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# Load security universe
secu = SecurityUniverse(secinfo_dir)

# Load portfolios for all user accounts
pgrp = UserPortfolioGroup(secu, accinfo_dir)
logging.info("\npgrp=%s\n"%pgrp)

ag = AccountGroup(pgrp.accounts(),None,None)
logging.info("ag.accounts=%s\n"%ag.accounts())
logging.info("ag.positions=%s\n"%ag.positions())

# Authenticate and open our two workbooks
gsauth = GspreadAuth()
ForeverIncome = WbIncome(gsauth)
SecurityMaster = WbSecMaster(gsauth)

#------------------------------------------------------------------------------
# Update a json security file from SecurityMaster workbook
#------------------------------------------------------------------------------

def security_update_json(SecurityId):
    logging.debug(f"security_update_json({SecurityId})")
    # Base security definition
    df = SecurityMaster.worksheet_to_df(WS_SECURITY_INFO)
    records = df[(df['sname'] == SecurityId)].to_dict('records')
    if len(records) < 1:
        logging.debug(f"security_update_json: '{SecurityId}' not found")
        return
    sec_info = records[0]
    freq = sec_info['div-freq']
    sec_info.pop('div-freq')
    for tag in ['alias', 'SEDOL', 'fund-class']:
        if sec_info[tag] is None or sec_info[tag] == "":
            sec_info.pop(tag)

    # Previous dividends
    defn = sec_info
    defn['divis'] = {}
    defn['divis']['freq'] = freq

    bySecurity = WsDividendsBySecurity(ForeverIncome, SecurityMaster)
    prev = bySecurity.json_prev_divis(SecurityId)
    if len(prev) > 0:
        defn['divis']['prev'] = prev

    # Add url information if present
    df = SecurityMaster.worksheet_to_df(WS_SECURITY_URLS)
    sec_urls = df[(df['SecurityId'] == SecurityId)].to_dict('records')
    if len(sec_urls) > 0:
        defn['info'] = {}
        for u in sec_urls:
            defn['info'][u['Platform']] = u['Url']

    # Copy existing file in the Archive directory then recreate original
    sec_dir = f"{os.getenv('HOME')}/SecurityInfo"
    arc_dir = f"{sec_dir}/Archive"
    sec_file = f"{sec_dir}/{SecurityId}.json"
    arc_file = f"{arc_dir}/{SecurityId}.json"

    shutil.copy(sec_file, arc_file)
    with open(sec_file, 'w') as fp:
        json.dump(defn, fp, indent=2)


#------------------------------------------------------------------------------
# Function to use when looking at income in next 3 months
#------------------------------------------------------------------------------

def end_of_month_after_next(date):
    # Move to the first day of the next month
    next_month = date.replace(day=28) + timedelta(days=4)  # Ensures we are in the next month
    first_day_next_month = next_month.replace(day=1)
    
    # Now move to the month after that
    month_after_next = first_day_next_month + timedelta(days=32)
    month_after_next = month_after_next.replace(day=1)
    
    # Find the last day of that month
    last_day = calendar.monthrange(month_after_next.year, month_after_next.month)[1]
    return month_after_next.replace(day=last_day)


#------------------------------------------------------------------------------
# -------------------- PROCESS START ------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Update dividend information
# Needs a steer on which security dividend information may be stale
# Also reproduce json security file(s) from Security Master worksheet

######## TO BE DEVELOPED

if True:
    for SecurityId in ["LG-StratBond"]:
        security_update_json(SecurityId)

#------------------------------------------------------------------------------
# By Security - Create/Update sheet with dividends for all securities

if False:
    bySecurity = WsDividendsBySecurity(ForeverIncome,SecurityMaster)
    print(bySecurity.aggregated())
    bySecurity.refresh()

#------------------------------------------------------------------------------
# Estimated Income - Create/Update sheet with estimated dividends for all positions

if False:
    estimatedIncome = WsEstimatedIncome(ForeverIncome)
    estimatedIncome.projected_income(ag.positions(), secu)
    print(estimatedIncome.df())
    estimatedIncome.refresh()

#------------------------------------------------------------------------------
# Updates for 'P'

userCode='P'

if False:
    p = AJB()
    p.update_positions('P', 'Pens')
    
if False:
    p = AJB()
    p.update_positions('P', 'ISA')

if False:
    p = II()
    cashAmount = 10644.23
    p.update_positions(userCode, 'Pens', cashAmount)

if False:
    p = AV()
    # 1) Scrape Aviva positions into worksheet ... and
    # 2) Run create_aviva_download_file ... before ...
    p.update_positions('P', 'Pens')


#------------------------------------------------------------------------------
# Updates for 'C'
#------------------------------------------------------------------------------

userCode='C'

if False:
    p = II()
    cashAmount = 0.53
    p.update_positions(userCode, 'ISA', cashAmount)
if False:
    p = II()
    cashAmount = 0.53
    p.update_positions(userCode, 'Pens', cashAmount)
if False:
    p = II()
    cashAmount = 0.53
    p.update_positions(userCode, 'Trd', cashAmount)

if False:
    # Changes to cash accounts
    p = GSM()
    p = FSB()
    p = CSB()
    p = NW()
    p = NSI()
    cashAmount = 20000.00
    p.update_positions(userCode, 'Sav', cashAmount)

#------------------------------------------------------------------------------
# Create sheet 'By Positions' with income attributed to each position
# This is run as a final step to update worksheet based on new positions
# Is it worth archiving positions sheet on a monthly basis?

if False:
    # print(ForeverIncome.get_fillcolour(range_name='By Security!D2'))
    # print(ForeverIncome.get_fillcolour(range_name='By Security!F2'))
    bypos = WsByPosition(ForeverIncome)
    bypos.refresh(ag.positions())

#------------------------------------------------------------------------------
# Generate details of expected income for current month + 2 following months

if False:

    # Current date
    # today = datetime.today()
    # Calculate the end of the month after next
    # result_date = end_of_month_after_next(today)

    end_projection = datetime.today() + timedelta(weeks=13)
    
    for pos in ag.positions():
        if pos.sname() == "Art-MthlyDist":
            sname = f"{pos.sname()}"
            print(f"Income to {end_projection.strftime('%Y%m%d')}")
            key = f"{pos.username()[0]}_{pos.platform()}_{pos.account_type()}"
            print(f"{key} {sname} q={pos.quantity()} p={pos.price()} v={pos.value()}")

            # Dividend payments in next 3m from position
            for dp in pos.projected_dividends():
                print(f"pos-projected{dp}")
            print()

            # Details of dividend payable for security
            sec = secu.find_security(pos.sname())
            # print(f"recent={sec.recent_divis()}")
            for dp in sec.projected_dividends():
                print(f"sec-projected{dp}")

            print("---sec.recent_divis()")
            print(sec.recent_divis())


#------------------------------------------------------------------------------
# -------------------- PROCESS END --------------------------------------------
#------------------------------------------------------------------------------

# SecurityInfo - Create/Update Security Information sheet based on json files
# This is only needed if the worksheet needs to be updated

if False:
    sec_info = WsSecInfo(SecurityMaster, secu)
    sec_info.refresh()

# SecurityUrls - Create/Update Detailed Information sheet based on json files
# This is only needed as a one-off to gather all URLs into a worksheet

if False:
    sec_urls = WsSecUrls(SecurityMaster, secu)
    sec_urls.refresh()

#------------------------------------------------------------------------------
# By SecurityHL - Create/Update sheet with aggregate dividends from 'hl'
# This is only needed to unit test processing of 'hl' dividends

if False:
    hl = WsDividendsHL(ForeverIncome,SecurityMaster)
    print(hl.rawdata())
    print(hl.normalised())
    print(hl.aggregated())
    hl.refresh()

#------------------------------------------------------------------------------
# By SecurityFE - Create/Update sheet with aggregate dividends from 'fe'
# This is only needed to unit test processing of 'fe' dividends

if False:
    fe = WsDividendsFE(ForeverIncome,SecurityMaster)
    print(fe.rawdata())
    print(fe.normalised())
    print(fe.aggregated())
    fe.refresh()
   


