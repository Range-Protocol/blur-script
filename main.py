import json
import sys

from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

whitelisted_functions = ["refinanceAuction", "startAuction", "seize", "getCurrentDebtByLien",
	"getRefinancingAuctionRate", "getVaultBalance", "cleanup"]

requires_calldata = {
	"refinanceAuction": True,
	"startAuction": True,
	"seize": True,
	"getCurrentDebtByLien": False,
	"getRefinancingAuctionRate": False,
	"getVaultBalance": False,
	"cleanup": False
}

function_name = sys.argv[1]
if function_name not in whitelisted_functions:
	raise Exception("function not found")

pk = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
rpc = {"mainnet": "https://eth.llamarpc.com", "localhost": "http://127.0.0.1:8545"}

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
if requires_calldata[function_name]:
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
