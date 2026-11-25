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
  if (!value) {
    throw new Error(`Missing required setting ${name}`);
  }
  return value;
}

async function run() {
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
    const accountName = payload.accountName.trim().toLowerCase();
    const matchingAccounts = accounts.filter(
      item => typeof item.name === 'string'
        && item.name.trim().toLowerCase() === accountName
    );
    if (matchingAccounts.length === 0) {
      throw new Error(`Bankinter account "${payload.accountName}" was not found`);
    }
    if (matchingAccounts.length > 1) {
      throw new Error(`Bankinter account name "${payload.accountName}" is ambiguous`);
    }
    const account = matchingAccounts[0];
    if (account.closed) {
      throw new Error('Configured Bankinter account is closed');
    }

    const result = await actual.importTransactions(
      account.id,
      payload.transactions,
      {
        defaultCleared: false,
        payeeNameNormalization: 'original',
        reimportDeleted: false,
      }
    );
    const errors = Array.isArray(result.errors)
      ? result.errors
      : (result.errors ? [result.errors] : []);
    if (errors.length > 0) {
      throw new Error(`Actual rejected the import: ${JSON.stringify(errors)}`);
    }

    process.stdout.write(JSON.stringify({
      added: result.added.length,
      updated: result.updated.length,
    }) + '\n');
  } finally {
    if (initialized) {
      await actual.shutdown();
    }
  }
}

run().catch(error => {
  console.error(`Actual Budget import failed: ${error.message}`);
  process.exitCode = 1;
});
