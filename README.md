# Spain2Actual: Conversor CSV de bancos españoles e importación

![AI-Generated Code](https://img.shields.io/badge/AI--Generated-Code-7B61FF?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)
![Build Status](https://img.shields.io/github/actions/workflow/status/rpadafo/spain2actual/docker-publish.yml?branch=main&style=for-the-badge&logo=github)

[Ver en inglés](README.english.md)

Servicio automatizado en segundo plano para convertir extractos bancarios españoles a archivos CSV y, opcionalmente, importar transacciones de Bankinter, Caixa, Santander, Trade Republic y SumUp en **[Actual Budget](https://actualbudget.org/)**. Los demás formatos compatibles se siguen exportando como CSV para su importación manual.

---

> [!IMPORTANT]
> **Requisitos previos:**
> * Una instancia de **Actual Budget** en funcionamiento si `SYNC_API` está habilitado.
> * **Docker** y **Docker Compose** instalados.
> * Carpetas dedicadas en el host para `/input` (documentos de origen), `/output` (archivos CSV generados), `/imported` (archivos CSV importados correctamente) y `/error` (archivos CSV cuya importación en Actual ha fallado).
> * La contraseña del servidor de Actual, el Sync ID del presupuesto y los nombres visibles de las cuentas de Bankinter, Caixa, Santander, Trade Republic y SumUp para habilitar las importaciones automáticas.

---
> **Aviso sobre el uso de IA:** Este proyecto contiene código generado con la ayuda de inteligencia artificial.
---

## 🚀 Funcionalidades

* **Procesamiento automatizado:** Supervisa el directorio `/input` y convierte archivos en tiempo real.
* **Detección inteligente de bancos:** Enruta automáticamente los archivos al procesador correcto según sus nombres y estructuras.
* **Importaciones opcionales:** Cuando `SYNC_API` es `true`, importa transacciones de Bankinter, Caixa, Santander, Trade Republic y SumUp mediante el cliente oficial de la API de Actual; los CSV importados correctamente se mueven a `/imported`.
* **Importaciones fallidas:** Mueve a `/error` los CSV de Bankinter, Caixa, Santander, Trade Republic o SumUp si falla su importación en Actual.
* **Limpieza automática:** Elimina los CSV antiguos de `/output` y `/imported` tras un periodo de retención configurable.
* **Preparado para el formato español:** Da formato correctamente a las fechas, los números (comas para los decimales) y la codificación UTF-8.

### 🏦 Bancos compatibles

| Banco | Formato de origen | Prefijo de salida | Sincronización API
| :--- | :--- | :--- | :--- |
| **Bankinter** | `.xlsx` / `.xls` | `BK_*.csv` | Sí |
| **CaixaBank** | `.xlsx` / `.xls` | `LC_*.csv` | Sí |
| **Banco Santander** | `.xlsx` / `.xls` | `SA_*.csv` | Sí |
| **Banco Sabadell** | `.txt` | `BS_*.csv` | No |
| **Trade Republic** | `Exportación de transacción.csv` | `TR_*.csv` | Sí |
| **SumUp** | `SumUp*.pdf` | `SUM_*.csv` | Sí |

---

## 🛠️ Despliegue y uso

Usa el siguiente fragmento de `docker-compose.yml` para desplegar el contenedor:

```yaml
services:
  spain2actual:
    image: ghcr.io/rpadafo/spain2actual:latest
    container_name: spain2actual
    restart: unless-stopped
    environment:
      #Configuración del importador >>
      RETENTION_HOUR: "12"
      SYNC_API: true
      #Conector de Actual Budget >>
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
          cpus: '1'
          memory: 256M
    volumes:
      - /path/to/your/input:/input
      - /path/to/your/output:/output
      - /path/to/your/imported:/imported
      - /path/to/your/error:/error
      - /path/to/your/actual-data:/data
#Opcional >>
    networks:
        lan:
            ipv4_address: 192.168.x.x
    dns:
            - 8.8.8.8
networks:
    lan:
        external: true
#Opcional <<
```

## Configuración de la API de Actual Budget

* Establece `SYNC_API` en `"true"` para habilitar la conexión con Actual y las importaciones de Bankinter/Caixa/Santander/Trade Republic/SumUp, o en `"false"` para limitarse a convertir archivos a CSV; su valor predeterminado es `"false"`. Cuando esté habilitado, configura los demás valores de conexión con Actual directamente en la sección `environment` del archivo Compose que despliegues, sustituyendo los valores de ejemplo anteriores. La URL del servidor incluye su puerto.
* `ACTUAL_PASSWORD` es la contraseña que se usa para iniciar sesión en el servidor de Actual.
* `ACTUAL_SYNC_ID` es el **Sync ID** del presupuesto, que se encuentra en la sección de configuración avanzada.
* Establece `ACTUAL_ACCOUNT_NAME_BANKINTER`, `ACTUAL_ACCOUNT_NAME_CAIXA`, `ACTUAL_ACCOUNT_NAME_SANTANDER`, `ACTUAL_ACCOUNT_NAME_TRADEREPUBLIC` y `ACTUAL_ACCOUNT_NAME_SUMUP` con los nombres visibles de las cuentas en ese presupuesto; cada búsqueda ignora las mayúsculas y los espacios al principio y al final, y falla si el nombre no existe o no es único. Si la contraseña contiene `$`, escríbelo como `$$` para que Compose lo pase literalmente. No guardes contraseñas reales en un repositorio público.

### Asignación de campos bancarios

| Banco | Fecha | Beneficiario | Notas | Importe
| :--- | :--- | :--- | :--- | :--- |
| **Bankinter** | `Fecha Contable` | `Descripción` | `Descripción` | `Importe` |
| **CaixaBank** | `Fecha` | `Movimiento` | `Más datos` | `Importe` |
| **Banco Santander** | `Fecha valor` | `Concepto` | `Concepto` | `Importe EUR` |
| **Trade Republic** | `Date` | `Name` | `Description` | `Amount_Calc` |
| **SumUp** | `Fecha` | `Descripción` | `Tipo` | `Importe` |

* Actual previsualiza la detección de duplicados antes de importar: las transacciones coincidentes se omiten y permanecen intactas; solo se añaden como no conciliadas las transacciones nuevas.
* Tras una conversión correcta, el archivo de origen se elimina de `/input`. Con `SYNC_API=false`, todos los archivos compatibles solo se convierten y sus CSV permanecen en `/output`; no se establece ninguna conexión con Actual.
* Con `SYNC_API=true`, los CSV de Bankinter, Caixa, Santander, Trade Republic y SumUp se mueven de `/output` a `/imported` tras importarse correctamente, o a `/error` si falla la importación. Los CSV cuya importación ha fallado se conservan para investigarlos; para reintentarlo, vuelve a enviar el archivo de origen a `/input`.
* `RETENTION_HOUR` controla la limpieza de `/output` y `/imported`, que se ejecuta al procesar un nuevo archivo de entrada; los archivos de `/error` se conservan para su investigación.
