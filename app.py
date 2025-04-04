import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random
from web3 import Web3
import json
import time

def get_transaction_history(wallet_address, contract, num_transactions=10):
    """Fetch transaction history for the given wallet address"""
    try:
        # Get the latest block number
        latest_block = w3.eth.block_number
        
        # Get all transactions for the wallet
        txs = []
        for i in range(latest_block, max(0, latest_block - 1000), -1):
            block = w3.eth.get_block(i, full_transactions=True)
            for tx in block.transactions:
                if tx['to'] == contract.address or tx['from'].lower() == wallet_address.lower():
                    receipt = w3.eth.get_transaction_receipt(tx['hash'])
                    
                    # Parse transaction data based on function called
                    func, params = None, {}
                    if tx['input'] and tx['input'] != '0x':
                        try:
                            func_obj = contract.decode_function_input(tx['input'])
                            func = func_obj[0].fn_name
                            params = func_obj[1]
                        except:
                            pass
                    
                    # Determine transaction type and description
                    tx_type = "Unknown"
                    description = "Blockchain Transaction"
                    tokens = 0
                    
                    if func == "rewardPurchase":
                        tx_type = "Earned"
                        description = "Purchase Reward"
                        tokens = (params['usdSpent'] * 5) / (10 * 54)  # 5 TKN per $10 at 0.54 rate
                    elif func == "burn":
                        if 'cause' in params:  # This is a donation
                            tx_type = "Donated"
                            description = f"Donation: {params['cause']}"
                        else:
                            tx_type = "Spent"
                            description = params.get('description', 'Token Burn')
                        tokens = -params['amount'] / 10**18
                    elif func == "redeemPartnerReward":
                        tx_type = "Spent"
                        description = f"Partner Redemption: {params['partnerName']}"
                        tokens = -params['amount'] / 10**18
                    elif func == "donate":
                        tx_type = "Donated"
                        description = f"Donation: {params['cause']}"
                        tokens = -params['amount'] / 10**18
                    
                    txs.append({
                        "hash": tx['hash'].hex(),
                        "date": datetime.fromtimestamp(block['timestamp']).strftime("%Y-%m-%d"),
                        "description": description,
                        "tokens": tokens,
                        "type": tx_type,
                        "status": "Confirmed",
                        "partner": params.get('partnerName', ''),
                        "block": i
                    })
                    
                    if len(txs) >= num_transactions:
                        return txs
        
        return txs
    except Exception as e:
        st.error(f"Error fetching transactions: {str(e)}")
        return []
# Set page config
st.set_page_config(page_title="Token Rewards Portal", page_icon="🪙", layout="wide")

# Define fixed TKN to USD conversion rate
TKN_TO_USD = 0.54

# Connect to local Ganache blockchain
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
if not w3.is_connected():
    st.error("Failed to connect to local blockchain. Ensure Ganache is running on port 8545.")
    st.stop()

# Load contract ABI and address from Truffle build
with open("build/contracts/TKNToken.json") as f:
    contract_data = json.load(f)
CONTRACT_ADDRESS = "0x561a10113D03852281d895E58bAb24a786c90300"  # Confirm this matches your latest deployment
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_data["abi"])

