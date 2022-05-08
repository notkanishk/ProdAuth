// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

contract ProdAuth {
    address[] ownersG;
    enum Status { forSale, sold }
    struct Article {
        string asin;
        address[] owners;
        address soldTo;
        Status status;
        bool exists;
    }

    string[] articlesOwnedG;
    struct Owner {
        string name;
        string[] articlesOwned;
        bool exists;
    }

    // string[] articlesSellingG;
    string[] articlesSoldG;
    struct Seller {
        string name;
        // string[] articlesSelling;
        string[] articlesSold;
        bool exists;
    }

    mapping (string => Article) articlesList;
    mapping (address => Owner) ownersList;
    mapping (address => Seller) sellersList;

    function registerSeller(string memory name) public payable {
        address addr = tx.origin;
        require (sellersList[addr].exists == false, "Seller already exists");
        Seller memory newSeller;
        newSeller.name = name;
        newSeller.exists = true;
        sellersList[addr] = newSeller;
    }

    function registerOwner(string memory name) public payable {
        address addr = tx.origin;
        require (ownersList[addr].exists == false, "Owner already exists");
        Owner memory newOwner;
        newOwner.name = name;
        newOwner.exists = true;
        ownersList[addr] = newOwner;
    }

    function newArticle(string memory itemId, string memory asin) public payable {
        address sellerId = tx.origin;
        require (sellersList[sellerId].exists == true, "Please register as a seller first!");
        require (articlesList[itemId].exists == false, "Article already exists!");
        ownersG.push(tx.origin);
        Article memory newItem;
        newItem.asin = asin;
        newItem.owners = ownersG;
        newItem.status = Status.forSale;
        newItem.exists = true;
        articlesList[itemId] = newItem;
        delete ownersG;
        // articlesSellingG.push(itemId);
        // sellersList[sellerId].articlesSelling = articlesSellingG;
        // delete articlesSellingG;
    }

    function initSold(string memory itemId, address buyerId) public payable {
        address sellerId = tx.origin;
        require (sellersList[sellerId].exists == true, "Please register as a seller first!");
        require (ownersList[buyerId].exists == true, "Buyer not registered!");
        require (articlesList[itemId].exists == true, "Article not found!");
        require (articlesList[itemId].status == Status.forSale, "Article not for sale!");
        require (articlesList[itemId].owners[articlesList[itemId].owners.length -1] == sellerId, "The seller does not own the article!");
        articlesList[itemId].status = Status.sold;
        articlesList[itemId].soldTo = buyerId;
    }

    function postVerification(string memory itemId, address sellerId, address buyerId) internal {
        ownersG = articlesList[itemId].owners;
        ownersG.push(buyerId);
        articlesList[itemId].owners = ownersG;
        delete ownersG;
        articlesOwnedG = ownersList[buyerId].articlesOwned;
        articlesOwnedG.push(itemId);
        ownersList[buyerId].articlesOwned = articlesOwnedG;
        delete articlesOwnedG;
        articlesSoldG = sellersList[sellerId].articlesSold;
        articlesSoldG.push(itemId);
        sellersList[sellerId].articlesSold = articlesSoldG;
        delete articlesSoldG;
        // articlesSellingG = sellersList[sellerId].articlesSelling;
        // articlesSellingG.remove(itemId);
        // sellersList[sellerId].articlesSelling = articlesSellingG;
        // delete articlesSellingG;
        articlesList[itemId].status = Status.forSale;
        articlesList[itemId].soldTo = address(0);
    }

    function verifyPurchase(string memory itemId, address sellerId) public payable returns (Article memory){
        address buyerId = tx.origin;
        require (ownersList[buyerId].exists == true, "Buyer not registered!");
        require (sellersList[sellerId].exists == true, "Seller not registered!");
        require (articlesList[itemId].exists == true, "Article not found!");
        require (articlesList[itemId].status == Status.sold, "Article not for sale!");
        require (articlesList[itemId].owners[articlesList[itemId].owners.length -1] == sellerId, "The seller does not own the article!");
        require (articlesList[itemId].soldTo == buyerId, "The article has not been sold to you!");
        postVerification(itemId, sellerId, buyerId);
        return articlesList[itemId];
    }

    function viewItem(string memory itemId) public view returns (Article memory){
        return articlesList[itemId];
    }

    function viewSeller(address sellerId) public view returns (Seller memory){
        return sellersList[sellerId];
    }
}