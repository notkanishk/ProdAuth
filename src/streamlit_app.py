from web3 import Web3, exceptions
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import qrcode
import io
import uuid
from pyzbar.pyzbar import decode
from pathlib import Path

# ============= DevEnv =============
import json

chain = "5777"
mapFilePath = Path(__file__).parent /'artifacts/deployments/map.json'

abiFilePath = Path(__file__).parent /'artifacts/deployments/{chain}/{contractAddress}.json'
with open(mapFilePath) as f:
  data = json.load(f)
contractAddress = data[chain]["ProdAuth"][0]

with open(abiFilePath) as f:
  data = json.load(f)
abi = data["abi"]


w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))

contract = w3.eth.contract(address=contractAddress, abi=abi)

# contract.all_functions()
# st.write(contract.all_functions())

# item = contract.functions.see("f176c109f74d4766b16410379ddbf5a4").call()

# st.write(item)
# st.session_state



# ============= Contract Interaction =============

def registerSeller():
    try:
        contract.functions.registerSeller(st.session_state.sellerName).transact({'from': st.session_state.sellerAddress})
        st.success("Seller registered successfully")
    except exceptions.SolidityError as e:
        st.error(e)

def registerBuyer():
    try:
        contract.functions.registerOwner(st.session_state.buyerName).transact({'from': st.session_state.buyerAddress})
        st.success("Buyer registered successfully")
    except exceptions.SolidityError as e:
        st.error(e)


def addProduct(uid):
    try:
        contract.functions.newArticle(str(uid), st.session_state.asin).transact({'from': st.session_state.sellerAddress})
        # st.success("Product added successfully")
    except exceptions.SolidityError as e:
        st.error(e)


def initSale():
    prodId = st.session_state.qrData if 'qrData' in st.session_state else st.session_state.sellerProductId
    try:
        contract.functions.initSold(prodId, st.session_state.receiverAddress).transact({'from': st.session_state.sellerAddress})
        st.success("Sale initiated successfully")
    except exceptions.SolidityError as e:
        st.error(e)

def verifyProduct():
    prodId = st.session_state.qrData if 'qrData' in st.session_state else st.session_state.buyerProductId
    try:
        contract.functions.verifyPurchase(prodId, st.session_state.senderAddress).transact({'from': st.session_state.buyerAddress})
        st.success("Product verified and ownership transferred successfully")
    except exceptions.SolidityError as e:
        st.error(e)


# ============= Helper Functions =============

def idGen():
    asin = st.session_state.asin
    uid = uuid.uuid4().hex
    asin = asin.encode().hex()
    uid = str(hex(int(uid, 16) + int(asin, 16))[2:])
    qrGen(uid)
    st.success("Product added successfully. Product ID: " + uid)
    addProduct(uid)


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
    st.image(output, width=300)
    # FIX: Clicking download refreshes state of the page
    st.download_button(
        label="Download QR Code",
        file_name="qr.png",
        data=output.getvalue(),
        mime="image/png",
    )


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
    st.header("Registration")
    with st.expander("Register as Seller"):
        if not st.session_state.sellerAddress:
            st.error("Please enter your Account Address")
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
    st.header("Registration")
    with st.expander("Register as Buyer"):
        if not st.session_state.buyerAddress:
            st.error("Please enter your Account Address")
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
    role = option_menu(
        "Select you Role",
        ["Seller", "Buyer"],
        default_index=0,
        orientation="horizontal",
    )
    if role == "Seller":
        sellerPage()
    elif role == "Buyer":
        buyerPage()



def homePage():
    st.title("Home Page")
    st.header("Welcome to the Product Marketplace")
    st.text("This is a demo of the Product Marketplace")
# ============= Main =================

with st.sidebar:
    page = option_menu(
        "Menu",
        ["Home", "FAQ", "ProdAuth"],
        default_index=0,
        # orientation="horizontal"
    )


if page == "Home":
    homePage()
elif page == "FAQ":
    st.title("FAQ")
    st.markdown("Hello world")
elif page == "ProdAuth":
    prodPgae()

