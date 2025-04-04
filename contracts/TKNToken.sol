// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TKNToken is ERC20, Ownable {
    uint256 constant TKN_TO_USD = 54; // 1 TKN = $0.54 (scaled by 100)
    
    struct Partner {
        string name;
        string description;
        uint256 discountRate;
        bool isActive;
    }
    
    struct Donation {
        address donor;
        uint256 amount;
        string cause;
        uint256 timestamp;
    }
    
    mapping(string => Partner) public partners;
    string[] public partnerNames;
    Donation[] public donations;
    
    // Events
    event TokensRewarded(address indexed to, uint256 usdSpent, uint256 tokens, string description, string partner);
    event TokensBurned(address indexed from, uint256 amount, string description, string partner);
    event DonationMade(address indexed donor, uint256 amount, string cause);
    event PartnerAdded(string name, string description, uint256 discountRate);
    event PartnerUpdated(string name, string description, uint256 discountRate);

    constructor() ERC20("Token Rewards", "TKN") Ownable(msg.sender) {
        _mint(msg.sender, 1000 * 10**18); // Initial supply
        
        // Initialize default partners
        _addPartner("Amazon Gift Coupon", "E-Commerce", 30);
        _addPartner("Apple Store Gift Card", "Tech Store", 20);
        _addPartner("Xbox", "Gaming", 15);
    }

    // Add/update partners (owner only)
    function _addPartner(string memory name, string memory description, uint256 discountRate) internal {
        require(!partners[name].isActive, "Partner already exists");
        partners[name] = Partner(name, description, discountRate, true);
        partnerNames.push(name);
        emit PartnerAdded(name, description, discountRate);
    }
    
    function addPartner(string memory name, string memory description, uint256 discountRate) public onlyOwner {
        _addPartner(name, description, discountRate);
    }
    
    function updatePartner(string memory name, string memory description, uint256 discountRate) public onlyOwner {
        require(partners[name].isActive, "Partner does not exist");
        partners[name].description = description;
        partners[name].discountRate = discountRate;
        emit PartnerUpdated(name, description, discountRate);
    }
    
    function togglePartner(string memory name, bool isActive) public onlyOwner {
        require(bytes(partners[name].name).length > 0, "Partner does not exist");
        partners[name].isActive = isActive;
    }

    // Reward tokens for purchases
    function rewardPurchase(address to, uint256 usdSpent) public {
        require(to != address(0), "Invalid address");
        require(usdSpent > 0, "Amount must be greater than 0");
        uint256 tokensToReward = (usdSpent * 5 * 10**18) / 10 / TKN_TO_USD; // 5 TKN per $10 spent
        _mint(to, tokensToReward);
        emit TokensRewarded(to, usdSpent, tokensToReward, "Purchase Reward", "Main Store");
    }

    // Burn tokens for general redemptions
    function burn(uint256 amount, string memory description) public {
        require(amount > 0, "Amount must be greater than 0");
        _burn(msg.sender, amount);
        emit TokensBurned(msg.sender, amount, description, "");
    }

    // Burn tokens for donations
    function donate(uint256 amount, string memory cause) public {
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
        donations.push(Donation(msg.sender, amount, cause, block.timestamp));
        emit DonationMade(msg.sender, amount, cause);
        emit TokensBurned(msg.sender, amount, string(abi.encodePacked("Donation to ", cause)), "");
    }

    // Burn tokens for partner network redemptions
    function redeemPartnerReward(address user, uint256 amount, string memory partnerName) public {
        require(user != address(0), "Invalid address");
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(user) >= amount, "Insufficient balance");
        require(partners[partnerName].isActive, "Partner is not active");
        
        _burn(user, amount);
        emit TokensBurned(user, amount, "Partner Redemption", partnerName);
    }

    // Get all active partners
    function getActivePartners() public view returns (Partner[] memory) {
        uint256 activeCount = 0;
        for (uint256 i = 0; i < partnerNames.length; i++) {
            if (partners[partnerNames[i]].isActive) {
                activeCount++;
            }
        }
        
        Partner[] memory activePartners = new Partner[](activeCount);
        uint256 index = 0;
        for (uint256 i = 0; i < partnerNames.length; i++) {
            if (partners[partnerNames[i]].isActive) {
                activePartners[index] = partners[partnerNames[i]];
                index++;
            }
        }
        return activePartners;
    }

    // Get donation history for a donor
    function getDonations(address donor) public view returns (Donation[] memory) {
        uint256 count = 0;
        for (uint256 i = 0; i < donations.length; i++) {
            if (donations[i].donor == donor) {
                count++;
            }
        }
        
        Donation[] memory donorDonations = new Donation[](count);
        uint256 index = 0;
        for (uint256 i = 0; i < donations.length; i++) {
            if (donations[i].donor == donor) {
                donorDonations[index] = donations[i];
                index++;
            }
        }
        return donorDonations;
    }

    // Mint function restricted to owner (for admin purposes)
    function mint(address to, uint256 amount) public onlyOwner {
        _mint(to, amount);
    }
}