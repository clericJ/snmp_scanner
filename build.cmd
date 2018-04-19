@echo off
setlocal enableextensions

call compile_resources.cmd

pyinstaller --noconfirm --clean snmp_scanner_app.spec
mkdir  "dist\SNMP Scanner\icons"
mkdir "dist\SNMP Scanner\i18n"
copy icons "dist\SNMP Scanner\icons"
copy i18n "dist\SNMP Scanner\i18n"
mkdir "dist\SNMP Scanner\PyQt5\Qt\plugins\styles"
copy /y qwindowsvistastyle.dll "dist\SNMP Scanner\PyQt5\Qt\plugins\styles"
rmdir /s /q build
