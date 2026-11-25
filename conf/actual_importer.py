import csv
import json
import logging
import os
import subprocess
import unicodedata

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


logger = logging.getLogger(__name__)
API_IMPORTER_PATH = os.path.join(os.path.dirname(__file__), "actual_api_importer.js")


def _normalize_header(value):
    normalized = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(character for character in normalized if not unicodedata.combining(character))


def _parse_date(value):
    value = value.strip()
    if not value:
        raise ValueError("Bankinter transaction has an empty date")

    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        for date_format in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, date_format).date().isoformat()
            except ValueError:
                pass

    raise ValueError(f"Unsupported Bankinter date: {value!r}")


def _parse_amount(value):
    amount = value.strip().replace("\u00a0", "").replace(" ", "").replace("€", "")
    if not amount:
        raise ValueError("Bankinter transaction has an empty amount")

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
        raise ValueError(f"Unsupported Bankinter amount: {value!r}") from error

    cents = (decimal_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def load_bankinter_transactions(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        if not reader.fieldnames:
            raise ValueError("Bankinter CSV has no header row")

        columns = {_normalize_header(name): name for name in reader.fieldnames if name}
        required_columns = {
            "fecha contable": "date",
            "importe": "amount",
            "descripcion": "payee",
        }
        missing_columns = [
            column for column in required_columns
            if _normalize_header(column) not in columns
        ]
        if missing_columns:
            raise ValueError(
                "Bankinter CSV is missing required columns: "
                + ", ".join(missing_columns)
            )

        date_column = columns["fecha contable"]
        amount_column = columns["importe"]
        payee_column = columns["descripcion"]
        transactions = []

        for row_number, row in enumerate(reader, start=2):
            date_value = (row.get(date_column) or "").strip()
            amount_value = (row.get(amount_column) or "").strip()
            payee = (row.get(payee_column) or "").strip()
            if not date_value and not amount_value and not payee:
                continue

            try:
                transaction = {
                    "date": _parse_date(date_value),
                    "amount": _parse_amount(amount_value),
                }
            except ValueError as error:
                raise ValueError(
                    f"Invalid Bankinter CSV row {row_number}: {error}"
                ) from error
            if payee:
                transaction["payee_name"] = payee
                transaction["imported_payee"] = payee
            transactions.append(transaction)

        if not transactions:
            raise ValueError("Bankinter CSV contains no transactions")

        return transactions


def import_bankinter_csv(csv_path):
    server_url = os.environ.get("ACTUAL_SERVER_URL", "").strip()
    if not server_url:
        logger.info("Actual import is not configured; keeping the CSV in output")
        return False

    required_settings = (
        "ACTUAL_PASSWORD",
        "ACTUAL_BUDGET_ID",
        "ACTUAL_ACCOUNT_NAME_BANKINTER",
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

    payload = {
        "accountName": os.environ["ACTUAL_ACCOUNT_NAME_BANKINTER"].strip(),
        "transactions": load_bankinter_transactions(csv_path),
    }

    try:
        result = subprocess.run(
            ["node", API_IMPORTER_PATH],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as error:
        raise RuntimeError("Node.js is required for Actual Budget imports") from error

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            f"Actual Budget import failed with exit code {result.returncode}: {details}"
        )

    if result.stdout.strip():
        logger.info("Actual import result: %s", result.stdout.strip())
    return True