# Custom CSS for styling with black background and white text
st.markdown(
    """
    <style>
    .main {
        background-color: #000000;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
        background-color: #333333;
        color: #ffffff;
    }
    .token-card {
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background-color: #1a1a1a;
        box-shadow: 0 2px 4px rgba(255,255,255,0.1);
        color: #ffffff;
    }
    .header {
        color: #ffffff;
    }
    .highlight {
        color: #4CAF50;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #1a1a1a;
        border-radius: 10px 10px 0 0;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .donation-card {
        border: 1px solid #444;
        padding: 15px;
        border-radius: 8px;
        background-color: #222;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state for wallet and balance
if "wallet_address" not in st.session_state:
    st.session_state.wallet_address = None
if "balance" not in st.session_state:
    st.session_state.balance = 0

# Mock data for transactions and partners
def generate_mock_data():
    transactions = []
    for i in range(20):
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        transactions.append(
            {
                "Date": date.strftime("%Y-%m-%d"),
                "Description": random.choice(
                    ["Purchase Reward", "Referral Bonus", "Engagement Reward", "Partner Bonus"]
                ),
                "Tokens": random.randint(5, 100),
                "Status": random.choice(["Confirmed", "Pending"]),
                "Partner": random.choice(["Main Store", "Amazon", "Apple", "Xbox", None]),
                "Type": random.choice(["Earned", "Spent", "Donated"])
            }
        )
    partners = [
        {"name": "Amazon Gift Coupon", "description": "E-Commerce", "discount": "30% off + free shipping"},
        {"name": "Apple Store Gift Card", "description": "Tech Store", "discount": "50$ off on apple products"},
        {"name": "Xbox", "description": "Gaming", "discount": "15% off on adventures"},
    ]
    return {"transactions": transactions, "partners": partners}

data = generate_mock_data()

# Wallet connection
# st.sidebar.subheader("Wallet Connection")
# ganache_accounts = w3.eth.accounts  # Get accounts from Ganache
# selected_account = st.sidebar.selectbox("Select Wallet", ganache_accounts)
# if st.sidebar.button("Connect Wallet"):
#     st.session_state.wallet_address = selected_account
#     try:
#         balance = contract.functions.balanceOf(selected_account).call() / 10**18
#         st.session_state.balance = balance
#         st.sidebar.success(f"Connected: {selected_account[:6]}...{selected_account[-4:]}")
#     except Exception as e:
#         st.sidebar.error(f"Error fetching balance: {str(e)}")

# Header with balance
st.markdown(
    """
<style>
.header-container {
    position: relative;
    width: 100%;
    height: 200px;
    margin-bottom: 30px;
    overflow: hidden;
    border-radius: 15px;
}
.header-banner {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.5;
    z-index: 0;
}
.header-content {
    position: relative;
    z-index: 1;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 100%;
}
.title-text {
    font-size: 80px;
    color: white;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
    margin: 0;
}
.balance-box {
    background-color: rgba(26, 26, 26, 0.7);
    padding: 15px 25px;
    border-radius: 10px;
    text-align: right;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="header-container">
    <img class="header-banner" src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNm5pZnM4ZDhvYjFqZ2EyN2czeGt6MWlvNXI3bGtsNnhreTd3MWhvdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/7SHF5dpGlltj4bwqFY/giphy.gif">
    <div class="header-content">
        <h1 class="title-text">Earn♾️finity</h1>
        <div class="balance-box">
            <h3 style='margin-bottom: 5px;'>Your Balance</h3>
            <h1 class="highlight" style='font-size: 32px; margin-top: 0;'>{st.session_state.balance} TKN</h1>
            <small>Wallet: {st.session_state.wallet_address[:6] + "..." + st.session_state.wallet_address[-4:] if st.session_state.wallet_address else "Not Connected"}</small>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# Tabs styling
st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        padding: 6px 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 25px;
        font-size: 18px;
        font-weight: 500;
        background-color: #1a1a1a;
        border-radius: 10px 10px 0 0;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #333333;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
        font-size: 18px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Dashboard", "💰 Earn Tokens", "🛒 Redeem Tokens", "🤝 Partner Network", "⚙️ Wallet Settings"])

with tab1:
    # Price chart and metrics (keep existing)
    def generate_price_data():
        random.seed(42)
        now = datetime.now()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        time_points = [start_time + timedelta(minutes=15 * i) for i in range(96)]
        base_price = TKN_TO_USD
        prices = [base_price]
        for _ in range(95):
            change = random.uniform(-0.005, 0.005)
            new_price = max(0.49, min(0.59, prices[-1] + change))
            prices.append(new_price)
        return pd.DataFrame({"Time": [t.strftime("%H:%M") for t in time_points], "Price (USD)": prices, "Volume": [random.randint(1000, 50000) for _ in range(96)]})

    price_data = generate_price_data()
    st.markdown("### TKN/USD Price Today")
    price_chart = px.line(price_data, x="Time", y="Price (USD)", title="", labels={"Price (USD)": "Price (USD)", "Time": "Time"}, template="plotly_dark")
    price_chart.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#333333"), margin=dict(l=20, r=20, t=30, b=20), height=300, hovermode="x unified")
    price_chart.add_bar(x=price_data["Time"], y=price_data["Volume"], name="Volume", marker_color="#4CAF50", opacity=0.3, yaxis="y2")
    price_chart.update_layout(yaxis2=dict(title="Volume", overlaying="y", side="right", showgrid=False))
    st.plotly_chart(price_chart, use_container_width=True)

    current_price = TKN_TO_USD
    price_change_24h = price_data["Price (USD)"].iloc[-1] - price_data["Price (USD)"].iloc[0]
    percent_change = (price_change_24h / price_data["Price (USD)"].iloc[0]) * 100
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        st.metric("24h Change", f"${price_change_24h:.4f}", f"{percent_change:.2f}%")
    with col3:
        st.metric("24h Volume", f"${price_data['Volume'].sum():,}")

    st.markdown("---")
    st.subheader("Recent Transactions")

    if not st.session_state.wallet_address:
        st.warning("Please connect your wallet to view transactions")
    else:
        blockchain_txs = get_transaction_history(st.session_state.wallet_address, contract, 10)
        
        if not blockchain_txs:
            st.info("No blockchain transactions found for this wallet")
        else:
            for tx in blockchain_txs:
                # Combined transaction component with expandable details
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{tx['description']}**")
                        st.caption(f"{tx['date']} • Block {tx['block']}")
                    with col2:
                        st.markdown(f"<h3 style='color: {'#4CAF50' if tx['tokens'] > 0 else '#f44336'}; text-align: right;'>{'+' if tx['tokens'] > 0 else ''}{abs(tx['tokens']):.2f} TKN</h3>", unsafe_allow_html=True)
                        st.caption(f"{tx['status']} • {tx['type']}", help="Transaction status and type")
                    
                    # Expandable details section
                    with st.expander("View transaction details", expanded=False):
                        try:
                            full_tx = w3.eth.get_transaction(tx['hash'])
                            receipt = w3.eth.get_transaction_receipt(tx['hash'])
                            block = w3.eth.get_block(full_tx['blockNumber'])
                            
                            st.markdown(f"""
                            **Transaction Hash:** `{tx['hash']}`  
                            **Block Number:** {full_tx['blockNumber']}  
                            **Block Time:** {datetime.fromtimestamp(block['timestamp']).strftime('%a %b %d %Y %H:%M:%S GMT%z')}  
                            **From:** `{full_tx['from']}`  
                            **To:** `{full_tx['to']}`  
                            **Contract Created:** `{receipt['contractAddress'] if receipt['contractAddress'] else 'None'}`  
                            **Gas Used:** {receipt['gasUsed']}  
                            **Gas Price:** {w3.from_wei(full_tx['gasPrice'], 'gwei'):.2f} Gwei  
                            **Value:** {w3.from_wei(full_tx['value'], 'ether')} ETH  
                            **Nonce:** {full_tx['nonce']}  
                            **Transaction Index:** {receipt['transactionIndex']}  
                            **Status:** {'✅ Success' if receipt['status'] == 1 else '❌ Failed'}  
                            """)
                            
                            if full_tx['input'] and full_tx['input'] != '0x':
                                try:
                                    func_obj = contract.decode_function_input(full_tx['input'])
                                    st.markdown("**Function Called:**")
                                    st.code(f"""
                                    {func_obj[0].fn_name}
                                    {json.dumps(func_obj[1], indent=4)}
                                    """)
                                except Exception as e:
                                    st.markdown("**Raw Input Data:**")
                                    st.code(full_tx['input'])
                        except Exception as e:
                            st.error(f"Error loading transaction details: {str(e)}")
                    
                    st.markdown("---")

    # Token metrics (without current balance)
    if st.session_state.wallet_address:
        st.subheader("Your Progress")
        col1, col2 = st.columns(2)
        
        try:
            # Calculate earned and spent from blockchain
            earned = sum(tx['tokens'] for tx in blockchain_txs if tx['tokens'] > 0) if blockchain_txs else 0
            spent = sum(abs(tx['tokens']) for tx in blockchain_txs if tx['type'] == 'Spent') if blockchain_txs else 0
            
            with col1:
                st.metric("Total Earned", f"{earned:.2f} TKN", f"${earned * TKN_TO_USD:.2f}")
            with col2:
                st.metric("Total Spent", f"{spent:.2f} TKN", f"${spent * TKN_TO_USD:.2f}")
        except Exception as e:
            st.error(f"Error calculating token metrics: {str(e)}")

    # Token activity chart
    if st.session_state.wallet_address and blockchain_txs:
        st.subheader("Token Activity")
        summary_data = pd.DataFrame({
            "Category": ["Earned", "Spent"],
            "Tokens": [
                sum(tx['tokens'] for tx in blockchain_txs if tx['tokens'] > 0),
                sum(abs(tx['tokens']) for tx in blockchain_txs if tx['type'] == 'Spent')
            ],
            "Color": ["#4CAF50", "#F44336"]
        })
        
        fig = px.bar(summary_data, 
                    x="Category", 
                    y="Tokens",
                    color="Color",
                    color_discrete_map="identity",
                    title="",
                    text="Tokens",
                    labels={"Tokens": "Token Amount", "Category": ""})
        
        fig.update_traces(texttemplate='%{y:.2f} TKN', textposition='outside')
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white",
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=False),
            margin=dict(t=30, b=20, l=20, r=20),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown(
        """
    <div class="token-card">
        <h3>🛍️ Make Purchases</h3>
        <p>Earn 5 TKN for every $10 spent at our store or partner locations.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

    if "item_quantities" not in st.session_state:
        st.session_state.item_quantities = {"T-Shirt": 0, "Headphones": 0, "Sneakers": 0, "Backpack": 0, "Smartwatch": 0, "Sunglasses": 0}

    st.markdown(
        """
    <div style="background-color: #808080; padding: 5px; border-radius: 15px; width: 100%; color: #ffffff; margin-top: 5px; margin-bottom: 5px;">
        <h2 style="text-align: center; font-size: 36px; margin-bottom: 30px; margin-top: 30px;"><b>OUR PRODUCTS</b></h2>
    """,
        unsafe_allow_html=True,
    )

    items = [
        {"name": "T-Shirt", "price_usd": 20,  "img": "https://cyberriedstore.com/wp-content/uploads/2024/04/royal-challengers-Banglore9rcb-virat-kohli-jersey-number-18-printed-front.png"},
        {"name": "Headphones", "price_usd": 50,  "img": "https://i5.walmartimages.com/asr/43b4d325-d149-432d-8af2-a0d4adf6e5e1_1.7d4b30a4a0bc8a4e656e55e2abccc219.png"},
        {"name": "Sneakers", "price_usd": 80,  "img": "https://th.bing.com/th/id/R.2546c72e7cccbe85b7a0d6e674fbb614?rik=rnCy1ZkBoRfJaA&riu=http%3a%2f%2fwww.pngall.com%2fwp-content%2fuploads%2f2%2fWhite-Sneakers-PNG.png&ehk=TkP0Gpxb4ofY0BOIuGgk2lo05h25%2fmceW6jn5XXB%2fHE%3d&risl=&pid=ImgRaw&r=0"},
        {"name": "Backpack", "price_usd": 30,  "img": "https://www.pngmart.com/files/15/Red-Sports-Backpack-PNG-Transparent-Image.png"},
        {"name": "Smartwatch", "price_usd": 100,  "img": "https://www.pngmart.com/files/13/GPS-Smartwatch-PNG-Image.png"},
        {"name": "Sunglasses", "price_usd": 25,  "img": "https://www.pngmart.com/files/20/Picart-Sunglasses-PNG-Isolated-Pic.png"},
    ]

    st.markdown(
        """
    <style>
    .item-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 370px;
        margin-bottom: 25px;
        background-color: #222222;
        border-radius: 12px;
        padding: 15px;
        transition: transform 0.3s;
    }
    .item-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    .item-image-container {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        width: 100%;
    }
    .item-image {
        max-width: 100%;
        max-height: 200px;
        object-fit: contain;
    }
    .item-details {
        text-align: center;
        width: 100%;
    }
    .item-name {
        font-size: 18px;
        margin: 10px 0 5px;
        text-transform: uppercase;
        font-weight: bold;
    }
    .item-price {
        font-size: 16px;
        margin-bottom: 12px;
        color: #4CAF50;
    }
    .quantity-display {
        width: 40px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        background-color: #333;
        padding: 5px 0;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    cols = st.columns(3)
    for i, item in enumerate(items):
        with cols[i % 3]:
            st.markdown(
                f"""
            <div class="item-card">
                <div class="item-image-container">
                    <img src="{item['img']}" class="item-image">
                </div>
                <div class="item-details">
                    <p class="item-name">{item['name']}</p>
                    <p class="item-price">${item['price_usd']}</p>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            qty_cols = st.columns([1, 1, 1])
            with qty_cols[0]:
                if st.button("➖", key=f"minus_{item['name']}", use_container_width=True):
                    if st.session_state.item_quantities[item["name"]] > 0:
                        st.session_state.item_quantities[item["name"]] -= 1
                        st.rerun()
            with qty_cols[1]:
                st.markdown(f'<div style="display: flex; justify-content: center; align-items: center; height: 36px;"><div class="quantity-display">{st.session_state.item_quantities[item["name"]]}</div></div>', unsafe_allow_html=True)
            with qty_cols[2]:
                if st.button("➕", key=f"plus_{item['name']}", use_container_width=True):
                    st.session_state.item_quantities[item["name"]] += 1
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    button_col1, button_col2, button_col3 = st.columns([1, 3, 1])
    with button_col2:
        if st.button("🛒 Buy Selected Items", key="buy_items", use_container_width=True, type="primary"):
            if not st.session_state.wallet_address:
                st.error("Please connect a wallet first!")
            else:
                selected_items = {item: qty for item, qty in st.session_state.item_quantities.items() if qty > 0}
                if selected_items:
                    total_usd = sum(item["price_usd"] * st.session_state.item_quantities[item["name"]] for item in items if st.session_state.item_quantities[item["name"]] > 0)
                    total_tkn = round(total_usd / TKN_TO_USD)  # Approximate total TKN cost (for display only)
                # Match the contract's reward calculation: 5 TKN per $10 spent, adjusted by TKN_TO_USD
                    usd_spent_cents = int(total_usd * 100)
                    tokens_earned = (usd_spent_cents * 5) / (1000 * TKN_TO_USD)  # No 10**18 since we want human-readable TKN
                    try:
                        tx = contract.functions.rewardPurchase(st.session_state.wallet_address, usd_spent_cents).transact({"from": st.session_state.wallet_address})
                        w3.eth.wait_for_transaction_receipt(tx)
                        st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                        st.success(f"Purchase successful! Total: ${total_usd:.2f}. You earned {tokens_earned:.2f} TKN! Updating in 5 seconds...")
                        st.session_state.item_quantities = {item: 0 for item in st.session_state.item_quantities}
                        data["transactions"].append({
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Description": "Purchase Reward",
                        "Tokens": tokens_earned,
                        "Status": "Confirmed",
                        "Partner": "Main Store",
                        "Type": "Earned"
                        })
                        time.sleep(5)  # Wait for 3 seconds
                        st.rerun()  # Rerun the app to update the UI
                    except Exception as e:
                        st.error(f"Transaction failed: {str(e)}")
                else:
                    st.warning("Please select at least one item!")

import streamlit as st
import time
from datetime import datetime

# Dummy conversion rates (USD is fixed, others are placeholders)
TKN_TO_USD = 0.25  # Fixed rate: 1 TKN = $0.25
TKN_TO_ETH = 0.0001  # Dummy rate: 1 TKN = 0.0001 ETH
TKN_TO_BTC = 0.00001  # Dummy rate: 1 TKN = 0.00001 BTC

with tab3:
    st.subheader("Redeem Your Tokens")
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        # Convert Tokens Section
        with st.container():
            st.markdown("### 📁 Convert Tokens")
            st.markdown("Exchange your tokens to other currencies")
            
            amount = st.number_input("Amount to convert", min_value=1.0, value=100.0, step=1.0, key="convert_amount")
            
            col_from, col_to = st.columns(2)
            with col_from:
                from_currency = st.selectbox("From", ["TKN"], key="from_currency")
            with col_to:
                to_currency = st.selectbox("To", ["USD"], key="to_currency")
            
            # Calculate conversion
            if from_currency == "TKN":
                if to_currency == "USD":
                    converted_amount = amount * TKN_TO_USD
                    fee = amount * 0.01  # 1% fee
                    st.markdown(f"""
                    **Conversion Rate:** 1 TKN = ${TKN_TO_USD:.2f}  
                    **You'll Receive:** ${converted_amount - fee:.2f}  
                    **Fee (1%):** {fee:.2f} TKN
                    """)
                elif to_currency == "ETH":
                    converted_amount = amount * TKN_TO_ETH
                    fee = amount * 0.01  # 1% fee
                    st.markdown(f"""
                    **Conversion Rate:** 1 TKN = {TKN_TO_ETH:.6f} ETH  
                    **You'll Receive:** {converted_amount - fee:.6f} ETH  
                    **Fee (1%):** {fee:.2f} TKN
                    """)
                elif to_currency == "BTC":
                    converted_amount = amount * TKN_TO_BTC
                    fee = amount * 0.01  # 1% fee
                    st.markdown(f"""
                    **Conversion Rate:** 1 TKN = {TKN_TO_BTC:.8f} BTC  
                    **You'll Receive:** {converted_amount - fee:.8f} BTC  
                    **Fee (1%):** {fee:.2f} TKN
                    """)
            
            if st.button("Convert Now", key="convert_now", 
                        disabled=not st.session_state.wallet_address,
                        help="Connect wallet to convert tokens" if not st.session_state.wallet_address else None):
                try:
                    # In a real implementation, you would call a conversion function here
                    st.success(f"Converted {amount} TKN to {converted_amount - fee:.6f} {to_currency}")
                    data["transactions"].append({
                        "Date": datetime.now().strftime("%Y-%m-%d"),
                        "Description": f"Converted to {to_currency}",
                        "Tokens": -amount,
                        "Status": "Confirmed",
                        "Partner": "",
                        "Type": "Spent"
                    })
                    
                except Exception as e:
                    st.error(f"Conversion failed: {str(e)}")

        # Premium Experiences Section
        with st.container():
            st.markdown("### 🎟️ Premium Experiences")
            st.markdown("Redeem tokens for exclusive access")
            
            # VIP Event Pass
            with st.expander("VIP Event Pass - 750 TKN"):
                st.markdown("Access to exclusive virtual events with special guests")
                st.markdown(f"**Value:** ${750 * TKN_TO_USD:.2f}")
                
                if st.button("Redeem VIP Pass", key="redeem_vip"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= 750:
                        try:
                            tx = contract.functions.burn(750 * 10**18, "VIP Event Pass").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success("VIP Event Pass redeemed successfully!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "VIP Event Pass Redemption",
                                "Tokens": -750,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Spent"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Redemption failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")
            
            # Early Product Access
            with st.expander("Early Product Access - 500 TKN"):
                st.markdown("Get new products 1 week before public release")
                st.markdown(f"**Value:** ${500 * TKN_TO_USD:.2f}")
                
                if st.button("Redeem Early Access", key="redeem_early"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= 500:
                        try:
                            tx = contract.functions.burn(500 * 10**18, "Early Product Access").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success("Early Product Access redeemed successfully!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "Early Product Access Redemption",
                                "Tokens": -500,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Spent"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Redemption failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")

    with col2:
        # Digital Collectibles Section
        with st.container():
            st.markdown("### 🎨 Digital Collectibles")
            st.markdown("Redeem for exclusive NFTs and profile customizations")
            
            # Art NFT
            with st.expander("Art NFT - 300 TKN"):
                st.image("https://img.freepik.com/premium-photo/digital-art-selected-greek-statute_483949-136.jpg", width=200)
                st.markdown(f"**Value:** ${300 * TKN_TO_USD:.2f}")
                
                if st.button("Redeem Art NFT", key="redeem_art"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= 300:
                        try:
                            tx = contract.functions.burn(300 * 10**18, "Art NFT").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success("Art NFT redeemed successfully!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "Art NFT Redemption",
                                "Tokens": -300,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Spent"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Redemption failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")
            
            # Gaming NFT
            with st.expander("Gaming NFT - 150 TKN"):
                st.image("https://pics.craiyon.com/2023-09-23/00f91fdc87fb48eca89d4ffb1aaf2b14.webp", width=200)
                st.markdown(f"**Value:** ${150 * TKN_TO_USD:.2f}")
                
                if st.button("Redeem Gaming NFT", key="redeem_game"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= 150:
                        try:
                            tx = contract.functions.burn(150 * 10**18, "Gaming NFT").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success("Gaming NFT redeemed successfully!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "Gaming NFT Redemption",
                                "Tokens": -150,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Spent"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Redemption failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")

        # Token Donations Section
        with st.container():
            st.markdown("### 🌱 Token Donations")
            st.markdown("Support causes you care about")
            
            # Environmental Causes
            with st.expander("Environmental Causes"):
                st.image("https://webneel.com/daily/sites/default/files/images/daily/06-2016/6-tree-drawing-by-serhii-liakhevych.jpg", width=100)
                st.markdown("Support tree planting and conservation efforts")
                env_amount = st.number_input("Amount (TKN)", min_value=1, max_value=1000, value=50, key="env_amount")
                
                if st.button("Donate to Environment", key="donate_env"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= env_amount:
                        try:
                            tx = contract.functions.burn(env_amount * 10**18, "Environmental Donation").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success(f"Donated {env_amount} TKN to Environmental Causes!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-d"),
                                "Description": "Environmental Donation",
                                "Tokens": -env_amount,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Donated"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Donation failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")
            
            # Education
            with st.expander("Education"):
                st.image("https://assets.thehansindia.com/h-upload/2022/07/31/1305709-education.jpg", width=100)
                st.markdown("Contribute to schools and learning programs")
                edu_amount = st.number_input("Amount (TKN)", min_value=1, max_value=1000, value=50, key="edu_amount")
                
                if st.button("Donate to Education", key="donate_edu"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= edu_amount:
                        try:
                            tx = contract.functions.burn(edu_amount * 10**18, "Education Donation").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success(f"Donated {edu_amount} TKN to Education!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "Education Donation",
                                "Tokens": -edu_amount,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Donated"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Donation failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")
            
            # Health Research
            with st.expander("Health Research"):
                st.image("https://static.vecteezy.com/system/resources/previews/020/296/495/non_2x/health-and-wellness-logo-design-template-free-free-vector.jpg", width=100)
                st.markdown("Fund medical research and breakthroughs")
                health_amount = st.number_input("Amount (TKN)", min_value=1, max_value=1000, value=50, key="health_amount")
                
                if st.button("Donate to Health", key="donate_health"):
                    if not st.session_state.wallet_address:
                        st.error("Please connect a wallet first!")
                    elif st.session_state.balance >= health_amount:
                        try:
                            tx = contract.functions.burn(health_amount * 10**18, "Health Donation").transact({"from": st.session_state.wallet_address})
                            w3.eth.wait_for_transaction_receipt(tx)
                            st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                            st.success(f"Donated {health_amount} TKN to Health Research!")
                            data["transactions"].append({
                                "Date": datetime.now().strftime("%Y-%m-%d"),
                                "Description": "Health Donation",
                                "Tokens": -health_amount,
                                "Status": "Confirmed",
                                "Partner": "",
                                "Type": "Donated"
                            })
                            time.sleep(3)  # Wait 3 seconds
                            st.rerun()  # Rerun the app
                        except Exception as e:
                            st.error(f"Donation failed: {str(e)}")
                    else:
                        st.error("Insufficient balance!")

with tab4:
    st.subheader("Partner Network")
    st.markdown(
        """
    <p>Use your tokens across our partner network. All partners accept TKN tokens for discounts and special offers.</p>
    """,
        unsafe_allow_html=True,
    )
    for partner in data["partners"]:
        st.markdown(
            f"""
        <div class="token-card">
            <div style="display: flex; gap: 20px;">
                <img src="{['https://th.bing.com/th/id/R.45b0e69add05f7cdbee40cc9997bd7b4?rik=tXf%2fiMSa7boX3g&riu=http%3a%2f%2flofrev.net%2fwp-content%2fphotos%2f2016%2f06%2famazon-logo-1.png&ehk=ideqrZcqNA%2f4jGcxPjOuRtmkvXlfeBZu%2fgCoZDUbApg%3d&risl=&pid=ImgRaw&r=0', 'https://cdn.topuplive.com/uploads/images/goods/20230419/1681884478_7Y7cRk9ww7.png', 'https://static.vecteezy.com/system/resources/previews/018/970/091/original/xbox-black-logo-symbol-free-vector.jpg'][data['partners'].index(partner)]}" width="100" height="100" style="border-radius: 5px;">
                <div style="flex-grow: 1;">
                    <h3>{partner['name']}</h3>
                    <p>{partner['description']}</p>
                    <p><strong>Special Offer:</strong> {partner['discount']}</p>
                </div>
                <div style="display: flex; align-items: center;">
                    <button style="background-color: #101010; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;"> {600 if partner['name'] == 'Amazon Gift Coupon' else 800 if partner['name'] == 'Apple Store Gift Card' else 500} TKN (${(600 if partner['name'] == 'Amazon Gift Coupon' else 800 if partner['name'] == 'Apple Store Gift Card' else 500) * TKN_TO_USD:.2f})</button>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        
        if st.button(f"Redeem {partner['name']}", key=f"redeem_{partner['name']}"):
            if not st.session_state.wallet_address:
                st.error("Please connect a wallet first!")
            else:
                required_tokens = 600 if partner['name'] == 'Amazon Gift Coupon' else 800 if partner['name'] == 'Apple Store Gift Card' else 500
                if st.session_state.balance >= required_tokens:
                    try:
                        tx = contract.functions.redeemPartnerReward(
                            st.session_state.wallet_address,
                            required_tokens * 10**18,
                            partner['name']
                        ).transact({"from": st.session_state.wallet_address})
                        w3.eth.wait_for_transaction_receipt(tx)
                        st.session_state.balance = contract.functions.balanceOf(st.session_state.wallet_address).call() / 10**18
                        st.success(f"Successfully redeemed {partner['name']} offer!")
                        data["transactions"].append({
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Description": f"Partner Redemption: {partner['name']}",
                            "Tokens": -required_tokens,
                            "Status": "Confirmed",
                            "Partner": partner['name'],
                            "Type": "Spent"
                        })
                        
                        # Add a delay and rerun
                        time.sleep(3)
                        st.experimental_rerun()
                        
                    except Exception as e:
                        st.error(f"Redemption failed: {str(e)}")
                else:
                    st.error(f"Insufficient balance! You need {required_tokens} TKN for this redemption.")

with tab5:
    st.subheader("Wallet Settings")
    
    # Wallet Connection Section
    st.markdown("### Wallet Connection")
    
    if not st.session_state.wallet_address:
        ganache_accounts = w3.eth.accounts
        selected_account = st.selectbox("Select Wallet", ganache_accounts)
        
        if st.button("Connect Wallet"):
            st.session_state.wallet_address = selected_account
            try:
                balance = contract.functions.balanceOf(selected_account).call() / 10**18
                st.session_state.balance = balance
                st.success(f"Connected: {selected_account[:6]}...{selected_account[-4:]}")
                st.rerun()  # Refresh to show connected state
            except Exception as e:
                st.error(f"Error fetching balance: {str(e)}")
    else:
        st.success(f"Wallet Connected: {st.session_state.wallet_address[:6]}...{st.session_state.wallet_address[-4:]}")
        if st.button("Disconnect Wallet"):
            st.session_state.wallet_address = None
            st.session_state.balance = 0
            st.rerun()  # Refresh to show disconnected state
    
    # Only show other settings if wallet is connected
    if st.session_state.wallet_address:
        with st.form("wallet_settings_form"):
            st.markdown("### Wallet Information")
            current_address = st.text_input("Wallet Address", value=st.session_state.wallet_address, disabled=True)
            
            st.markdown("### Security")
            enable_2fa = st.checkbox("Enable Two-Factor Authentication")
            notification_pref = st.selectbox("Notification Preferences", ["All notifications", "Only large transactions", "None"])
            
            st.markdown("### Connected Accounts")
            st.checkbox("Link to MetaMask", value=True)
            st.checkbox("Link to Coinbase Wallet")
            st.checkbox("Link to Trust Wallet")
            
            if st.form_submit_button("Save Settings"):
                st.success("Settings updated successfully!")

# Footer
st.markdown("---")
st.markdown(
    """
<div style="text-align: center; color: #777; font-size: 0.9em;">
    <p>Token Rewards Portal • Powered by Blockchain Technology</p>
    <p>Need help? Contact support@tokenrewards.com</p>
</div>
""",
    unsafe_allow_html=True,
)