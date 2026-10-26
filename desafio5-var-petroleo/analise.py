# %% 0. PAINEL DE CONTROLE - altere aqui durante a apresentação
"""EAD6034 | Rafael Palazzi | Renan de Luca Avila.
Pergunta: o repasse do petróleo ao IPCA mudou depois de outubro de 2016?
Para apresentar, abra apresentacao.ipynb. Este arquivo reúne os cálculos reutilizáveis.
Também pode executar no terminal: python analise.py
Para regenerar sem janelas/pausas: python analise.py --lote
"""
INICIO = "2004-01-01"           # Início da tarefa. Avançar reduz informação histórica.
FIM = "2026-09-01"              # Fotografia dos dados. 2023-04-01 evita misturar a mudança de 2023.
QUEBRA = "2016-10-01"           # Primeiro mês do segundo regime. Experimente 2018-01-01.
ORDEM = ["brent", "cambio", "ipa", "ipca", "selic"]  # Anteriores afetam posteriores no mesmo mês.
ORDEM_ALT = ["cambio", "brent", "ipa", "selic", "ipca"]  # Hipótese alternativa de reação no mês.
P_FIXO = None                   # None seleciona p. Inteiro força p: experimente 1, 2 ou 4.
P_MAX = 6                       # Teto parcimonioso: 5 variáveis custam 25 coeficientes por lag.
CRITERIO = "bic"                # BIC penaliza tamanho; "aic" ou "hq" permitem mais persistência.
AJUSTAR_P_RESIDUOS = True       # Tenta p >= escolhido até passar Portmanteau, limitado a P_MAX.
SAZONAIS = True                 # 11 indicadores mensais. False deixa sazonalidade nos resíduos.
DUMMIES = True                  # Pulsos isolam episódios extremos sem apagar meses.
MESES_ATIPICOS = ["2018-05", "2018-06", "2020-03", "2020-04", "2020-05", "2020-06"]
EXCLUIR_2020 = False            # Retira equações/defasagens que tocam 2020; não cola 2019 em 2021.
DIFERENCIAR_SELIC = False       # Nível segue a aula. True testa sensibilidade à raiz unitária.
INCLUIR_SELIC = True            # False estima o VAR sem a Selic, fonte da autocorrelação residual.
RESTRICOES = {}                 # Zeros nas defasagens. Ex.: {"brent": ["cambio", "ipa", "ipca", "selic"]}.
H = 24                         # Horizonte IRF. Aumentar amplia incerteza e custo.
H_REPASSE = 12                  # Acumulação h=0 até h=12, inclusive.
CHOQUE_PCT = 10.0               # Alta exata de 10%: impacto em log = 100*log(1.10).
CONFIANCA = 0.90                # Bandas pontuais como na aula. 0.95 alarga as bandas.
BOOT = 399                     # Wild bootstrap: 99 para ensaio rápido, 999 para mais precisão.
SEMENTE = 20261025              # Reprodutibilidade. Mudar altera apenas erro Monte Carlo.
ALFA = 0.05                    # Limiar dos testes, distinto de CONFIANCA das IRFs.
LAG_DIAG = 12                  # Autocorrelação até um ano, sempre deve superar p.
LAG_ARCH = 4                   # ARCH por equação: janela curta para limitar parâmetros.
LAG_HAC = 12                   # Newey-West/Bartlett: autocovariâncias até 12 meses.
CUSUM_INICIAL = 36            # Aquecimento mínimo de 3 anos; maior valor atrasa o diagnóstico.
REG_TESTES = "c"               # Constante, sem tendência nas taxas. "ct" admite tendência e muda H0.
ADF_CRITERIO = "BIC"           # Escolhe lags do teste ADF, independentemente do critério do VAR.
KPSS_LAGS = "auto"              # Largura automática; inteiro fixa a correção de dependência.
MIN_GRAUS_LIVRES = 10           # Margem mínima para estimar variância. Aumentar exige mais dados.
THREADS = 1                    # Uma thread reduz custo em matrizes pequenas; mais pode atrasar.
ADF_MAX = 12                   # ADF até um ano, seleção BIC; KPSS usa largura automática.
D_MAX = 1                      # Toda-Yamamoto: 1 lag extra não testado, admite variáveis I(1).
JANELA = 96                    # Repasse móvel em 8 anos. Menor janela aumenta imprecisão.
PASSO_JANELA = 3               # Reestima a cada trimestre por velocidade; 1 gera curva mensal.
FEVD_H = [1, 12, 24]           # h passos soma inovações de 0 a h-1, convenção da FEVD.
EPISODIO = ("2021-01-01", "2022-12-01")  # Episódio da decomposição histórica.
INICIO_PREV = "2017-01-01"      # Primeira origem, treino até esse mês. Mais cedo amplia avaliação.
H_PREV = [1, 12]               # Inflação DO MÊS t+h, não inflação acumulada dos h meses.
SIM_N = 600                    # Observações simuladas; mais dados aproximam parâmetros verdadeiros.
SIM_DESCARTE = 200             # Aquecimento para reduzir influência da condição inicial.
SIM_A = [[0.6, 0, -0.2], [0.15, 0.5, -0.1], [0.1, 0.2, 0.7]]  # Dinâmica conhecida, estável.
# SIM_A: valores didáticos assumidos; diagonais controlam persistência, cruzados transmitem efeitos.
SIM_P = [[1, 0, 0], [0.3, 0.7, 0], [0.5, 0.4, 0.6]]  # Impacto recursivo, zeros são hipóteses.
# SIM_P: diagonais dão escala às surpresas; termos abaixo da diagonal dão impactos no mesmo mês.
PAUSAR = True                  # Enter entre blocos; --lote desliga pausas e janelas.
MOSTRAR = True                 # Feche cada janela de gráfico para continuar.
PASTA_SAIDA = "resultados"      # Use resultados_teste para preservar os resultados de referência.
EXIBIR_TUDO = False             # No notebook, True também mostra itens secundários; todos são gravados.
DPI = 150                      # Qualidade PNG, sem efeito estatístico.
FONT_SIZE = 11                 # Letras dos gráficos, sem efeito estatístico.
MAX_LINHAS_TELA = 24           # Limita tabelas longas no terminal; CSV sempre contém tudo.
CASAS = 4                      # Arredondamento na tela; CSV mantém precisão.
TOL = 1e-8                     # Tolerância numérica das checagens, não significância.

