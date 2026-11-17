"""시장판 데이터 갱신: 한경 데이터센터 금리 + 네이버 환율 → market/data.json (GitHub Actions가 주기 실행)."""
import json, os, re, time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data.json")
KST = timezone(timedelta(hours=9))
UA = {"User-Agent": "Mozilla/5.0"}
RATES = {"kr30": "국고30년", "kr10": "국고10년", "kr3": "국고3년",
         "us30": "미국 국채 30년", "us10": "미국 국채 10년", "us2": "미국 국채 2년"}


def get(url):
    return urlopen(Request(url, headers=UA), timeout=20).read()


def load():
    try:
        return json.load(open(OUT, encoding="utf-8"))
    except Exception:
        return {"now": {}, "hist": []}


def main():
    old = load()
    now = dict(old.get("now", {}))
    try:
        h = get("https://datacenter.hankyung.com/rates-bonds").decode("utf-8", "ignore")
        for k, title in RATES.items():
            m = re.search(r'title="%s">.*?data-value="([-+\d.]+)".*?data-value="([-+\d.]+)"' % re.escape(title), h, re.S)
            if m:
                now[k] = [float(m.group(1)), float(m.group(2))]
    except Exception as e:
        print("rates fail", e)
    try:
        d = json.loads(get("https://api.stock.naver.com/marketindex/exchange/FX_USDKRW"))["exchangeInfo"]
        now["fx"] = [float(str(d["calcPrice"]).replace(",", "")), float(d.get("fluctuationsRatio") or 0)]
    except Exception as e:
        print("fx fail", e)
    hist = old.get("hist", [])
    point = {"t": int(time.time()), "kr30": now.get("kr30", [None])[0], "us30": now.get("us30", [None])[0], "fx": now.get("fx", [None])[0]}
    if not hist or any(hist[-1].get(k) != point[k] for k in ("kr30", "us30", "fx")):
        hist.append(point)
    out = {"updated": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), "ts": int(time.time()),
           "now": now, "hist": hist[-600:],
           "source": "금리: 한국경제 데이터센터 · 환율: 네이버(하나은행 고시)"}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(out["updated"], {k: v[0] for k, v in now.items()})


if __name__ == "__main__":
    main()
