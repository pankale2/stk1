# Use static instrument keys from instruments_daily.json
import json

def update_strategy_scrips(symbols, in_file="instruments_daily.json", out_file="strategy_scrips.py"):
    with open(in_file, "r") as f:
        instruments = json.load(f)
    scrips_list = []
    for symbol in symbols:
        key = instruments.get(symbol)
        scrips_list.append(f"    {{'symbol': '{symbol}', 'token': '{key}'}}")
    scrips_py_content = "# List of scrips for strategy (static)\nSCRIPS = [\n" + ",\n".join(scrips_list) + "\n]"
    with open(out_file, "w") as f:
        f.write(scrips_py_content)
    print(f"Updated {out_file} with static instrument keys.")

if __name__ == "__main__":
    symbols = ["RELIANCE", "ICICIBANK", "INFY", "ITC", "LT"]
    update_strategy_scrips(symbols)
