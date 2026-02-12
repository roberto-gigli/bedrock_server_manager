# @date 29/10/2025
# @project bedrock-server-updater
# @author roberto.gigli

import configparser
import json
import logging
import os
import platform
import shutil
import tempfile
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
    """Classe per gestire gli aggiornamenti del server Minecraft Bedrock"""

    def __init__(self, current_dir: str = "."):
        self.current_dir = Path(current_dir).resolve()
        self.system = System.get_system()

        # Carica configurazione
        self.config = self._load_config()

        # Configura logging
        self._setup_logging()

        # URL primario e di fallback per l'API
        self.api_urls = [
            "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links",
            "https://www.minecraft.net/api/v1.0/download/links",
        ]

        # File e cartelle da escludere durante l'aggiornamento (caricati dalla configurazione)
        self.exclude_files = set()
        self.exclude_dirs = set()

        # Carica file e cartelle da escludere dalla configurazione
        self._load_exclude_lists()

    def _load_config(self) -> configparser.ConfigParser:
        """Carica il file di configurazione"""
        config = configparser.ConfigParser()
        config_file = self.current_dir / "config.ini"

        if config_file.exists():
            config.read(config_file)

        return config

    def _setup_logging(self):
        """Configura il sistema di logging"""
        log_level = self.config.get("logging", "log_level", fallback="INFO")
        save_logs = self.config.getboolean("logging", "save_logs", fallback=True)
        log_file = self.config.get("logging", "log_file", fallback="updater.log")

        # Configura il logger
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                (
                    logging.FileHandler(self.current_dir / log_file)
                    if save_logs
                    else logging.NullHandler()
                ),
            ],
        )

        self.logger = logging.getLogger(__name__)

    def _load_exclude_lists(self):
        """Carica file e cartelle da escludere dalla configurazione"""
        # Carica file da escludere
        exclude_files = self.config.get("files", "exclude_files", fallback="").strip()
        exclude_dirs = self.config.get("files", "exclude_dirs", fallback="").strip()

        # Aggiungi file da escludere
        if exclude_files:
            for file_name in exclude_files.split("\n"):
                file_name = file_name.strip()
                if file_name and not file_name.startswith("#"):
                    self.exclude_files.add(file_name)

        # Aggiungi cartelle da escludere
        if exclude_dirs:
            for dir_name in exclude_dirs.split("\n"):
                dir_name = dir_name.strip()
                if dir_name and not dir_name.startswith("#"):
                    self.exclude_dirs.add(dir_name)

    def get_download_links(self) -> Dict:
        """Ottiene i link di download dall'API di Minecraft"""
        last_error = None

        for api_url in self.api_urls:
            try:
                print(f"Tentativo di connessione a: {api_url}")
                response = requests.get(api_url, timeout=30)
                response.raise_for_status()
                print("Connessione riuscita!")
                return response.json()
            except requests.RequestException as e:
                last_error = e
                print(f"Errore con {api_url}: {e}")
                continue

        # Se nessun URL funziona, solleva un'eccezione
        raise Exception(
            f"Impossibile connettersi all'API di Minecraft. Ultimo errore: {last_error}"
        )

    def get_server_url(self, preview: bool = False) -> str:
        """Ottiene l'URL del server appropriato per il sistema corrente"""
        links_data = self.get_download_links()
        links = links_data.get("result", {}).get("links", [])

        # Determina il tipo di download in base al sistema e se è preview
        if self.system == System.WINDOWS:
            download_type = (
                "serverBedrockPreviewWindows" if preview else "serverBedrockWindows"
            )
        elif self.system == System.LINUX:
            download_type = (
                "serverBedrockPreviewLinux" if preview else "serverBedrockLinux"
            )
        else:
            raise Exception(f"Sistema operativo non supportato: {self.system}")

        # Trova il link corretto
        for link in links:
            if link.get("downloadType") == download_type:
                return link.get("downloadUrl")

        raise Exception(f"Link di download non trovato per il tipo: {download_type}")

    def extract_version_from_url(self, url: str) -> str:
        """Estrae la versione dall'URL di download"""
        try:
            # Esempio: bedrock-server-1.21.120.4.zip
            filename = url.split("/")[-1]
            # Rimuove bedrock-server- e .zip
            version = filename.replace("bedrock-server-", "").replace(".zip", "")
            return version
        except:
            return "unknown"

    def download_server(self, url: str, temp_dir: Path) -> Path:
        """Scarica il file del server nella directory temporanea"""
        print(f"Download del server da: {url}")

        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            zip_path = temp_dir / "bedrock-server.zip"

            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"Download completato: {zip_path}")
            return zip_path

        except requests.RequestException as e:
            raise Exception(f"Errore durante il download: {e}")

    def extract_server(self, zip_path: Path, extract_dir: Path) -> None:
        """Estrae il file zip del server"""
        print(f"Estrazione del server in: {extract_dir}")

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            print("Estrazione completata")
        except zipfile.BadZipFile as e:
            raise Exception(f"File zip corrotto: {e}")

    def clean_extracted_files(self, extract_dir: Path) -> None:
        """Rimuove i file e le cartelle da escludere"""
        print("Rimozione dei file di configurazione...")

        # Rimuovi le cartelle da escludere
        for dir_name in self.exclude_dirs:
            dir_path = extract_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                print(f"Rimossa cartella: {dir_name}")

        # Rimuovi i file da escludere
        for file_name in self.exclude_files:
            file_path = extract_dir / file_name
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                print(f"Rimosso file: {file_name}")

    def copy_files_to_current_dir(self, source_dir: Path) -> None:
        """Copia i file rimanenti nella cartella corrente"""
        print(f"Copia dei file nella cartella corrente: {self.current_dir}")

        for item in source_dir.iterdir():
            dest_path = self.current_dir / item.name

            if item.is_file():
                shutil.copy2(item, dest_path)
                print(f"Copiato file: {item.name}")
            elif item.is_dir():
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                shutil.copytree(item, dest_path)
                print(f"Copiata cartella: {item.name}")

    def get_current_version(self) -> Optional[str]:
        """Tenta di ottenere la versione corrente del server"""
        # Controlla se esiste un file che contiene la versione
        version_files = ["bedrock_server_exe.version", "version.txt", "CHANGES.txt"]

        for version_file in version_files:
            version_path = self.current_dir / version_file
            if version_path.exists():
                try:
                    with open(version_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        # Cerca pattern di versione
                        import re

                        version_match = re.search(r"\d+\.\d+\.\d+\.\d+", content)
                        if version_match:
                            return version_match.group()
                except:
                    continue

        return None

    def update_server(self, preview: bool = False, force: bool = False) -> bool:
        """Aggiorna il server Bedrock"""
        try:
            print("=" * 50)
            print("BEDROCK SERVER UPDATER")
            print("=" * 50)

            # Ottieni l'URL di download
            download_url = self.get_server_url(preview)
            new_version = self.extract_version_from_url(download_url)

            print(f"Sistema: {self.system.value}")
            print(f"Modalità: {'Preview' if preview else 'Release'}")
            print(f"Nuova versione disponibile: {new_version}")

            # Controlla la versione corrente
            current_version = self.get_current_version()
            if current_version:
                print(f"Versione corrente: {current_version}")
                if current_version == new_version and not force:
                    print("Il server è già aggiornato!")
                    return False
            else:
                print("Versione corrente: non rilevata")

            if not force:
                response = input(
                    f"Procedere con l'aggiornamento alla versione {new_version}? (y/N): "
                )
                if response.lower() not in ["y", "yes", "s", "si"]:
                    print("Aggiornamento annullato.")
                    return False

            # Crea directory temporanea
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                extract_path = temp_path / "extracted"
                extract_path.mkdir()

                # Download del server
                zip_path = self.download_server(download_url, temp_path)

                # Estrazione
                self.extract_server(zip_path, extract_path)

                # Pulizia dei file di configurazione
                self.clean_extracted_files(extract_path)

                # Backup della cartella corrente (opzionale)
                backup_path = (
                    self.current_dir.parent / f"backup_{new_version}_{platform.node()}"
                )
                if not backup_path.exists():
                    print(f"Creazione backup in: {backup_path}")
                    shutil.copytree(
                        self.current_dir,
                        backup_path,
                        ignore=shutil.ignore_patterns("*.log", "__pycache__"),
                    )

                # Copia dei nuovi file
                self.copy_files_to_current_dir(extract_path)

                # Salva la versione
                version_file = self.current_dir / "bedrock_server_exe.version"
                with open(version_file, "w") as f:
                    f.write(f"Bedrock Server {new_version}\n")

                print("=" * 50)
                print(f"AGGIORNAMENTO COMPLETATO!")
                print(f"Versione: {new_version}")
                print(f"Backup creato in: {backup_path}")
                print("=" * 50)

                return True

        except Exception as e:
            print(f"Errore durante l'aggiornamento: {e}")
            return False


def main():
    """Funzione principale"""
    import argparse

    parser = argparse.ArgumentParser(description="Aggiorna il server Minecraft Bedrock")
    parser.add_argument(
        "--preview", action="store_true", help="Scarica la versione preview"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forza l'aggiornamento anche se la versione è la stessa",
    )
    parser.add_argument(
        "--dir", default=".", help="Directory del server (default: cartella corrente)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Controlla solo se ci sono aggiornamenti disponibili",
    )

    args = parser.parse_args()

    updater = BedrockServerUpdater(args.dir)

    if args.check_only:
        try:
            download_url = updater.get_server_url(args.preview)
            new_version = updater.extract_version_from_url(download_url)
            current_version = updater.get_current_version()

            print(f"Versione corrente: {current_version or 'non rilevata'}")
            print(f"Versione disponibile: {new_version}")

            if current_version and current_version == new_version:
                print("Il server è aggiornato!")
            else:
                print("È disponibile un aggiornamento!")

        except Exception as e:
            print(f"Errore nel controllo degli aggiornamenti: {e}")
    else:
        updater.update_server(args.preview, args.force)


if __name__ == "__main__":
    main()
