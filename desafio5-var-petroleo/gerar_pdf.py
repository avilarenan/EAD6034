"""Gera os 5 slides de introdução a partir dos resultados reais.
Uso: python analise.py --lote && python gerar_pdf.py
Requer apenas ReportLab além da biblioteca padrão. Não roda a análise de novo.
"""
from pathlib import Path
import json
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

# 3. Explicar o mecanismo antes de mostrar os números.
pagina(3, "Comparação com o mesmo choque")
paragrafo(f"<b>VAR({r['p']})</b>: cada variável depende do passado de todas as cinco.",
          MARGEM, 378, 855, 24)
paragrafo("<b>Ordem contemporânea:</b> "+", ".join({"brent":"Brent","cambio":"câmbio","ipa":"IPA","ipca":"IPCA","selic":"Selic"}[x] for x in r["ordem"])+".",
          MARGEM, 310, 855, 22)
paragrafo(f"<b>Choque de +{r['choque_pct']:g}%</b> no Brent ou no câmbio, normalizado igualmente nos dois períodos.",
          MARGEM, 237, 840, 22)
paragrafo(f"<b>Medida:</b> resposta do IPCA somada de h=0 a h={r['h_repasse']}.<br/>Bandas pontuais de {r['confianca']:.0%}, com {r['bootstrap']} réplicas bootstrap.",
          MARGEM, 155, 845, 22)
texto(MARGEM, 58, "Constante, sazonalidade mensal e pulsos para greve/pandemia.", NOTA, CINZA)
c.showPage()

# 4. Uma única tabela concentra os resultados que orientam a demonstração.
pagina(4, "Resposta estimada do IPCA")
texto(MARGEM, 382, f"Acúmulo após o mesmo choque de +{r['choque_pct']:g}%", 23, DESTAQUE)
xs = [MARGEM, 279, 414, 556]
for x, s in zip(xs, ["Choque", "Antes", "Depois", f"Diferença [IC {r['confianca']:.0%}]"]):
    texto(x, 321, s, 19, negrito=True)
for i, choque in enumerate(["brent","cambio"]):
    vals = {x["amostra"]:x["resposta"] for x in r["respostas"] if x["choque"]==choque}
    delta = next(x for x in r["diferenca"] if x["index"]==choque)
    linha = [choque.capitalize() if choque=="brent" else "Câmbio",
             numero(vals["antes"]),numero(vals["depois"]),
             f"{numero(delta['depois_menos_antes'])}  [{numero(delta['inferior'])}; {numero(delta['superior'])}]"]
    for x, s in zip(xs, linha):
        texto(x, 270-i*53, s, 22, DESTAQUE if i==0 else COR)
paragrafo("O sinal negativo do câmbio no pós-período pede cautela na interpretação econômica.",
          MARGEM, 160, 855, 20)
paragrafo("<b>Resíduos autocorrelacionados limitam a confiança nas bandas.</b>",
          MARGEM, 100, 855, 20)
texto(MARGEM, 50, f"Unidade: p.p. de inflação acumulada, aprox. Soma h=0,...,{r['h_repasse']}. Fonte: analise.py.", NOTA, CINZA)
c.showPage()

# 5. Fechar a abertura com a conclusão condicional e o roteiro ao vivo.
pagina(5, "Conclusões e demonstração ao vivo")
paragrafo("<b>A especificação-base sugere maior resposta ao petróleo após 2016.</b>",
          MARGEM, 379, 855, 25)
paragrafo("A comparação entre regimes não isola o efeito causal da política da Petrobras.",
          MARGEM, 293, 835, 23)
paragrafo("Previsão: o VAR supera o AR em 1 mês nesta amostra.<br/>Em 12 meses, o AR tem erro ligeiramente menor.",
          MARGEM, 216, 835, 21)
paragrafo("<b>No código:</b> diagnósticos, respostas a choques, ordenações alternativas e decomposições. Depois, mudamos um parâmetro.",
          MARGEM, 128, 840, 20)
texto(MARGEM, 47, "A amostra inclui pandemia e mudanças posteriores a 2016. Sensibilidades no guia.", NOTA, CINZA)
c.showPage()
c.save()
print(f"{TOTAL} slides: {DESTINO}")
