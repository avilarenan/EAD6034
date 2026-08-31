from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .plots import BLUE, GRAY, LIGHT_BLUE, NAVY, RED, TEAL, set_style


PAGE_SIZE = (11.69, 8.27)  # A4 paisagem


def _wrap(text: str, width: int = 82) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _page_header(fig: plt.Figure, title: str, subtitle: str | None = None) -> None:
    fig.patches.extend(
        [plt.Rectangle((0, 0.91), 1, 0.09, transform=fig.transFigure, color=NAVY, zorder=-1)]
    )
    fig.text(0.045, 0.953, title, color="white", fontsize=20, fontweight="bold", va="center")
    if subtitle:
        fig.text(0.955, 0.953, subtitle, color="#D9E7F5", fontsize=9.5, ha="right", va="center")


def _image_page(pdf: PdfPages, title: str, image_path: Path, footer: str) -> None:
    fig = plt.figure(figsize=PAGE_SIZE)
    _page_header(fig, title, "EAD6034 - Entrega 31/08/2026")
    image = plt.imread(image_path)
    ax = fig.add_axes([0.035, 0.08, 0.93, 0.80])
    ax.imshow(image)
    ax.axis("off")
    fig.text(0.045, 0.028, footer, fontsize=8.5, color=GRAY)
    pdf.savefig(fig)
    plt.close(fig)


