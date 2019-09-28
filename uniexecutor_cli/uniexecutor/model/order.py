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
