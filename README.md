# Loyalty Rewards Blockchain Setup

This guide will help you set up and run the loyalty rewards blockchain application using Truffle, Ganache, and Streamlit.

## Prerequisites

- Node.js and npm installed
- Python 3.7+ with pip installed
- A text editor or IDE
- MetaMask wallet (for seed phrase)
- Infura account (for project ID)

## Installation Steps

### 1. Install Global Dependencies

```bash
# Install Truffle globally
npm install -g truffle

# Install Ganache globally
npm install -g ganache
```

### 2. Project Setup

```bash
# Create and enter project directory
mkdir token-rewards-portal
cd token-rewards-portal

# Initialize Truffle project
truffle init

# Initialize npm project
npm init -y

# Install OpenZeppelin contracts
npm install @openzeppelin/contracts
```

### 3. Create Environment File

Create a `.env` file in the project root directory:

```
MNEMONIC="your metamask seed phrase"
INFURA_PROJECT_ID="your infura project id"
```

### 4. Start Blockchain Environment

Open a terminal and start Ganache:

```bash
ganache
```

This will start a local blockchain at `http://127.0.0.1:8545` by default.

### Deploy Smart Contracts

Open another terminal window, navigate to your project directory, and deploy the contracts:

```bash
cd token-rewards-portal
truffle migrate --network development --reset
```

Make note of the contract address that is output after successful deployment. You'll need to add this to your `app.py` file.

### 6. Run the Streamlit Application

In a third terminal window:

```bash
streamlit run app.py
```

This will start the Streamlit server and automatically open the web application in your default browser.

## Important Notes

- Make sure Ganache and Truffle are configured to use the same port (8545 by default)
- Update the contract address in `app.py` with the address from your contract deployment
- Keep your MetaMask seed phrase secure and never share it

## Troubleshooting

- If you encounter connection issues, verify that Ganache is running and the port matches in your Truffle configuration
- For contract deployment failures, check that your `.env` file is properly set up
- If Streamlit throws errors, ensure all Python dependencies are installed (`web3`, `streamlit`, etc.)

Happy coding! 🚀
