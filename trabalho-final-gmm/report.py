"""Gera o PDF do checkpoint, diretamente a partir da tabela de comparação."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

REPO = "https://github.com/avilarenan/EAD6034/tree/main/trabalho-final-gmm"
INK = "#172D37"
TEAL = "#095D66"
MUTED = "#4C6067"


def build(comparison_dataframe, dest_pdf):
    d = comparison_dataframe
    nds = d.loc[d.panel == "NDS"].sort_values("lag")
    nd = d.loc[d.panel == "ND"].sort_values("lag")
    if any(x.lag.tolist() != [1, 2, 4, 6] for x in (nds, nd)):
        raise ValueError("São necessárias quatro linhas por painel.")
    dest_pdf = Path(dest_pdf)
    dest_pdf.parent.mkdir(parents=True, exist_ok=True)
    c = Canvas(str(dest_pdf), pagesize=A4, invariant=1, pageCompression=1)
    c.setTitle("Checkpoint | Consumo e retorno de ações nos Estados Unidos")
    c.setAuthor("Renan de Luca Avila")
    w,h = A4
    x, end = 17*mm, w-17*mm
    inner=end-x

    def txt(a,b,s,size=10,font="Helvetica",color=INK,align="left"):
        c.setFillColor(colors.HexColor(color))
        c.setFont(font,size)
        {"left":c.drawString,"right":c.drawRightString,"center":c.drawCentredString}[align](a,b,str(s))

    def para(t,y,size=10.2,leading=14.5,color=INK):
        p=Paragraph(t,ParagraphStyle("p",fontName="Helvetica",fontSize=size,leading=leading,textColor=colors.HexColor(color)))
        _,height=p.wrap(inner,500)
        p.drawOn(c,x,y-height)
        return y-height

    def rule(y,color="#B8CCCF",width=.6):
        c.setStrokeColor(colors.HexColor(color))
        c.setLineWidth(width)
        c.line(x,y,end,y)

    def label(t,y):
        txt(x,y,t,9,"Helvetica-Bold",TEAL)
        return y-8

    def n(value,places=4):
        return f"{value:.{places}f}".replace(".",",")

    def href(url,s):
        return f'<a href="{url}" color="{TEAL}"><u>{s}</u></a>'

    y=h-42
    txt(x,y,"FEA-USP   /   EAD6034  ·  ECONOMETRIA DE SÉRIES TEMPORAIS",8.5,"Helvetica-Bold",TEAL)
    txt(end,y,"CHECKPOINT  ·  PRAZO: 19 NOV 2026",8.5,"Helvetica-Bold",TEAL,"right")
    rule(y-10,TEAL,1.5)
    y-=43
    txt(x,y,"Consumo e retorno de ações nos Estados Unidos",21,"Helvetica-Bold")
    y-=20
    txt(x,y,"Replicação parcial da Tabela I de Hansen e Singleton (1982), com a errata de 1984",11.3,"Helvetica",MUTED)
    y-=18
    txt(x,y,"Renan de Luca Avila   |   Novembro de 2026",9.6,"Helvetica",MUTED)
    y-=22
    y=para("Hansen (1982) desenvolve a teoria do método dos momentos generalizado (GMM), sem tabelas empíricas. Para examinar o método com dados observados, reproduzo os dois painéis de Hansen e Singleton para o retorno acionário ponderado por valor de mercado (VWR).",y)
    y=label("Dados e estimação",y-20)
    y=para("<b>NDS:</b> consumo de não duráveis e serviços por habitante, retorno da NYSE com dividendos e deflator de consumo, a partir do arquivo de A. R. Gallant. <b>ND:</b> só não duráveis; reconstrução pública da QuantEcon com séries revisadas do FRED e a carteira de mercado de Kenneth French, mais ampla que a NYSE.",y)
    y=para("De fev/1959 a dez/1978 há 239 pares mensais. O erro de Euler é <b>β (C<sub>t</sub>/C<sub>t−1</sub>)<super>α</super> R<sub>t</sub> − 1</b>, em que R é o retorno real bruto e C é o consumo real per capita. Os instrumentos são uma constante e L defasagens de retorno e crescimento do consumo. Estimo por GMM iterado, com covariância centrada dos momentos; a análise de sensibilidade no repositório inclui GMM em duas etapas.",y-6)

    y=label("Tabela 1  |  Comparação com a errata, p. 268",y-20)
    # The group headers compare like with like, instead of comparing two blocks of estimates.
    widths=[45,25,32,60,60,57,57,48,48,0]
    widths[-1]=inner-sum(widths)
    edges=[x]
    for width in widths: edges.append(edges[-1]+width)
    centers=[(a+b)/2 for a,b in zip(edges,edges[1:])]
    c.setFillColor(colors.HexColor("#DCECEE"))
    c.rect(x,y-32,inner,32,fill=1,stroke=0)
    for i,name in [(0,"Série"),(1,"L"),(2,"n")]:
        txt(centers[i],y-20,name,9,"Helvetica-Bold",align="center")
    for left,right,caption in [(3,4,"Expoente α"),(5,6,"Desconto β"),(7,8,"Teste J")]:
        txt((edges[left]+edges[right+1])/2,y-12,caption,9,"Helvetica-Bold",align="center")
        txt(centers[left],y-25,"Errata",8,"Helvetica",MUTED,"center")
        txt(centers[right],y-25,"Réplica",8,"Helvetica",MUTED,"center")
    txt(centers[9],y-12,"p-valor",9,"Helvetica-Bold",align="center")
    txt(centers[9],y-25,"Réplica",8,"Helvetica",MUTED,"center")
    y-=32
    for panel in [nds,nd]:
        rule(y,width=.9)
        for row in panel.itertuples():
            if row.lag in (2,6):
                c.setFillColor(colors.HexColor("#F2F6F6"))
                c.rect(x,y-20,inner,20,fill=1,stroke=0)
            values=[row.panel,int(row.lag),int(row.n),n(row.alpha_original),n(row.alpha),n(row.beta_original),
                    n(row.beta),n(row.j_original,3),n(row.j,3),n(row.p_value,3)]
            for i,value in enumerate(values):
                txt(centers[i],y-13.7,value,9.8,"Helvetica-Bold" if i==0 else "Helvetica",align="center")
            y-=20
    rule(y)
    y=para("n = 239 − L. No teste J, a hipótese nula é que os momentos são conjuntamente válidos. Os graus de liberdade são 2L − 1. A coluna <i>Prob</i> do artigo é a probabilidade acumulada; aqui o p-valor é a cauda superior.",y-6,8.8,11.5,MUTED)
    y=label("O que os números permitem concluir",y-19)
    ge=abs(nds.alpha-nds.alpha_original).max()
    nds2=nds.loc[nds.lag==2].iloc[0]
    y=para(f"No painel histórico NDS, a diferença máxima em α é inferior a {n(ge,4)} e os quatro valores de J coincidem com os publicados a três casas decimais. Com duas defasagens, a aversão ao risco estimada (−α) é {n(-nds2.alpha,3)}, mas o erro-padrão é {n(nds2.se_alpha,2)}: a estimativa é pouco precisa. A coincidência numérica não identifica o algoritmo exato dos autores.",y)
    y=para(f"No painel ND, a mudança de fontes altera as estimativas. Mesmo assim, o teste J não rejeita as restrições a 5% em nenhuma linha (menor p-valor: {n(nd.p_value.min(),3)}). Não rejeitar os momentos não demonstra que os instrumentos identificam com precisão a aversão ao risco.",y-5)
    y=para("<b>Próxima etapa:</b> ampliar a comparação para as equações com múltiplos retornos da Tabela III, realizar a simulação de Monte Carlo e testar a extensão brasileira prevista na proposta.",y-5,9.2,12.3)
    rule(y-11)
    refs=para("Referências: "+href("https://doi.org/10.2307/1912775","Hansen (1982)")+"  ·  "+href("https://doi.org/10.2307/1911873","Hansen e Singleton (1982)")+"  ·  "+href("https://doi.org/10.2307/1911486","Errata (1984)")+"  ·  "+href("https://www.aronaldg.org/papers/curve.pdf","Gallant, §7.4")+"  ·  "+href("https://python.quantecon.org/hansen_singleton_1982.html","QuantEcon"),y-17,8.5,11)
    refs=para(href(REPO,"Repositório: código Python, bases e resultados completos"),refs-3,9,12)
    if refs < 20: raise ValueError(f"Página excedida: margem {refs:.1f} pontos")
    c.showPage()
    c.save()
