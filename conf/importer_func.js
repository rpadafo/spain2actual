const actual = require('@actual-app/api');

function readInput() {
  return new Promise((resolve, reject) => {
    let input = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => {
      input += chunk;
    });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(input));
      } catch (error) {
        reject(new Error(`Invalid import payload: ${error.message}`));
      }
    });
    process.stdin.on('error', reject);
  });
}

function requiredSetting(name) {
  const value = process.env[name];
  if (!value || !value.trim()) {
    throw new Error(`Missing required setting ${name}`);
  }
  return value.trim();
}

function importErrors(result) {
  return Array.isArray(result.errors)
    ? result.errors
    : (result.errors ? [result.errors] : []);
}

async function importForAccount(bankName, accountSetting) {
  const payload = await readInput();
  let initialized = false;

  try {
    await actual.init({
      dataDir: process.env.ACTUAL_DATA_DIR || '/data',
      serverURL: requiredSetting('ACTUAL_SERVER_URL'),
      password: requiredSetting('ACTUAL_PASSWORD'),
    });
    initialized = true;

    await actual.downloadBudget(requiredSetting('ACTUAL_SYNC_ID'));

    const accounts = await actual.getAccounts();
    const accountName = requiredSetting(accountSetting);
    const matchingAccounts = accounts.filter(
      item => typeof item.name === 'string'
        && item.name.trim().toLowerCase() === accountName.toLowerCase()
    );
    if (matchingAccounts.length === 0) {
      throw new Error(
        `Configured ${bankName} account "${accountName}" was not found`
      );
    }
    if (matchingAccounts.length > 1) {
      throw new Error(
        `Configured ${bankName} account "${accountName}" is ambiguous`
      );
    }
    const account = matchingAccounts[0];
    if (account.closed) {
      throw new Error(`Configured ${bankName} account is closed`);
    }

    const importOptions = {
      defaultCleared: false,
      payeeNameNormalization: 'original',
      reimportDeleted: false,
    };
    // Preview matches so the write pass can skip existing records entirely.
    const inputIndexField = '__spain2actualInputIndex';
    const preview = await actual.importTransactions(
      account.id,
      payload.transactions.map((transaction, index) => ({
        ...transaction,
        [inputIndexField]: index,
      })),
      { ...importOptions, dryRun: true }
    );
    const previewErrors = importErrors(preview);
    if (previewErrors.length > 0) {
      throw new Error(
        `Actual rejected the import preview: ${JSON.stringify(previewErrors)}`
      );
    }
    if (!Array.isArray(preview.updatedPreview)) {
      throw new Error(
        'Actual did not return duplicate-match details; refusing to import '
        + 'to avoid modifying existing transactions'
      );
    }

    const existingTransactionIndexes = new Set();
    for (const match of preview.updatedPreview) {
      const inputIndex = match.transaction?.[inputIndexField];
      if (
        !Number.isInteger(inputIndex)
        || inputIndex < 0
        || inputIndex >= payload.transactions.length
      ) {
        throw new Error(
          'Could not identify a matched transaction in the Actual preview; '
          + 'refusing to import to avoid modifying existing transactions'
        );
      }
      existingTransactionIndexes.add(inputIndex);
    }

    const transactionsToImport = payload.transactions.map(
      (transaction, index) => existingTransactionIndexes.has(index)
        ? { ...transaction, skipTransaction: true }
        : transaction
    );
    const result = await actual.importTransactions(
      account.id,
      transactionsToImport,
      importOptions
    );
    const errors = importErrors(result);
    if (errors.length > 0) {
      throw new Error(`Actual rejected the import: ${JSON.stringify(errors)}`);
    }

    process.stdout.write(JSON.stringify({
      added: result.added.length,
      updated: result.updated.length,
      skipped: existingTransactionIndexes.size,
    }) + '\n');
  } finally {
    if (initialized) {
      await actual.shutdown();
    }
  }
}

module.exports = { importForAccount };
