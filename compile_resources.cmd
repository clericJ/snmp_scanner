@echo off
setlocal enableextensions

pyuic5.exe snmp_scanner_mainwindow.ui -o ui_snmp_scanner_mainwindow.py
pylupdate5 snmp_scanner_mainwindow.py ui_snmp_scanner_mainwindow.py scanresults_tablemodel.py snmpscannerthread.py -ts i18n/ru_RU.ts