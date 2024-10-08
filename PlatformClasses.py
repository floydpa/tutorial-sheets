# Platform accounts making up a portfolio

import pandas as pd
import re
import sys
import os

import logging
import datetime

from pathlib import Path

from SecurityClasses import SecurityUniverse
from PositionClasses import Position

def platformCode_to_class(code):
    return getattr(sys.modules[__name__], code)


class Platform:
    def __init__(self):
        self._fullname = None
        self._vdate = None

    def name(self, fullname=False):
        return self._fullname if fullname else self.__class__.__name__

    def vdate(self):
        return self._vdate

    def set_vdate(self, summary_file):
        # filename = os.readlink(self.userdata_dirname() + '/' + summary_file)
        filename = os.readlink(summary_file)
        self._vdate = re.sub('\.csv$','',re.sub('^.*_','',filename))

    def load_positions(self, secu, userCode, accountType, summary_file=None):
        positions = []
        if summary_file is None:
            summary_file = self.latest_file(userCode,accountType)
        self.set_vdate(summary_file)
        df = pd.read_csv(summary_file)
        # print(summary_file)
        # print(df)
        labels = ['Investment', 'Quantity', 'Price', 'Value (£)']
        for n in range(0, len(df)):
            inv = df['Investment'][n]
            sym = inv
            qty = float(re.sub(',', '', str(df['Quantity'][n])))
            price = float(df['Price'][n])
            value = float(re.sub(',', '', str(df['Value (£)'][n])))

            security = secu.find_security(sym)
            pos = Position(security, qty, price, value, self.vdate())

            # print("New Position=%s" % (pos))
            positions.append(pos)

        return positions

    def download_dirname(self):
        return "/mnt/chromeos/MyFiles/Downloads"

    def userdata_dirname(self):
        return "%s/UserData" % (os.getenv('HOME'))
    
    def download_filename(self, username, accountType):
        return None

    def current_filename(self, userCode, accountType):
        destlink   = self.latest_file(userCode,accountType)
        return os.readlink(destlink)

    def temp_filename(self, userCode, accountType):
        logging.debug("temp_filename(%s,%s)"%(userCode,accountType))
        return "%s/%s_%s.tmp" % (self.download_dirname(), userCode, accountType)

    def download_formname(self):
        return None

    def dated_file(self, userCode, accountType, dt=None):
        datadir = self.userdata_dirname()
        if dt is None:
            dt = datetime.datetime.now().strftime("%Y%m%d")
        return "%s/%s_%s_%s_%s.csv" % (datadir, userCode, self.name(), accountType, dt)
    
    def latest_file(self, userCode, accountType):
        datadir = self.userdata_dirname()
        return "%s/%s_%s_%s_latest" % (datadir, userCode, self.name(), accountType)

    def update_savings(self, userCode, accountType, cashAmount):
        datadir    = self.userdata_dirname()
        destfile   = self.dated_file(userCode, accountType)
        destlink   = self.latest_file(userCode,accountType)
        sourcefile = "%s/%s" % (datadir, os.readlink(destlink))
        tempfile   = self.temp_filename(userCode, accountType)

        logging.debug("src=%s dest=%s link=%s temp=%s" % (sourcefile,destfile,destlink,tempfile))

        # Create new file in temporary location
        with open(sourcefile, 'r', encoding='utf-8-sig') as fpin:
            lines = fpin.readlines()
            fpin.close()

        security = re.sub(',.*$','',lines[1].rstrip())
        lines[1] = '%s,"%.2f","100","%.2f","%.2f"\n' % (security, cashAmount, cashAmount, cashAmount)

        fpout = open(tempfile, "w")
        fpout.writelines(lines)
        fpout.close()

        # Copy temp file into place
        fpout = open(destfile, "w")
        with open(tempfile, 'r', encoding='utf-8-sig') as fpin:
            for line in fpin:
                fpout.write(line)
        fpout.close()
        fpin.close()

        # Update latest link to point to newly created file
        # Remove the temporary file from the download area
        self.update_latest_link(tempfile, destfile, destlink)

    def update_latest_link(self, downloadFile, destFile, destLink, removeSource=True):
        """Update the 'latest' link to point to the new file and remove downloaded file"""
        os.unlink(destLink)
        os.symlink(destFile, destLink)
        logging.debug("symlink(%s,%s)" % (destFile, destLink))

        # Finally remove the source file which had been downloaded
        if removeSource:
            logging.debug("unlink(%s)" % (downloadFile))
            os.unlink(downloadFile)

    def __repr__(self):
        return "PLATFORM(%s,%s)" % (self.name(), self.name(True))


