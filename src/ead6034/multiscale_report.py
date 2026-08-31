from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .plots import BLUE, GRAY, LIGHT_BLUE, NAVY, RED, TEAL, set_style


PAGE_SIZE = (11.69, 8.27)  # A4 paisagem


def _wrap(text: str, width: int = 92) -> str:
    return "\n".join(textwrap.wrap(text, width=width))


def _page_header(fig: plt.Figure, title: str) -> None:
    fig.patches.extend(
        [plt.Rectangle((0, 0.91), 1, 0.09, transform=fig.transFigure, color=NAVY, zorder=-1)]
    )
    fig.text(0.045, 0.953, title, color="white", fontsize=20, fontweight="bold", va="center")
    fig.text(
        0.955,
        0.953,
        "EAD6034 - Entrega 31/08/2026",
        color="#D9E7F5",
        fontsize=9.5,
        ha="right",
        va="center",
    )


def _image_page(pdf: PdfPages, title: str, image_path: Path, footer: str) -> None:
    fig = plt.figure(figsize=PAGE_SIZE)
    _page_header(fig, title)
    image = plt.imread(image_path)
    ax = fig.add_axes([0.035, 0.075, 0.93, 0.81])
    ax.imshow(image)
    ax.axis("off")
    fig.text(0.045, 0.025, footer, fontsize=8.4, color=GRAY)
    pdf.savefig(fig, dpi=180)
    plt.close(fig)


