# Seminário I — requisitos do professor

Anotações feitas por Renan de Luca Avila durante as aulas da disciplina EAD6034 (Econometria de Séries Temporais), registradas neste repositório em 27/09/2026 para orientar o seminário final de 28/09/2026.

Fonte: anotações de aula fornecidas pelo aluno. Este documento preserva os requisitos relatados, sem afirmar que já foram atendidos e sem substituir o enunciado ou o checklist oficial.

## Relevância, dados e horizonte

1. Why is it important to predict the chosen series?
2. What is the data source? Where it comes from?
3. Is the predictive horizon relevant? Why?

## Estacionariedade e especificação

4. Is the series stationary or not?
   - Classificar a série como uma das seguintes opções:
     - "sem constante e sem tendência";
     - "com constante e com tendência";
     - "com constante e sem tendência".
5. É necessário mostrar a equação do modelo ARIMA ajustado.

## Diagnóstico dos resíduos

6. **Obrigatório: "tem que passar no teste de Ljung–Box".**
   - Tem que tratar as autocorrelações.
   - Escolher somente o modelo selecionado: não é necessário fazer com outros modelos.

## Previsão e avaliação fora da amostra

7. É necessário mostrar medidas **out of sample**.
8. É necessário ter uma figura do valor real versus o valor estimado pelo modelo (ou pelos modelos).
9. É necessário indicar se estamos fazendo previsões **one-step-ahead** ou **multi-step-ahead** ("previsão encavalada com previsão").
10. É necessário usar **RMSE, MAE e MAPE**.
11. É importante comparar com o **artigo de referência**.
12. Elaborar a **avaliação preditiva final**.