class AJB(Platform):
    def __init__(self):
        Platform.__init__(self)
        self._fullname = "AJ Bell Youinvest"

    def download_filename(self, userCode, accountType):
        logging.debug("download_filename(%s,%s)"%(userCode,accountType))
        if userCode == 'C' and accountType == 'ISA':
            filename = "portfolio-AB9F2PI-ISA.csv"
        elif userCode == 'P' and accountType == 'Pens':
            filename = "portfolio-A20782S-SIPP.csv"
        else:
            filename = None
        return "%s/%s" % (self.download_dirname(), filename) if filename else None

    def download_formname(self):
        return "FileDownloadForm"

    def load_positions(self, secu, userCode, accountType, summary_file=None):
        positions = []
        if summary_file is None:
            summary_file = self.latest_file(userCode,accountType)
        self.set_vdate(summary_file)
        df = pd.read_csv(summary_file)
        labels = ['Investment', 'Quantity', 'Price', 'Value (£)']
        for n in range(0, len(df)):
            inv = df['Investment'][n]
            if 'LSE:' in inv:
                sym = re.sub('.*\(LSE:(.*)\).*', '\\1', inv) + ".L"
            elif 'FUND:' in inv:
                sym = re.sub('.*\(FUND:(.*)\).*', '\\1', inv)
            elif 'SEDOL:' in inv:
                sym = re.sub('.*\(SEDOL:(.*)\).*', '\\1', inv)
            else:
                sym = inv

            qty = float(re.sub(',', '', df['Quantity'][n]))
            price = float(df['Price'][n]) * 100.0
            value = float(re.sub(',', '', df['Value (£)'][n]))

            if sym in ('Cash GBP'):
                security = secu.find_security('Cash')
            else:
                security = secu.find_security(sym)

            pos = Position(security, qty, price, value, self.vdate())
            # print("New Position=%s" % (pos))
            positions.append(pos)

        return positions

    def update_positions(self, userCode, accountType):
        destfile = self.dated_file(userCode, accountType)
        destlink = self.latest_file(userCode,accountType)
        filename = self.download_filename(userCode,accountType)

        logging.debug("source=%s" % (filename))
        logging.debug("destfile=%s" % (destfile))
        logging.debug("destlink=%s" % (destlink))

        # Copy all lines across
        fpout = open(destfile, "w")
        with open(filename, 'r', encoding='utf-8-sig') as fpin:
            for line in fpin:
                fpout.write(line)
        fpout.close()
        fpin.close()

        # Update latest link to point to newly created file
        # Remove the source file from the download area
        self.update_latest_link(filename, destfile, destlink)

if __name__ == '__main__':
    
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    
    # Load details of all securities held in positions
    secinfo_dir = os.getenv('HOME') + '/SecurityInfo'
    secu  = SecurityUniverse(secinfo_dir)

    # uport = UserPortfolios(secu)
 
    # a = platformCode_to_class('AJB')()
    # print(a.name())

    p = AJB()
    print(p.name(True))
    print(p.latest_file('P','ISA'))

    # Set 'latest' symlink to point to dated file associated with YYYYMMDD (today)
    # There's no need to specify a cash amount for AJB as it's in the downloaded file
    # p.update_positions('P','ISA')


