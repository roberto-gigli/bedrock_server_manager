# Bedrock Server Manager

Uno script Python per aggiornare automaticamente il server Minecraft Bedrock Edition.

## Caratteristiche

- ✅ Controllo automatico degli aggiornamenti dall'API ufficiale di Minecraft
- ✅ Supporto per Windows e Linux
- ✅ Supporto per versioni Release e Preview
- ✅ Backup automatico prima dell'aggiornamento
- ✅ Preservazione delle configurazioni esistenti
- ✅ Rilevamento automatico della versione corrente
- ✅ Modalità controllo-solo per verificare gli aggiornamenti

## Installazione

1. Clona o scarica questo repository
2. Installa le dipendenze Python:
   ```bash
   pip install requests
   ```

## Utilizzo

### Aggiornamento Base
```bash
python update.py
```

### Opzioni Disponibili

| Opzione | Descrizione |
|---------|-------------|
| `--preview` | Scarica la versione preview invece della release |
| `--force` | Forza l'aggiornamento anche se la versione è già aggiornata |
| `--dir <path>` | Specifica la directory del server (default: cartella corrente) |
| `--check-only` | Controlla solo se ci sono aggiornamenti disponibili |

### Esempi

**Controllo aggiornamenti:**
```bash
python update.py --check-only
```

**Aggiornamento alla versione preview:**
```bash
python update.py --preview
```

**Aggiornamento forzato:**
```bash
python update.py --force
```

**Aggiornamento di un server in una cartella specifica:**
```bash
python update.py --dir "C:\MinecraftServer"
```

## Come Funziona

1. **Controllo versione**: Lo script controlla la versione corrente del server (se presente)
2. **API call**: Interroga l'API di Minecraft per ottenere i link di download più recenti
3. **Download**: Scarica il file ZIP del server appropriato per il sistema operativo
4. **Estrazione**: Estrae il contenuto in una cartella temporanea
5. **Pulizia**: Rimuove i file di configurazione per preservare le impostazioni esistenti:
   - Cartella `config`
   - File `allowlist.json`
   - File `packetlimitconfig.json`
   - File `permissions.json`
   - File `profanity_filter.wlist`
   - File `server.properties`
6. **Backup**: Crea un backup della cartella corrente
7. **Aggiornamento**: Copia i nuovi file nella cartella del server
8. **Verifica**: Salva le informazioni sulla nuova versione

## File Preservati

Lo script preserva automaticamente tutti i file configurati in `config.ini`:

**File esclusi (configurabili in `config.ini`):**
- `server.properties` - Configurazioni principali del server
- `allowlist.json` - Lista dei giocatori autorizzati
- `permissions.json` - Permessi dei giocatori
- `packetlimitconfig.json` - Configurazione limiti pacchetti
- `profanity_filter.wlist` - Filtro linguaggio inappropriato

**Cartelle escluse:**
- `config/` - Cartella configurazioni

**Altri file sempre preservati:**
- Mondi salvati
- Log files
- Plugin e modifiche personalizzate

## Configurazione

Il file `config.ini` permette di personalizzare:
- File e cartelle da escludere durante l'aggiornamento (`exclude_files` e `exclude_dirs`)
- Timeout per download e API
- Configurazioni di logging
- Directory di backup personalizzate

## Struttura dei Backup

I backup vengono creati con il formato:
```
backup_{versione}_{nome_computer}/
```

Esempio: `backup_1.21.120.4_DESKTOP-ABC123/`

## API Endpoint

Lo script utilizza l'endpoint ufficiale di Minecraft:
```
https://net-secondary.web.minecraft-services.net/api/v1.0/download/links
```

## Requisiti di Sistema

- Python 3.7+
- Libreria `requests`
- Windows o Linux
- Connessione internet per il download

## Risoluzione Problemi

### Errore di connessione
Se ottieni errori di connessione, verifica:
- La connessione internet
- Eventuali firewall o proxy che bloccano l'accesso

### Permessi di scrittura
Assicurati di avere i permessi di scrittura nella cartella del server.

### File in uso
Su Windows, assicurati che il server sia completamente chiuso prima di eseguire l'aggiornamento.

## Licenza

Questo progetto è rilasciato sotto licenza MIT.

## Contribuire

I contributi sono benvenuti! Sentiti libero di aprire issue o pull request.

## Changelog

### v1.0.0 (29/10/2025)
- Prima release
- Supporto per Windows e Linux
- Supporto versioni Release e Preview
- Sistema di backup automatico
- Preservazione configurazioni
