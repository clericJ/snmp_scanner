# -*- mode: python -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys, os

sysnmpmibs_path=os.path.join(os.path.split(sys.executable)[0], 'Lib\\site-packages\\pysnmp\\smi\\mibs\\')
block_cipher = None
x = Tree(sysnmpmibs_path, prefix='pysnmp/smi/mibs', excludes='.py')
a = Analysis(['snmp_scanner_app.py'],
             pathex=[os.path.abspath(os.path.curdir)],
             binaries=[],
             datas=collect_data_files('pysnmp'),
             hiddenimports=['pysnmp.smi.exval','pysnmp.cache']+collect_submodules('pysmi')+collect_submodules('ply') + collect_submodules('pyasn1') + collect_submodules('pysnmp'),
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='SNMPScanner',
          debug=False,
          strip=False,
          icon='icons\\appicon.ico',
          upx=False,
          console=False,
          version='version.py')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               x,
               strip=False,
               upx=False,
               name='SNMP Scanner')

# vim: ft=python
