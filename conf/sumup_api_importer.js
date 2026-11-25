const { importForAccount } = require('./importer_func');

importForAccount('SumUp', 'ACTUAL_ACCOUNT_NAME_SUMUP').catch(error => {
  console.error(`SumUp import failed: ${error.message}`);
  process.exitCode = 1;
});