from pathlib import Path
from types import SimpleNamespace
from copy import deepcopy
from itertools import permutations
import json, sys, time, warnings, os, hashlib
from importlib.metadata import version
os.environ["OPENBLAS_NUM_THREADS"] = str(THREADS)  # Uma thread: matrizes pequenas ficam mais rápidas.
os.environ["OMP_NUM_THREADS"] = str(THREADS)       # Mesmo motivo; sem efeito nas escolhas econômicas.
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import acorr_ljungbox, breaks_cusumolsresid, het_arch, recursive_olsresiduals
from statsmodels.tools.sm_exceptions import InterpolationWarning
import matplotlib
if "--lote" in sys.argv:
    MOSTRAR = PAUSAR = False
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = BASE / PASTA_SAIDA
OUT.mkdir(exist_ok=True)
EM_NOTEBOOK = False
TODAS = ["brent", "cambio", "ipa", "ipca", "selic"]
NOMES = list(TODAS)             # Variáveis do VAR; configurar() retira a Selic se pedido.
CORES = ["#166a8f", "#d78222", "#55a39b", "#8b659d", "#687786"]
plt.rcParams.update({"font.size": FONT_SIZE, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.figsize": (10, 5)})
pd.set_option("display.max_columns", 20)
pd.set_option("display.width", 160)
warnings.filterwarnings("ignore", category=FutureWarning, message=".*currently returns a plain tuple.*")
warnings.filterwarnings("ignore", category=InterpolationWarning)  # P-valores de fronteira: guia.
inicio_execucao = time.perf_counter()
assert ALFA in (0.01,0.05,0.10), "CUSUM aceita ALFA 0.01, 0.05 ou 0.10."
assert 0 < CONFIANCA < 1 and CHOQUE_PCT > 0
assert H >= max(H_REPASSE, max(FEVD_H)) and BOOT >= 39
assert sorted(ORDEM) == sorted(ORDEM_ALT) == sorted(NOMES)


# Gravados sempre; no notebook enxuto, aparecem só no anexo para a apresentação caber em 5 minutos.
SECUNDARIAS = ["02_residuos_antes", "02_residuos_depois", "02_ciclos", "02_raizes", "04_razao_antes", "04_razao_depois"]


def tabela(nome, df, tela=None):
    """Mostra e grava. tela: colunas exibidas; o CSV mantém todas."""
    df.to_csv(OUT / (nome + ".csv"), encoding="utf-8-sig", lineterminator="\n")  # Mesmo arquivo em Windows e Linux.
    if EM_NOTEBOOK and not EXIBIR_TUDO and nome in SECUNDARIAS:
        return
    df = df if tela is None else df[tela]
    visivel = df if len(df)<=MAX_LINHAS_TELA else pd.concat([df.head(MAX_LINHAS_TELA//2),df.tail(MAX_LINHAS_TELA//2)])
    if EM_NOTEBOOK:
        from IPython.display import display, Markdown
        display(Markdown("**"+nome.replace("_", " ")+"**"))
        display(visivel.round(CASAS))
    else:
        print("\n" + nome + "\n" + visivel.round(CASAS).to_string())
    if len(df)>MAX_LINHAS_TELA:
        print("[Linhas intermediárias omitidas na tela; arquivo CSV completo.]")


def figura(nome):
    plt.tight_layout()
    plt.savefig(OUT / (nome + ".png"), dpi=DPI)
    if MOSTRAR and not (EM_NOTEBOOK and not EXIBIR_TUDO and nome in SECUNDARIAS):
        plt.show()
    plt.close()


def mostrar_secundarias():
    """No notebook enxuto, exibe no anexo os itens que as células de apresentação só gravaram."""
    if not EM_NOTEBOOK or EXIBIR_TUDO:
        return
    from IPython.display import display, Markdown, Image
    etapa("A1. Itens secundários dos passos 2 e 3: resíduos por regime, raízes, ciclos e razões")
    for nome in SECUNDARIAS:
        display(Markdown("**"+nome.replace("_", " ")+"**"))
        if (OUT/(nome+".png")).exists():
            display(Image(filename=str(OUT/(nome+".png"))))
        else:
            display(pd.read_csv(OUT/(nome+".csv"),index_col=0,encoding="utf-8-sig").round(CASAS))


def etapa(texto):
    if EM_NOTEBOOK:
        from IPython.display import display, Markdown
        display(Markdown("### "+texto))
    else:
        print("\n" + "=" * 72 + "\n" + texto)
    if PAUSAR and sys.stdin.isatty():
        input("Enter para executar este bloco...")


def deterministicas(datas, sazonais=None, pulsos=None):
    sazonais = SAZONAIS if sazonais is None else sazonais
    pulsos = DUMMIES if pulsos is None else pulsos
    d = {"const": np.ones(len(datas))}  # Montado de uma vez: o bootstrap chama milhares de vezes.
    if sazonais:
        for mes in range(2, 13):  # Janeiro é referência: evita colinearidade com a constante.
            d[f"mes_{mes}"] = (datas.month == mes).astype(float)
    if pulsos:
        rotulos = datas.strftime("%Y-%m")
        for mes in MESES_ATIPICOS:
            d[mes] = (rotulos == mes).astype(float)
    return pd.DataFrame(d, index=datas)


def ajusta(y, p, sazonais=None, pulsos=None, excluir=None, d=None):
    """VAR por MQO. lstsq evita inverter para estimar.
    Criar lags ANTES das exclusões garante que um lag continue sendo um mês.
    d: determinísticas já montadas para y.index; o bootstrap as reaproveita.
    """
    excluir = EXCLUIR_2020 if excluir is None else excluir
    d = deterministicas(y.index, sazonais, pulsos) if d is None else d
    x = pd.concat([d] + [y.shift(j).add_suffix(f"_L{j}") for j in range(1, p + 1)], axis=1)
    ok = x.notna().all(axis=1)
    if excluir:
        anos = pd.Series(y.index.year == 2020, index=y.index)
        ok &= ~pd.concat([anos.shift(j, fill_value=False) for j in range(p + 1)], axis=1).any(axis=1)
    x, z = x.loc[ok], y.loc[ok]
    x = x.loc[:, (x != 0).any()]  # Pulsos fora da subamostra não são identificados.
    X, Y = x.to_numpy(), z.to_numpy()
    n, k, m = len(X), X.shape[1], y.shape[1]
    if n <= k + MIN_GRAUS_LIVRES or np.linalg.matrix_rank(X) < k:
        raise ValueError(f"Amostra insuficiente/colinear: n={n}, k={k}, p={p}. Reduza p.")
    b = np.linalg.lstsq(X, Y, rcond=None)[0]
    origem = [c.rsplit("_L",1)[0] if "_L" in c else None for c in x.columns]  # Variável de cada defasagem.
    for eq,excluidas in RESTRICOES.items():  # Restrição de zero: reestima a equação só com os regressores livres.
        if eq in y.columns:
            j, livres = y.columns.get_loc(eq), [c for c,o in enumerate(origem) if o not in excluidas]
            b[:,j] = 0
            b[livres,j] = np.linalg.lstsq(X[:,livres],Y[:,j],rcond=None)[0]
    e = Y - X @ b
    a = b[-p*m:].reshape(p, m, m).transpose(0, 2, 1)
    F = np.zeros((p*m, p*m)); F[:m] = np.concatenate(a, axis=1)
    if p > 1:
        F[m:, :-m] = np.eye((p-1)*m)
    return SimpleNamespace(y=y, X=X, Y=Y, b=b, e=e, A=a, sigma=e.T@e/(n-k),
                           n=n, k=k, m=m, p=p, datas=z.index, colunas=x.columns,
                           det=list(x.columns[:k-p*m]), raizes=np.linalg.eigvals(F))


def trecho_continuo(r):
    """Resíduos do maior trecho de meses consecutivos. Só difere de r.e ao excluir 2020."""
    meses = r.datas.to_period("M").asi8
    cortes = np.r_[0, np.flatnonzero(np.diff(meses) != 1)+1, len(r.e)]
    trecho = np.argmax(np.diff(cortes))
    return r.e[cortes[trecho]:cortes[trecho+1]]


def portmanteau(r):
    """Teste multivariado ajustado. Com buracos, usa o maior trecho contínuo."""
    e = trecho_continuo(r)
    n = len(e); L = max(LAG_DIAG, r.p + 1)
    if n <= L + r.m:
        return np.nan
    inv = np.linalg.inv(e.T@e/n)
    q = 0.0
    for j in range(1, L+1):
        c = e[j:].T @ e[:-j] / n
        q += np.trace(c.T @ inv @ c @ inv) / (n-j)
    return stats.chi2.sf(n*n*q, r.m*r.m*(L-r.p))


def criterios(y):
    linhas = []
    for p in range(1, P_MAX+1):
        r = ajusta(y.iloc[P_MAX-p:], p)  # Todos os p usam a mesma amostra efetiva.
        logdet = np.linalg.slogdet(r.e.T@r.e/r.n)[1]
        linhas.append([p, logdet+2*r.k*r.m/r.n, logdet+np.log(r.n)*r.k*r.m/r.n,
                       logdet+2*np.log(np.log(r.n))*r.k*r.m/r.n, portmanteau(r)])
    return pd.DataFrame(linhas, columns=["p", "aic", "bic", "hq", "p_autocorr"]).set_index("p")


def ma(r, horizonte=None):
    horizonte = H if horizonte is None else horizonte
    psi = np.zeros((horizonte+1, r.m, r.m)); psi[0] = np.eye(r.m)
    for h in range(1, horizonte+1):
        psi[h] = sum(r.A[j-1] @ psi[h-j] for j in range(1, min(h, r.p)+1))
    return psi


def irf(r, ordem, horizonte=None, sigma=None):
    idx = [list(r.y.columns).index(v) for v in ordem]
    s = r.sigma if sigma is None else sigma
    P = np.zeros_like(s)
    P[np.ix_(idx, idx)] = np.linalg.cholesky(s[np.ix_(idx, idx)])
    return ma(r, horizonte) @ P  # Desfaz a permutação de respostas E choques.


def resposta(r, ordem=None, sigma=None):
    ordem = ORDEM if ordem is None else ordem
    t = irf(r, ordem, sigma=sigma)
    impacto = 100*np.log1p(CHOQUE_PCT/100)
    # IPCA/IPA são taxas % simples: somar IRFs aproxima a alteração do nível de preços.
    return t[:, 3, :2].cumsum(axis=0) * impacto / np.diag(t[0])[:2]


def repasse(r, ordem=None):
    ordem = ORDEM if ordem is None else ordem
    t = irf(r, ordem, horizonte=H_REPASSE).sum(axis=0)
    return t[3, :2] / np.diag(t)[:2]  # Razão das acumuladas, distinta do choque de 10%.


def bootstrap(r, seed):
    """Wild bootstrap recursivo: um sinal comum às cinco inovações por mês.
    Preserva comovimento e permite heterocedasticidade temporal.
    Não corrige autocorrelação omitida. Mantém p/determinísticas fixos.
    """
    rng = np.random.default_rng(seed)
    bandas, razoes, denominadores, instaveis = [], [], [], 0
    pos = r.y.index.get_indexer(r.datas)
    todas = deterministicas(r.y.index)  # Mesmas datas em todas as réplicas: monta uma vez.
    d = todas.reindex(columns=r.det, fill_value=0).to_numpy()
    for _ in range(BOOT):
        ys = r.y.to_numpy().copy()
        erros = (r.e-r.e.mean(axis=0)) * np.sqrt(r.n/(r.n-r.k))
        erros *= rng.choice([-1.0, 1.0], size=(r.n, 1))
        for i, t in enumerate(pos):
            ys[t] = d[t]@r.b[:len(r.det)] + sum(r.A[j-1]@ys[t-j] for j in range(1,r.p+1)) + erros[i]
        b = ajusta(pd.DataFrame(ys, index=r.y.index, columns=r.y.columns), r.p, d=todas)
        instaveis += max(abs(b.raizes)) >= 1
        bandas.append(resposta(b)); razoes.append(repasse(b))
        denominadores.append(np.diag(irf(b,ORDEM,horizonte=H_REPASSE).sum(axis=0))[:2])
    # Não descartar réplicas instáveis: isso selecionaria resultados.
    return np.array(bandas), np.array(razoes), np.array(denominadores), instaveis/BOOT


def hac(scores, lag, meses=None):
    """Soma Newey-West com pesos Bartlett; usado no Wald e no DM/CW."""
    meat = scores.T@scores
    for j in range(1, min(lag, len(scores)-1)+1):
        ok = np.ones(len(scores)-j, bool) if meses is None else meses[j:]-meses[:-j] == j
        c = scores[j:][ok].T@scores[:-j][ok]
        meat += (1-j/(lag+1))*(c+c.T)
    return meat


def wald_granger(r, causam, recebem, p_testado):
    k, m = r.k, r.m
    if not hasattr(r, "robusta"):
        inv = np.linalg.inv(r.X.T@r.X)
        bread = np.kron(np.eye(m), inv)
        scores = np.einsum("ti,tj->tij", r.e, r.X).reshape(r.n, m*k)
        r.robusta = bread @ hac(scores,LAG_HAC,r.datas.to_period("M").asi8) @ bread * r.n/(r.n-k)
        r.usual = np.kron(r.sigma, inv)
    indices = [dest*k+len(r.det)+j*m+orig for dest in recebem for j in range(p_testado) for orig in causam]
    b = r.b.T.ravel()[indices]
    return [stats.chi2.sf(b @ np.linalg.pinv(v[np.ix_(indices, indices)]) @ b, len(indices))
            for v in (r.usual, r.robusta)]


def previsao(r, datas_futuras):
    hist = list(r.y.to_numpy())
    # Pulsos futuros sempre zero: sem conhecimento antecipado de pandemia ou greve.
    d = deterministicas(datas_futuras,pulsos=False).reindex(columns=r.det,fill_value=0).to_numpy()
    for linha in d:
        hist.append(linha@r.b[:len(r.det)] + sum(r.A[j-1]@hist[-j] for j in range(1,r.p+1)))
    return np.asarray(hist[-len(datas_futuras):])


def teste_media(x, h, unilateral=False):
    """DM: correção HLN, bilateral. CW: normal unilateral em favor do VAR."""
    n = len(x); s = np.asarray(x)-np.mean(x)
    se = np.sqrt(hac(s[:, None], max(h-1,LAG_HAC))[0,0])/n
    z = np.mean(x)/se if se > 0 else np.nan
    if unilateral:
        return stats.norm.sf(z)
    z *= np.sqrt((n+1-2*h+h*(h-1)/n)/n)
    return 2*stats.t.sf(abs(z),n-1)



PARAMETROS_PADRAO = deepcopy({nome: globals()[nome] for nome in ["INICIO","FIM","QUEBRA","ORDEM","ORDEM_ALT","P_FIXO","P_MAX","CRITERIO","AJUSTAR_P_RESIDUOS","SAZONAIS","DUMMIES","MESES_ATIPICOS","EXCLUIR_2020","DIFERENCIAR_SELIC","INCLUIR_SELIC","RESTRICOES","H","H_REPASSE","CHOQUE_PCT","CONFIANCA","BOOT","SEMENTE","ALFA","LAG_DIAG","LAG_ARCH","LAG_HAC","CUSUM_INICIAL","REG_TESTES","ADF_CRITERIO","KPSS_LAGS","MIN_GRAUS_LIVRES","THREADS","ADF_MAX","D_MAX","JANELA","PASSO_JANELA","FEVD_H","EPISODIO","INICIO_PREV","H_PREV","SIM_N","SIM_DESCARTE","SIM_A","SIM_P","PAUSAR","MOSTRAR","PASTA_SAIDA","EXIBIR_TUDO","DPI","FONT_SIZE","MAX_LINHAS_TELA","CASAS","TOL"]})

def configurar(parametros=None, notebook=False):
    """Reinicia as opções para permitir comparar cenários sem herdar alterações anteriores."""
    global OUT, EM_NOTEBOOK, PAUSAR, MOSTRAR, inicio_execucao, NOMES, ORDEM, ORDEM_ALT
    parametros = parametros or {}
    desconhecidos = set(parametros)-set(PARAMETROS_PADRAO)
    if desconhecidos:
        raise ValueError(f"Parâmetros desconhecidos: {desconhecidos}")
    globals().update(deepcopy(PARAMETROS_PADRAO | parametros))
    NOMES = [n for n in TODAS if INCLUIR_SELIC or n != "selic"]
    # Sem a Selic, ela sai das ordens; incluída mas ausente de uma ordem, entra por último.
    ORDEM, ORDEM_ALT = ([n for n in o if INCLUIR_SELIC or n != "selic"]+(["selic"] if INCLUIR_SELIC and "selic" not in o else [])
                        for o in (ORDEM, ORDEM_ALT))
    EM_NOTEBOOK = notebook
    if notebook:
        PAUSAR, MOSTRAR = False, True  # A célula é a pausa; o backend inline integra o gráfico.
    elif "--lote" in sys.argv:
        PAUSAR = MOSTRAR = False
    OUT = BASE / PASTA_SAIDA
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({"font.size":FONT_SIZE})
    assert ALFA in (0.01,0.05,0.10)
    assert H >= max(H_REPASSE,max(FEVD_H)) and BOOT >= 39
    assert 0 < CONFIANCA < 1 and CHOQUE_PCT > 0
    assert sorted(ORDEM) == sorted(ORDEM_ALT) == sorted(NOMES)
    assert all(n in TODAS for k,v in RESTRICOES.items() for n in [k,*v]), "RESTRICOES: use os nomes das variáveis."
    inicio_execucao = time.perf_counter()



def preparar_dados():
    """Lê e transforma as séries, sem tela nem gravação: as variantes reutilizam esta etapa."""
    partes = []
    for nome in ["cambio", "ipa", "ipca", "selic"]:
        d = pd.read_json(BASE/"dados"/(nome+".json"))
        partes.append(pd.Series(d["valor"].astype(float).values,
                               index=pd.to_datetime(d["data"],dayfirst=True),name=nome))
    d = pd.read_csv(BASE/"dados"/"brent.csv",index_col=0,parse_dates=True)
    partes.append(d.iloc[:,0].rename("brent"))
    brutos = pd.concat(partes,axis=1).sort_index()[TODAS]
    brutos.index.name = "data"
    assert not brutos.index.duplicated().any() and not brutos.isna().any().any()
    assert np.all(np.diff(brutos.index.to_period("M").asi8) == 1)
    assert (brutos[["brent","cambio"]] > 0).all().all()
    dados = brutos.copy()
    dados[["brent","cambio"]] = 100*np.log(brutos[["brent","cambio"]]).diff()
    if DIFERENCIAR_SELIC:
        dados["selic"] = brutos["selic"].diff()
    dados = dados.loc[INICIO:FIM, NOMES].dropna()
    assert len(dados)>JANELA and dados.index.min()<pd.Timestamp(QUEBRA)<dados.index.max()
    return brutos, dados


def carregar_dados():
    etapa(f"1. Dados: {len(NOMES)} séries mensais, públicas e salvas no repositório")
    brutos, dados = preparar_dados()
    consolidado, destino = brutos.to_csv(lineterminator="\n"), BASE/"dados"/"mensal.csv"
    if not destino.exists() or destino.read_text(encoding="utf-8") != consolidado:
        destino.write_text(consolidado, encoding="utf-8", newline="\n")  # Só regrava se os dados mudarem.
    dados.to_csv(OUT/"dados_transformados.csv", lineterminator="\n")
    print(f"{dados.index[0]:%m/%Y} a {dados.index[-1]:%m/%Y}: {len(dados)} meses. Ordem: {ORDEM}")
    fig,axs = plt.subplots(len(NOMES),1,figsize=(11,2*len(NOMES)),sharex=True)
    rotulos = ["Brent (petróleo em US$)","Câmbio (reais por dólar)","IPA-DI (produtor)","IPCA (consumidor)","Selic"]
    unidades = ["100 × Δlog\n(% aprox.)","100 × Δlog\n(% aprox.)","% no mês","% no mês","Variação (p.p.)" if DIFERENCIAR_SELIC else "% ao ano"]
    for ax,nome,titulo,unidade,cor in zip(axs,NOMES,rotulos,unidades,CORES):
        ax.plot(dados.index,dados[nome],color=cor)
        ax.set_title(titulo,loc="left",fontsize=FONT_SIZE)
        ax.set_ylabel(unidade)
    axs[-1].set_xlabel("Mês de referência")
    figura("01_series")
    linhas = []
    testadas = {**{n:dados[n] for n in NOMES}, "log_Brent_nivel":np.log(brutos.brent),
                "log_cambio_nivel":np.log(brutos.cambio)}
    for nome,x in testadas.items():
        x = x.loc[INICIO:FIM].dropna()
        linhas.append([nome,adfuller(x,maxlag=ADF_MAX,regression=REG_TESTES,autolag=ADF_CRITERIO)[1],
                       kpss(x,regression=REG_TESTES,nlags=KPSS_LAGS)[1]])
    tabela("01_estacionariedade",pd.DataFrame(linhas,columns=["serie","ADF_p","KPSS_p"]).set_index("serie"))
    print("ADF: H0 raiz unitária. KPSS: H0 estacionariedade. P-valores de fronteira são limites.")
    return dados


def escolher_p(dados):
    """Critério de informação; se pedido, o primeiro p maior ou igual que passa o Portmanteau."""
    ic = criterios(dados)
    p_ic = int(ic[CRITERIO].idxmin())
    candidatos = ic.loc[ic.index >= p_ic]
    aceitos = candidatos.index[candidatos.p_autocorr > ALFA]
    p = int(P_FIXO) if P_FIXO is not None else (int(aceitos[0]) if AJUSTAR_P_RESIDUOS and len(aceitos) else p_ic)
    return p, ic


def separar_regimes(dados, p):
    """Mesmo p antes e depois; cada regime usa seus primeiros p meses como condição inicial."""
    return {"antes":ajusta(dados.loc[dados.index < QUEBRA],p),
            "depois":ajusta(dados.loc[dados.index >= QUEBRA],p)}


def estimar_modelos(dados):
    etapa("2. Escolha de p, resíduos e estabilidade dinâmica")
    p, ic = escolher_p(dados); tabela("02_defasagens",ic)
    modelo = ajusta(dados,p)
    regimes = separar_regimes(dados,p)
    diagnosticos, autocorrelacionadas = [], {}
    for nome,r in {"completa":modelo,**regimes}.items():
        raio = max(abs(r.raizes))
        meia = np.log(0.5)/np.log(raio) if 0 < raio < 1 else np.nan
        diagnosticos.append([nome,r.n,r.k,p,raio,meia,portmanteau(r)])
        e = trecho_continuo(r)  # Ljung-Box por equação localiza a autocorrelação do Portmanteau.
        eq = pd.DataFrame({"LB_p":[acorr_ljungbox(e[:,j],lags=[LAG_DIAG])["lb_pvalue"].iloc[0] for j in range(r.m)],
                           "JB_p":[stats.jarque_bera(r.e[:,j]).pvalue for j in range(r.m)],
                           "ARCH_p":[het_arch(r.e[:,j],nlags=LAG_ARCH,ddof=r.k)[1] for j in range(r.m)]},index=NOMES)
        autocorrelacionadas[nome] = list(eq.index[eq.LB_p <= ALFA])
        tabela("02_residuos_"+nome,eq)
        inv = np.linalg.inv(r.X.T@r.X)
        coef = []
        for j,variavel in enumerate(NOMES):
            usual = np.sqrt(np.diag(inv)*r.sigma[j,j])
            robusta = inv@hac(r.X*r.e[:,j,None],LAG_HAC,r.datas.to_period("M").asi8)@inv*r.n/(r.n-r.k)
            se_hac = np.sqrt(np.maximum(np.diag(robusta),0))
            for k,regressor in enumerate(r.colunas):
                coef.append([variavel,regressor,r.b[k,j],usual[k],r.b[k,j]/usual[k],se_hac[k],r.b[k,j]/se_hac[k]])
        pd.DataFrame(coef,columns=["equacao","regressor","coef","se_usual","t_usual","se_HAC","z_HAC"]).to_csv(OUT/("02_coeficientes_"+nome+".csv"),index=False,lineterminator="\n")
        if raio >= 1:
            print("ATENÇÃO:",nome,"instável: não interpretar meia-vida nem respostas como convergentes.")
    diag = pd.DataFrame(diagnosticos,columns=["amostra","n","k_por_eq","p","raio","meia_vida","Portmanteau_p"]).set_index("amostra")
    tabela("02_diagnostico",diag)
    ciclos = [[abs(z),2*np.pi/abs(np.angle(z))] for z in modelo.raizes if z.imag > TOL]
    tabela("02_ciclos",pd.DataFrame(ciclos,columns=["modulo","periodo_meses"]))
    print("Meia-vida: modo dominante, não necessariamente a meia-vida de cada IRF.")
    if (diag.Portmanteau_p <= ALFA).any():
        print("RESSALVA: autocorrelação residual. Bootstrap e p-valores exigem cautela; teste outro p.")
        print("Equações com Ljung-Box <= ALFA:", ", ".join(f"{k}: {v or 'nenhuma'}" for k,v in autocorrelacionadas.items()))
    
    fig,ax = plt.subplots(figsize=(5,5))
    ang = np.linspace(0,2*np.pi,300)  # 300 pontos apenas desenham o círculo unitário.
    ax.plot(np.cos(ang),np.sin(ang),color="gray",ls="--")
    ax.scatter(modelo.raizes.real,modelo.raizes.imag,color=CORES[0])
    ax.set(xlabel="Parte real",ylabel="Parte imaginária",title="Autovalores da matriz companheira",aspect="equal")
    figura("02_raizes")
    return modelo, regimes, diag


def testar_granger(dados, p):
    etapa("A2. Granger condicional, usual e robusto HAC")
    g = ajusta(dados,p+D_MAX)  # Toda-Yamamoto: só os p primeiros lags são testados.
    linhas = []
    for causa in range(len(NOMES)):
        for destino in range(len(NOMES)):
            if causa != destino:
                linhas.append([NOMES[causa],NOMES[destino],*wald_granger(g,[causa],[destino],p)])
    linhas.append(["Brent+câmbio","IPA+IPCA",*wald_granger(g,[0,1],[2,3],p)])
    granger = pd.DataFrame(linhas,columns=["causa","destino","Wald_usual_p","Wald_HAC_p"])
    tabela("03_granger",granger)
    print(f"VAR aumentado p+dmax={p+D_MAX}; testamos p={p}. dmax={D_MAX} deve cobrir a integração.")
    return granger


def comparar_choques(regimes):
    etapa("3. Experimento: resposta do IPCA ao Brent e ao câmbio, antes e depois da quebra")
    q = [(1-CONFIANCA)/2,(1+CONFIANCA)/2]
    boots,ratios,denominadores,fracao_instavel = {},{},{},{}
    for i,(nome,r) in enumerate(regimes.items()):
        boots[nome],ratios[nome],denominadores[nome],fracao_instavel[nome] = bootstrap(r,SEMENTE+i)
        print(nome,f"{BOOT} réplicas; {100*fracao_instavel[nome]:.1f}% com raiz >= 1")
    fig,axes = plt.subplots(1,2,figsize=(12,4.8))
    linhas = []
    for j,choque in enumerate(["brent","cambio"]):
        for nome,cor in zip(regimes,CORES):
            ponto = resposta(regimes[nome])[:,j]
            lo,hi = np.quantile(boots[nome][:,:,j],q,axis=0)
            axes[j].plot(range(H+1),ponto,label=nome,color=cor)
            axes[j].fill_between(range(H+1),lo,hi,alpha=.15,color=cor)
            s = regimes[nome].sigma  # Correlação, no mesmo mês, entre as surpresas da origem e do IPCA.
            linhas.append([choque,nome,ponto[H_REPASSE],lo[H_REPASSE],hi[H_REPASSE],ponto[0],s[3,j]/np.sqrt(s[3,3]*s[j,j])])
        axes[j].axhline(0,color="gray",lw=1); axes[j].set_title(f"{choque.capitalize()}: +{CHOQUE_PCT:g}% no impacto")
        axes[j].set(xlabel="Meses após o choque",ylabel="IPCA acumulado (p.p., aprox.)"); axes[j].legend()
    figura("04_irf_antes_depois")
    resumo = pd.DataFrame(linhas,columns=["choque","amostra","resposta","inferior","superior","impacto_h0","corr_residuo_ipca"])
    tabela("04_respostas_12m",resumo)
    print(f"impacto_h0: resposta no próprio mês do choque, já incluída na soma até h={H_REPASSE}.")
    delta = boots["depois"][:,H_REPASSE,:]-boots["antes"][:,H_REPASSE,:]
    mudanca = resposta(regimes["depois"])[H_REPASSE]-resposta(regimes["antes"])[H_REPASSE]
    limites = np.quantile(delta,q,axis=0)
    dif = pd.DataFrame({"depois_menos_antes":mudanca,"inferior":limites[0],"superior":limites[1]},index=NOMES[:2])
    tabela("04_diferenca",dif)
    print("Compare a banda da DIFERENÇA com zero. Sobreposição de bandas separadas não é um teste.")
    for nome,r in regimes.items():
        d_lo,d_hi = np.quantile(denominadores[nome],q,axis=0)
        fragil = (d_lo <= 0) & (d_hi >= 0)
        t = irf(r,ORDEM,horizonte=H_REPASSE)  # Alta acumulada da própria origem após o mesmo choque inicial.
        origem = np.diag(t.sum(axis=0))[:2]*100*np.log1p(CHOQUE_PCT/100)/np.diag(t[0])[:2]
        tabela("04_razao_"+nome,pd.DataFrame({"elasticidade_aprox":repasse(r),
               "inferior":np.quantile(ratios[nome],q[0],axis=0),
               "superior":np.quantile(ratios[nome],q[1],axis=0),"denominador_cruza_zero":fragil,
               "origem_acumulada":origem},index=NOMES[:2]))
        if fragil.any():
            print("ATENÇÃO: razão frágil, denominador compatível com zero. Priorize resposta normalizada.")
    print(f"origem_acumulada: 100×log da própria origem em h={H_REPASSE}. Mesmo choque inicial, trajetórias diferentes.")
    return {"respostas":resumo,"diferenca":dif,"bootstrap_instavel":fracao_instavel}


def identificacao(regimes):
    """Ordem dos choques e repasse no mesmo mês. Rápido: reaproveita os dois VARs, sem bootstrap."""
    ordens = [list(o) for o in permutations(NOMES)]
    etapa(f"4. Identificação: {len(ordens)} ordens e mesmo mês versus defasagens")
    mudancas_ordens = np.array([resposta(regimes["depois"],o)[H_REPASSE]-resposta(regimes["antes"],o)[H_REPASSE] for o in ordens])
    base = resposta(regimes["depois"])[H_REPASSE]-resposta(regimes["antes"])[H_REPASSE]
    ipca_antes = np.array([[o.index("ipca") < o.index(v) for v in NOMES[:2]] for o in ordens])  # IPCA não reage no mês.
    envelope = pd.DataFrame({"min_delta":mudancas_ordens.min(axis=0),
           "max_delta":mudancas_ordens.max(axis=0),"fracao_delta_positivo":(mudancas_ordens>0).mean(axis=0),
           "base":base,"quantil_base":(mudancas_ordens <= base+TOL).mean(axis=0),
           "min_IPCA_antes":np.where(ipca_antes,mudancas_ordens,np.inf).min(axis=0),
           "max_IPCA_antes":np.where(ipca_antes,mudancas_ordens,-np.inf).max(axis=0)},index=NOMES[:2])
    tabela(f"05_mudanca_{len(ordens)}_ordens",envelope)
    print("quantil_base = fração das ordens com diferença <= base; 1 indica a ordem-base no topo do envelope.")
    print("IPCA_antes: ordens com o IPCA antes da origem do choque, isto é, sem repasse no mesmo mês.")
    # Linhas trocam A (propagação pelas defasagens); colunas trocam Sigma (relações no mesmo mês).
    # Decomposição descritiva e não única; não identifica a Petrobras.
    grade = pd.DataFrame([[choque,nome,*[resposta(ra,sigma=rs.sigma)[H_REPASSE,j] for rs in regimes.values()]]
                          for j,choque in enumerate(NOMES[:2]) for nome,ra in regimes.items()],
                         columns=["choque","A_defasagens","Sigma_antes","Sigma_depois"]).set_index(["choque","A_defasagens"])
    tabela("05_impacto_vs_propagacao",grade)
    # Uma restrição só, contra 55 do Chow do sistema: a relação Brent-IPCA no mesmo mês mudou?
    ea,ed = regimes["antes"].e,regimes["depois"].e
    x,y,pos = np.r_[ea[:,0],ed[:,0]],np.r_[ea[:,3],ed[:,3]],np.r_[np.zeros(len(ea)),np.ones(len(ed))]
    mm = sm.OLS(y,np.column_stack([np.ones_like(x),pos,x,x*pos])).fit(cov_type="HC1")
    impacto = 100*np.log1p(CHOQUE_PCT/100)
    tabela("05_teste_mesmo_mes",pd.DataFrame([{"impacto_antes":mm.params[2]*impacto,"impacto_depois":(mm.params[2]+mm.params[3])*impacto,
           "diferenca":mm.params[3]*impacto,"p_HC1":mm.pvalues[3],"restricoes":1}]))
    print("Mesmo mês: resíduo do IPCA sobre o do Brent, com interação pós-quebra. Uma restrição; o Chow do sistema testa 55.")
    g = grade.loc["brent"]
    efeito_sigma = [g.loc[a,"Sigma_depois"]-g.loc[a,"Sigma_antes"] for a in ("antes","depois")]
    efeito_a = [g.loc["depois",s]-g.loc["antes",s] for s in ("Sigma_antes","Sigma_depois")]
    print(f"Brent: trocar só Sigma muda {min(efeito_sigma):+.3f} a {max(efeito_sigma):+.3f} p.p.; "
          f"trocar só A, {min(efeito_a):+.3f} a {max(efeito_a):+.3f} p.p.")
    return {"envelope":envelope,"impacto_propagacao":grade}


def verificar_robustez(dados, modelo, regimes, choques):
    p = modelo.p
    q = [(1-CONFIANCA)/2,(1+CONFIANCA)/2]
    fracao_instavel = choques["bootstrap_instavel"]
    ordens = [list(o) for o in permutations(NOMES)]
    etapa(f"A3. Envelope de {len(ordens)} ordens na amostra completa, correlação residual e FEVD")
    b_total,_,_,inst_total = bootstrap(modelo,SEMENTE+2)
    fracao_instavel["completa"] = inst_total
    envoltorio = np.array([resposta(modelo,o) for o in ordens])
    corr = pd.DataFrame(np.corrcoef(modelo.e.T),index=NOMES,columns=NOMES)
    tabela("05_correlacao_residuos",corr)
    fig,axes = plt.subplots(1,2,figsize=(12,4.8))
    for j,ax in enumerate(axes):
        ax.fill_between(range(H+1),envoltorio[:,:,j].min(axis=0),envoltorio[:,:,j].max(axis=0),alpha=.2,color=CORES[j],label=f"{len(ordens)} ordens (min-max)")
        lo,hi = np.quantile(b_total[:,:,j],q,axis=0)
        ax.plot(lo,color=CORES[j],ls=":",label=f"IC pontual {CONFIANCA:.0%}")
        ax.plot(hi,color=CORES[j],ls=":")
        ax.plot(resposta(modelo)[:,j],color=CORES[j],label="Ordem-base")
        ax.axhline(0,color="gray",lw=1); ax.set(title=NOMES[j],xlabel="Meses",ylabel="IPCA acumulado (p.p., aprox.)"); ax.legend()
    figura("05_envelope")
    print("Envelope: sensibilidade à identificação, NÃO intervalo de confiança.")
    fevds = []
    for label,ordem in [("base",ORDEM),("alternativa",ORDEM_ALT)]:
        t = irf(modelo,ordem)
        for h in FEVD_H:
            v = (t[:h]**2).sum(axis=0); v = v/v.sum(axis=1,keepdims=True)
            assert np.allclose(v.sum(axis=1),1,atol=TOL)
            fevds.append([label,h,*100*v[3]])
    tabela("05_fevd_ipca",pd.DataFrame(fevds,columns=["ordem","h",*NOMES]))

    etapa("A4. Chow na data conhecida, CUSUM e repasse móvel")
    r = modelo
    post = (r.datas >= QUEBRA).astype(float)
    quebram = [0]+list(range(len(r.det),r.k))  # Constante/lags mudam; calendário/pulsos comuns.
    XU = np.column_stack([r.X,r.X[:,quebram]*post[:,None]])
    R = np.eye(XU.shape[1])[r.k:]
    linhas,erros_u = [],[]
    for j,nome in enumerate(NOMES):
        ols = sm.OLS(r.Y[:,j],XU).fit()
        linhas.append([nome,float(ols.f_test(R).pvalue),float(ols.get_robustcov_results(cov_type="HAC",maxlags=LAG_HAC,use_correction=True).f_test(R).pvalue)])
        erros_u.append(ols.resid)
    tabela("06_chow",pd.DataFrame(linhas,columns=["equacao","Chow_F_p","Wald_HAC_p"]).set_index("equacao"))
    tabela("06_cusum_ols",pd.DataFrame([[nome,*breaks_cusumolsresid(r.e[:,j],ddof=r.k)[:2]] for j,nome in enumerate(NOMES)],
           columns=["equacao","estatistica","p"]).set_index("equacao"))
    print("OLS-CUSUM de Ploberger-Krämer, padrão de vars::stability() no R. H0: coeficientes estáveis.")
    eu = np.column_stack(erros_u)
    lr = r.n*(np.linalg.slogdet(r.e.T@r.e/r.n)[1]-np.linalg.slogdet(eu.T@eu/r.n)[1])
    q_chow = len(quebram)*r.m
    tabela("06_quebra_conjunta",pd.DataFrame([{"LR":lr,"restricoes":q_chow,"p_assintotico":stats.chi2.sf(lr,q_chow)}]))
    print(f"{len(quebram)} restrições/equação; {q_chow} no sistema. LR supõe covariância comum; inferência exploratória em níveis.")
    # CUSUM recursivo auxiliar SEM pulsos: pulsos tardios tornam singular a amostra inicial.
    rc = ajusta(dados,p,pulsos=False)
    fig,axs = plt.subplots(len(NOMES),1,figsize=(10,2*len(NOMES)),sharex=True)
    for j,ax in enumerate(axs):
        skip = max(rc.k+1,CUSUM_INICIAL)  # Pelo menos 3 anos e posto completo antes da recursão.
        rr = recursive_olsresiduals(sm.OLS(rc.Y[:,j],rc.X).fit(),skip=skip,alpha=1-ALFA)
        cs,band = rr[5][1:],rr[6]
        xs = rc.datas[-len(cs):]
        ax.plot(xs,cs,color=CORES[j]); ax.plot(xs,band.T,color="gray",ls="--")
        ax.set_ylabel(NOMES[j]); ax.axvline(pd.Timestamp(QUEBRA),color="black",lw=.7)
    figura("06_cusum")
    movel = []
    for fim in range(JANELA,len(dados)+1,PASSO_JANELA):
        rw = ajusta(dados.iloc[fim-JANELA:fim],p)
        movel.append([dados.index[fim-1],*repasse(rw),max(abs(rw.raizes))])
    movel = pd.DataFrame(movel,columns=["data","brent","cambio","raio"]).set_index("data")
    tabela("06_repasse_movel",movel)
    fig,ax = plt.subplots(figsize=(11,5))
    for nome,label,cor in zip(["brent","cambio"],["Petróleo (Brent)","Câmbio (reais por dólar)"],CORES):
        ax.plot(movel.index,movel[nome],label=label,color=cor)
    ax.axvline(pd.Timestamp(QUEBRA),color="gray",ls="--",label="Início do regime pós-quebra: "+pd.Timestamp(QUEBRA).strftime("%m/%Y"))
    ax.set(title=f"Repasse em janelas móveis de {JANELA} meses",xlabel="Fim da janela de estimação",
           ylabel=f"Razão acumulada até h={H_REPASSE}\n(elasticidade aproximada)")
    ax.legend(); figura("06_repasse_movel")
    print("CUSUM sem pulsos: episódios extremos também podem provocar rejeição. Janelas se sobrepõem.")
    return movel


def completar_analise(dados, modelo):
    p = modelo.p
    etapa("A5. Decomposição histórica, com conferência exata da soma")
    r = modelo; Y = dados.to_numpy(); n = len(Y)
    P = irf(r,ORDEM,horizonte=0)[0]
    d = deterministicas(dados.index).reindex(columns=r.det,fill_value=0).to_numpy()
    base = Y.copy(); contribuicoes = np.zeros((n,r.m,r.m))
    for t in range(p,n):
        esperado = d[t]@r.b[:len(r.det)]+sum(r.A[j-1]@Y[t-j] for j in range(1,p+1))
        u = np.linalg.solve(P,Y[t]-esperado)
        base[t] = d[t]@r.b[:len(r.det)]+sum(r.A[j-1]@base[t-j] for j in range(1,p+1))
        contribuicoes[t] = P*u[None,:]+sum(r.A[j-1]@contribuicoes[t-j] for j in range(1,p+1))
    erro_hd = float(np.max(abs(base+contribuicoes.sum(axis=2)-Y)))
    assert erro_hd < TOL
    hd = pd.DataFrame(contribuicoes[:,3,:],index=dados.index,columns=NOMES)
    hd["deterministica_iniciais"] = base[:,3]; hd["observado"] = Y[:,3]
    hd.to_csv(OUT/"07_decomposicao.csv",lineterminator="\n")
    ep = hd.loc[EPISODIO[0]:EPISODIO[1]]
    ax = ep[NOMES].set_axis(ep.index.strftime("%Y-%m")).plot.bar(stacked=True,color=CORES[:r.m],figsize=(12,5))
    ax.plot(range(len(ep)),ep.observado-ep.deterministica_iniciais,color="black",label="IPCA menos base")
    ax.set_xticklabels(ep.index.strftime("%Y-%m"),rotation=60); ax.set_ylabel("IPCA mensal (p.p.)"); ax.legend(ncol=3)
    figura("07_decomposicao")
    print(f"Erro máximo de reconstrução: {erro_hd:.2e}. Base: constante, calendário, pulsos e condições iniciais.")
    
    etapa("A6. Simulação com dinâmica e impactos conhecidos")
    rng = np.random.default_rng(SEMENTE); A = np.asarray(SIM_A); P = np.asarray(SIM_P)
    assert max(abs(np.linalg.eigvals(A))) < 1
    sim = np.zeros((SIM_N+SIM_DESCARTE,3)); shocks = rng.standard_normal(sim.shape)
    for t in range(1,len(sim)):
        sim[t] = A@sim[t-1]+P@shocks[t]
    sim = pd.DataFrame(sim[SIM_DESCARTE:],columns=["produto","inflacao","juros"],index=pd.date_range("1900-01-01",periods=SIM_N,freq="MS"))
    s = ajusta(sim,1,sazonais=False,pulsos=False,excluir=False)
    verdade = np.array([np.linalg.matrix_power(A,h)@P for h in range(H+1)])
    certa = irf(s,list(sim.columns)); errada = irf(s,["juros","produto","inflacao"])
    fig,axs = plt.subplots(1,3,figsize=(12,4))
    for j,ax in enumerate(axs):
        ax.plot(verdade[:,j,2]/P[2,2],label="Verdade",color="black")
        ax.plot(certa[:,j,2]/certa[0,2,2],label="Ordem certa",color=CORES[0])
        ax.plot(errada[:,j,2]/errada[0,2,2],label="Ordem errada",color=CORES[1],ls="--")
        ax.set_title(sim.columns[j]); ax.set_xlabel("Horizonte"); ax.legend()
    figura("08_simulacao")
    rmse_certa = np.sqrt(np.mean((verdade[:,:,2]/P[2,2]-certa[:,:,2]/certa[0,2,2])**2))
    rmse_errada = np.sqrt(np.mean((verdade[:,:,2]/P[2,2]-errada[:,:,2]/errada[0,2,2])**2))
    print("Ordem correta mais próxima nesta simulação:", rmse_certa < rmse_errada)
    tabela("08_simulacao",pd.DataFrame({"RMSE_IRF":[rmse_certa,rmse_errada]},index=["certa","errada"]))
    
    etapa("A7. Previsão em janela expansiva: VAR contra AR e passeio aleatório")
    previsoes = []
    for t in range(P_MAX+24,len(dados)-min(H_PREV)):
        if dados.index[t] < pd.Timestamp(INICIO_PREV):
            continue
        treino = dados.iloc[:t+1]
        pv = int(P_FIXO) if P_FIXO is not None else int(criterios(treino)[CRITERIO].idxmin())
        rv = ajusta(treino,pv)
        univ = treino[["ipca"]]
        pa = pv  # Mesmo p e determinísticas: AR é a restrição univariada do VAR (teste CW).
        ra = ajusta(univ,pa)
        datas = pd.date_range(treino.index[-1]+pd.offsets.MonthBegin(1),periods=max(H_PREV),freq="MS")
        fv,fa = previsao(rv,datas)[:,3],previsao(ra,datas)[:,0]
        # Ingênuo sazonal repete os últimos 12 meses. Referência não aninhada para DM se p<12.
        for h in H_PREV:
            if t+h < len(dados):
                previsoes.append([dados.index[t],dados.index[t+h],h,dados.ipca.iloc[t+h],fv[h-1],fa[h-1],dados.ipca.iloc[t],dados.ipca.iloc[t-11+(h-1)%12],pv,pa])
    prev = pd.DataFrame(previsoes,columns=["origem","alvo","h","real","VAR","AR","RW","Sazonal","p_VAR","p_AR"])
    prev.to_csv(OUT/"09_previsoes.csv",index=False,lineterminator="\n")
    metricas = []
    for h in H_PREV:
        v = prev.loc[prev.h==h]
        ev = v.real-v.VAR
        for nome in ["VAR","AR","RW","Sazonal"]:
            e = v.real-v[nome]
            dm = teste_media(ev**2-e**2,h) if nome=="Sazonal" and v.p_VAR.max()<12 else np.nan
            cw = teste_media(e**2-ev**2+(v[nome]-v.VAR)**2,h,True) if nome=="AR" else np.nan
            metricas.append([h,nome,len(v),np.sqrt(np.mean(e**2)),np.mean(abs(e)),dm,cw])
    metricas = pd.DataFrame(metricas,columns=["h","modelo","n","RMSE","MAE","DM_VAR_vs_modelo_p","CW_favor_VAR_p"])
    tabela("09_metricas",metricas)
    fig,axs = plt.subplots(1,2,figsize=(12,4))
    for ax,h in zip(axs,H_PREV):
        v = prev[prev.h==h]
        ax.plot(v.alvo,v.real,color="black",lw=1,label="Real")
        ax.plot(v.alvo,v.VAR,color=CORES[0],lw=1,label="VAR")
        ax.set_title(f"IPCA do mês t+{h}"); ax.set_ylabel("% no mês"); ax.legend()
    figura("09_previsao")
    print("Pseudo fora da amostra: séries atuais/revisadas, sem reconstruir vintages/calendário de divulgação.")
    print("Sem dados posteriores à origem na estimação. DM: VAR vs sazonal, bilateral; CW: VAR vs AR, unilateral.")
    print("RW é referência descritiva. AR é aninhado no VAR; não interpretar DM entre eles.")
    return {"erro_hd":erro_hd,"sim_certa":rmse_certa,"sim_errada":rmse_errada,"metricas":metricas}


VARIANTES = [  # (grupo, rótulo, mudanças). As demais opções vêm do painel; edite ou acrescente linhas.
    ("Referência", "Base: painel atual", {}),
    ("Defasagens", "p = 1", {"P_FIXO": 1}),
    ("Defasagens", "p = 4", {"P_FIXO": 4}),
    ("Selic", "Selic em diferença", {"DIFERENCIAR_SELIC": True}),
    ("Selic", "Sem a Selic (4 variáveis)", {"INCLUIR_SELIC": False}),
    ("Episódios", "Sem pulsos de 2018 e 2020", {"DUMMIES": False}),
    ("Episódios", "Excluir 2020", {"EXCLUIR_2020": True}),
    ("Episódios", "Pulsos: corte do ICMS 07-08/2022", {"MESES_ATIPICOS": MESES_ATIPICOS+["2022-07", "2022-08"]}),
    ("Episódios", "Pulsos: tarifaço 01-03/2015", {"MESES_ATIPICOS": MESES_ATIPICOS+["2015-01", "2015-02", "2015-03"]}),
    ("Amostra", "Fim em 04/2023 (antes da nova estratégia)", {"FIM": "2023-04-01"}),
    ("Amostra", "Fim em 12/2025 (sem a alta de 2026)", {"FIM": "2025-12-01"}),
    ("Amostra", "Fim em 12/2021 (sem 2022 em diante)", {"FIM": "2021-12-01"}),
    ("Identificação", "Câmbio antes do Brent", {"ORDEM": ["cambio", "brent", "ipa", "ipca", "selic"]}),
    ("Identificação", "IPCA primeiro (sem repasse no mês)", {"ORDEM": ["ipca", "brent", "cambio", "ipa", "selic"]}),
    ("Restrição", "Brent exógeno ao Brasil", {"RESTRICOES": {"brent": ["cambio", "ipa", "ipca", "selic"]}}),
]


def variantes(lista=None):
    """Repete o experimento principal mudando uma escolha por vez, sem gravar etapas intermediárias.
    Mesmas sementes da célula 4: com o painel inalterado, a linha-base reproduz a banda principal.
    """
    global inicio_execucao
    lista = VARIANTES if lista is None else lista
    etapa(f"5. Variantes: o sinal, a magnitude e a banda resistem? ({len(lista)} especificações)")
    painel, notebook, relogio = {nome:deepcopy(globals()[nome]) for nome in PARAMETROS_PADRAO}, EM_NOTEBOOK, inicio_execucao
    q = [(1-CONFIANCA)/2,(1+CONFIANCA)/2]
    linhas = []
    try:
        for grupo,rotulo,mudancas in lista:
            try:
                configurar(painel | mudancas, notebook)
                dados = preparar_dados()[1]
                regimes = separar_regimes(dados,escolher_p(dados)[0])
                boots = [bootstrap(r,SEMENTE+i)[0][:,H_REPASSE,:] for i,r in enumerate(regimes.values())]
                antes,depois = (resposta(r)[H_REPASSE] for r in regimes.values())
                lo,hi = np.quantile(boots[1]-boots[0],q,axis=0)
                linhas.append([grupo,rotulo,regimes["antes"].p,regimes["antes"].n,regimes["depois"].n,antes[0],depois[0],
                               depois[0]-antes[0],lo[0],hi[0],depois[1]-antes[1],lo[1],hi[1]])
            except (ValueError, AssertionError, np.linalg.LinAlgError) as erro:
                print(f"Variante '{rotulo}' não estimada: {erro}")
                linhas.append([grupo,rotulo,*[np.nan]*11])
    finally:
        configurar(painel, notebook)  # Volta ao painel; as células seguintes não herdam a última variante.
        inicio_execucao = relogio
    tab = pd.DataFrame(linhas,columns=["grupo","variante","p","n_antes","n_depois","brent_antes","brent_depois",
                                       "brent_diferenca","brent_inferior","brent_superior",
                                       "cambio_diferenca","cambio_inferior","cambio_superior"]).set_index("variante")
    tabela("10_variantes",tab,tela=["grupo","p","brent_diferenca","brent_inferior","brent_superior"])
    grafico_variantes(tab)
    especificacao = tab[tab.grupo != "Identificação"].dropna(subset=["brent_diferenca"])
    exclui = (especificacao.brent_inferior > 0) | (especificacao.brent_superior < 0)
    print(f"Brent, {len(especificacao)} especificações: diferença positiva em {(especificacao.brent_diferenca > 0).sum()}, "
          f"de {especificacao.brent_diferenca.min():.2f} a {especificacao.brent_diferenca.max():.2f} p.p.; "
          f"banda de {CONFIANCA:.0%} exclui zero em {exclui.sum()}.")
    print("Identificação muda a pergunta: IPCA primeiro proíbe o repasse no mês e mostra o peso do impacto imediato.")
    print("Câmbio: compare magnitude e banda entre linhas; a instabilidade impede leitura estrutural.")
    return tab


def grafico_variantes(tab):
    """Uma série, uma cor. Ponto cheio: banda exclui zero; vazio: inclui. Grupos separam as perguntas."""
    fig,ax = plt.subplots(figsize=(11,0.36*(len(tab)+tab.grupo.nunique())+1.8))
    marcas, pos = [], 0.0
    for i,(rotulo,row) in enumerate(tab.iterrows()):
        if i == 0 or row.grupo != tab.grupo.iloc[i-1]:
            pos += 0.4 if i else 0
            if row.grupo != "Referência":
                marcas.append((pos,row.grupo,"grupo")); pos += 1
        marcas.append((pos,rotulo,"base" if row.grupo == "Referência" else "variante"))
        exclui = row.brent_inferior > 0 or row.brent_superior < 0
        ax.plot([row.brent_inferior,row.brent_superior],[pos,pos],color=CORES[0],lw=2,solid_capstyle="round")
        ax.plot(row.brent_diferenca,pos,"o",ms=8,mew=1.5 if exclui else 2,
                mfc=CORES[0] if exclui else "white",mec="white" if exclui else CORES[0])
        pos += 1
    ax.axvline(0,color="#56616b",lw=1)
    referencia = tab.loc[tab.grupo == "Referência","brent_diferenca"]
    if len(referencia):
        ax.axvline(referencia.iloc[0],color=CORES[0],lw=1,alpha=.35)
        ax.text(referencia.iloc[0],-0.75,f"base {referencia.iloc[0]:+.2f}",ha="center",va="bottom",color="#56616b")
    ax.set_yticks([y for y,_,_ in marcas],[t for _,t,_ in marcas])
    for (_,_,tipo),texto in zip(marcas,ax.get_yticklabels()):
        texto.set_fontweight("normal" if tipo == "variante" else "bold")
        texto.set_color("#56616b" if tipo == "grupo" else "black")
    ax.set_ylim(pos-0.4,-1.3)  # Invertido: primeira variante no topo.
    ax.tick_params(axis="y",length=0); ax.spines["left"].set_visible(False)
    ax.grid(axis="x",color="#e3e6e8",lw=.8); ax.set_axisbelow(True)
    ax.legend(handles=[Line2D([],[],color=CORES[0],lw=2,marker="o",ms=8,mfc=CORES[0],mec="white",mew=1.5,
                              label=f"Banda de {CONFIANCA:.0%} exclui zero"),
                       Line2D([],[],color=CORES[0],lw=2,marker="o",ms=8,mfc="white",mec=CORES[0],mew=2,
                              label="Banda inclui zero")],loc="upper center",bbox_to_anchor=(0.5,-0.07),ncol=2,frameon=False)
    ax.set_title(f"Diferença depois − antes: IPCA acumulado até h={H_REPASSE} após +{CHOQUE_PCT:g}% no Brent",loc="left")
    ax.set_xlabel("p.p. (ponto: estimativa; linha: banda bootstrap)")
    figura("10_variantes")


def anexo(dados, modelo, regimes, diag, choques, ident=None, tabela_variantes=None):
    """Demais exigências do desafio numa chamada: rode depois da apresentação ou quando pedirem."""
    mostrar_secundarias()
    testar_granger(dados,modelo.p)
    verificar_robustez(dados,modelo,regimes,choques)
    complemento = completar_analise(dados,modelo)
    return salvar_resumo(dados,modelo,diag,choques,complemento,ident,tabela_variantes)


def salvar_resumo(dados, modelo, diag, choques, complemento, ident=None, tabela_variantes=None):
    p = modelo.p
    resumo, dif = choques["respostas"], choques["diferenca"]
    fracao_instavel = choques["bootstrap_instavel"]
    erro_hd = complemento["erro_hd"]
    rmse_certa,rmse_errada = complemento["sim_certa"],complemento["sim_errada"]
    metricas = complemento["metricas"]
    etapa("A8. Síntese e arquivos para a apresentação")
    cautela = {"cambio":" Magnitude e banda instáveis entre especificações: não é efeito estrutural da depreciação."}
    mensagens = []
    for choque,row in dif.iterrows():
        conclusao = "aumento" if row.inferior>0 else ("redução" if row.superior<0 else "mudança inconclusiva")
        msg = f"{choque.capitalize()}: {conclusao} na resposta acumulada do IPCA em h={H_REPASSE}, nesta especificação.{cautela.get(choque,'')}"
        mensagens.append(msg)
    r = resumo.set_index(["choque","amostra"]).loc["brent"]
    mensagens.append(f"Brent no mês do choque: {r.loc['antes','impacto_h0']:+.3f} p.p. antes e {r.loc['depois','impacto_h0']:+.3f} depois; "
                     f"correlação das surpresas Brent-IPCA {r.loc['antes','corr_residuo_ipca']:+.2f} e {r.loc['depois','corr_residuo_ipca']:+.2f}.")
    if tabela_variantes is not None:
        e = tabela_variantes[tabela_variantes.grupo != "Identificação"].dropna(subset=["brent_diferenca"])
        mensagens.append(f"Brent em {len(e)} especificações: positiva em {(e.brent_diferenca > 0).sum()}, de "
                         f"{e.brent_diferenca.min():.2f} a {e.brent_diferenca.max():.2f} p.p.; banda exclui zero em "
                         f"{((e.brent_inferior > 0) | (e.brent_superior < 0)).sum()}.")
    for msg in mensagens:
        print(msg)
    print("Antes/depois é associação entre regimes. Pandemia, tributos, composição de choques e 2023 também importam.")
    resumo_json = {"inicio":str(dados.index[0].date()),"fim":str(dados.index[-1].date()),"n":len(dados),
                  "quebra":QUEBRA,"p":p,"ordem":ORDEM,"variaveis":NOMES,"choque_pct":CHOQUE_PCT,"confianca":CONFIANCA,
                  "bootstrap":BOOT,"h_repasse":H_REPASSE,"diferenciar_selic":DIFERENCIAR_SELIC,"respostas":resumo.to_dict("records"),"diferenca":dif.reset_index().to_dict("records"),
                  "narrativa":mensagens,"diagnostico":diag.reset_index().replace({np.nan:None}).to_dict("records"),
                  "bootstrap_instavel":fracao_instavel,"erro_hd":erro_hd,"sim_certa":rmse_certa,
                  "sim_errada":rmse_errada,"metricas":metricas.replace({np.nan:None}).to_dict("records"),
                  "envelope":None if ident is None else ident["envelope"].reset_index().to_dict("records"),
                  "impacto_propagacao":None if ident is None else ident["impacto_propagacao"].reset_index().to_dict("records"),
                  "variantes":None if tabela_variantes is None else tabela_variantes.reset_index().replace({np.nan:None}).to_dict("records"),
                  "tempo_segundos":time.perf_counter()-inicio_execucao,
                  "parametros":{nome:globals()[nome] for nome in PARAMETROS_PADRAO},
                  "versoes":{x:version(x) for x in ["numpy","pandas","scipy","statsmodels","matplotlib"]},
                  "sha256":{f.relative_to(BASE).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in [BASE/"analise.py",*sorted((BASE/"dados").glob("*.json")),BASE/"dados"/"brent.csv"]}}
    (OUT/"resumo.json").write_text(json.dumps(resumo_json,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8",newline="\n")
    print(f"Tempo total: {resumo_json['tempo_segundos']:.1f}s. Resultados em {PASTA_SAIDA}")
    return resumo_json


if __name__ == "__main__":
    configurar()
    dados = carregar_dados()
    modelo, regimes, diagnostico = estimar_modelos(dados)
    choques = comparar_choques(regimes)
    ident = identificacao(regimes)
    tabela_variantes = variantes()
    anexo(dados,modelo,regimes,diagnostico,choques,ident,tabela_variantes)
