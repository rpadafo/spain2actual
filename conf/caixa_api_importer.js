const { importForAccount } = require('./importer_func');

importForAccount('Caixa', 'ACTUAL_ACCOUNT_NAME_CAIXA').catch(error => {
  console.error(`Caixa import failed: ${error.message}`);
  process.exitCode = 1;
});
