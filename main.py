import logging
import os

from SecurityClasses import SecurityUniverse
from PortfolioClasses import UserPortfolioGroup
from AccountClasses import AccountGroup
from PlatformClasses import AJB,II,AV
from PlatformClasses import GSM, FSB, CSB, NW, NSI

from wb import GspreadAuth, WbIncome, WbSecMaster
from wb import WsSecInfo, WsByPosition
from bysecurity import WsDividendsHL, WsDividendsFE, WsDividendsBySecurity

#---------------------------------------------------------
# Directories holding the configuration files
secinfo_dir = os.getenv('HOME') + '/SecurityInfo'
accinfo_dir = './tmp'

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
# -------------------- PROCESS START ------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Update dividend information
# Needs a steer on which security dividend information may be stale
# Also reproduce json security file(s) from Security Master worksheet

######## TO BE DEVELOPED

#------------------------------------------------------------------------------
# By Security - Create/Update sheet with dividends for all securities

if False:
    bySecurity = WsDividendsBySecurity(ForeverIncome,SecurityMaster)
    print(bySecurity.aggregated())
    bySecurity.refresh()

#------------------------------------------------------------------------------
# Updates for 'P'

userCode='P'

if False:
    p = AJB()
    p.update_positions('P', 'Pans')
    
if False:
    p = AJB()
    p.update_positions('P', 'ISA')

if False:
    cashAmount = 20000.00
    p.update_positions(userCode, 'Pens', cashAmount)

if False:
    p = AV()
    # 1) Scrape Aviva positions into worksheet ... and
    # 2) Run create_aviva_download_file ... before ...
    p.update_positions('P', 'Pans')


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

if True:
    # print(ForeverIncome.get_fillcolour(range_name='By Security!D2'))
    # print(ForeverIncome.get_fillcolour(range_name='By Security!F2'))
    bypos = WsByPosition(ForeverIncome)
    bypos.refresh(ag.positions())

#------------------------------------------------------------------------------
# Generate details of expected income for current month + 2 following months

######## TO BE DEVELOPED

#------------------------------------------------------------------------------
# -------------------- PROCESS END --------------------------------------------
#------------------------------------------------------------------------------

# SecurityInfo - Create/Update Security Information sheet based on json files
# This is only needed if the worksheet needs to be updated

if False:
    sec_info = WsSecInfo(SecurityMaster, secu)
    sec_info.refresh()

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
   