def create_multiscale_pdf_report(
    output_path: Path,
    overview_path: Path,
    descriptives_path: Path,
    correlograms_path: Path,
    dependence_path: Path,
    summary: dict[str, object],
) -> Path:
    set_style()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    scale_results = {row["scale"]: row for row in summary["scale_results"]}
    daily = scale_results["1d"]
    five_minute = scale_results["5min"]
    horizon = int(summary["comparison_horizon_minutes"])
    five_minute_n = f"{five_minute['n']:,}".replace(",", ".")

    with PdfPages(
        output_path,
        metadata={
            "Title": "EAD6034 - Análise multiescala do WIN",
            "Author": "Renan de Luca Avila",
            "Subject": "Entrega de 31/08/2026 - análise visual, FAC e FACP",
        },
    ) as pdf:
        fig = plt.figure(figsize=PAGE_SIZE)
        fig.patches.extend(
            [plt.Rectangle((0, 0), 0.028, 1, transform=fig.transFigure, color=TEAL, zorder=-1)]
        )
        fig.text(
            0.075,
            0.83,
            "EAD6034 - ECONOMETRIA DE SÉRIES TEMPORAIS",
            color=BLUE,
            fontsize=14,
            fontweight="bold",
        )
        fig.text(0.075, 0.69, "Análise visual multiescala", color=NAVY, fontsize=30, fontweight="bold")
        fig.text(0.075, 0.61, "FAC e FACP do WIN em seis escalas", color=GRAY, fontsize=20)
        fig.text(0.075, 0.52, "Renan de Luca Avila", color=NAVY, fontsize=13, fontweight="bold")
        fig.text(0.075, 0.48, "Entrega semanal - 31 de agosto de 2026", color=GRAY, fontsize=11)

        cards = [
            ("Amostra de identificação", str(summary["train_period"])),
            ("Pregões comuns", f"{summary['train_days']}"),
            ("Escalas", "1, 5, 15, 30, 60 min e 1 dia"),
        ]
        for index, (label, value) in enumerate(cards):
            x = 0.075 + index * 0.295
            fig.patches.extend(
                [plt.Rectangle((x, 0.26), 0.265, 0.14, transform=fig.transFigure, color=LIGHT_BLUE, zorder=-1)]
            )
            fig.text(x + 0.018, 0.365, label, fontsize=9.5, color=GRAY, fontweight="bold")
            fig.text(x + 0.018, 0.307, value, fontsize=11.5, color=NAVY)

        fig.text(
            0.075,
            0.12,
            _wrap(
                "O retorno de 5 minutos permanece como replicação adaptada do benchmark de "
                "Matías e Reboredo (2012). As demais frequências isolam a dimensão escala da "
                "proposta, mantendo o mesmo ativo, os mesmos pregões e o mesmo holdout."
            ),
            fontsize=10.5,
            color=GRAY,
            linespacing=1.45,
        )
        pdf.savefig(fig)
        plt.close(fig)

        fig = plt.figure(figsize=PAGE_SIZE)
        _page_header(fig, "Protocolo comparável entre escalas")
        excluded_dates = ", ".join(summary["excluded_train_dates"])
        decisions = [
            ("Ativo", "WIN, usando o encadeamento de contrato ativo fornecido. Nesta etapa, a classe de ativo fica fixa para isolar a escala."),
            ("Janela", "09:05-18:05 em America/Sao_Paulo: 540 minutos e nove blocos de 60 minutos, sem barra terminal parcial."),
            ("Âncora", "Nas escalas intradiárias, o fechamento do candle iniciado às 09:04 ancora o primeiro bloco. O diário usa o open da barra 09:05."),
            ("Cobertura", f"Mesmos {summary['train_days']} pregões completos em todas as escalas; excluídos no treino: {excluded_dates}."),
            ("Retornos", "Diferenças logarítmicas percentuais dentro do pregão. Zeros e extremos mantidos; sem retorno overnight ou de rolagem."),
            ("Diário", "Open-to-close da janela comum, conforme a proposta; close-to-close aparece apenas como robustez e inclui overnight."),
            ("Dependência", "FAC usa correlação pooled de pares válidos e FACP usa AR(k) pooled, sem atravessar pregões. A lacuna integral de 2024-04-16 e trocas de ticker quebram a sequência diária."),
            ("Holdout", f"2025 permanece fora da identificação; primeiro dia OOS comum: {summary['test_start']}."),
        ]
        for index, (label, body) in enumerate(decisions):
            y = 0.835 - index * 0.092
            fig.text(0.062, y, label, color=BLUE, fontsize=10.8, fontweight="bold", va="top")
            fig.text(0.18, y, _wrap(body, 112), color=NAVY, fontsize=9.8, va="top", linespacing=1.25)

        raw_rows = f"{summary['raw_rows']:,}".replace(",", ".")
        audit_line = (
            f"Auditoria bruta: {raw_rows} linhas; {summary['raw_contracts']} contratos; "
            f"duplicatas={summary['duplicates']}; valores NA={summary['missing_values']}; "
            f"violações OHLC={summary['invalid_ohlc']}."
        )
        fig.text(0.062, 0.075, audit_line, color=GRAY, fontsize=8.8)
        pdf.savefig(fig)
        plt.close(fig)

        _image_page(
            pdf,
            "Série principal: benchmark de 5 minutos",
            overview_path,
            "A janela de 5 minutos é a série principal do seminário. Níveis não são retroajustados; retornos não atravessam ticker ou pregão.",
        )
        _image_page(
            pdf,
            "O que muda com a agregação",
            descriptives_path,
            "Todas as estatísticas usam os mesmos pregões completos de 2024. O diário usa o open da barra 09:05 e o último close da janela comum.",
        )
        _image_page(
            pdf,
            "FAC e FACP por escala intradiária",
            correlograms_path,
            f"A comparação usa separação física de até {horizon} minutos e origem 09:05; bandas pontuais não corrigem múltiplos lags ou heteroscedasticidade.",
        )
        _image_page(
            pdf,
            "Magnitude e escala diária",
            dependence_path,
            "O diário usa open-to-close e lags em pregões. Dependência em |r| não equivale a previsibilidade linear da média.",
        )

        fig = plt.figure(figsize=PAGE_SIZE)
        _page_header(fig, "Conclusões da extensão multiescala")
        acf_min, acf_max = summary["acf_at_common_horizon_range"]
        magnitude_min, magnitude_max = summary["abs_acf_at_common_horizon_range"]
        conclusions = [
            f"A série de 5 minutos continua sendo o núcleo da replicação adaptada: {five_minute_n} retornos no protocolo comum, com FAC de lag 1={five_minute['acf_lag1']:.4f}.",
            f"Na origem 09:05 e separação de {horizon} minutos, as FACs variam de {acf_min:.4f} a {acf_max:.4f} e mudam de sinal. Deslocar a grade é uma robustez futura; não há assinatura linear simples.",
            f"A FAC de |r| em {horizon} minutos permanece positiva em todas as escalas intradiárias, entre {magnitude_min:.3f} e {magnitude_max:.3f}; o padrão é compatível com persistência da volatilidade.",
            "Os zeros diminuem monotonicamente; o excesso de curtose se atenua nas escalas mais grossas, sem monotonicidade perfeita. A dispersão cresce aproximadamente com a raiz do tempo. Essas mudanças não demonstram previsibilidade.",
            f"A escala diária possui apenas {daily['n']} observações. Picos isolados em FAC/FACP, diante de amostra pequena e múltiplos testes, não justificam escolher uma ordem ARMA.",
            "Os resultados descrevem dependência amostral e geram candidatos para Box-Jenkins. Ainda não estabelecem estacionariedade, especificação final ou ganho preditivo OOS.",
        ]
        for index, item in enumerate(conclusions, 1):
            y = 0.825 - (index - 1) * 0.118
            fig.text(
                0.065,
                y,
                str(index),
                color="white",
                fontsize=10.5,
                fontweight="bold",
                ha="center",
                va="center",
                bbox=dict(boxstyle="circle,pad=0.35", facecolor=BLUE, edgecolor="none"),
            )
            fig.text(0.105, y + 0.011, _wrap(item, 108), color=NAVY, fontsize=10.2, va="top", linespacing=1.28)
        fig.text(
            0.065,
            0.06,
            "Referência principal: Matías, J.M.; Reboredo, J.C. (2012). Journal of Forecasting, 31(2), 172-188. DOI 10.1002/for.1218.",
            color=GRAY,
            fontsize=8.6,
        )
        pdf.savefig(fig)
        plt.close(fig)

    return output_path
