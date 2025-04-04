const HDWalletProvider = require("@truffle/hdwallet-provider");
require("dotenv").config();

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545, // Ganache default port
      network_id: "*",
    },
    sepolia: {
      provider: () => new HDWalletProvider(
        process.env.MNEMONIC, // Your MetaMask seed phrase (store in .env)
        "https://sepolia.infura.io/v3/510d67a43ab5439090f85c1e89c1ffc4" // Infura endpoint
      ),
      network_id: 11155111, // Sepolia network ID
      gas: 5500000,
      gasPrice: 20000000000, // 20 Gwei
    },
  },
  compilers: {
    solc: {
      version: "0.8.20",
    },
  },
};