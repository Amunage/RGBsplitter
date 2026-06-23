from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.version import Version

from ..version import __version__

GITHUB_LATEST_RELEASE_URL = "https://api.github.com/repos/Amunage/RGBsplitter/releases/latest"
USER_AGENT = f"RGBsplitter-updater/{__version__}"
VERSION_TAG_PATTERN = re.compile(r"^[vV]?\d+\.\d+\.\d+$")


@dataclass(frozen=True)
class ReleaseInfo:
    version: Version
    tag_name: str
    asset_name: str
    download_url: str
    size: int


@dataclass(frozen=True)
class UpdateCheckResult:
    current_version: Version
    latest_release: ReleaseInfo | None


class UpdateError(RuntimeError):
    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\n\n{self.details}"
        return self.message


def should_check_for_updates() -> bool:
    return sys.platform == "win32" and bool(getattr(sys, "frozen", False))


def current_executable_path() -> Path | None:
    if not should_check_for_updates():
        return None
    return Path(sys.executable).resolve()


def parse_release_version(tag_name: str) -> Version:
    clean_tag = tag_name.strip()
    if not VERSION_TAG_PATTERN.match(clean_tag):
        raise UpdateError(
            "Unsupported release tag.",
            f"Expected a tag like v1.0.1, but got: {tag_name}",
        )

    if clean_tag[0] in {"v", "V"}:
        clean_tag = clean_tag[1:]
    return Version(clean_tag)


def release_info_from_payload(payload: Mapping[str, Any]) -> ReleaseInfo:
    tag_name = str(payload.get("tag_name", "")).strip()
    version = parse_release_version(tag_name)
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise UpdateError("Invalid GitHub release payload.", "The release payload does not contain an assets list.")

    exe_assets = [
        asset
        for asset in assets
        if isinstance(asset, Mapping)
        and str(asset.get("name", "")).lower().endswith(".exe")
        and str(asset.get("browser_download_url", "")).strip()
    ]
    if len(exe_assets) != 1:
        raise UpdateError(
            "Invalid GitHub release assets.",
            f"Expected exactly one .exe asset, but found {len(exe_assets)}.",
        )

    asset = exe_assets[0]
    asset_name = str(asset.get("name", "")).strip()
    download_url = str(asset.get("browser_download_url", "")).strip()
    try:
        size = int(asset.get("size", 0))
    except (TypeError, ValueError) as error:
        raise UpdateError("Invalid GitHub release asset size.", repr(error)) from error
    if size <= 0:
        raise UpdateError("Invalid GitHub release asset size.", f"Asset {asset_name} reported size {size}.")

    return ReleaseInfo(
        version=version,
        tag_name=tag_name,
        asset_name=asset_name,
        download_url=download_url,
        size=size,
    )


def check_release_payload(payload: Mapping[str, Any], current_version: str = __version__) -> UpdateCheckResult:
    parsed_current_version = parse_release_version(current_version)
    latest_release = release_info_from_payload(payload)
    if latest_release.version <= parsed_current_version:
        latest_release = None
    return UpdateCheckResult(current_version=parsed_current_version, latest_release=latest_release)


def check_for_update(
    current_version: str = __version__,
    release_url: str = GITHUB_LATEST_RELEASE_URL,
    timeout: float = 8,
) -> UpdateCheckResult:
    try:
        payload = _read_json_url(release_url, timeout=timeout)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise UpdateError("Failed to check for updates.", repr(error)) from error

    return check_release_payload(payload, current_version=current_version)


