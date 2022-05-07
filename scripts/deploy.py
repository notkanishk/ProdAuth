from brownie import accounts, ProdAuth

def main():
    print("Deploying contracts...")
    account = accounts[0]
    print("Account:", account)
    prodAuth = ProdAuth.deploy({"from": account})
    # transaction = prodAuth.newArticle("1","asdf",{"from": account})
    # transaction.wait(1)
    # saw = prodAuth.see("1").dict()
    # print(saw["owners"][0])
