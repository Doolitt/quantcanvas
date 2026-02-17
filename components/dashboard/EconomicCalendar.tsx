"use client";

import { useState } from "react";

interface EconomicEvent {
  id: string;
  time: string;
  name: string;
  country: string;
  importance: 1 | 2 | 3 | 4 | 5; // 1=low, 5=high
  forecast: string;
  actual: string;
  surprise: "positive" | "negative" | "neutral";
}

export default function EconomicCalendar() {
  const [selectedDate, setSelectedDate] = useState<string>("2026-02-13");
  const [events, setEvents] = useState<EconomicEvent[]>([
    { id: "1", time: "08:30 ET", name: "CPI Inflation", country: "US", importance: 5, forecast: "3.2%", actual: "3.1%", surprise: "positive" },
    { id: "2", time: "08:30 ET", name: "Retail Sales", country: "US", importance: 4, forecast: "+0.4%", actual: "+0.6%", surprise: "positive" },
    { id: "3", time: "10:00 ET", name: "Business Inventories", country: "US", importance: 2, forecast: "+0.2%", actual: "+0.1%", surprise: "negative" },
    { id: "4", time: "11:30 ET", name: "4-Week Bill Auction", country: "US", importance: 3, forecast: "4.85%", actual: "4.82%", surprise: "positive" },
    { id: "5", time: "13:00 ET", name: "3-Yr Note Auction", country: "US", importance: 3, forecast: "4.25%", actual: "4.28%", surprise: "negative" },
    { id: "6", time: "14:00 ET", name: "Treasury Buyback Results", country: "US", importance: 2, forecast: "N/A", actual: "Completed", surprise: "neutral" },
    { id: "7", time: "15:15 ET", name: "Raphael Bostic Speaks", country: "US", importance: 4, forecast: "N/A", actual: "Scheduled", surprise: "neutral" },
  ]);

  const highImpactEvents = events.filter(event => event.importance >= 4);
  const mediumImpactEvents = events.filter(event => event.importance === 3);
  const lowImpactEvents = events.filter(event => event.importance <= 2);

  const getImportanceColor = (importance: number) => {
    switch (importance) {
      case 5: return "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200";
      case 4: return "bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200";
      case 3: return "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200";
      case 2: return "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200";
      default: return "bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200";
    }
  };

  const getSurpriseIcon = (surprise: string) => {
    switch (surprise) {
      case "positive": return "↗️";
      case "negative": return "↘️";
      default: return "➡️";
    }
  };

  const getSurpriseColor = (surprise: string) => {
    switch (surprise) {
      case "positive": return "text-green-600 dark:text-green-400";
      case "negative": return "text-red-600 dark:text-red-400";
      default: return "text-gray-600 dark:text-gray-400";
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 h-full">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Economic Calendar</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Powered by</span>
          <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded text-xs font-medium">
            Econoday
          </span>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg border-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {highImpactEvents.length} high impact events today
          </div>
        </div>

        <div className="flex items-center space-x-4 mb-4">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">High Impact</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Medium</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
            <span className="text-sm text-gray-600 dark:text-gray-400">Low</span>
          </div>
        </div>
      </div>

      <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
        {events.map((event) => (
          <div key={event.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center">
                <span className={`px-2 py-1 rounded text-xs font-medium mr-2 ${getImportanceColor(event.importance)}`}>
                  {event.importance === 5 ? "🔥" : event.importance === 4 ? "⚠️" : ""} Impact {event.importance}
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">{event.country}</span>
              </div>
              <div className="text-sm font-medium text-gray-900 dark:text-white">{event.time}</div>
            </div>
            
            <div className="flex justify-between items-center">
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white">{event.name}</h4>
                <div className="flex items-center space-x-4 mt-2">
                  <div className="text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Forecast: </span>
                    <span className="font-medium">{event.forecast}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Actual: </span>
                    <span className={`font-medium ${getSurpriseColor(event.surprise)}`}>
                      {event.actual} {getSurpriseIcon(event.surprise)}
                    </span>
                  </div>
                </div>
              </div>
              <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium">
                Analyze
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-white">AI Market Analysis</h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              CPI surprise positive → Bullish for equities, bearish for bonds
            </p>
          </div>
          <button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-all">
            Ask AI
          </button>
        </div>
      </div>
    </div>
  );
}