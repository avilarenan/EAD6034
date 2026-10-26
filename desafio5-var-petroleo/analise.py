# %% 0. PAINEL DE CONTROLE - altere aqui durante a apresentação
"""EAD6034 | Rafael Palazzi | Renan de Luca Avila.
Pergunta: o repasse do petróleo ao IPCA mudou depois de outubro de 2016?
Execute as células (# %%) no VS Code/Spyder ou: python analise.py
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
DPI = 150                      # Qualidade PNG, sem efeito estatístico.
FONT_SIZE = 11                 # Letras dos gráficos, sem efeito estatístico.
MAX_LINHAS_TELA = 24           # Limita tabelas longas no terminal; CSV sempre contém tudo.
CASAS = 4                      # Arredondamento na tela; CSV mantém precisão.
TOL = 1e-8                     # Tolerância numérica das checagens, não significância.

# %% 1. FERRAMENTAS - execute uma vez; apresente a partir da célula 2
from pathlib import Path
from types import SimpleNamespace
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
from statsmodels.stats.diagnostic import het_arch, recursive_olsresiduals
from statsmodels.tools.sm_exceptions import InterpolationWarning
import matplotlib
if "--lote" in sys.argv:
    MOSTRAR = PAUSAR = False
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
OUT = BASE / PASTA_SAIDA
OUT.mkdir(exist_ok=True)
NOMES = ["brent", "cambio", "ipa", "ipca", "selic"]
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


def tabela(nome, df):
    visivel = df if len(df)<=MAX_LINHAS_TELA else pd.concat([df.head(MAX_LINHAS_TELA//2),df.tail(MAX_LINHAS_TELA//2)])
    print("\n" + nome + "\n" + visivel.round(CASAS).to_string())
    if len(df)>MAX_LINHAS_TELA:
        print("[Linhas intermediárias omitidas na tela; arquivo CSV completo.]")
    df.to_csv(OUT / (nome + ".csv"), encoding="utf-8-sig")


def figura(nome):
    plt.tight_layout()
    plt.savefig(OUT / (nome + ".png"), dpi=DPI)
    if MOSTRAR:
        plt.show()
    plt.close()


def etapa(texto):
    print("\n" + "=" * 72 + "\n" + texto)
    if PAUSAR and sys.stdin.isatty():
        input("Enter para executar este bloco...")


def deterministicas(datas, sazonais=None, pulsos=None):
    sazonais = SAZONAIS if sazonais is None else sazonais
    pulsos = DUMMIES if pulsos is None else pulsos
    d = pd.DataFrame({"const": 1.0}, index=datas)
    if sazonais:
        for mes in range(2, 13):  # Janeiro é referência: evita colinearidade com a constante.
            d[f"mes_{mes}"] = (datas.month == mes).astype(float)
    if pulsos:
        for mes in MESES_ATIPICOS:
            d[mes] = (datas.strftime("%Y-%m") == mes).astype(float)
    return d


def ajusta(y, p, sazonais=None, pulsos=None, excluir=None):
    """VAR por MQO. lstsq evita inverter para estimar.
    Criar lags ANTES das exclusões garante que um lag continue sendo um mês.
    """
    excluir = EXCLUIR_2020 if excluir is None else excluir
    d = deterministicas(y.index, sazonais, pulsos)
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
    e = Y - X @ b
    a = b[-p*m:].reshape(p, m, m).transpose(0, 2, 1)
    F = np.zeros((p*m, p*m)); F[:m] = np.concatenate(a, axis=1)
    if p > 1:
        F[m:, :-m] = np.eye((p-1)*m)
    return SimpleNamespace(y=y, X=X, Y=Y, b=b, e=e, A=a, sigma=e.T@e/(n-k),
                           n=n, k=k, m=m, p=p, datas=z.index, colunas=x.columns,
                           det=list(x.columns[:k-p*m]), raizes=np.linalg.eigvals(F))


def portmanteau(r):
    """Teste multivariado ajustado. Com buracos, usa o maior trecho contínuo."""
    e = r.e
    meses = r.datas.to_period("M").asi8
    cortes = np.r_[0, np.flatnonzero(np.diff(meses) != 1)+1, len(e)]
    if len(cortes) > 2:
        trecho = np.argmax(np.diff(cortes)); e = e[cortes[trecho]:cortes[trecho+1]]
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
    d = deterministicas(r.y.index).reindex(columns=r.det, fill_value=0).to_numpy()
    for _ in range(BOOT):
        ys = r.y.to_numpy().copy()
        erros = (r.e-r.e.mean(axis=0)) * np.sqrt(r.n/(r.n-r.k))
        erros *= rng.choice([-1.0, 1.0], size=(r.n, 1))
        for i, t in enumerate(pos):
            ys[t] = d[t]@r.b[:len(r.det)] + sum(r.A[j-1]@ys[t-j] for j in range(1,r.p+1)) + erros[i]
        b = ajusta(pd.DataFrame(ys, index=r.y.index, columns=r.y.columns), r.p)
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


# %% 2. DADOS - "Petróleo em dólares e câmbio são dois canais diferentes."
etapa("1. Dados: cinco séries mensais, públicas e salvas no repositório")
partes = []
for nome in ["cambio", "ipa", "ipca", "selic"]:
    d = pd.read_json(BASE/"dados"/(nome+".json"))
    partes.append(pd.Series(d["valor"].astype(float).values,
                           index=pd.to_datetime(d["data"],dayfirst=True),name=nome))
d = pd.read_csv(BASE/"dados"/"brent.csv",index_col=0,parse_dates=True)
partes.append(d.iloc[:,0].rename("brent"))
brutos = pd.concat(partes,axis=1).sort_index()[NOMES]
brutos.index.name = "data"
assert not brutos.index.duplicated().any() and not brutos.isna().any().any()
assert np.all(np.diff(brutos.index.to_period("M").asi8) == 1)
assert (brutos[["brent","cambio"]] > 0).all().all()
dados = brutos.copy()
dados[["brent","cambio"]] = 100*np.log(brutos[["brent","cambio"]]).diff()
if DIFERENCIAR_SELIC:
    dados["selic"] = brutos["selic"].diff()
dados = dados.loc[INICIO:FIM].dropna()
assert len(dados)>JANELA and dados.index.min()<pd.Timestamp(QUEBRA)<dados.index.max()
brutos.to_csv(BASE/"dados"/"mensal.csv")
dados.to_csv(OUT/"dados_transformados.csv")
print(f"{dados.index[0]:%m/%Y} a {dados.index[-1]:%m/%Y}: {len(dados)} meses. Ordem: {ORDEM}")
dados.plot(subplots=True,figsize=(10,8),legend=False,color=CORES)
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

# %% 3. MODELO - "Mais lags lembram mais meses, mas gastam observações."
etapa("2. Escolha de p, resíduos e estabilidade dinâmica")
ic = criterios(dados); tabela("02_defasagens",ic)
p_ic = int(ic[CRITERIO].idxmin())
candidatos = ic.loc[ic.index >= p_ic]
aceitos = candidatos.index[candidatos.p_autocorr > ALFA]
p = int(P_FIXO) if P_FIXO is not None else (int(aceitos[0]) if AJUSTAR_P_RESIDUOS and len(aceitos) else p_ic)
modelo = ajusta(dados,p)
regimes = {"antes":ajusta(dados.loc[dados.index < QUEBRA],p),
           "depois":ajusta(dados.loc[dados.index >= QUEBRA],p)}
diagnosticos = []
for nome,r in {"completa":modelo,**regimes}.items():
    raio = max(abs(r.raizes))
    meia = np.log(0.5)/np.log(raio) if 0 < raio < 1 else np.nan
    diagnosticos.append([nome,r.n,r.k,p,raio,meia,portmanteau(r)])
    eq = pd.DataFrame({"JB_p":[stats.jarque_bera(r.e[:,j]).pvalue for j in range(r.m)],
                       "ARCH_p":[het_arch(r.e[:,j],nlags=LAG_ARCH,ddof=r.k)[1] for j in range(r.m)]},index=NOMES)
    tabela("02_residuos_"+nome,eq)
    inv = np.linalg.inv(r.X.T@r.X)
    coef = []
    for j,variavel in enumerate(NOMES):
        usual = np.sqrt(np.diag(inv)*r.sigma[j,j])
        robusta = inv@hac(r.X*r.e[:,j,None],LAG_HAC,r.datas.to_period("M").asi8)@inv*r.n/(r.n-r.k)
        se_hac = np.sqrt(np.maximum(np.diag(robusta),0))
        for k,regressor in enumerate(r.colunas):
            coef.append([variavel,regressor,r.b[k,j],usual[k],r.b[k,j]/usual[k],se_hac[k],r.b[k,j]/se_hac[k]])
    pd.DataFrame(coef,columns=["equacao","regressor","coef","se_usual","t_usual","se_HAC","z_HAC"]).to_csv(OUT/("02_coeficientes_"+nome+".csv"),index=False)
    if raio >= 1:
        print("ATENÇÃO:",nome,"instável: não interpretar meia-vida nem respostas como convergentes.")
diag = pd.DataFrame(diagnosticos,columns=["amostra","n","k_por_eq","p","raio","meia_vida","Portmanteau_p"]).set_index("amostra")
tabela("02_diagnostico",diag)
ciclos = [[abs(z),2*np.pi/abs(np.angle(z))] for z in modelo.raizes if z.imag > TOL]
tabela("02_ciclos",pd.DataFrame(ciclos,columns=["modulo","periodo_meses"]))
print("Meia-vida: modo dominante, não necessariamente a meia-vida de cada IRF.")
if (diag.Portmanteau_p <= ALFA).any():
    print("RESSALVA: autocorrelação residual. Bootstrap e p-valores exigem cautela; teste outro p.")

fig,ax = plt.subplots(figsize=(5,5))
ang = np.linspace(0,2*np.pi,300)  # 300 pontos apenas desenham o círculo unitário.
ax.plot(np.cos(ang),np.sin(ang),color="gray",ls="--")
ax.scatter(modelo.raizes.real,modelo.raizes.imag,color=CORES[0])
ax.set(xlabel="Parte real",ylabel="Parte imaginária",title="Autovalores da matriz companheira",aspect="equal")
figura("02_raizes")

# %% 4. GRANGER - "Ajuda a prever? Isso não identifica causalidade econômica."
etapa("3. Granger condicional, usual e robusto HAC")
g = ajusta(dados,p+D_MAX)  # Toda-Yamamoto: só os p primeiros lags são testados.
linhas = []
for causa in range(5):
    for destino in range(5):
        if causa != destino:
            linhas.append([NOMES[causa],NOMES[destino],*wald_granger(g,[causa],[destino],p)])
linhas.append(["Brent+câmbio","IPA+IPCA",*wald_granger(g,[0,1],[2,3],p)])
granger = pd.DataFrame(linhas,columns=["causa","destino","Wald_usual_p","Wald_HAC_p"])
tabela("03_granger",granger)
print(f"VAR aumentado p+dmax={p+D_MAX}; testamos p={p}. dmax={D_MAX} deve cobrir a integração.")

# %% 5. IRFs - "Comparamos o mesmo aumento de 10%, não volatilidades diferentes."
etapa("4. Resposta do IPCA ao Brent e ao câmbio, antes e depois da quebra")
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
        linhas.append([choque,nome,ponto[H_REPASSE],lo[H_REPASSE],hi[H_REPASSE]])
    axes[j].axhline(0,color="gray",lw=1); axes[j].set_title(f"{choque.capitalize()}: +{CHOQUE_PCT:g}% no impacto")
    axes[j].set(xlabel="Meses após o choque",ylabel="IPCA acumulado (p.p., aprox.)"); axes[j].legend()
figura("04_irf_antes_depois")
resumo = pd.DataFrame(linhas,columns=["choque","amostra","resposta","inferior","superior"])
tabela("04_respostas_12m",resumo)
delta = boots["depois"][:,H_REPASSE,:]-boots["antes"][:,H_REPASSE,:]
mudanca = resposta(regimes["depois"])[H_REPASSE]-resposta(regimes["antes"])[H_REPASSE]
limites = np.quantile(delta,q,axis=0)
dif = pd.DataFrame({"depois_menos_antes":mudanca,"inferior":limites[0],"superior":limites[1]},index=NOMES[:2])
tabela("04_diferenca",dif)
print("Compare a banda da DIFERENÇA com zero. Sobreposição de bandas separadas não é um teste.")
for nome,r in regimes.items():
    d_lo,d_hi = np.quantile(denominadores[nome],q,axis=0)
    fragil = (d_lo <= 0) & (d_hi >= 0)
    tabela("04_razao_"+nome,pd.DataFrame({"elasticidade_aprox":repasse(r),
           "inferior":np.quantile(ratios[nome],q[0],axis=0),
           "superior":np.quantile(ratios[nome],q[1],axis=0),"denominador_cruza_zero":fragil},index=NOMES[:2]))
    if fragil.any():
        print("ATENÇÃO: razão frágil, denominador compatível com zero. Priorize resposta normalizada.")

# %% 6. ROBUSTEZ - "A ordem distribui a surpresa compartilhada."
etapa("5. Todas as 120 ordenações e FEVD")
b_total,_,_,inst_total = bootstrap(modelo,SEMENTE+2)
fracao_instavel["completa"] = inst_total
envoltorio = np.array([resposta(modelo,list(o)) for o in permutations(NOMES)])
corr = pd.DataFrame(np.corrcoef(modelo.e.T),index=NOMES,columns=NOMES)
tabela("05_correlacao_residuos",corr)
fig,axes = plt.subplots(1,2,figsize=(12,4.8))
for j,ax in enumerate(axes):
    ax.fill_between(range(H+1),envoltorio[:,:,j].min(axis=0),envoltorio[:,:,j].max(axis=0),alpha=.2,color=CORES[j],label="120 ordens (min-max)")
    lo,hi = np.quantile(b_total[:,:,j],q,axis=0)
    ax.plot(lo,color=CORES[j],ls=":",label=f"IC pontual {CONFIANCA:.0%}")
    ax.plot(hi,color=CORES[j],ls=":")
    ax.plot(resposta(modelo)[:,j],color=CORES[j],label="Ordem-base")
    ax.axhline(0,color="gray",lw=1); ax.set(title=NOMES[j],xlabel="Meses",ylabel="IPCA acumulado (p.p., aprox.)"); ax.legend()
figura("05_envelope")
print("Envelope: sensibilidade à identificação, NÃO intervalo de confiança.")
mudancas_ordens = np.array([resposta(regimes["depois"],list(o))[H_REPASSE]-resposta(regimes["antes"],list(o))[H_REPASSE] for o in permutations(NOMES)])
tabela("05_mudanca_120_ordens",pd.DataFrame({"min_delta":mudancas_ordens.min(axis=0),
       "max_delta":mudancas_ordens.max(axis=0),"fracao_delta_positivo":(mudancas_ordens>0).mean(axis=0)},index=NOMES[:2]))
fevds = []
for label,ordem in [("base",ORDEM),("alternativa",ORDEM_ALT)]:
    t = irf(modelo,ordem)
    for h in FEVD_H:
        v = (t[:h]**2).sum(axis=0); v = v/v.sum(axis=1,keepdims=True)
        assert np.allclose(v.sum(axis=1),1,atol=TOL)
        fevds.append([label,h,*100*v[3]])
tabela("05_fevd_ipca",pd.DataFrame(fevds,columns=["ordem","h",*NOMES]))
# Sigma comum separa mudança de propagação de mudança dos impactos; não identifica a Petrobras.
comparacao = pd.DataFrame({"A_antes_Sigma_comum":resposta(regimes["antes"],sigma=modelo.sigma)[H_REPASSE],
                           "A_depois_Sigma_comum":resposta(regimes["depois"],sigma=modelo.sigma)[H_REPASSE]},index=NOMES[:2])
tabela("05_propagacao_covariancia_comum",comparacao)

# %% 7. QUEBRA - "Parâmetros diferentes não provam qual instituição causou a mudança."
etapa("6. Chow na data conhecida, CUSUM e repasse móvel")
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
eu = np.column_stack(erros_u)
lr = r.n*(np.linalg.slogdet(r.e.T@r.e/r.n)[1]-np.linalg.slogdet(eu.T@eu/r.n)[1])
q_chow = len(quebram)*r.m
tabela("06_quebra_conjunta",pd.DataFrame([{"LR":lr,"restricoes":q_chow,"p_assintotico":stats.chi2.sf(lr,q_chow)}]))
print(f"{len(quebram)} restrições/equação; {q_chow} no sistema. LR supõe covariância comum; inferência exploratória em níveis.")
# CUSUM recursivo auxiliar SEM pulsos: pulsos tardios tornam singular a amostra inicial.
rc = ajusta(dados,p,pulsos=False)
fig,axs = plt.subplots(5,1,figsize=(10,10),sharex=True)
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
movel[["brent","cambio"]].plot(color=CORES[:2]); plt.axvline(pd.Timestamp(QUEBRA),color="gray",ls="--")
plt.ylabel("Razão acumulada em 12 meses (aprox.)"); figura("06_repasse_movel")
print("CUSUM sem pulsos: episódios extremos também podem provocar rejeição. Janelas se sobrepõem.")

# %% 8. HISTÓRIA - "Quanto cada surpresa contribuiu para o IPCA observado?"
etapa("7. Decomposição histórica, com conferência exata da soma")
r = modelo; Y = dados.to_numpy(); n = len(Y)
P = irf(r,ORDEM,horizonte=0)[0]
d = deterministicas(dados.index).reindex(columns=r.det,fill_value=0).to_numpy()
base = Y.copy(); contribuicoes = np.zeros((n,5,5))
for t in range(p,n):
    esperado = d[t]@r.b[:len(r.det)]+sum(r.A[j-1]@Y[t-j] for j in range(1,p+1))
    u = np.linalg.solve(P,Y[t]-esperado)
    base[t] = d[t]@r.b[:len(r.det)]+sum(r.A[j-1]@base[t-j] for j in range(1,p+1))
    contribuicoes[t] = P*u[None,:]+sum(r.A[j-1]@contribuicoes[t-j] for j in range(1,p+1))
erro_hd = float(np.max(abs(base+contribuicoes.sum(axis=2)-Y)))
assert erro_hd < TOL
hd = pd.DataFrame(contribuicoes[:,3,:],index=dados.index,columns=NOMES)
hd["deterministica_iniciais"] = base[:,3]; hd["observado"] = Y[:,3]
hd.to_csv(OUT/"07_decomposicao.csv")
ep = hd.loc[EPISODIO[0]:EPISODIO[1]]
ax = ep[NOMES].set_axis(ep.index.strftime("%Y-%m")).plot.bar(stacked=True,color=CORES,figsize=(12,5))
ax.plot(range(len(ep)),ep.observado-ep.deterministica_iniciais,color="black",label="IPCA menos base")
ax.set_xticklabels(ep.index.strftime("%Y-%m"),rotation=60); ax.set_ylabel("IPCA mensal (p.p.)"); ax.legend(ncol=3)
figura("07_decomposicao")
print(f"Erro máximo de reconstrução: {erro_hd:.2e}. Base: constante, calendário, pulsos e condições iniciais.")

# %% 9. SIMULAÇÃO - "Em dados artificiais eu conheço a resposta correta."
etapa("8. Verificação com dinâmica e impactos conhecidos")
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

# %% 10. PREVISÃO - "Explicar choques e prever inflação são objetivos diferentes."
etapa("9. Janela expansiva: VAR contra AR e passeio aleatório")
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
prev.to_csv(OUT/"09_previsoes.csv",index=False)
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

# %% 11. FECHAMENTO - os resultados alimentam automaticamente os slides
etapa("10. Conclusão e arquivos para a apresentação")
mensagens = []
for choque,row in dif.iterrows():
    conclusao = "aumento" if row.inferior>0 else ("redução" if row.superior<0 else "mudança inconclusiva")
    msg = f"{choque.capitalize()}: {conclusao} na resposta acumulada do IPCA em h={H_REPASSE}."
    mensagens.append(msg); print(msg)
print("Antes/depois é associação entre regimes. Pandemia, tributos, composição de choques e 2023 também importam.")
resumo_json = {"inicio":str(dados.index[0].date()),"fim":str(dados.index[-1].date()),"n":len(dados),
              "quebra":QUEBRA,"p":p,"ordem":ORDEM,"choque_pct":CHOQUE_PCT,"confianca":CONFIANCA,
              "bootstrap":BOOT,"h_repasse":H_REPASSE,"diferenciar_selic":DIFERENCIAR_SELIC,"respostas":resumo.to_dict("records"),"diferenca":dif.reset_index().to_dict("records"),
              "narrativa":mensagens,"diagnostico":diag.reset_index().replace({np.nan:None}).to_dict("records"),
              "bootstrap_instavel":fracao_instavel,"erro_hd":erro_hd,"sim_certa":rmse_certa,
              "sim_errada":rmse_errada,"metricas":metricas.replace({np.nan:None}).to_dict("records"),
              "tempo_segundos":time.perf_counter()-inicio_execucao,
              "versoes":{x:version(x) for x in ["numpy","pandas","scipy","statsmodels","matplotlib"]},
              "sha256":{str(f.relative_to(BASE)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [BASE/"analise.py",*(BASE/"dados").glob("*.json"),BASE/"dados"/"brent.csv"]}}
(OUT/"resumo.json").write_text(json.dumps(resumo_json,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
print(f"Tempo total: {resumo_json['tempo_segundos']:.1f}s. Resultados em {OUT}")
