require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const { SEPOLIA_RPC_URL, PRIVATE_KEY, ETHERSCAN_API_KEY } = process.env;

/** @type import("hardhat/config").HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    hardhat: {},
    sepolia: {
      url: SEPOLIA_RPC_URL || "",
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
    },
  },
  etherscan: {
    // ✅ V2 推荐写法：只填一个字符串
    apiKey: ETHERSCAN_API_KEY || "",
    // 可选：把 sourcify 关掉，少点噪音日志
    sourcify: {
      enabled: false,
    },
  },
};