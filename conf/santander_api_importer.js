const { importForAccount } = require('./importer_func');

importForAccount('Santander', 'ACTUAL_ACCOUNT_NAME_SANTANDER').catch(error => {
  console.error(`Santander import failed: ${error.message}`);
  process.exitCode = 1;
});
