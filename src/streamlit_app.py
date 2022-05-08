from web3 import Web3
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import qrcode
import io
import uuid
from pyzbar.pyzbar import decode
from pathlib import Path
from dotenv import load_dotenv
import os
import json
from web3.middleware import construct_sign_and_send_raw_middleware

# ============= DevEnv =============

load_dotenv()
WEB3_INFURA_API_SECRET = os.getenv("WEB3_INFURA_API_SECRET")
WEB3_INFURA_PROJECT_ID = os.getenv("WEB3_INFURA_PROJECT_ID")

# chain = "5777"  # Local Blockchain

chain = "3" # Ropsten

mapFilePath = Path(__file__).parent /'artifacts/deployments/map.json'

with open(mapFilePath) as f:
  data = json.load(f)
contractAddress = data[chain]["ProdAuth"][0]

abiFilePath = Path(__file__).parent /f'artifacts/deployments/{chain}/{contractAddress}.json'

with open(abiFilePath) as f:
  data = json.load(f)
abi = data["abi"]


w3 = Web3(Web3.HTTPProvider(f'https://:{WEB3_INFURA_API_SECRET}@ropsten.infura.io/v3/{WEB3_INFURA_PROJECT_ID}'))

contract = w3.eth.contract(address=contractAddress, abi=abi)

# ============= Contract Interaction =============

def registerSeller():
    try:
        sellerAccount = w3.eth.account.from_key(st.session_state.sellerPrivateKey)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(sellerAccount))
        w3.eth.default_account = sellerAccount.address
        contract.functions.registerSeller(st.session_state.sellerName).transact({'from': sellerAccount.address})
        st.success("Seller registered successfully")
    except Exception as e:
        st.error(e)

def registerBuyer():
    try:
        buyerAccount = w3.eth.account.from_key(st.session_state.buyerPrivateKey)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(buyerAccount))
        w3.eth.default_account = buyerAccount.address
        contract.functions.registerOwner(st.session_state.buyerName).transact({'from': buyerAccount.address})
        st.success("Buyer registered successfully")
    except Exception as e:
        st.error(e)


def addProduct(uid, output):
    try:
        sellerAccount = w3.eth.account.from_key(st.session_state.sellerPrivateKey)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(sellerAccount))
        w3.eth.default_account = sellerAccount.address
        contract.functions.newArticle(str(uid), st.session_state.asin).transact({'from': sellerAccount.address})
        st.image(output, width=300)
        # FIX: Clicking download refreshes state of the page
        st.download_button(
            label="Download QR Code",
            file_name="qr.png",
            data=output.getvalue(),
            mime="image/png",
        )
        st.success("Product added successfully. Product ID: " + uid)
    except Exception as e:
        st.error(e)


def initSale():
    prodId = st.session_state.qrData if 'qrData' in st.session_state else st.session_state.sellerProductId
    try:
        sellerAccount = w3.eth.account.from_key(st.session_state.sellerPrivateKey)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(sellerAccount))
        w3.eth.default_account = sellerAccount.address
        contract.functions.initSold(prodId, st.session_state.receiverAddress).transact({'from': sellerAccount.address})
        st.success("Sale initiated successfully")
    except Exception as e:
        st.error(e)

def verifyProduct():
    prodId = st.session_state.qrData if 'qrData' in st.session_state else st.session_state.buyerProductId
    try:
        buyerAccount = w3.eth.account.from_key(st.session_state.buyerPrivateKey)
        w3.middleware_onion.add(construct_sign_and_send_raw_middleware(buyerAccount))
        w3.eth.default_account = buyerAccount.address
        contract.functions.verifyPurchase(prodId, st.session_state.senderAddress).transact({'from': buyerAccount.address})
        st.success("Product verified and ownership transferred successfully")
    except Exception as e:
        st.error(e)


# ============= Helper Functions =============

def idGen():
    asin = st.session_state.asin
    uid = uuid.uuid4().hex
    asin = asin.encode().hex()
    uid = str(hex(int(uid, 16) + int(asin, 16))[2:])
    qrGen(uid)


#  ============= QR Code Handling =============
def qrGen(uid):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uid)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    output = io.BytesIO()
    img.save(output, format="PNG")
    addProduct(uid, output)



def readQr(img):
    res = decode(img)
    try:
        data = res[0][0].decode("utf-8")
        st.session_state.qrData = data
        data
    except:
        st.error("QR Code not recognized")


#  ============= Page-lets =============


def expScanQR():
    qrImg = st.camera_input("")
    if qrImg is not None:
        img = Image.open(qrImg)
        readQr(img)


def expUploadQR():
    qrImg = st.file_uploader("", type=["png", "jpg", "jpeg"])
    if qrImg is not None:
        img = Image.open(qrImg)
        readQr(img)


#  ============= Pages =============


