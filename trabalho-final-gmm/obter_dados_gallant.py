"""Reconstrói o painel NDS–VWR de Hansen–Singleton a partir do arquivo de Gallant.

Uso: python obter_dados_gallant.py --out data
Alternativa sem rede: python obter_dados_gallant.py --source hansena.dat --out data
"""
import argparse
import calendar
import csv
import hashlib
import io
import math
from pathlib import Path
from urllib.request import urlopen

URL = "https://www.aronaldg.org/webfiles/data/hansena.dat"
# Hash do CSV canônico (mesmos campos numéricos, sem depender de espaços no DAT).
LEVELS_SHA256 = "5054c0e9e199ae53a7a9868934412cdb53292419a45694c5520cba02e7df0143"


def parse_levels(text):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(("date", "consum", "pop", "stocks", "deflat"))
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        seq, year_field, month_field, *nums = line.split()
        i = len(rows)
        year, month = 1959 + i // 12, i % 12 + 1
        if int(seq) != i or int(month_field) != month or year_field != (str(year) if month == 1 else "."):
            raise ValueError(f"Data ou sequência inesperada na observação {i}: {line}")
        if len(nums) != 4:
            raise ValueError(f"Esperadas quatro variáveis econômicas: {line}")
        c, p, r, d = map(float, nums)
        if not all(map(math.isfinite, (c, p, r, d))) or min(c, p, 1 + r, d) <= 0:
            raise ValueError(f"Nível ou retorno impossível: {line}")
        writer.writerow([f"{year}-{month:02d}-01", *nums])
        rows.append((year, month, c, p, r, d))
    levels = out.getvalue().encode("utf-8")
    if len(rows) != 240 or hashlib.sha256(levels).hexdigest() != LEVELS_SHA256:
        raise ValueError("A fonte diverge do snapshot de 240 meses usado no checkpoint.")
    return levels, rows


def build(text, dest):
    levels, rows = parse_levels(text)
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(("date", "gross_real_return", "gross_cons_growth"))
    for prev, cur in zip(rows, rows[1:]):
        year, month, cons, pop, stock, defl = cur
        date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
        real_return = (1.0 + stock) / (defl / prev[5])
        growth = (cons / pop) / (prev[2] / prev[3])
        writer.writerow([date, real_return, growth])
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "gallant_levels.csv").write_bytes(levels)
    (dest / "gallant_nds_vwr.csv").write_bytes(out.getvalue().encode("utf-8"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Cópia local de hansena.dat")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    if args.source:
        raw = args.source.read_bytes()
    else:
        with urlopen(URL, timeout=30) as response:
            raw = response.read()
    build(raw.decode("ascii"), args.out)
