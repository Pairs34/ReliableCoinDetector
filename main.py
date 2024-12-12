import requests
from tabulate import tabulate

def get_reliable_coins(market_cap_min=1000000000, volume_min=50000000):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 250,
        "page": 1,
        "sparkline": "false"
    }

    response = requests.get(url, params=params)
    coins = response.json()

    reliable = []
    for coin in coins:
        if (coin["market_cap"] is not None and coin["market_cap"] >= market_cap_min) and \
           (coin["total_volume"] is not None and coin["total_volume"] >= volume_min):
            reliable.append({
                "id": coin["id"],
                "name": coin["name"],
                "symbol": coin["symbol"].upper(),  # Uppercase for CryptoCompare compatibility
                "price": coin["current_price"],
                "market_cap": coin["market_cap"],
                "volume_24h": coin["total_volume"]
            })
    return reliable

def get_historical_data_cryptocompare(fsym="BTC", tsym="USD", limit=30):
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    params = {
        "fsym": fsym,
        "tsym": tsym,
        "limit": limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data.get("Response") == "Success":
        return data["Data"]["Data"]
    else:
        return None

def get_2y_change(fsym="BTC", tsym="USD"):
    data = get_historical_data_cryptocompare(fsym, tsym, 730)
    if data and len(data) > 1:
        first_price = data[0]["close"]
        last_price = data[-1]["close"]
        if first_price > 0:
            change = ((last_price - first_price) / first_price) * 100
        else:
            change = 0
        return change
    return 0

def get_1m_buy_sell_ratio(fsym="BTC", tsym="USD"):
    data = get_historical_data_cryptocompare(fsym, tsym, 30)
    if data and len(data) > 0:
        buy_days = 0
        sell_days = 0
        for day in data:
            o = day["open"]
            c = day["close"]
            if c > o:
                buy_days += 1
            elif c < o:
                sell_days += 1
            else:
                buy_days += 0.5
                sell_days += 0.5

        total_days = buy_days + sell_days
        if total_days > 0:
            buy_ratio = (buy_days / total_days) * 100
            sell_ratio = (sell_days / total_days) * 100
            return buy_ratio, sell_ratio
        else:
            return 50, 50
    return 50, 50

def color_if_over_100(value_str):
    # Bu fonksiyon değer metin içinden sayısal değeri bulup 100 üzerindeyse renklendirme yapar.
    # value_str "%XX" formatında veya düz sayısal olabilir.
    # Önce sayısal değeri ayıklayalım.
    # Eğer birden fazla yüzde varsa (örn buy/sell ratio) ikisini de işleyelim.
    segments = value_str.split('/')
    colored_segments = []
    for seg in segments:
        seg = seg.strip()
        # Seg örneğin "%120.5 buy" veya "%95 sell" gibi olabilir.
        # Sayısal değeri çekelim:
        import re
        match = re.search(r"(\d+(\.\d+)?)", seg)
        if match:
            num = float(match.group(1))
            if num > 100:
                # Renklendir
                seg = f"\033[92m{seg}\033[0m"
        colored_segments.append(seg)
    return ' / '.join(colored_segments)

if __name__ == "__main__":
    reliable_coins = get_reliable_coins()
    cheap_coins = [c for c in reliable_coins if c['price'] < 10.0]

    if not cheap_coins:
        # Hiç ucuz coin yoksa sadece boş bir tablo verebilir veya hiçbir şey yazmayabiliriz.
        print(tabulate([], headers=["Name","Symbol","Price($)","Market Cap($)","24h Volume($)","Potential(%)","Popularity(%)","1 Month Buy/Sell Ratio","2 Year Change(%)"], tablefmt="fancy_grid"))
    else:
        avg_volume = sum(c['volume_24h'] for c in cheap_coins) / len(cheap_coins) if len(cheap_coins) > 0 else 1
        results = []
        for coin in cheap_coins:
            potential = (coin['volume_24h'] / coin['market_cap']) * 100 if coin['market_cap'] != 0 else 0
            popularity = (coin['volume_24h'] / avg_volume) * 100 if avg_volume > 0 else 0
            change_2y = get_2y_change(coin['symbol'], "USD")
            buy_ratio, sell_ratio = get_1m_buy_sell_ratio(coin['symbol'], "USD")

            # Formatları string olarak hazırlayalım
            potential_str = f"%{round(potential,2)}"
            popularity_str = f"%{round(popularity,2)}"
            buy_sell_str = f"%{round(buy_ratio,2)} buy / %{round(sell_ratio,2)} sell"
            change_2y_str = f"%{round(change_2y,2)}"

            # Renklendirme
            potential_str = color_if_over_100(potential_str)
            popularity_str = color_if_over_100(popularity_str)
            buy_sell_str = color_if_over_100(buy_sell_str)
            change_2y_str = color_if_over_100(change_2y_str)

            results.append([
                coin['name'],
                coin['symbol'],
                coin['price'],
                coin['market_cap'],
                coin['volume_24h'],
                potential_str,
                popularity_str,
                buy_sell_str,
                change_2y_str
            ])

        headers = [
            "Name",
            "Symbol",
            "Price($)",
            "Market Cap($)",
            "24h Volume($)",
            "Potential(%)",
            "Popularity(%)",
            "1 Month Buy/Sell Ratio",
            "2 Year Change(%)"
        ]

        # Sadece tablo çıktısı veriyoruz.
        print(tabulate(results, headers=headers, tablefmt="fancy_grid"))
