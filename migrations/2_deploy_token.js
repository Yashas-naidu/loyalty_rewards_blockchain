const TKNToken = artifacts.require("TKNToken");

module.exports = function (deployer) {
  deployer.deploy(TKNToken);
};