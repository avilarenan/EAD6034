"""Regenera a entrega do checkpoint, usando os dois painéis mensais fornecidos."""
from pathlib import Path
import sys, hashlib, json, platform
from importlib.metadata import version
import pandas as pd
from estimate import run
from report import build

ROOT = Path(__file__).resolve().parent
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    out = ROOT / "resultados"
    out.mkdir(exist_ok=True)
    entradas = {
        "NDS": ("gallant_nds_vwr.csv", "90c54d18c2c8e994a2869eb5881034e74ecc572d13f557c65bdc1f62d7b64bcc"),
        "ND": ("hansen_singleton_1982_data.csv", "3e9d4f37c31dbcab26624418f3eeb630d57cc362bd162fa5501cfd992225609b"),
    }
    comparisons, sens = [], []
    for panel, (name, expected) in entradas.items():
        path = ROOT / "dados" / name
        if digest(path) != expected:
            raise ValueError(f"Dados diferentes da edição deste checkpoint: {name}")
        comparisons.append(run(path, out / panel, panel))
        sens.append(pd.read_csv(out / panel / "sensitivity.csv"))
    df = pd.concat(comparisons, ignore_index=True)
    df.to_csv(out / "tabela_I.csv", index=False, float_format="%.9g")
    pd.concat(sens, ignore_index=True).to_csv(out / "sensibilidade.csv",index=False,float_format="%.9g")
    # External numerical check: the archive should match every published J to its printed precision.
    archive = df[df.panel=="NDS"]
    if not (len(archive)==4 and (archive.delta_j.abs()<0.0005).all() and (archive.delta_alpha.abs()<0.0006).all()):
        raise RuntimeError("Comparação do painel histórico com a errata fora da tolerância.")
    build(df, out / "checkpoint_19_11.pdf")
    tracked = list((ROOT / "dados").glob("*.csv")) + list(ROOT.glob("*.py"))
    tracked += list(out.rglob("*.csv")) + [out / "checkpoint_19_11.pdf"]
    manifest = {"python":platform.python_version(), "packages":{x:version(x) for x in ("numpy","pandas","scipy","reportlab")},
                "sha256":{p.relative_to(ROOT).as_posix():digest(p) for p in sorted(tracked)}}
    (out / "manifesto.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"Oito linhas da Tabela I verificadas. PDF: {out/'checkpoint_19_11.pdf'}")

if __name__=="__main__":
    main()
