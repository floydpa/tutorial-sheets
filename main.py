import logging
import os

from SecurityClasses import SecurityUniverse
from PortfolioClasses import UserPortfolioGroup
from AccountClasses import AccountGroup

from wb import WbIncome
from wb import WsSecInfo, WsDividendsHL, WsDividendsFE, WsByPosition

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

# Open the main Google Sheets workbook
ForeverIncome = WbIncome()
workbook = ForeverIncome.workbook()

#------------------------------------------------------------------------------
# SecurityInfo - Create/Update Security Information sheet based on json files

if True:
    sec_info = WsSecInfo(ForeverIncome, secu)
    sec_info.refresh()

#------------------------------------------------------------------------------
# By SecurityHL - Create/Update sheet with aggregate dividends from 'hl'

if True:
    hl = WsDividendsHL(ForeverIncome)
    print(hl.rawdata())
    print(hl.normalised())
    print(hl.aggregated())
    hl.refresh()

#------------------------------------------------------------------------------
# By SecurityFE - Create/Update sheet with aggregate dividends from 'fe'

if True:
    fe = WsDividendsFE(ForeverIncome)
    print(fe.rawdata())
    print(fe.normalised())
    print(fe.aggregated())
    fe.refresh()
    
#------------------------------------------------------------------------------
# Create sheet 'By Positions' with income attributed to each position

if True:
    # print(ForeverIncome.get_fillcolour(range_name='By Security!D2'))
    # print(ForeverIncome.get_fillcolour(range_name='By Security!F2'))

    bypos = WsByPosition(ForeverIncome)
    bypos.refresh(ag.positions())




