#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import encodings.idna
from traceback import format_exc
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from logger import logger

I18N_PATH = 'i18n'
I18N_FILEEXT = '.qm'

def load_translations(translatator):
    for filename in os.listdir(I18N_PATH):
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext == I18N_FILEEXT:
            translatator.load(os.path.join(I18N_PATH, filename))


def main():
    logger.debug('application started')
    try:
        app = QApplication(sys.argv)
        syslocale = QtCore.QLocale.system().name()
        logger.debug('system locale - {}'.format(syslocale))
        translator = QtCore.QTranslator()
        load_translations(translator)
        app.installTranslator(translator)

        from snmp_scanner_mainwindow import SNMPScannerWindow
        main_window = SNMPScannerWindow()
        main_window.show()
        retcode = app.exec_()

    except Exception as error:
        logger.debug('catched excetion: {}'.format(str(type(error))))
        logger.debug('traceback: {}'.format(format_exc()))
        raise

    logger.debug('application finished')
    sys.exit(retcode)


if __name__ == '__main__':
    main()
