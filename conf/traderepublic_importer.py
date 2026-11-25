from importer_func import (
    import_transactions,
    load_csv_rows,
    parse_amount,
    parse_date,
    require_columns,
)


def load_traderepublic_transactions(csv_path):
    bank_name = "Trade Republic"
    available_columns, rows = load_csv_rows(csv_path, bank_name, delimiter=",")
    columns = require_columns(
        available_columns,
        ("date", "name", "description", "amount_calc"),
        bank_name,
    )
    transactions = []

    for row_number, row in enumerate(rows, start=2):
        date_value = (row.get(columns["date"]) or "").strip()
        amount_value = (row.get(columns["amount_calc"]) or "").strip()
        payee = (row.get(columns["name"]) or "").strip()
        notes = (row.get(columns["description"]) or "").strip()
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


def import_traderepublic_csv(csv_path):
    return import_transactions(
        load_traderepublic_transactions(csv_path),
        "ACTUAL_ACCOUNT_NAME_TRADEREPUBLIC",
        "traderepublic_api_importer.js",
    )
