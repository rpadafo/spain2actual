from importer_func import (
    import_transactions,
    load_csv_rows,
    parse_amount,
    parse_date,
    require_columns,
)


def load_bankinter_transactions(csv_path):
    bank_name = "Bankinter"
    columns, rows = load_csv_rows(csv_path, bank_name)
    columns = require_columns(
        columns,
        ("Fecha contable", "Importe", "Descripción"),
        bank_name,
    )
    transactions = []

    for row_number, row in enumerate(rows, start=2):
        date_value = (row.get(columns["fecha contable"]) or "").strip()
        amount_value = (row.get(columns["importe"]) or "").strip()
        payee = (row.get(columns["descripcion"]) or "").strip()
        if not date_value and not amount_value and not payee:
            continue

        try:
            transaction = {
                "date": parse_date(date_value, bank_name),
                "amount": parse_amount(amount_value, bank_name),
            }
        except ValueError as error:
            raise ValueError(
                f"Invalid {bank_name} CSV row {row_number}: {error}"
            ) from error

        if payee:
            transaction["payee_name"] = payee
            transaction["imported_payee"] = payee
            transaction["notes"] = payee
        transactions.append(transaction)

    if not transactions:
        raise ValueError(f"{bank_name} CSV contains no transactions")

    return transactions


def import_bankinter_csv(csv_path):
    return import_transactions(
        load_bankinter_transactions(csv_path),
        "ACTUAL_ACCOUNT_NAME_BANKINTER",
        "bankinter_api_importer.js",
    )
