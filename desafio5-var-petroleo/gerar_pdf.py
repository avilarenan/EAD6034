"""Gera os 5 slides de introdução a partir dos resultados reais.
Uso: python analise.py --lote && python gerar_pdf.py
Requer apenas ReportLab além da biblioteca padrão. Não roda a análise de novo.
"""
from pathlib import Path
import json
from datetime import date, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# Aparência: ajuste aqui. Nenhum destes parâmetros altera a análise estatística.
BASE = Path(__file__).resolve().parent
RESULTADOS = BASE / "resultados" / "resumo.json"  # Mude se usou outra PASTA_SAIDA.
DESTINO = BASE / "introducao.pdf"                # PDF final do repositório.
LARGURA, ALTURA = 960, 540                       # Proporção 16:9 para projetar.
MARGEM = 48                                     # Área de respiro nas bordas.
COR = "#12384a"                                 # Títulos.
DESTAQUE = "#166a8f"                            # Resultado principal.
CINZA = "#56616b"                               # Apoio e fontes.
TITULO, CORPO, NOTA = 32, 21, 12                 # Pontos, para leitura em sala.
AUTOR = "Renan de Luca Avila"
DISCIPLINA = "EAD6034 - Rafael Palazzi"
TOTAL = 5                                      # Cinco páginas, incluindo a abertura.

r = json.loads(RESULTADOS.read_text(encoding="utf-8"))
c = canvas.Canvas(str(DESTINO), pagesize=(LARGURA, ALTURA))
c.setTitle("Petróleo e inflação no Brasil - EAD6034")
c.setAuthor(AUTOR)

def texto(x, y, s, tamanho=CORPO, cor=COR, negrito=False):
    c.setFillColor(HexColor(cor))
    c.setFont("Helvetica-Bold" if negrito else "Helvetica", tamanho)
    c.drawString(x, y, s)

def paragrafo(s, x, topo, largura, tamanho=CORPO, cor=COR):
    estilo = ParagraphStyle("p", fontName="Helvetica", fontSize=tamanho,
                            leading=tamanho*1.35, textColor=HexColor(cor))
    p = Paragraph(s, estilo)
    _, altura = p.wrap(largura, ALTURA)
    p.drawOn(c, x, topo-altura)

def pagina(n, titulo):
    texto(MARGEM, ALTURA-40, DISCIPLINA, NOTA, CINZA)
    texto(MARGEM, ALTURA-101, titulo, TITULO, negrito=True)
    texto(MARGEM, 25, AUTOR, NOTA, CINZA)
    texto(LARGURA-90, 25, f"{n} / {TOTAL}", NOTA, CINZA)

def numero(v):
    return f"{v:+.2f}".replace(".", ",")

def data(s):
    return s[5:7]+"/"+s[:4]

# 1. Abrir com a pergunta econômica, sem antecipar detalhes técnicos.
pagina(1, "Petróleo e inflação no Brasil")
texto(MARGEM, 358, "Repasse antes e depois de outubro de 2016", 26, DESTAQUE)
paragrafo("Um mesmo aumento do petróleo produz a mesma resposta nos preços ao consumidor?",
          MARGEM, 282, 780, 30)
texto(MARGEM, 124, "Desafio 5 - um VAR com cinco variáveis", CORPO, CINZA)
texto(MARGEM, 87, f"Dados mensais de {data(r['inicio'])} a {data(r['fim'])}", CORPO, CINZA)
c.showPage()

# 2. Definir cada variável e distinguir preço do petróleo de variação cambial.
pagina(2, "Cinco séries, um sistema")
xs = [MARGEM, 215, 501]
for x, s in zip(xs, ["Variável", "Medida no VAR", "Papel na história"]):
    texto(x, 373, s, 19, negrito=True)
linhas = [
    ("Brent", "100 x variação do log", "Petróleo em dólares"),
    ("Câmbio", "100 x variação do log", "R$/US$; alta = depreciação"),
    ("IPA-DI", "Variação mensal (%)", "Preços ao produtor"),
    ("IPCA", "Variação mensal (%)", "Preços ao consumidor"),
    ("Selic", "Variação da taxa (p.p.)" if r.get("diferenciar_selic") else "Taxa anualizada (%)", "Condição monetária"),
]
for i, linha in enumerate(linhas):
    for x, s in zip(xs, linha):
        texto(x, 325-i*43, s, 18)
texto(MARGEM, 88, f"{r['n']} meses. Brent: FMI/FRED. Demais séries: BCB/SGS.", 17, CINZA)
texto(MARGEM, 60, "Fontes e códigos das séries no README e em dados/README.md.", NOTA, CINZA)
c.showPage()

