from json import JSONEncoder, JSONDecoder

class Order:
    def __init__(self, fromToken, toToken, minReturn, fee, owner, secret, witness, tx):
        self.tx = tx
        self.fromToken = fromToken
        self.toToken = toToken
        self.minReturn = minReturn
        self.fee = fee
        self.owner = owner
        self.secret = secret
        self.witness = witness

    @staticmethod
    def fromList(data_list, tx=None):
        return Order(*data_list, tx)

    def __hash__(self):
        return int(self.tx, 16)

    def __eq__(self, other):
        return self.tx == other.tx

class OrderEncoder(JSONEncoder):
    def default(self, o):
        return {
            "tx": o.tx,
            "fromToken": o.fromToken,
            "toToken": o.toToken,
            "minReturn": o.minReturn,
            "fee": o.fee,
            "owner": o.owner,
            "secret": o.secret.hex(),
            "witness": o.witness
        }

class OrderDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)
    def object_hook(self, j):
        return Order(
            j["fromToken"],
            j["toToken"],
            j["minReturn"],
            j["fee"],
            j["owner"],
            bytes.fromhex(j["secret"]),
            j["witness"],
            j["tx"]
        )
