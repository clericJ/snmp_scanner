@echo off
setlocal enableextensions

pyuic5.exe snmp_scanner_mainwindow.ui -o ui_snmp_scanner_mainwindow.py
pylupdate5 snmp_scanner_mainwindow.py ui_snmp_scanner_mainwindow.py scanresults_tablemodel.py snmpscannerthread.py -ts i18n/ru_RU.ts
pyinstaller --noconfirm --clean snmp_scanner_app.spec
mkdir  "dist\SNMP Scanner\icons"
mkdir "dist\SNMP Scanner\i18n"
copy icons "dist\SNMP Scanner\icons"
copy i18n "dist\SNMP Scanner\i18n"
mkdir "dist\SNMP Scanner\PyQt5\Qt\plugins\styles"
copy /y qwindowsvistastyle.dll "dist\SNMP Scanner\PyQt5\Qt\plugins\styles"
rmdir /s /q build
