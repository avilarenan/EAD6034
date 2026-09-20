# Registro de validação — 20/09/2026

Entrega cumulativa de 21/09/2026, com [código fixado nesta versão](https://github.com/avilarenan/EAD6034/tree/a6c7de81989e586ea117e994f366a1bb6933a66b/src/ead6034) e [testes](https://github.com/avilarenan/EAD6034/tree/a6c7de81989e586ea117e994f366a1bb6933a66b/tests).

## Verificações concluídas

- **84 testes automatizados aprovados**, incluindo os módulos históricos e as novas invariantes de tempo de negociação, estimação, previsão causal, variância, alinhamento e apresentação.
- **216 candidatos ARMA** e **18 seleções**: mínimos de BIC conferidos dentro da família declarada e somente com 2024.
- **378 linhas de acurácia** recalculadas independentemente a partir dos erros locais; diferença máxima inferior a 10⁻¹⁶.
- **1.989 alvos horários comuns** nas cinco escalas, com mesmas origens, finais e máscaras entre modelos. Divergência máxima da reconciliação dos retornos inferior a 1,71 × 10⁻¹³ pontos percentuais (tolerância 10⁻¹⁰).
- Nenhuma origem descartada por previsão não finita. Nenhum parâmetro ou ordem estimado com 2025.
- **Sete slides** renderizados e inspecionados visualmente; código clicável em todas as páginas. Tabelas, conclusões e gráficos confrontados com os CSV consolidados.
- Dados brutos, preços, retornos, previsões e resíduos individuais permanecem privados. Estatísticas do perfil intradiário com menos de dez observações são suprimidas.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  PYTHONPATH=src python -m unittest discover -s tests
```

Foram emitidos avisos de compatibilidade futura de `statsmodels` e de inicialização numérica em testes sintéticos, sem falhas. As versões utilizadas e hashes do código constam no [manifesto](analysis_summary.json).

## Limites que a validação de código não elimina

Testes de software não validam as hipóteses econômicas ou estatísticas. Permanecem sensibilidade dos testes de estacionariedade à tendência, heteroscedasticidade, dependência residual em algumas especificações, multiplicidade, filtro retrospectivo de dias completos e calendário histórico incompleto. O estudo não identifica causalmente leilões/overnight nem avalia lucros após custos.

Na comparação comum de 60 minutos, nenhum modelo avaliado supera o retorno zero pelo MSE. Esse resultado negativo foi preservado, assim como os artefatos originais das entregas anteriores.

## Revisão de apresentação, referências e defesa — 20/09/2026

Esta revisão acrescenta a fonte oficial Alpha Lab, sua regra retrospectiva de seleção de contratos, a conclusão crítica, o roteiro oral dos sete slides e as perguntas dos professores. Os modelos não foram reestimados e as tabelas numéricas permanecem iguais às da validação original acima.

Os cinco testes específicos de apresentação/resultados passaram novamente. Os sete slides foram renderizados e inspecionados, sem avisos de overflow do LaTeX. Cada página mantém uma referência clicável ao código, e a primeira inclui a página oficial do BTG-ATS-A26. As notas orais e a conclusão foram revisadas contra os CSV e as Aulas 2–6 disponíveis. O gerador verifica hashes de 18 tabelas para impedir a reutilização silenciosa desse texto com outra execução empírica.

A documentação oficial revela que o fornecedor escolhe o contrato de maior volume do próprio dia. Portanto, o controle de causalidade temporal do filtro não elimina a seleção ex post da composição da série. Essa limitação se soma ao filtro retrospectivo de pregões completos e está explicitada nos materiais revisados.
