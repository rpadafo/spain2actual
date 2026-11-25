from importer_func import (
    import_transactions,
    load_csv_rows,
    parse_amount,
    parse_date,
    require_columns,
)


def load_caixa_transactions(csv_path):
    bank_name = "Caixa"
    columns, rows = load_csv_rows(csv_path, bank_name)
    columns = require_columns(
        columns,
        ("Fecha", "Movimiento", "Más datos", "Importe"),
        bank_name,
    )
    transactions = []

    for row_number, row in enumerate(rows, start=2):
        date_value = (row.get(columns["fecha"]) or "").strip()
        amount_value = (row.get(columns["importe"]) or "").strip()
        payee = (row.get(columns["movimiento"]) or "").strip()
        notes = (row.get(columns["mas datos"]) or "").strip()
        if not date_value and not amount_value and not payee and not notes:
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
        if notes:
            transaction["notes"] = notes
        transactions.append(transaction)

    if not transactions:
        raise ValueError(f"{bank_name} CSV contains no transactions")

    return transactions


def import_caixa_csv(csv_path):
    return import_transactions(
        load_caixa_transactions(csv_path),
        "ACTUAL_ACCOUNT_NAME_CAIXA",
        "caixa_api_importer.js",
    )
