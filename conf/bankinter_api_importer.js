const { importForAccount } = require('./importer_func');

importForAccount('Bankinter', 'ACTUAL_ACCOUNT_NAME_BANKINTER').catch(error => {
  console.error(`Bankinter import failed: ${error.message}`);
  process.exitCode = 1;
});