def download_update(
    release_info: ReleaseInfo,
    destination: Path,
    progress_callback: Callable[[int, int], None] | None = None,
    timeout: float = 30,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial_destination = destination.with_name(f"{destination.name}.download")
    bytes_received = 0

    request = urllib.request.Request(
        release_info.download_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            with partial_destination.open("wb") as output_file:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    output_file.write(chunk)
                    bytes_received += len(chunk)
                    if progress_callback is not None:
                        progress_callback(bytes_received, release_info.size)
    except (OSError, urllib.error.URLError) as error:
        _unlink_if_exists(partial_destination)
        raise UpdateError("Failed to download update.", repr(error)) from error

    partial_destination.replace(destination)
    validate_downloaded_exe(destination, release_info.size)
    return destination


def validate_downloaded_exe(exe_path: Path, expected_size: int) -> None:
    if not exe_path.is_file():
        raise UpdateError("Downloaded update file is missing.", str(exe_path))

    actual_size = exe_path.stat().st_size
    if actual_size != expected_size:
        raise UpdateError(
            "Downloaded update file size does not match.",
            f"Expected {expected_size} bytes, got {actual_size} bytes.",
        )

    with exe_path.open("rb") as file:
        signature = file.read(2)
    if signature != b"MZ":
        raise UpdateError("Downloaded update is not a Windows executable.", f"Invalid header: {signature!r}")


def default_update_download_path(release_info: ReleaseInfo) -> Path:
    local_app_data = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))
    return local_app_data / "RGBsplitter" / "updates" / f"RGB Splitter-{release_info.version}.exe"


def preflight_update_target(target_exe: Path) -> None:
    if not target_exe.is_file():
        raise UpdateError("Current executable was not found.", str(target_exe))

    try:
        target_exe.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".rgbsplitter-update-", dir=target_exe.parent, delete=True):
            pass
    except OSError as error:
        raise UpdateError("Cannot write to the application folder.", repr(error)) from error


def create_update_script(new_exe: Path, target_exe: Path, process_id: int) -> Path:
    log_file = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "RGBsplitter" / "update.log"
    script_path = log_file.parent / "apply_update.ps1"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    backup_exe = target_exe.with_name(f"{target_exe.name}.bak")

    script = f"""$ErrorActionPreference = 'Stop'
$TargetPid = {process_id}
$NewExe = {_powershell_quote(str(new_exe))}
$TargetExe = {_powershell_quote(str(target_exe))}
$BackupExe = {_powershell_quote(str(backup_exe))}
$LogFile = {_powershell_quote(str(log_file))}

function Write-UpdateLog($Message) {{
    $dir = Split-Path -Parent $LogFile
    if (-not (Test-Path -LiteralPath $dir)) {{
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }}
    Add-Content -LiteralPath $LogFile -Value ("[{{0}}] {{1}}" -f (Get-Date -Format o), $Message)
}}

try {{
    Write-UpdateLog ("Applying update. Target=" + $TargetExe)
    Wait-Process -Id $TargetPid -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 300

    if (Test-Path -LiteralPath $BackupExe) {{
        Remove-Item -LiteralPath $BackupExe -Force
    }}
    if (Test-Path -LiteralPath $TargetExe) {{
        Move-Item -LiteralPath $TargetExe -Destination $BackupExe -Force
    }}
    Move-Item -LiteralPath $NewExe -Destination $TargetExe -Force
    Start-Process -FilePath $TargetExe -WorkingDirectory (Split-Path -Parent $TargetExe)
    Write-UpdateLog "Update applied successfully."

    if (Test-Path -LiteralPath $BackupExe) {{
        Remove-Item -LiteralPath $BackupExe -Force -ErrorAction SilentlyContinue
    }}
    Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
}} catch {{
    Write-UpdateLog ("Update failed: " + $_.Exception.ToString())
    try {{
        if ((-not (Test-Path -LiteralPath $TargetExe)) -and (Test-Path -LiteralPath $BackupExe)) {{
            Move-Item -LiteralPath $BackupExe -Destination $TargetExe -Force
        }}
    }} catch {{
        Write-UpdateLog ("Restore failed: " + $_.Exception.ToString())
    }}
    try {{
        if (Test-Path -LiteralPath $TargetExe) {{
            Start-Process -FilePath $TargetExe -WorkingDirectory (Split-Path -Parent $TargetExe)
        }}
    }} catch {{
        Write-UpdateLog ("Restart failed: " + $_.Exception.ToString())
    }}
}}
"""
    script_path.write_text(script, encoding="utf-8-sig")
    return script_path


def launch_update_script(script_path: Path) -> None:
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ],
        close_fds=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _read_json_url(url: str, timeout: float) -> Mapping[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _unlink_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
