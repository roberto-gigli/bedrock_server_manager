# @date 29/10/2025
# @project bedrock_server_manager
# @author roberto.gigli

import configparser
import itertools
import json
import logging
import os
import platform
import shutil
import sys
import tempfile
import threading
import time
import zipfile
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import requests


class System(Enum):
    WINDOWS = "Windows"
    LINUX = "Linux"
    MACOS = "MacOS"
    UNKNOWN = "Unknown"

    @staticmethod
    def get_system():
        os_name = platform.system().lower()
        if "windows" in os_name:
            return System.WINDOWS
        elif "linux" in os_name:
            return System.LINUX
        elif "darwin" in os_name:
            return System.MACOS
        else:
            return System.UNKNOWN


class BedrockServerUpdater:
    """Class to manage Minecraft Bedrock server updates"""

    def __init__(self, current_dir: str = "."):
        # Directory where bedrock_server_manager.py is located
        self.script_dir = Path(__file__).parent.resolve()
        # Directory where server files are located (target for install/update)
        self.current_dir = Path(current_dir).resolve()
        self.system = System.get_system()

        # Load configuration
        self.config = self._load_config()

        # Setup logging
        self._setup_logging()

        # Primary and fallback URLs for API
        self.api_urls = [
            "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links",
            "https://www.minecraft.net/api/v1.0/download/links",
        ]

        # Files and folders to exclude during update (loaded from configuration)
        self.exclude_files = set()
        self.exclude_dirs = set()

        # Load files and folders to exclude from configuration
        self._load_exclude_lists()

        # Download settings
        self.download_timeout = self._get_optional_timeout(
            "download", "download_timeout", 60
        )
        self.api_timeout = self._get_optional_timeout("download", "api_timeout", 30)
        self.max_retries = max(
            1, self.config.getint("download", "max_retries", fallback=3)
        )

    def _get_optional_timeout(
        self, section: str, option: str, fallback: int
    ) -> Optional[int]:
        value = self.config.get(section, option, fallback=str(fallback)).strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return fallback

    def _load_config(self) -> configparser.ConfigParser:
        """Load the configuration file"""
        config = configparser.ConfigParser()

        # Try to load update_config.ini first (server-specific config in server dir)
        update_config_file = self.current_dir / "update_config.ini"
        # Then try config.ini from script directory
        config_file = self.script_dir / "config.ini"

        if update_config_file.exists():
            config.read(update_config_file)
            print(f"Loaded configuration from: {update_config_file}")
        elif config_file.exists():
            config.read(config_file)

        return config

    def _setup_logging(self):
        """Configure the logging system"""
        log_level = self.config.get("logging", "log_level", fallback="INFO")
        save_logs = self.config.getboolean("logging", "save_logs", fallback=True)
        log_file = self.config.get("logging", "log_file", fallback="updater.log")

        # Configure logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                (
                    logging.FileHandler(self.script_dir / log_file)
                    if save_logs
                    else logging.NullHandler()
                ),
            ],
        )

        self.logger = logging.getLogger(__name__)

    def _load_exclude_lists(self):
        """Load files and folders to exclude from configuration"""
        # Load files to exclude
        exclude_files = self.config.get("files", "exclude_files", fallback="").strip()
        exclude_dirs = self.config.get("files", "exclude_dirs", fallback="").strip()

        # Add files to exclude
        if exclude_files:
            for file_name in exclude_files.split("\n"):
                file_name = file_name.strip()
                if file_name and not file_name.startswith("#"):
                    self.exclude_files.add(file_name)

        # Add folders to exclude
        if exclude_dirs:
            for dir_name in exclude_dirs.split("\n"):
                dir_name = dir_name.strip()
                if dir_name and not dir_name.startswith("#"):
                    self.exclude_dirs.add(dir_name)

    def get_download_links(self) -> Dict:
        """Get download links from Minecraft API"""
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            for api_url in self.api_urls:
                try:
                    print(f"Attempting connection to: {api_url} (try {attempt})")
                    response = requests.get(api_url, timeout=self.api_timeout)
                    response.raise_for_status()
                    print("Connection successful!")
                    return response.json()
                except requests.RequestException as e:
                    last_error = e
                    print(f"Error with {api_url}: {e}")
                    continue

        # Se nessun URL funziona, solleva un'eccezione
        raise Exception(f"Unable to connect to Minecraft API. Last error: {last_error}")

    def get_server_url(self, preview: bool = False) -> str:
        """Get the appropriate server URL for the current system"""
        links_data = self.get_download_links()
        links = links_data.get("result", {}).get("links", [])

        # Determine download type based on system and if preview
        if self.system == System.WINDOWS:
            download_type = (
                "serverBedrockPreviewWindows" if preview else "serverBedrockWindows"
            )
        elif self.system == System.LINUX:
            download_type = (
                "serverBedrockPreviewLinux" if preview else "serverBedrockLinux"
            )
        else:
            raise Exception(f"System not supported: {self.system}")

        # Find correct link
        for link in links:
            if link.get("downloadType") == download_type:
                return link.get("downloadUrl")

        raise Exception(f"Download link not found for type: {download_type}")

    def extract_version_from_url(self, url: str) -> str:
        """Extract version from download URL"""
        try:
            # Example: bedrock-server-1.21.120.4.zip
            filename = url.split("/")[-1]
            # Remove bedrock-server- and .zip
            version = filename.replace("bedrock-server-", "").replace(".zip", "")
            return version
        except:
            return "unknown"

    def download_server(self, url: str, temp_dir: Path) -> Path:
        """Download server file to temporary directory"""
        print(f"Downloading server from: {url}")

        zip_path = temp_dir / "bedrock-server.zip"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }

        download_error: requests.RequestException | Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            download_error = None
            download_complete = threading.Event()
            downloaded_bytes = [0]
            total_bytes = [0]

            if zip_path.exists():
                zip_path.unlink()

            def perform_download():
                nonlocal download_error
                try:
                    timeout = None
                    if self.download_timeout is not None:
                        timeout = (self.download_timeout, self.download_timeout)

                    with requests.get(
                        url,
                        headers=headers,
                        stream=True,
                        timeout=timeout,
                    ) as r:
                        r.raise_for_status()
                        total_bytes[0] = int(r.headers.get("content-length", 0))

                        with open(zip_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_bytes[0] += len(chunk)
                except requests.RequestException as e:
                    download_error = e
                except Exception as e:
                    download_error = e
                finally:
                    download_complete.set()

            # Start download in separate thread
            download_thread = threading.Thread(target=perform_download, daemon=True)
            download_thread.start()

            # Show spinner and progress while downloading
            spinner = itertools.cycle(["|", "/", "-", "\\"])
            while not download_complete.is_set():
                spin_char = next(spinner)

                if total_bytes[0] > 0:
                    percent = (downloaded_bytes[0] / total_bytes[0]) * 100
                    bar_length = 30
                    filled = int(bar_length * downloaded_bytes[0] // total_bytes[0])
                    bar = "█" * filled + "░" * (bar_length - filled)
                    mb_downloaded = downloaded_bytes[0] / (1024 * 1024)
                    mb_total = total_bytes[0] / (1024 * 1024)

                    sys.stdout.write(
                        f"\r{spin_char} |{bar}| {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)"
                    )
                else:
                    mb_downloaded = downloaded_bytes[0] / (1024 * 1024)
                    sys.stdout.write(
                        f"\r{spin_char} Downloading... ({mb_downloaded:.1f} MB)"
                    )

                sys.stdout.flush()
                time.sleep(0.1)

            if not download_error:
                print("\n")
                print(f"Download completed: {zip_path}")
                return zip_path

            print(f"\nDownload failed (try {attempt}): {download_error}")

        raise Exception(f"Error during download: {download_error}")

    def extract_server(self, zip_path: Path, extract_dir: Path) -> None:
        """Extract server zip file"""
        print(f"Extracting server to: {extract_dir}")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            print("Extraction completed")
        except zipfile.BadZipFile as e:
            raise Exception(f"Corrupted zip file: {e}")

    def clean_extracted_files(self, extract_dir: Path) -> None:
        """Remove excluded files and folders"""
        print("Removing configuration files...")

        # Remove excluded folders
        for dir_name in self.exclude_dirs:
            dir_path = extract_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                print(f"Removed folder: {dir_name}")

        # Remove excluded files
        for file_name in self.exclude_files:
            file_path = extract_dir / file_name
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                print(f"Removed file: {file_name}")

    def copy_files_to_current_dir(self, source_dir: Path) -> None:
        """Copy remaining files to current folder"""
        print(f"Copying files to current folder: {self.current_dir}")

        for item in source_dir.iterdir():
            dest_path = self.current_dir / item.name

            if item.is_file():
                shutil.copy2(item, dest_path)
                print(f"Copied file: {item.name}")
            elif item.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(item, dest_path)
                print(f"Copied folder: {item.name}")

    def get_current_version(self) -> Optional[str]:
        """Try to get current server version"""
        # Check if version file exists
        version_files = ["bedrock_server_exe.version", "version.txt", "CHANGES.txt"]

        for version_file in version_files:
            version_path = self.current_dir / version_file
            if version_path.exists():
                try:
                    with open(version_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        # Search for version pattern
                        import re

                        version_match = re.search(r"\d+\.\d+\.\d+\.\d+", content)
                        if version_match:
                            return version_match.group()
                except:
                    continue

        return None

    def install_server(self, preview: bool = False, force: bool = False) -> bool:
        """Install Bedrock server from scratch"""
        try:
            print("=" * 50)
            print("BEDROCK SERVER INSTALLER")
            print("=" * 50)

            # Get download URL
            download_url = self.get_server_url(preview)
            new_version = self.extract_version_from_url(download_url)

            print(f"System: {self.system.value}")
            print(f"Mode: {'Preview' if preview else 'Release'}")
            print(f"Version to install: {new_version}")

            # Check if server is already present
            current_version = self.get_current_version()
            if current_version and not force:
                print(f"Warning: Version {current_version} already installed!")
                response = input(
                    f"Proceed with installation of version {new_version}? (y/N): "
                )
                if response.lower() not in ["y", "yes", "s", "si"]:
                    print("Installation cancelled.")
                    return False
            elif not force:
                response = input(
                    f"Proceed with installation of version {new_version}? (y/N): "
                )
                if response.lower() not in ["y", "yes", "s", "si"]:
                    print("Installation cancelled.")
                    return False

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                extract_path = temp_path / "extracted"
                extract_path.mkdir()

                # Download server
                zip_path = self.download_server(download_url, temp_path)

                # Extract
                self.extract_server(zip_path, extract_path)

                # Copy files (no need to exclude files during fresh install)
                self.copy_files_to_current_dir(extract_path)

                # Save version
                version_file = self.current_dir / "bedrock_server_exe.version"
                with open(version_file, "w") as f:
                    f.write(f"Bedrock Server {new_version}\n")

                print("=" * 50)
                print(f"INSTALLATION COMPLETED!")
                print(f"Version: {new_version}")
                print("=" * 50)

                return True

        except Exception as e:
            print(f"Error during installation: {e}")
            return False

    def update_server(self, preview: bool = False, force: bool = False) -> bool:
        """Update Bedrock server"""
        try:
            print("=" * 50)
            print("BEDROCK SERVER UPDATER")
            print("=" * 50)

            # Get download URL
            download_url = self.get_server_url(preview)
            new_version = self.extract_version_from_url(download_url)

            print(f"System: {self.system.value}")
            print(f"Mode: {'Preview' if preview else 'Release'}")
            print(f"New version available: {new_version}")

            # Check current version
            current_version = self.get_current_version()
            if current_version:
                print(f"Current version: {current_version}")
                if current_version == new_version and not force:
                    print("Server is already up to date!")
                    return False
            else:
                print("Current version: not detected")

            if not force:
                response = input(
                    f"Proceed with update to version {new_version}? (y/N): "
                )
                if response.lower() not in ["y", "yes", "s", "si"]:
                    print("Update cancelled.")
                    return False

            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                extract_path = temp_path / "extracted"
                extract_path.mkdir()

                # Download server
                zip_path = self.download_server(download_url, temp_path)

                # Extract
                self.extract_server(zip_path, extract_path)

                # Clean configuration files
                self.clean_extracted_files(extract_path)

                # Backup current folder (optional)
                backup_path = (
                    self.current_dir.parent / f"backup_{new_version}_{platform.node()}"
                )
                if not backup_path.exists():
                    print(f"Creating backup at: {backup_path}")
                    shutil.copytree(
                        self.current_dir,
                        backup_path,
                        ignore=shutil.ignore_patterns("*.log", "__pycache__"),
                    )

                # Copy new files
                self.copy_files_to_current_dir(extract_path)

                # Save version
                version_file = self.current_dir / "bedrock_server_exe.version"
                with open(version_file, "w") as f:
                    f.write(f"Bedrock Server {new_version}\n")

                print("=" * 50)
                print(f"UPDATE COMPLETED!")
                print(f"Version: {new_version}")
                print(f"Backup created at: {backup_path}")
                print("=" * 50)

                return True

        except Exception as e:
            print(f"Error during update: {e}")
            return False


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Install or update Minecraft Bedrock server"
    )
    parser.add_argument(
        "--preview", action="store_true", help="Download preview version"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation even if version is the same",
    )
    parser.add_argument(
        "--dir", default=".", help="Server directory (default: current folder)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check only if updates are available",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install server from scratch (do not update)",
    )

    args = parser.parse_args()

    updater = BedrockServerUpdater(args.dir)

    if args.check_only:
        try:
            download_url = updater.get_server_url(args.preview)
            new_version = updater.extract_version_from_url(download_url)
            current_version = updater.get_current_version()

            print(f"Current version: {current_version or 'not detected'}")
            print(f"Available version: {new_version}")

            if current_version and current_version == new_version:
                print("Server is up to date!")
            else:
                print("Update available!")

        except Exception as e:
            print(f"Error checking for updates: {e}")
    elif args.install:
        updater.install_server(args.preview, args.force)
    else:
        updater.update_server(args.preview, args.force)


if __name__ == "__main__":
    main()
