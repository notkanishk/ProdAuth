import os
from brownie import accounts, ProdAuth, web3
from dotenv import load_dotenv
load_dotenv()

# def main():
#     print("Deploying contracts...")
#     account = accounts[0]
#     print("Account:", account)
#     prodAuth = ProdAuth.deploy({"from": account})
    # transaction = prodAuth.newArticle("1","asdf",{"from": account})
    # transaction.wait(1)
    # saw = prodAuth.see("1").dict()
    # print(saw["owners"][0])



def main():
    print("Deploying contracts...")
    account = accounts.add(os.getenv("ACCOUNT_PRIVATE_KEY"))
    try:
        prodAuth = ProdAuth.deploy({"from": account})
        print("ProdAuth deployed at:", prodAuth.address)
    except Exception as e:
        print("error:", e)