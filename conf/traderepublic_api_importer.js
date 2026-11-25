const { importForAccount } = require('./importer_func');

importForAccount('Trade Republic', 'ACTUAL_ACCOUNT_NAME_TRADEREPUBLIC').catch(error => {
  console.error(`Trade Republic import failed: ${error.message}`);
  process.exitCode = 1;
});