def create_pdf_report(
    output_path: Path,
    overview_path: Path,
    correlogram_path: Path,
    dependence_path: Path,
    summary: dict[str, object],
) -> Path:
    set_style()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(
        output_path,
        metadata={
            "Title": "EAD6034 - Análise visual, FAC e FACP do WIN",
            "Author": "Renan de Luca Avila",
            "Subject": "Entrega de 31/08/2026",
        },
    ) as pdf:
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.patches.extend(
            [plt.Rectangle((0, 0), 0.028, 1, transform=fig.transFigure, color=TEAL, zorder=-1)]
        )
        fig.text(0.075, 0.83, "EAD6034 - ECONOMETRIA DE SÉRIES TEMPORAIS", color=BLUE, fontsize=14, fontweight="bold")
        fig.text(0.075, 0.69, "Análise visual, FAC e FACP", color=NAVY, fontsize=30, fontweight="bold")
        fig.text(0.075, 0.61, "Retornos intradiários de 5 minutos do WIN", color=GRAY, fontsize=20)
        fig.text(0.075, 0.52, "Renan de Luca Avila", color=NAVY, fontsize=13, fontweight="bold")
        fig.text(0.075, 0.48, "Entrega semanal - 31 de agosto de 2026", color=GRAY, fontsize=11)

        cards = [
            ("Amostra de identificação", str(summary["train_period"])),
            ("Pregões / retornos", f"{summary['train_days']:,} / {summary['train_returns']:,}".replace(",", ".")),
            ("Série-alvo", r"$r_{d,j}=100[\log(P_{d,j})-\log(P_{d,j-1})]$"),
        ]
        for i, (label, value) in enumerate(cards):
            x = 0.075 + i * 0.295
            fig.patches.extend(
                [plt.Rectangle((x, 0.26), 0.265, 0.14, transform=fig.transFigure, color=LIGHT_BLUE, zorder=-1)]
            )
            fig.text(x + 0.018, 0.365, label, fontsize=9.5, color=GRAY, fontweight="bold")
            fig.text(x + 0.018, 0.307, value, fontsize=12, color=NAVY)

        fig.text(
            0.075,
            0.12,
            _wrap(
                "Piloto da replicação linear em futuro de índice da B3. O arquivo permite testar "
                "candles de 1 minuto e suas agregações, mas não sustenta ainda a escala de segundos, "
                "midquotes, ações ou opções previstas como extensões na proposta."
            ),
            fontsize=10.5,
            color=GRAY,
            linespacing=1.45,
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=PAGE_SIZE)
        _page_header(fig, "Construção da série", "EAD6034 - Entrega 31/08/2026")
        excluded = int(summary["excluded_days"])
        excluded_dates = ", ".join(str(item) for item in summary["excluded_train_dates"])
        exclusion_text = (
            f"{excluded} pregão de horário reduzido excluído do treino ({excluded_dates})."
            if excluded == 1
            else f"{excluded} pregões de horário reduzido excluídos do treino."
        )
        decisions = [
            ("Dados", "Candles de 1 minuto do encadeamento de contrato ativo WIN fornecido no arquivo."),
            ("Horário", "Timestamps tratados como UTC e convertidos para America/Sao_Paulo; janela regular 09:05-18:25."),
            ("Agregação", "Último negócio em barras [t-5min,t), sem interpolação; carregamento do último preço apenas dentro do pregão."),
            ("Retorno", "Diferença logarítmica percentual apenas dentro da mesma data e do mesmo contrato; overnight e rolagens excluídos."),
            ("Qualidade", f"Cobertura mínima de 95%; {exclusion_text}"),
            ("Holdout", f"2025 reservado e não utilizado nos correlogramas; primeiro dia OOS: {summary['test_start']}."),
        ]
        for i, (label, body) in enumerate(decisions):
            y = 0.82 - i * 0.115
            fig.text(0.065, y, label, color=BLUE, fontsize=11.5, fontweight="bold", va="top")
            fig.text(0.19, y, _wrap(body, 105), color=NAVY, fontsize=10.5, va="top", linespacing=1.35)

        fig.text(0.065, 0.155, "Auditoria e descritivas", color=RED, fontsize=11.5, fontweight="bold")
        audit_line = (
            f"{summary['raw_rows']:,} linhas WIN; {summary['raw_contracts']} contratos; "
            f"duplicatas={summary['duplicates']}; ausentes={summary['missing_values']}; "
            f"violações OHLC={summary['invalid_ohlc']}."
        ).replace(",", ".")
        fig.text(0.065, 0.115, audit_line, color=GRAY, fontsize=10)
        descriptive_line = (
            f"Treino: média={summary['mean_return']:.6f}%; desvio-padrão={summary['standard_deviation']:.6f}%; "
            f"zeros={100 * summary['zero_share']:.2f}%; mínimo={summary['minimum_return']:.4f}%; "
            f"máximo={summary['maximum_return']:.4f}%."
        )
        fig.text(0.065, 0.072, descriptive_line, color=GRAY, fontsize=10)
        pdf.savefig(fig)
        plt.close(fig)

        _image_page(
            pdf,
            "Leitura visual da série",
            overview_path,
            "O nível é mostrado apenas para contexto: mudanças de contrato não são retroajustadas. Os retornos nunca atravessam a rolagem.",
        )
        _image_page(
            pdf,
            "FAC e FACP dos retornos",
            correlogram_path,
            "FAC/FACP calculadas somente em 2024 e com defasagens restritas ao mesmo pregão.",
        )
        _image_page(
            pdf,
            "Dependência na volatilidade",
            dependence_path,
            "A persistência em |r| e r^2 é compatível com heteroscedasticidade e também contém sazonalidade intradiária; não equivale à previsibilidade linear da média.",
        )

        fig = plt.figure(figsize=PAGE_SIZE)
        _page_header(fig, "Conclusões da primeira entrega", "EAD6034 - Entrega 31/08/2026")
        conclusions = [
            "Os retornos de 5 minutos oscilam em torno de zero, com episódios concentrados de maior magnitude e caudas pronunciadas. A avaliação formal de estacionariedade fica reservada para 14/09.",
            f"A FAC e a FACP apresentam magnitudes pequenas e nenhum padrão simples de truncamento ou decaimento. O maior |FAC| entre 1 e 30 lags é {summary['max_abs_acf']:.4f}; picos isolados devem ser avaliados com cautela por causa de múltiplos testes.",
            f"Na separação de 60 minutos (lag 12), FAC={summary['acf_12']:.4f} e FACP={summary['pacf_12']:.4f}. Isso não é um retorno agregado de 60 minutos e não autoriza selecionar, nesta etapa, um ARMA específico.",
            f"A dependência é substancialmente maior na magnitude: FAC(|r|) no lag 1={summary['abs_acf_1']:.3f}. O padrão é compatível com clustering de volatilidade, mas também reflete a sazonalidade intradiária mostrada na página anterior.",
            "Na próxima entrega, ADF/PP/KPSS e o ciclo identificação-estimação-diagnóstico de Box-Jenkins serão aplicados apenas ao treino, complementando FAC/FACP com BIC, raízes e Ljung-Box.",
        ]
        for i, item in enumerate(conclusions, 1):
            y = 0.82 - (i - 1) * 0.14
            fig.text(0.065, y, str(i), color="white", fontsize=11, fontweight="bold", ha="center", va="center", bbox=dict(boxstyle="circle,pad=0.35", facecolor=BLUE, edgecolor="none"))
            fig.text(0.105, y + 0.012, _wrap(item, 105), color=NAVY, fontsize=10.7, va="top", linespacing=1.35)
        fig.text(
            0.065,
            0.075,
            "Referência de desenho: Matías, J.M.; Reboredo, J.C. (2012). Forecasting performance of nonlinear models for intraday stock returns. Journal of Forecasting, 31(2), 172-188.",
            color=GRAY,
            fontsize=8.6,
        )
        pdf.savefig(fig)
        plt.close(fig)

    return output_path
