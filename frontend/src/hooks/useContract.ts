import { useState, useEffect } from 'react';
import { ethers } from 'ethers';
import { CONTRACT_ADDRESS, SEPOLIA_RPC_URL } from '@/utils/constants';

// Contract ABI (simplified - only the functions we need)
const CONTRACT_ABI = [
  'function getMarketRisk(bytes32 marketId) external view returns (uint8)',
  'function getUserConfig(address user, bytes32 marketId) external view returns (uint8 threshold, bool alertEnabled)',
  'function setUserConfig(bytes32 marketId, uint8 threshold, bool alertEnabled) external',
  'event RiskUpdated(bytes32 indexed marketId, uint8 newLevel, uint256 timestamp)',
  'event AlertTriggered(address indexed user, bytes32 indexed marketId, uint8 riskLevel, uint256 timestamp)',
];

/**
 * Hook to interact with the RiskMonitor smart contract
 */
export function useContract() {
  const [provider, setProvider] = useState<ethers.JsonRpcProvider | null>(null);
  const [contract, setContract] = useState<ethers.Contract | null>(null);
  const [signer, setSigner] = useState<ethers.Signer | null>(null);

  useEffect(() => {
    // Initialize provider
    const rpcProvider = new ethers.JsonRpcProvider(SEPOLIA_RPC_URL);
    setProvider(rpcProvider);

    // Initialize contract
    const contractInstance = new ethers.Contract(
      CONTRACT_ADDRESS,
      CONTRACT_ABI,
      rpcProvider
    );
    setContract(contractInstance);
  }, []);

  /**
   * Connect to user's wallet
   */
  const connectWallet = async () => {
    if (!window.ethereum) {
      throw new Error('MetaMask is not installed');
    }

    try {
      await window.ethereum.request({ method: 'eth_requestAccounts' });
      const web3Provider = new ethers.BrowserProvider(window.ethereum);
      const web3Signer = await web3Provider.getSigner();
      setSigner(web3Signer);

      // Update contract with signer
      if (contract) {
        setContract(contract.connect(web3Signer));
      }

      return web3Signer;
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      throw error;
    }
  };

  /**
   * Get current risk level for a market
   */
  const getMarketRisk = async (marketId: string) => {
    if (!contract) throw new Error('Contract not initialized');

    try {
      const marketIdBytes = ethers.id(marketId);
      const riskLevel = await contract.getMarketRisk(marketIdBytes);
      return Number(riskLevel);
    } catch (error) {
      console.error('Failed to get market risk:', error);
      throw error;
    }
  };

  /**
   * Get user's alert configuration
   */
  const getUserConfig = async (userAddress: string, marketId: string) => {
    if (!contract) throw new Error('Contract not initialized');

    try {
      const marketIdBytes = ethers.id(marketId);
      const config = await contract.getUserConfig(userAddress, marketIdBytes);
      return {
        threshold: Number(config.threshold),
        alertEnabled: config.alertEnabled,
      };
    } catch (error) {
      console.error('Failed to get user config:', error);
      throw error;
    }
  };

  /**
   * Set user's alert configuration
   */
  const setUserConfig = async (
    marketId: string,
    threshold: number,
    alertEnabled: boolean
  ) => {
    if (!contract || !signer) {
      throw new Error('Wallet not connected');
    }

    try {
      const marketIdBytes = ethers.id(marketId);
      const tx = await contract.setUserConfig(
        marketIdBytes,
        threshold,
        alertEnabled
      );
      await tx.wait();
      return tx;
    } catch (error) {
      console.error('Failed to set user config:', error);
      throw error;
    }
  };

  /**
   * Listen to RiskUpdated events
   */
  const subscribeToRiskUpdates = (callback: (marketId: string, newLevel: number) => void) => {
    if (!contract) return;

    const filter = contract.filters.RiskUpdated();
    contract.on(filter, (marketId, newLevel, timestamp) => {
      callback(ethers.toUtf8String(marketId), Number(newLevel));
    });

    return () => {
      contract.off(filter);
    };
  };

  return {
    provider,
    contract,
    signer,
    connectWallet,
    getMarketRisk,
    getUserConfig,
    setUserConfig,
    subscribeToRiskUpdates,
  };
}

// Extend Window interface for TypeScript
declare global {
  interface Window {
    ethereum?: any;
  }
}
