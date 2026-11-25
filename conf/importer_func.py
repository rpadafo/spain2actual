import csv
import json
import logging
import os
import subprocess
import unicodedata

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


logger = logging.getLogger(__name__)
IMPORTER_DIR = os.path.dirname(__file__)


def normalize_header(value):
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )


def load_csv_rows(csv_path, bank_name, delimiter=";"):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError(f"{bank_name} CSV has no header row")

        columns = {
            normalize_header(name): name
            for name in reader.fieldnames
            if name
        }
        return columns, list(reader)


def require_columns(columns, required_columns, bank_name):
    missing_columns = [
        column for column in required_columns
        if normalize_header(column) not in columns
    ]
    if missing_columns:
        raise ValueError(
            f"{bank_name} CSV is missing required columns: "
            + ", ".join(missing_columns)
        )

    return {
        normalize_header(column): columns[normalize_header(column)]
        for column in required_columns
    }


def parse_date(value, bank_name):
    value = value.strip()
    if not value:
        raise ValueError(f"{bank_name} transaction has an empty date")

    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                pass

    raise ValueError(f"Unsupported {bank_name} date: {value!r}")


def parse_amount(value, bank_name):
    amount = value.strip().replace("\u00a0", "").replace(" ", "").replace("€", "")
    if not amount:
        raise ValueError(f"{bank_name} transaction has an empty amount")

    if "," in amount and "." in amount:
        if amount.rfind(",") > amount.rfind("."):
            amount = amount.replace(".", "").replace(",", ".")
        else:
            amount = amount.replace(",", "")
    elif "," in amount:
        amount = amount.replace(",", ".")

    try:
        decimal_amount = Decimal(amount)
    except InvalidOperation as error:
        raise ValueError(f"Unsupported {bank_name} amount: {value!r}") from error

    cents = (decimal_amount * 100).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)


def import_transactions(transactions, account_setting, api_script):
    required_settings = (
        "ACTUAL_SERVER_URL",
        "ACTUAL_PASSWORD",
        "ACTUAL_SYNC_ID",
        account_setting,
    )
    missing_settings = [
        setting for setting in required_settings
        if not os.environ.get(setting, "").strip()
    ]
    if missing_settings:
        raise ValueError(
            "Actual import is missing required settings: "
            + ", ".join(missing_settings)
        )

    payload = {"transactions": transactions}
    api_script_path = os.path.join(IMPORTER_DIR, api_script)
    try:
        result = subprocess.run(
            ["node", api_script_path],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Node.js is required for Actual Budget imports") from error

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Actual Budget import failed with exit code {result.returncode}: "
            f"{details}"
        )

    if result.stdout.strip():
        logger.info("Actual import result: %s", result.stdout.strip())
    return True
