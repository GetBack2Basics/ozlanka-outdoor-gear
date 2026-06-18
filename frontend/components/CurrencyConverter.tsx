"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const DEFAULT_RATE = 190;

function formatCurrency(value: number, currency: "AUD" | "LKR"): string {
  const formatted = value.toLocaleString("en-AU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${currency} ${formatted}`;
}

export function CurrencyConverter() {
  const [rate, setRate] = useState<number>(DEFAULT_RATE);
  const [isCustom, setIsCustom] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("aud_lkr_rate");
    if (stored) {
      const parsed = parseFloat(stored);
      if (!isNaN(parsed) && parsed > 0) {
        setRate(parsed);
        setIsCustom(true);
      }
    }
  }, []);

  const handleChange = (value: string) => {
    const parsed = parseFloat(value);
    if (!isNaN(parsed) && parsed > 0) {
      setRate(parsed);
      setIsCustom(true);
      localStorage.setItem("aud_lkr_rate", parsed.toString());
    }
  };

  const handleReset = () => {
    setRate(DEFAULT_RATE);
    setIsCustom(false);
    localStorage.removeItem("aud_lkr_rate");
  };

  const convert = (aud: number) => Math.round(aud * rate * 100) / 100;

  return (
    <div className="absolute top-4 right-4">
      <div className="bg-slate-900/80 backdrop-blur-sm rounded-lg p-4 border border-slate-700 min-w-[220px]">
        <div className="flex items-center justify-between mb-3">
          <Label className="text-sm font-medium text-slate-200 mb-0">AUD → LKR Rate</Label>
          {isCustom && (
            <button
              onClick={handleReset}
              className="text-xs text-amber-400 hover:text-amber-300"
              title="Reset to default"
            >
              Reset
            </button>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">1 AUD =</span>
          <Input
            type="number"
            step="0.01"
            min="1"
            max="500"
            value={rate}
            onChange={(e) => handleChange(e.target.value)}
            className="w-24 text-right bg-slate-800 border-slate-600 text-white"
            aria-label="AUD to LKR conversion rate"
          />
          <span className="text-slate-400 text-sm">LKR</span>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Default: {DEFAULT_RATE} LKR | Current: {formatCurrency(rate, "LKR")}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Stored in browser. Used for all price calculations.
        </p>
      </div>
    </div>
  );
}

export function PriceDisplay({ priceAud, rate }: { priceAud: number; rate: number }) {
  const priceLkr = Math.round(priceAud * rate * 100) / 100;
  return (
    <div className="flex flex-col items-start gap-1">
      <span className="text-lg font-semibold text-slate-900">
        {formatCurrency(priceAud, "AUD")}
      </span>
      <span className="text-sm font-medium text-emerald-600">
        {formatCurrency(priceLkr, "LKR")}
      </span>
    </div>
  );
}