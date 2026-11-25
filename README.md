# Spain2Actual: Spain Banks Converter CSV and Import

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![AI-Generated Code](https://img.shields.io/badge/AI--Generated-Code-7B61FF?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Build Status](https://img.shields.io/github/actions/workflow/status/rpadafo/spain2actual/docker-publish.yml?branch=main&style=for-the-badge&logo=github)

> **AI disclosure:** This project contains code generated with the assistance of artificial intelligence.

Automated background service to convert Spanish bank statements into CSV files and optionally import Bankinter, Caixa, Santander, Trade Republic, and SumUp transactions into **[Actual Budget](https://actualbudget.org/)**. Other supported formats continue to be exported as CSV for manual import.

---

> [!IMPORTANT]
> **Prerequisites:**
> * An instance of **Actual Budget** running if `SYNC_API` is enabled.
> * **Docker** and **Docker Compose** installed.
> * Dedicated host folders for `/input` (source documents), `/output` (generated CSV files), `/imported` (successfully imported CSV files), and `/error` (CSV files whose Actual import failed).
> * The Actual server password, budget Sync ID, and visible Bankinter, Caixa, Santander, Trade Republic, and SumUp account names to enable automatic imports.

---

## 🚀 Features

* **Automated Processing:** Monitors the `/input` directory and converts files in real time.
* **Smart Bank Detection:** Automatically routes files to the correct processor based on file names and structures.
* **Optional Bank Imports:** When `SYNC_API` is `true`, imports Bankinter, Caixa, Santander, Trade Republic, and SumUp transactions through Actual's official API client; successfully imported CSVs are moved to `/imported`.
* **Failed Imports:** Moves Bankinter, Caixa, Santander, Trade Republic, or SumUp CSVs to `/error` if importing into Actual fails.
* **Auto-Cleanup:** Deletes old CSVs in `/output` and `/imported` after a configurable retention period.
* **Spanish Formatting Ready:** Properly formats dates, numbers (commas for decimals), and UTF-8 encoding.

### 🏦 Supported Banks

| Bank | Source Format | Output Prefix |
| :--- | :--- | :--- |
| **Bankinter** | `.xlsx` / `.xls` | `BK_*.csv` |
| **CaixaBank** | `.xlsx` / `.xls` | `LC_*.csv` |
| **Banco Santander** | `.xlsx` / `.xls` | `SA_*.csv` |
| **Banco Sabadell** | `.txt` | `BS_*.csv` |
| **Trade Republic** | `Exportación de transacción.csv` | `TR_*.csv` |
| **SumUp** | `SumUp*.pdf` | `SUM_*.csv` |

---

## 🛠️ Deployment & Usage

Use the following `docker-compose.yml` snippet to deploy the container:

```yaml
services:
  spain2actual:
    image: ghcr.io/rpadafo/spain2actual:latest
    container_name: spain2actual
    restart: unless-stopped
    environment:
      #Importer settings >>
      RETENTION_HOUR: "12"
      SYNC_API: true
      #Actual Budget connector >>
      ACTUAL_SERVER_URL: "http://your-actual-host:5006"
      ACTUAL_PASSWORD: "your-actual-server-password"
      ACTUAL_SYNC_ID: "your-budget-sync-id"
      ACTUAL_DATA_DIR: /data
      #Bankinter >>
      PREFIX_BANKINTER: BANK
      ACTUAL_ACCOUNT_NAME_BANKINTER: "your-bankinter-account-name"
      #CaixaBankNow >>
      PREFIX_CAIXA: CAIX
      ACTUAL_ACCOUNT_NAME_CAIXA: "your-caixa-account-name"
      #Sabadell >>
      PREFIX_SABADELL: SABA
      #Santander >>
      PREFIX_SANTANDER: SANT
      ACTUAL_ACCOUNT_NAME_SANTANDER: "your-santander-account-name"
      #Trade Republic >>
      PREFIX_TRADEREPUBLIC: TR
      ACTUAL_ACCOUNT_NAME_TRADEREPUBLIC: "your-trade-republic-account-name"
      #Sumup (Personal) >>
      PREFIX_SUMUP: SUM
      ACTUAL_ACCOUNT_NAME_SUMUP: "your-sumup-account-name"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    volumes:
      - /path/to/your/input:/input
      - /path/to/your/output:/output
      - /path/to/your/imported:/imported
      - /path/to/your/error:/error
      - /path/to/your/actual-data:/data
#Optional >>
    networks:
        lan:
            ipv4_address: 192.168.x.x
            mac_address: "02:42:C0:xx:xx:xx"
    dns:
            - 8.8.8.8
networks:
    lan:
        external: true
#Optional <<
```

### Actual Budget API configuration

Set `SYNC_API` to `"true"` to enable the Actual connection and Bankinter/Caixa/Santander/Trade Republic/SumUp imports, or `"false"` to only convert files to CSV; it defaults to `"false"`. When enabled, set the other Actual connection values directly in the `environment` section of the Compose file you deploy, replacing the example values above. The server URL includes its port. `ACTUAL_PASSWORD` is the password used to log in to your Actual server. `ACTUAL_SYNC_ID` is the budget's **Sync ID** from advanced settings. Set `ACTUAL_ACCOUNT_NAME_BANKINTER`, `ACTUAL_ACCOUNT_NAME_CAIXA`, `ACTUAL_ACCOUNT_NAME_SANTANDER`, `ACTUAL_ACCOUNT_NAME_TRADEREPUBLIC`, and `ACTUAL_ACCOUNT_NAME_SUMUP` to the visible account names in that budget; each lookup ignores case and surrounding spaces, and fails if the name is missing or ambiguous. If the password contains `$`, write it as `$$` so Compose passes it literally. Do not commit real passwords to a public repository.

Bankinter imports map `Fecha contable` to the date, `Descripción` to both payee and notes, and `Importe` to the signed amount in cents. Caixa imports map `Fecha` to the date, `Movimiento` to the payee, `Más datos` to notes, and `Importe` to the signed amount in cents. Santander imports map `Fecha valor` to the date, `Concepto` to both payee and notes, and `Importe EUR` to the signed amount in cents. Trade Republic imports map `date` to the date, `name` to the payee, `description` to notes, and `amount_calc` to the signed amount in cents. SumUp imports map `Fecha` to the date, `Descripción` to the payee, `Tipo` to notes, and `Importe` to the signed amount in cents. None of the importers sends a category; Caixa's `Fecha valor` and `Saldo`, and Santander's `Fecha operación` and `Saldo`, are ignored. Actual's duplicate matching is previewed before import: matching existing transactions are skipped and left untouched, while only new transactions are added as uncleared. After a successful conversion, the source file is removed from `/input`. With `SYNC_API=false`, all supported files are only converted and their CSVs remain in `/output`; no Actual connection is made. With `SYNC_API=true`, Bankinter, Caixa, Santander, Trade Republic, and SumUp CSVs move from `/output` to `/imported` after successful imports, or to `/error` if the import fails. Failed-import CSVs are kept for investigation; to retry, submit the original source file to `/input` again. `RETENTION_HOUR` controls cleanup in `/output` and `/imported`, which runs when a new input file is processed; `/error` is retained for investigation.