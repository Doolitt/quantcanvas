"use client";

import PortfolioTracker from "./PortfolioTracker";
import EconomicCalendar from "./EconomicCalendar";
import StrategyBuilder from "./StrategyBuilder";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-black p-4 md:p-8">
      <header className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">
          QuantCanvas
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          AI-powered investment strategy platform with economic data, backtesting, and portfolio tracking
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Portfolio Tracker - Left Column */}
        <div className="lg:col-span-1">
          <PortfolioTracker />
        </div>

        {/* Economic Calendar - Middle Column */}
        <div className="lg:col-span-1">
          <EconomicCalendar />
        </div>

        {/* Strategy Builder - Right Column */}
        <div className="lg:col-span-1">
          <StrategyBuilder />
        </div>
      </div>

      <div className="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>Connected to GitHub: <a href="https://github.com/Doolitt/quantcanvas" className="text-blue-600 dark:text-blue-400 hover:underline">Doolitt/quantcanvas</a></p>
        <p className="mt-1">Powered by OpenClaw AI agents • Ultra-budget system: $5/day</p>
      </div>
    </div>
  );
}