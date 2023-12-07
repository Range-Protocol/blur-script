import json
import sys
import os

from dotenv import load_dotenv
load_dotenv()

from web3 import Web3
from eth_account.messages import encode_structured_data
from eth_account import Account
from web3.middleware import construct_sign_and_send_raw_middleware

from liquidate_nft import prepare_liquidate_data

whitelisted_functions = ["refinanceAuction", "startAuction", "seize", "getCurrentDebtByLien",
	"getRefinancingAuctionRate", "getVaultBalance", "cleanup", "liquidateNFT"]

requires_read_from_file = {
	"refinanceAuction": True,
	"startAuction": True,
	"seize": True,
	"getCurrentDebtByLien": False,
	"getRefinancingAuctionRate": False,
	"getVaultBalance": False,
	"cleanup": False,
	"liquidateNFT": True
}

function_name = sys.argv[1]
if function_name not in whitelisted_functions:
	raise Exception("function not found")

pk = os.getenv("PRIV_KEY")
rpc = {"mainnet": "https://eth-mainnet.g.alchemy.com/v2/CjYmaEKxlp-_BuTgFt22DeY3YlTQWY8O", "localhost": "http://127.0.0.1:8545"}

w3 = Web3(Web3.HTTPProvider(rpc["mainnet"]))
account = w3.eth.account.from_key(pk)
w3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))

file_abi = open("RangeProtocolBlurVault.json")
VAULT_ABI = json.load(file_abi)
vault_address = "0xeD72A71161258FC3Dc31e57650E2b464c69f4dC1"
vault_instance = w3.eth.contract(address=vault_address, abi=VAULT_ABI)

file_blur_pool_abi = open("BlurPool.json")
BLUR_POOL_ABI = json.load(file_blur_pool_abi)
blur_pool_address = "0x0000000000A39bb272e79075ade125fd351887Ac"
blur_pool_instance = w3.eth.contract(address=blur_pool_address, abi=BLUR_POOL_ABI)

nonce = w3.eth.get_transaction_count(account.address)

data = None
if requires_read_from_file[function_name]:
	f = open(f"transaction_calldata/{function_name}.json")
	data = json.load(f)
unsent_tx = None
return_data = None

if function_name == "refinanceAuction":
	unsent_tx = vault_instance.functions.refinanceAuction(
		data["lien"], data["lienId"], data["rate"]
	)
elif function_name == "startAuction":
	unsent_tx = vault_instance.functions.startAuction(data["lien"], data["lienId"])
elif function_name == "seize":
	unsent_tx = vault_instance.functions.seize(data["lienPointers"])
elif function_name == "getCurrentDebtByLien":
	return_data = vault_instance.functions.getCurrentDebtByLien(data["lien"], data["lienId"]).call()
elif function_name == "getRefinancingAuctionRate":
	return_data = vault_instance.functions.getRefinancingAuctionRate(data["lien"],
		data["lienId"]).call()
elif function_name == "getVaultBalance":
	return_data = blur_pool_instance.functions.balanceOf(vault_address).call() / 10 ** 18
elif function_name == "cleanup":
	unsent_tx = vault_instance.functions.cleanUpLiensArray()
elif function_name == "liquidateNFT":
	eip712Domain = vault_instance.functions.eip712Domain().call()
	message = encode_structured_data(prepare_liquidate_data(eip712Domain, data))
	signature = w3.eth.account.sign_message(message, account.key)["signature"].hex()
	return_data = signature
else:
	raise Exception("function not found")

if return_data is not None:
	print(return_data)
else:
	signed_tx = w3.eth.account.sign_transaction(
		unsent_tx.build_transaction(
			{"from": account.address, "nonce": nonce, "gasPrice": w3.eth.gas_price}
		),
		private_key=account.key,
	)
	tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
	print("Transaction hash: ", tx_hash.hex())
	w3.eth.wait_for_transaction_receipt((tx_hash))