def sellerPage():
    st.title("Seller Page")
    st.text_input("Enter your Account Address", key="sellerAddress")
    st.text_input("Enter your Private Key", key="sellerPrivateKey", type="password")
    st.header("Registration")
    with st.expander("Register as Seller"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.sellerPrivateKey:
            st.error("Please enter your Private Key")
        else:
            st.text_input("Enter your name", key="sellerName")
            if st.button("Register"):
                if st.session_state.sellerName:
                    registerSeller()
                else:
                    st.error("Please enter your Name")


    st.header("Add Product to the network")
    with st.expander("Add your Product"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.sellerPrivateKey:
            st.error("Please enter your Private Key")
        else:
            st.text_input("Enter your Product ASIN", key="asin")
            if st.button("Add Product"):
                if st.session_state.asin:
                    idGen()
                else:
                    st.error("Please enter Product detail")


    st.header("Initiate a Sale")
    st.text_input("Please enter the Buyer's Account Address", key="receiverAddress")
    st.write("Select Product to be sold")
    with st.expander("Enter Product ID"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.sellerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.receiverAddress:
            st.error("Please enter the Buyer's Account Address")
        else:
            st.text_input("", key="sellerProductId")
            if st.button("Initiate Sale"):
                if st.session_state.sellerProductId:
                    initSale()
                else:
                    st.error("Please enter a Product ID")

    st.caption("Or")
    with st.expander("Scan Product QR Code"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.sellerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.receiverAddress:
            st.error("Please enter the Buyer's Account Address")
        else:
            expScanQR()
            if st.button("Initiate Sale", key="sScanQR"):
                if 'qrData' in st.session_state:
                    initSale()
                else:
                    st.error("Please scan a QR Code")

    st.caption("Or")
    with st.expander("Upload Product QR Code"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.sellerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.receiverAddress:
            st.error("Please enter the Buyer's Account Address")
        else:
            expUploadQR()
            if st.button("Initiate Sale", key="sUplQR"):
                if 'qrData' in st.session_state:
                    initSale()
                else:
                    st.error("Please upload a QR Code")


def buyerPage():
    st.title("Buyer Page")
    st.text_input("Enter your Account Address", key="buyerAddress")
    st.text_input("Enter your Private Key", key="buyerPrivateKey", type="password")
    st.header("Registration")
    with st.expander("Register as Buyer"):
        if not st.session_state.buyerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.buyerPrivateKey:
            st.error("Please enter your Private Key")
        else:
            st.text_input("Enter your name", key="buyerName")
            if st.button("Register"):
                if st.session_state.buyerName:
                    registerBuyer()
                else:
                    st.error("Please enter your Name")


    st.header("Verify your Product")
    st.text_input("Please enter the Seller's Account Address", key="senderAddress")
    st.write("Select Product to be verified")
    with st.expander("Enter Product ID"):
        if not st.session_state.buyerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.buyerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.senderAddress:
            st.error("Please enter the Seller's Account Address")
        else:
            st.text_input("", key="buyerProductId")
            if st.button("Verify Product"):
                if st.session_state.buyerProductId:
                    verifyProduct()
                else:
                    st.error("Please enter a Product ID")

    st.caption("Or")
    with st.expander("Scan QR Code"):
        if not st.session_state.buyerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.buyerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.senderAddress:
            st.error("Please enter the Seller's Account Address")
        else:
            expScanQR()
            if st.button("Verify Product", key="bScanQR"):
                if 'qrData' in st.session_state:
                    verifyProduct()
                else:
                    st.error("Please scan a QR Code")

    st.caption("Or")
    with st.expander("upload QR Code"):
        if not st.session_state.buyerAddress:
            st.error("Please enter your Account Address")
        elif not st.session_state.buyerPrivateKey:
            st.error("Please enter your Private Key")
        elif not st.session_state.senderAddress:
            st.error("Please enter the Seller's Account Address")
        else:
            expUploadQR()
            if st.button("Verify Product", key="bUplQR"):
                if 'qrData' in st.session_state:
                    verifyProduct()
                else:
                    st.error("Please upload a QR Code")


def prodPgae():
    st.header("ProdAuth")
    role = option_menu(
        "Select you Role",
        ["Seller", "Buyer"],
        icons=["person-plus", "person-check"],
        menu_icon="person",
        default_index=0,
        orientation="horizontal",
    )
    if role == "Seller":
        sellerPage()
    elif role == "Buyer":
        buyerPage()



def homePage():
    st.title("Home Page")
    st.header("Welcome to ProdAuth!")
    st.write("The motivation behind this project is to provide a decentralized authentication system for products. Online shopping is at the core of the industry and it is a very popular way to buy products. However, the current system is not secure and is not able to provide the necessary security to protect the authenticity of the products purchased.")
    st.write("This project provides a platform where the sellers can add their products and the buyers can verify the authenticity of the products. All the products are stored in a decentralized database and the sellers can verify the authenticity of the products by scanning the QR code or uploading the QR code.")
    st.write("The ownership history of the products is maintained and the ownership is only transfered to the inteded person who verifies the Product ID by scanning the QR code or uploading the QR code.")


def infoPage():
    st.title("Information")
    st.write("The main application is available on the third tab of the Main Menu.")

    st.header("For Seller:")
    st.write("1. Register as Seller")
    st.caption("Using your address and private key, you can register as a Seller.")
    st.write("2. Add Product")
    st.caption("Enter the product ASIN. This will add your product using a generated unique ID and give you a QR Code and the generated unique ID. You can engrave or attach this to your product before shipping it to the buyer.")
    st.write("3. Initiate Sale")
    st.caption("After the payment has been made and the product is to be shipped. Using the generated unique ID, and the buyer's address, you can initiate the sale mode of the product. This will put the product in _sold_ mode. Only the intended buyer will be able to scan the QR Code and verify the authenticy of the received product and then the ownership of the product will be changed to the buyer.")

    st.header("For Buyer:")
    st.write("1. Register as Buyer")
    st.caption("Using your address and private key, you can register as a Buyer.")
    st.write("2. Verify Product")
    st.caption("Using the seller's address, you can scan the QR Code or upload the QR Code to verify the authenticity of the product. Upon verification, the ownership of the product will be transferred to the buyer.")
# ============= Main =================

with st.sidebar:
    page = option_menu(
        "Menu",
        ["Home", "Information", "ProdAuth"],
        icons=["house", "info-circle", "app"],
        menu_icon="list",
        default_index=0,
        # orientation="horizontal"
    )


if page == "Home":
    homePage()
elif page == "Information":
    infoPage()
elif page == "ProdAuth":
    prodPgae()

