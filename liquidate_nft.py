def prepare_liquidate_data(eip712Domain, data):
	_, name, version, chain_id, verifying_contract, *_ = eip712Domain
	return {
		"types": {
			"EIP712Domain": [
				{"name": "name", "type": "string"},
				{"name": "version", "type": "string"},
				{"name": "chainId", "type": "uint256"},
				{"name": "verifyingContract", "type": "address"},
			],
			"LiquidateOrder": [
				{"name": "collection", "type": "address"},
				{"name": "tokenId", "type": "uint256"},
				{"name": "amount", "type": "uint256"},
				{"name": "recipient", "type": "address"},
				{"name": "nonce", "type": "uint256"},
				{"name": "deadline", "type": "uint256"},
			],
		},
		"primaryType": "LiquidateOrder",
		"domain": {
			"name": name,
			"version": version,
			"chainId": chain_id,
			"verifyingContract": verifying_contract,
		},
		"message": {
			"collection": data["collection"],
			"tokenId": data["tokenId"],
			"amount": data["amount"],
			"recipient": data["recipient"],
			"nonce": data["nonce"],
			"deadline": data["deadline"]
		},
	}
