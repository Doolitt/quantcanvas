"use client";

import { useState } from "react";

interface Strategy {
  id: string;
  name: string;
  description: string;
  assetClass: "equities" | "crypto" | "commodities" | "multi";
  sharpeRatio: number;
  totalReturn: number;
  maxDrawdown: number;
  status: "active" | "backtesting" | "paused";
}

export default function StrategyBuilder() {
  const [strategies, setStrategies] = useState<Strategy[]>([
    { id: "1", name: "CPI Momentum", description: "Buy when CPI < 3%, sell when > 5%", assetClass: "equities", sharpeRatio: 1.8, totalReturn: 24.5, maxDrawdown: -8.2, status: "active" },
    { id: "2", name: "Fed Speech Sentiment", description: "Long when Fed dovish, short when hawkish", assetClass: "equities", sharpeRatio: 2.1, totalReturn: 32.1, maxDrawdown: -6.5, status: "active" },
    { id: "3", name: "Bitcoin Halving Cycle", description: "Accumulate 6 months pre-halving, distribute post", assetClass: "crypto", sharpeRatio: 3.2, totalReturn: 185.4, maxDrawdown: -25.3, status: "active" },
    { id: "4", name: "Gold Inflation Hedge", description: "Allocate to gold when real yields negative", assetClass: "commodities", sharpeRatio: 1.5, totalReturn: 18.7, maxDrawdown: -12.4, status: "backtesting" },
    { id: "5", name: "Cross-Asset Risk Parity", description: "Risk-weighted allocation across stocks, bonds, gold, crypto", assetClass: "multi", sharpeRatio: 2.4, totalReturn: 28.9, maxDrawdown: -9.8, status: "paused" },
  ]);

  const [newStrategy, setNewStrategy] = useState({
    name: "",
    description: "",
    assetClass: "equities" as const,
  });

  const handleCreateStrategy = () => {
    if (!newStrategy.name.trim()) return;
    
    const newStrat: Strategy = {
      id: Date.now().toString(),
      name: newStrategy.name,
      description: newStrategy.description,
      assetClass: newStrategy.assetClass,
      sharpeRatio: 0,
      totalReturn: 0,
      maxDrawdown: 0,
      status: "backtesting",
    };
    
    setStrategies([newStrat, ...strategies]);
    setNewStrategy({ name: "", description: "", assetClass: "equities" });
  };

  const getAssetClassColor = (assetClass: string) => {
    switch (assetClass) {
      case "equities": return "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200";
      case "crypto": return "bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200";
      case "commodities": return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "multi": return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      default: return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200";
      case "backtesting": return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case "paused": return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
      default: return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 h-full">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Strategy Builder</h2>
        <span className="px-3 py-1 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-full text-sm font-medium">
          AI-Powered
        </span>
      </div>

      <div className="mb-6">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Create New Strategy</h3>
        <div className="space-y-3">
          <input
            type="text"
            placeholder="Strategy Name (e.g., 'CPI Momentum Trader')"
            value={newStrategy.name}
            onChange={(e) => setNewStrategy({...newStrategy, name: e.target.value})}
            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500"
          />
          <textarea
            placeholder="Strategy Logic (e.g., 'Buy S&P500 when CPI < 3%, exit when > 5%')"
            value={newStrategy.description}
            onChange={(e) => setNewStrategy({...newStrategy, description: e.target.value})}
            className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
          />
          <div className="flex items-center space-x-3">
            <select
              value={newStrategy.assetClass}
              onChange={(e) => setNewStrategy({...newStrategy, assetClass: e.target.value as any})}
              className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="equities">Equities</option>
              <option value="crypto">Cryptocurrency</option>
              <option value="commodities">Commodities</option>
              <option value="multi">Multi-Asset</option>
            </select>
            <button
              onClick={handleCreateStrategy}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Create
            </button>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="font-semibold text-gray-900 dark:text-white">My Strategies</h3>
          <span className="text-sm text-gray-600 dark:text-gray-400">{strategies.length} strategies</span>
        </div>
        
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
          {strategies.map((strategy) => (
            <div key={strategy.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">{strategy.name}</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{strategy.description}</p>
                </div>
                <div className="flex flex-col items-end space-y-1">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getAssetClassColor(strategy.assetClass)}`}>
                    {strategy.assetClass}
                  </span>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(strategy.status)}`}>
                    {strategy.status}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div className="text-center">
                  <div className="text-xs text-gray-600 dark:text-gray-400">Sharpe</div>
                  <div className={`font-bold ${strategy.sharpeRatio >= 2 ? 'text-green-600' : strategy.sharpeRatio >= 1 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {strategy.sharpeRatio.toFixed(2)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-600 dark:text-gray-400">Return</div>
                  <div className={`font-bold ${strategy.totalReturn >= 20 ? 'text-green-600' : strategy.totalReturn >= 0 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {strategy.totalReturn.toFixed(1)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-600 dark:text-gray-400">Drawdown</div>
                  <div className={`font-bold ${strategy.maxDrawdown >= -10 ? 'text-green-600' : strategy.maxDrawdown >= -20 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {strategy.maxDrawdown.toFixed(1)}%
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button className="px-3 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 rounded text-sm">
                    Backtest
                  </button>
                  <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm">
                    Deploy
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">AI Strategy Suggestions</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Based on current economic data and market conditions
            </p>
          </div>
          <button className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-medium py-2 px-4 rounded-lg transition-all">
            <span>Generate Ideas</span>
            <span>✨</span>
          </button>
        </div>
        
        <div className="mt-4 p-3 bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-lg">
          <div className="text-sm">
            <span className="font-medium text-gray-900 dark:text-white">Current AI Insight: </span>
            <span className="text-gray-600 dark:text-gray-300">
              "Fed dovish pivot expected Q2 2026 → Favor long-duration assets (tech stocks, crypto)"
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}