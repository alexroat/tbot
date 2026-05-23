#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per ottenere le quotazioni correnti (e altri dati) di più ticker da Yahoo Finance.
Uso:
  python get_quotes.py AAPL MSFT TSLA
  python get_quotes.py --file tickers.txt
"""

import argparse
import sys

import pandas as pd
import yfinance as yf

def fetch_quotes(tickers: list) -> pd.DataFrame:
    """
    Scarica i dati di mercato per la lista di ticker.
    Ritorna un DataFrame con open, high, low, close, volume.
    """
    data = yf.download(
        tickers=tickers,
        period="1d",
        interval="1m",
        group_by='ticker',
        progress=False,
        threads=True
    )
    results = []
    for tk in tickers:
        if tk not in data:
            print(f"⚠️  Attenzione: {tk} non ha restituito dati.", file=sys.stderr)
            continue
        df = data[tk].iloc[-1]
        results.append({
            "ticker": tk,
            "timestamp": df.name,
            "open":      df["Open"],
            "high":      df["High"],
            "low":       df["Low"],
            "close":     df["Close"],
            "volume":    df["Volume"],
        })
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Ottieni quotazioni da Yahoo Finance.")
    parser.add_argument(
        "tickers",
        metavar="TICKER",
        nargs="*",
        help="Lista di ticker (es. AAPL, MSFT, TSLA)."
    )
    parser.add_argument(
        "--file", "-f",
        help="File di testo con ticker (uno per riga)."
    )
    parser.add_argument(
        "--output", "-o",
        default="quotes.csv",
        help="File CSV di output (default: quotes.csv)."
    )
    args = parser.parse_args()

    tickers = args.tickers or []
    if args.file:
        with open(args.file, "r") as fp:
            from_file = [line.strip().upper() for line in fp if line.strip()]
        tickers.extend(from_file)

    if not tickers:
        parser.print_usage()
        sys.exit("Errore: devi specificare almeno un ticker o un file.")

    tickers = sorted(set(tk.strip().upper() for tk in tickers))

    print("Scaricando dati per:", tickers)
    df = fetch_quotes(tickers)

    df.to_csv(args.output, index=False)
    print(f"Completato. Risultati salvati in '{args.output}':")
    print(df.to_string(index=False))

if __name__ == "__main__":
    main()
