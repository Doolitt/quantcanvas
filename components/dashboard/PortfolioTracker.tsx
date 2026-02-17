"use client";

import { useState } from "react";

interface Holding {
  id: string;
  symbol: string;
  name: string;
  type: "stock" | "crypto" | "etf" | "commodity";
  quantity: number;
  currentPrice: number;
  averageCost: number;
  change: number;
}

export default function PortfolioTracker() {
  const [portfolioValue, setPortfolioValue] = useState(125430.75);
  const [dailyChange, setDailyChange] = useState(2456.32);
  const [holdings, setHoldings] = useState<Holding[]>([
    { id: "1", symbol: "AAPL", name: "Apple Inc.", type: "stock", quantity: 50, currentPrice: 175.25, averageCost: 165.50, change: 2.3 },
    { id: "2", symbol: "BTC", name: "Bitcoin", type: "crypto", quantity: 0.5, currentPrice: 62500.75, averageCost: 58000.00, change: 5.8 },
    { id: "3", symbol: "ETH", name: "Ethereum", type: "crypto", quantity: 3.2, currentPrice: 3250.50, averageCost: 3100.00, change: 1.9 },
    { id: "4", symbol: "GLD", name: "SPDR Gold Shares", type: "commodity", quantity: 25, currentPrice: 185.75, averageCost: 180.25, change: -0.5 },
    { id: "5", symbol: "NVDA", name: "NVIDIA Corp", type: "stock", quantity: 15, currentPrice: 950.25, averageCost: 850.50, change: 8.2 },
  ]);

  const totalGainLoss = holdings.reduce((sum, holding) => {
    const currentValue = holding.quantity * holding.currentPrice;
    const costBasis = holding.quantity * holding.averageCost;
    return sum + (currentValue - costBasis);
  }, 0);

  const totalGainLossPercent = (totalGainLoss / (portfolioValue - totalGainLoss)) * 100;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 h-full">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Portfolio Tracker</h2>
        <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium">
          $5.2M AUM
        </span>
      </div>

      <div className="mb-6">
        <div className="text-3xl font-bold text-gray-900 dark:text-white">
          ${portfolioValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </div>
        <div className={`text-lg ${dailyChange >= 0 ? 'text-green-600' : 'text-red-600'} mt-1`}>
          {dailyChange >= 0 ? '+' : ''}${dailyChange.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} today
        </div>
      </div>

      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-600 dark:text-gray-400">Total Gain/Loss</span>
          <span className={`font-bold ${totalGainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {totalGainLoss >= 0 ? '+' : ''}${totalGainLoss.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({totalGainLossPercent.toFixed(2)}%)
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${totalGainLoss >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min(100, Math.abs(totalGainLossPercent) * 3)}%` }}
          ></div>
        </div>
      </div>

      <div className="mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Holdings</h3>
        <div className="space-y-3">
          {holdings.map((holding) => {
            const currentValue = holding.quantity * holding.currentPrice;
            const gainLoss = currentValue - (holding.quantity * holding.averageCost);
            const gainLossPercent = (gainLoss / (holding.quantity * holding.averageCost)) * 100;

            return (
              <div key={holding.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3 ${
                    holding.type === 'stock' ? 'bg-blue-100 dark:bg-blue-900' :
                    holding.type === 'crypto' ? 'bg-purple-100 dark:bg-purple-900' :
                    holding.type === 'etf' ? 'bg-green-100 dark:bg-green-900' :
                    'bg-yellow-100 dark:bg-yellow-900'
                  }`}>
                    <span className={`font-bold ${
                      holding.type === 'stock' ? 'text-blue-600 dark:text-blue-300' :
                      holding.type === 'crypto' ? 'text-purple-600 dark:text-purple-300' :
                      holding.type === 'etf' ? 'text-green-600 dark:text-green-300' :
                      'text-yellow-600 dark:text-yellow-300'
                    }`}>
                      {holding.symbol.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">{holding.symbol}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{holding.name}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium text-gray-900 dark:text-white">
                    ${currentValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div className={`text-sm ${gainLoss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {gainLoss >= 0 ? '+' : ''}{gainLossPercent.toFixed(2)}%
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex space-x-3">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
          Add Holding
        </button>
        <button className="flex-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-medium py-2 px-4 rounded-lg transition-colors">
          Connect Wallet
        </button>
      </div>
    </div>
  );
}