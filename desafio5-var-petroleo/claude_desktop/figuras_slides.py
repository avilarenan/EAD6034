"""Gera as figuras dos slides com as rotinas de analise.py, na configuração de referência.
Uso, dentro de desafio5-var-petroleo: python claude_desktop/figuras_slides.py
As bandas usam as mesmas sementes da célula 3 do notebook: os números coincidem.
"""
import contextlib, io, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import analise as var

DESTINO = AQUI / "figuras"
DESTINO.mkdir(exist_ok=True)
virgula = FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",").replace("-", "−"))

var.configurar({"PAUSAR": False, "MOSTRAR": False, "FONT_SIZE": 15})
with contextlib.redirect_stdout(io.StringIO()):
    dados = var.preparar_dados()[1]
    regimes = var.separar_regimes(dados, var.escolher_p(dados)[0])

# 1. Resposta acumulada do IPCA a +10% no Brent, antes e depois, com bandas de 90%.
q = [(1-var.CONFIANCA)/2, (1+var.CONFIANCA)/2]
fig, ax = plt.subplots(figsize=(10, 5.6))
for i, (nome, rotulo, cor) in enumerate([("antes", "Antes: 01/2004–09/2016", var.CORES[0]),
                                         ("depois", "Depois: 10/2016–09/2026", var.CORES[1])]):
    r = regimes[nome]
    ponto = var.resposta(r)[:, 0]
    lo, hi = np.quantile(var.bootstrap(r, var.SEMENTE+i)[0][:, :, 0], q, axis=0)
    meses = np.arange(var.H_REPASSE+1)
    ax.fill_between(meses, lo[meses], hi[meses], color=cor, alpha=.12, lw=0)
    ax.plot(meses, ponto[meses], color=cor, lw=3, solid_capstyle="round")
    ax.text(var.H_REPASSE+0.3, ponto[var.H_REPASSE], f"{rotulo}\n{ponto[var.H_REPASSE]:+.2f} p.p.".replace(".", ",", 1),
            color="#26313a", va="center", fontsize=14)
ax.axhline(0, color="#56616b", lw=1)
ax.set_xlim(0, var.H_REPASSE+4.2)
ax.set_xticks(range(0, var.H_REPASSE+1, 2))
ax.yaxis.set_major_formatter(virgula)
ax.grid(axis="y", color="#e3e6e8", lw=.8); ax.set_axisbelow(True)
ax.set_xlabel("Meses após a alta de 10% no Brent")
ax.set_ylabel("IPCA acumulado (p.p.)")
plt.tight_layout(); plt.savefig(DESTINO/"irf_brent.png", dpi=200); plt.close()

# 2. Variantes: o mesmo gráfico do notebook, com vírgula decimal e sem título (o slide tem o seu).
def figura_slide(nome):
    for eixo in plt.gcf().axes:
        eixo.set_title("", loc="left")
        eixo.xaxis.set_major_formatter(virgula)
        for texto in eixo.texts:
            texto.set_text(texto.get_text().replace(".", ","))
    plt.tight_layout(); plt.savefig(DESTINO/"variantes.png", dpi=200); plt.close()

var.figura = figura_slide
var.grafico_variantes(pd.read_csv(AQUI.parent/"resultados"/"10_variantes.csv", index_col=0, encoding="utf-8-sig"))
print("Figuras em", DESTINO)
