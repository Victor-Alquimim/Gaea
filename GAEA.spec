# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/victo/Gaea/gaea_app.py'],
    pathex=['C:/Users/victo/Gaea/servidor'],
    binaries=[],
    datas=[('C:/Users/victo/Gaea/index.html', '.'), ('C:/Users/victo/Gaea/css', 'css'), ('C:/Users/victo/Gaea/js', 'js'), ('C:/Users/victo/Gaea/data', 'data'), ('C:/Users/victo/Gaea/gaea.ico', '.'), ('C:/Users/victo/Gaea/servidor', 'servidor')],
    hiddenimports=['gaea_api', 'config', 'armazenamento', 'seguranca', 'icone'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GAEA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:/Users/victo/Gaea/gaea.ico'],
)