# 3. Definir intervenção, comparação, períodos e condições de forma completa.
antes_fim = (date.fromisoformat(r["quebra"])-timedelta(days=1)).isoformat()
pagina(3, "O experimento: uma surpresa no petróleo")
paragrafo(f"<b>Choque inicial.</b> O Brent em US$/barril sobe {r['choque_pct']:g}% de surpresa (ex.: 100 para {100+r['choque_pct']:g}). Uma única alta no impacto.",
          MARGEM, 389, 857, 20)
paragrafo("<b>Comparação.</b> Mesmo ponto de partida: calculamos o IPCA com essa surpresa e sem ela, dentro de cada regime.",
          MARGEM, 327, 857, 20)
paragrafo(f"<b>Dois modelos.</b> VAR({r['p']}) reestimado em {data(r['inicio'])}-{data(antes_fim)} e em {data(r['quebra'])}-{data(r['fim'])}. Mesmas variáveis, controles de calendário e pulsos para greve/pandemia.",
          MARGEM, 265, 857, 20)
paragrafo("<b>Condições.</b> As demais surpresas são zero. Câmbio, IPA, IPCA e Selic podem reagir ao petróleo, conforme a dinâmica estimada.",
          MARGEM, 203, 857, 20)
paragrafo(f"<b>Medida.</b> Somamos a diferença no IPCA do impacto ao mês {r['h_repasse']}, inclusive: {r['h_repasse']+1} termos, em pontos percentuais (aprox.).",
          MARGEM, 141, 857, 20)
texto(MARGEM, 58, "Na ordem recursiva, anteriores podem afetar posteriores no mesmo mês: "+", ".join({"brent":"Brent","cambio":"câmbio","ipa":"IPA","ipca":"IPCA","selic":"Selic"}[x] for x in r["ordem"])+".", NOTA, CINZA)
c.showPage()

# 4. Um único choque e uma leitura concreta, sem misturar o experimento cambial.
valores = {x["amostra"]:x["resposta"] for x in r["respostas"] if x["choque"]=="brent"}
delta = next(x for x in r["diferenca"] if x["index"]=="brent")
pagina(4, "Quanto o IPCA responde ao petróleo?")
paragrafo(f"Alta inesperada de {r['choque_pct']:g}% no Brent em US$, uma única vez. Resposta do IPCA acumulada do impacto até o mês {r['h_repasse']}.",
          MARGEM, 392, 855, 21, DESTAQUE)
xs = [MARGEM, 332, 629]
for x,s in zip(xs,["Modelo anterior", "Modelo posterior", "Posterior menos anterior"]):
    texto(x, 305, s, 19, negrito=True)
for x,s in zip(xs,[data(r['inicio'])+" a "+data(antes_fim),data(r['quebra'])+" a "+data(r['fim']),"Diferença de resposta"]):
    texto(x, 278, s, 16, CINZA)
for x,v in zip(xs,[valores['antes'],valores['depois'],delta['depois_menos_antes']]):
    texto(x, 233, numero(v)+" p.p.", 34, DESTAQUE, True)
paragrafo(f"<b>Como ler:</b> no modelo posterior, o choque adiciona cerca de {numero(valores['depois']).lstrip('+')} p.p. à inflação acumulada, em relação à trajetória sem essa surpresa.",
          MARGEM, 197, 853, 20)
paragrafo(f"<b>Incerteza:</b> banda de {r['confianca']:.0%} para a diferença [{numero(delta['inferior'])}; {numero(delta['superior'])}] p.p. Autocorrelação residual e sensibilidade às defasagens limitam a conclusão.",
          MARGEM, 125, 853, 18)
texto(MARGEM, 54, "Comparação entre regimes, sem isolar o efeito causal da Petrobras. p.p. = pontos percentuais. Fonte: analise.py.", NOTA, CINZA)
c.showPage()

# 5. Fechar a abertura com a conclusão condicional e o roteiro ao vivo.
pagina(5, "Conclusões e demonstração ao vivo")
paragrafo("<b>A especificação-base sugere maior resposta ao petróleo após 2016.</b>",
          MARGEM, 379, 855, 25)
paragrafo("A comparação entre regimes não isola o efeito causal da política da Petrobras.",
          MARGEM, 293, 835, 23)
paragrafo("Previsão: o VAR supera o AR em 1 mês nesta amostra.<br/>Em 12 meses, o AR tem erro ligeiramente menor.",
          MARGEM, 216, 835, 21)
paragrafo("<b>No notebook:</b> diagnósticos, respostas a choques, ordenações alternativas e decomposições. Depois, mudamos um parâmetro.",
          MARGEM, 128, 840, 20)
texto(MARGEM, 47, "A amostra inclui pandemia e mudanças posteriores a 2016. Sensibilidades no guia.", NOTA, CINZA)
c.showPage()
c.save()
print(f"{TOTAL} slides: {DESTINO}")
