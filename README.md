# Spain2Actual: Spain Banks Converter CSV and Import

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Build Status](https://img.shields.io/github/actions/workflow/status/rpadafo/spain2actual/docker-publish.yml?branch=main&style=for-the-badge&logo=github)

Automated background service to convert Spanish bank statements into CSV files and import Bankinter transactions into **[Actual Budget](https://actualbudget.org/)**. Other supported formats continue to be exported as CSV for manual import.

---

> [!IMPORTANT]
> **Prerequisites:**
> * An instance of **Actual Budget** running.
> * **Docker** and **Docker Compose** installed.
> * Dedicated host folders for `/input` (source documents), `/output` (generated CSV files), and `/imported` (successfully imported CSV files).
> * The Actual server password, budget Sync ID, and Bankinter account ID to enable automatic imports.

---

## 🚀 Features

* **Automated Processing:** Monitors the `/input` directory and converts files in real time.
* **Smart Bank Detection:** Automatically routes files to the correct processor based on file names and structures.
* **Bankinter Import:** Imports Bankinter transactions through Actual's official API client; successfully imported CSVs are moved to `/imported`.
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
      RETENTION_HOUR: "12"
      PREFIX_BANKINTER: BANK
      PREFIX_CAIXA: CAIX
      PREFIX_SABADELL: SABA
      PREFIX_SANTANDER: SANT
      PREFIX_TRADEREPUBLIC: TR
      PREFIX_SUMUP: SUM
      ACTUAL_SERVER_URL: "http://your-actual-host:5006"
      ACTUAL_PASSWORD: "your-actual-server-password"
      ACTUAL_BUDGET_ID: "your-budget-sync-id"
      ACTUAL_ACCOUNT_ID_BANKINTER: "your-bankinter-account-id"
      ACTUAL_DATA_DIR: /data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    volumes:
      - /path/to/your/input:/input
      - /path/to/your/output:/output
      - /path/to/your/imported:/imported
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

Set the Actual connection values directly in the `environment` section of the Compose file you deploy, replacing the example values above. The server URL includes its port. `ACTUAL_PASSWORD` is the password used to log in to your Actual server. `ACTUAL_BUDGET_ID` is the budget's **Sync ID** from advanced settings. Set the account ID to the ID of the Bankinter account in that budget. If the password contains `$`, write it as `$$` so Compose passes it literally. Do not commit real passwords to a public repository.

Bankinter imports use `Fecha contable` as the date, `Importe` as the signed amount, and `Descripción` as the payee; the balance column is ignored. Actual applies its import rules and duplicate reconciliation. When Actual is not configured, Bankinter CSVs remain in `/output` as before. When configured, a CSV moves to `/imported` only after a successful import; on an error, the source and generated CSV are kept for investigation. To retry, fix the configuration and submit the source file to `/input` again. `RETENTION_HOUR` controls cleanup in both CSV folders, which runs when a new input file is processed.