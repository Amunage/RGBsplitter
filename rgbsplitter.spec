# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


project_root = Path(SPECPATH).resolve()
src_root = project_root / "src"
resource_root = src_root / "rgbsplitter" / "resources"
version_namespace = {}
exec((src_root / "rgbsplitter" / "version.py").read_text(encoding="utf-8"), version_namespace)
app_version = version_namespace["__version__"]
exe_name = f"RGBsplitter-v{app_version}"


a = Analysis(
    [str(src_root / "rgbsplitter" / "__main__.py")],
    pathex=[str(src_root)],
    binaries=[],
    datas=[
        (str(resource_root / "small_icon.png"), "rgbsplitter/resources"),
        (str(resource_root / "my_icon.ico"), "rgbsplitter/resources"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
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
    icon=str(resource_root / "my_icon.ico"),
)
