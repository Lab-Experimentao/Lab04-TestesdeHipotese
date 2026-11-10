# Roteiro da apresentação: 15 perguntas em 7 minutos

Cada resposta tem cerca de 30 segundos de fala. O formato é sempre o mesmo:

- **Mostrar:** onde clicar ou apontar no dashboard (o guia da barra lateral leva direto a cada lugar).
- **Resposta:** o que falar, lendo o que está na tela.
- **Se perguntarem mais:** uma frase de reserva, caso o professor aprofunde.

Os números são os do dashboard (α = 0,05, 10.000 simulações, semente 42). Se as simulações forem refeitas, confiram os valores na tela antes da apresentação.

## Divisão das perguntas

Cada integrante responde pelo menos 4 perguntas, mas o professor pode pedir qualquer uma a qualquer pessoa: todos devem ler o roteiro inteiro.

| Integrante | Perguntas |
|---|---|
| | 1, 2, 3, 4 |
| | 5, 6, 7, 8 |
| | 9, 10, 11, 12 |
| | 13, 14, 15 (+ demonstração do simulador) |

**Três ideias para ter na ponta da língua, porque aparecem em quase todas as respostas:**

1. **Real × simulado:** os dados reais mostram *como os PRs são*; os simulados permitem *testar os testes*, porque neles nós decidimos se o bot tem efeito e, por isso, sabemos a resposta certa.
2. **Média × ordem:** o t de Welch usa a média e a variância, que um único PR muito lento distorce; o Mann-Whitney usa só a ordem dos valores, e para ele um PR de uma semana ou de um ano conta igual.
3. **Efeito 0,5 = merges 3,9 vezes mais lentos.** É o efeito de exemplo usado nas seções 3, 5 e no simulador.

---

## Seção 1 · Cenário

### 1. Qual é o cenário de vocês e o que H₀ e H₁ afirmam, em palavras simples?

**Mostrar:** seção 1, a pergunta em destaque e os dois quadros H₀ e H₁.

**Resposta:** Queremos saber se um bot de revisão automática muda o tempo até o merge dos PRs. H₀ diz que não muda nada: o tempo tem a mesma distribuição com e sem bot. H₁ diz que muda, para mais ou para menos. Embaixo de cada hipótese está o que cada teste verifica: o t de Welch compara as médias, e o Mann-Whitney verifica se um PR com bot tende a demorar mais que um sem bot.

**Se perguntarem mais:** os dois testes não testam exatamente a mesma coisa. O Welch fala de médias; o Mann-Whitney, de P(X com bot > X sem bot) = ½.

### 2. O teste de vocês é unicaudal ou bicaudal? Por quê?

**Mostrar:** seção 1, item "Teste bicaudal"; depois, no G2 (seção 3), as duas pontas em rosa.

**Resposta:** Bicaudal. O bot pode acelerar o merge, com feedback imediato, ou atrasá-lo, com mais comentários para resolver antes da aprovação. As duas direções interessam e não tínhamos motivo para descartar nenhuma antes de ver os dados. No G2 isso aparece como as duas pontas rosa: os 5% de α são divididos em 2,5% de cada lado.

**Se perguntarem mais:** num teste unicaudal, os 5% ficariam todos numa ponta, e não poderíamos concluir nada se o bot acelerasse o merge.

---

## Seção 2 · Os dados (G1)

### 3. Como os dados reais foram coletados, e o que eles mostraram sobre a forma da distribuição?

**Mostrar:** seção 1, item "Dados reais"; depois o G1 (painéis da esquerda, "Reais") e a tabela "Conjuntos do G1".

**Resposta:** Coletamos pela API do GitHub os PRs mergeados do Ghost, antes e depois da adoção do CodeRabbit: 30 PRs sorteados de cada período, entre 845 elegíveis, excluindo os meses de transição. No G1, em escala log, a forma é muito assimétrica: a mediana fica abaixo de 1 hora (13 e 27 minutos), mas há PRs de dias. A tabela mostra assimetria de 3,6 a 3,9 e 13% a 17% de outliers.

**Se perguntarem mais:** o eixo do G1 é logarítmico porque, em escala normal, quase todos os PRs ficariam espremidos no primeiro intervalo.

### 4. Como os dados reais ajudaram a escolher os parâmetros da simulação?

**Mostrar:** seção 2, itens "Parâmetros da simulação" e "Real × simulado"; tabelas "Parâmetros da mistura" e "Ajuste aos 845 elegíveis".

**Resposta:** Calibramos a simulação nos 845 PRs elegíveis, e não só nos 60 da amostra, porque a amostra quase não pegou a cauda: o PR mais lento dela tem 138 horas, contra 10.807 entre os elegíveis. Os tempos têm dois perfis, merges rápidos e lentos, então usamos uma mistura de duas lognormais. A tabela de ajuste justifica a escolha: o P90 real é 83 h, a mistura dá 62 h e uma lognormal simples daria só 17 h.

**Se perguntarem mais:** a tabela "Parâmetros da mistura" mostra os dois perfis: 49% de merges rápidos (mediana de 0,14 h, uns 8 minutos) e 51% de lentos (mediana de 8,5 h).

---

## Seção 3 · Como os testes funcionam (G2)

### 5. O que cada um dos dois testes compara de fato?

**Mostrar:** seção 3, item "O que cada teste compara"; tabela "Conjunto de exemplo", linha "Estatística no exemplo".

**Resposta:** O t de Welch compara médias: pergunta se a média com bot é diferente da média sem bot, e mede essa diferença na estatística t. O Mann-Whitney compara postos, ou seja, a ordem: forma os 900 pares possíveis entre um PR com bot e um sem e conta em quantos o PR com bot demorou mais. Esse total é o U. Se o bot não mudasse nada, o esperado seria metade, 450.

**Se perguntarem mais:** no exemplo, U = 600,5: o PR com bot foi mais lento em cerca de dois terços dos pares.

### 6. No G2: o que é a distribuição da estatística sob H₀, e por que a região de rejeição fica onde fica?

**Mostrar:** o G2, as curvas coloridas e as pontas rosa; item "Região de rejeição".

**Resposta:** A curva mostra os valores que a estatística costuma ter quando o bot não muda nada: uma t de Student para o Welch e uma normal centrada em 450 para o Mann-Whitney. A região de rejeição fica nas pontas porque ali estão os 5% de resultados mais extremos, improváveis demais para serem acaso; como o teste é bicaudal, são 2,5% de cada lado. O Welch rejeita se t passar de ±2,04; o Mann-Whitney, se U sair de 317 a 583.

**Se perguntarem mais:** as barras cinza são 10.000 coletas simuladas sem efeito. No Mann-Whitney, elas seguem a curva; no Welch, formam dois morros perto de ±1, e é por isso que ele é conservador (pergunta 9).

### 7. O que significa o p-valor do exemplo mostrado no G2? E o que ele não significa?

**Mostrar:** o G2, as áreas hachuradas e as linhas do valor observado; item "P-valor do exemplo".

**Resposta:** No exemplo, o bot deixa os merges 3,9 vezes mais lentos. A área hachurada é o p-valor: a chance de ver um resultado tão extremo quanto este se o bot não mudasse nada. No Mann-Whitney ela é de 2,7%, então ele rejeita H₀ e acerta. No Welch é de 19,3%: ele não rejeita e comete um erro tipo II, porque o efeito existe. O p-valor não é a chance de H₀ ser verdadeira, nem mede o tamanho do efeito.

**Se perguntarem mais:** o tamanho do efeito está na mesma tabela: g = 0,34 e r = 0,33, parecidos nos dois testes, mas com p-valores muito diferentes.

---

## Seção 4 · Erro tipo I (G3)

### 8. No cenário de vocês, o que seria um erro tipo I e um erro tipo II? Qual dos dois seria mais grave?

**Mostrar:** seção 4, item "Erro tipo I e tipo II".

**Resposta:** Erro tipo I é concluir que o bot muda o tempo de merge quando ele não muda: um alarme falso. Erro tipo II é não perceber um atraso real causado pelo bot. Para nós o tipo II é mais grave: um alarme falso leva, no máximo, a reconfigurar um bot que não fazia diferença, mas um atraso não percebido continua custando tempo em todos os PRs, todos os dias.

**Se perguntarem mais:** o G3 mede o erro tipo I; o G4 mede o poder, que é 1 menos a chance de erro tipo II.

### 9. No G3, algum teste se afastou de 5%? Ele ficou liberal ou conservador, e por quê?

**Mostrar:** o G3 (pontos fora da faixa cinza) e a tabela "Erro tipo I por situação", coluna "Diagnóstico".

**Resposta:** O Mann-Whitney ficou perto de 5% em todas as situações, de 4,3% a 5,5%. O t de Welch se afastou e ficou conservador com dados assimétricos: 1,1% no cenário principal, 1,2% na lognormal e 0,5% com amostra pequena. Isso acontece porque um único PR muito lento infla a variância do grupo, o t fica pequeno e raramente chega à região de rejeição, como os dois morros do G2 mostram.

**Se perguntarem mais:** em "Grupos desiguais", os 4,1% do Welch parecem bons, mas 99% das rejeições apontam para o mesmo lado (merge mais lento com bot), quando deveriam se dividir entre os dois.

---

## Seção 5 · Poder (G4)

### 10. No G4, qual teste tem mais poder? A diferença entre eles muda conforme o tamanho do efeito?

**Mostrar:** o G4 (painel "Mistura") e a tabela "Poder com efeito 0,5"; se der tempo, o simulador.

**Resposta:** O Mann-Whitney, em todas as violações. No cenário principal, com merges 3,9 vezes mais lentos, ele detecta o efeito em 59% das coletas, contra 5% do Welch, que não passa de 33% nem com o maior efeito. A diferença cresce com o efeito: a curva do Mann-Whitney sobe rápido e a do Welch sobe muito devagar. Só no controle normal o Welch passa à frente, e por no máximo 3 pontos.

**Se perguntarem mais:** na tabela "Efeito necessário para 80% de poder", o Mann-Whitney chega a 80% com efeito 0,70 (merges 6,6 vezes mais lentos); o Welch não chega no cenário principal.

### 11. Que violação de pressuposto vocês simularam, e por que ela afeta mais um teste do que o outro?

**Mostrar:** tabela "Situações da simulação" na seção 2 (coluna "O que viola no Welch"); depois o G4, comparando "Normal (controle)" com "Mistura".

**Resposta:** Além do controle normal, simulamos seis situações, mudando uma coisa de cada vez: assimetria forte (mistura e lognormal), outliers, amostra pequena, grupos de tamanhos diferentes e variâncias diferentes. A principal violação é a assimetria, que é a forma real dos PRs. Ela afeta mais o Welch porque ele usa a média e a variância, que um PR muito lento domina; o Mann-Whitney usa só a ordem, então o tamanho do valor extremo não importa. No G4, no controle normal os dois empatam; na mistura, o Welch despenca.

**Se perguntarem mais:** com outliers isolados, a vantagem do Mann-Whitney é menor (até 8,8 pontos), porque ali a assimetria típica é de só 0,8, contra 4,1 na mistura.

### 12. Se vocês usassem α = 0,01 em vez de 0,05, o que mudaria no G3 e no G4?

**Mostrar:** trocar o seletor para α = 0,01 no G3 e no G4; itens "Com α = 0,01" e a tabela "α = 0,05 × 0,01", que aparece abaixo do G4.

**Resposta:** No G3, a referência passa de 5% para 1% de alarmes falsos. O Mann-Whitney acompanha, de 0,67% a 0,97%, e o Welch fica ainda mais conservador: 0,04% no cenário principal. No G4, os dois perdem poder porque exigem mais evidência: no controle, caem de cerca de 5 para 2 em cada 10 coletas. Mas com dados assimétricos o Welch quase some, de 5% para 0,2%, enquanto o Mann-Whitney ainda detecta em 33%. Quanto mais rigoroso o α, mais a escolha do teste pesa.

**Se perguntarem mais:** é a troca entre os dois erros: um α menor reduz o erro tipo I, mas aumenta o erro tipo II.

---

## Seção 7 · Conclusão (pergunta 13) e Seção 6 · Dados reais (pergunta 14)

### 13. A simulação confirmou o que o grupo esperava antes de simular? Se não, o que explica a diferença?

**Mostrar:** seção 7, os quadros "Antes de simular" e "Depois de simular"; item "O que não prevíamos".

**Resposta:** Confirmou, e com mais folga do que esperávamos. Antes de simular, apostamos no Mann-Whitney por causa da assimetria e dos outliers; no cenário principal ele detecta 59% contra 5% do Welch. O que não previmos foi como o Welch falha: achávamos que ele erraria demais sob H₀, mas ele erra de menos, só 1,1% de alarmes falsos em vez de 5%. Essa cautela é justamente o que tira o poder dele.

**Se perguntarem mais:** a expectativa ficou registrada na seção 1 antes das simulações; o histórico de commits do repositório mostra a ordem.

### 14. Nos dados reais, os dois testes chegaram à mesma conclusão? O tamanho do efeito tem importância prática?

**Mostrar:** seção 6, as duas tabelas (amostra e elegíveis) e o item "Importância prática".

**Resposta:** Na amostra de 30 + 30 PRs, os dois não rejeitam H₀, mas por motivos diferentes: o Mann-Whitney chega perto (p = 0,062) e o Welch não vê nada (p = 0,977). Com todos os 845 PRs, o Mann-Whitney rejeita (p = 0,032), mas na direção oposta, com merges mais rápidos com bot. Na prática, o efeito não importa: o PR típico leva 13 contra 27 minutos na amostra, e 35 contra 22 nos elegíveis. São minutos, e o sinal até muda.

**Se perguntarem mais:** a média dos elegíveis salta de 35 h para 81 h com bot, mas só por causa de 2 PRs abertos por mais de um ano; sem eles, fica em 32 contra 35 h. É um exemplo direto de por que a média engana neste cenário.

### 15. Qual teste vocês recomendam, em que situação mudariam a recomendação, e qual é a principal limitação do estudo?

**Mostrar:** seção 7, itens "Recomendação", "Quando a escolha mudaria" e "E nos dados reais".

**Resposta:** Recomendamos o Mann-Whitney: ele manteve o erro tipo I entre 4,3% e 5,5% em todas as situações e teve mais poder em todas as violações. Mudaríamos para o Welch em dois casos: dados próximos da normal, como o log dos tempos, ou uma pergunta sobre a média em horas, como o tempo total de espera, que o Mann-Whitney não testa. A principal limitação é o desenho antes × depois: outras coisas mudaram entre os períodos, então nenhuma diferença pode ser atribuída só ao bot.

**Se perguntarem mais:** a outra limitação é a amostra pequena: com o efeito real, o Mann-Whitney teria só 13% de poder com 30 PRs por grupo (seção 5, item "E nos dados reais").

---

## Demonstração do simulador (≈ 20 segundos, se sobrar tempo)

Fica no fim da seção 5, em "Explore o poder". Serve para as perguntas 10 e 12 e para a discussão sobre tamanho da amostra:

1. Clicar em **"Usar os dados reais"**: o n vai para 30 e o efeito para 0,16. Mostrar que o poder é baixo para os dois testes.
2. Arrastar **"PRs por grupo"** até 200: o Mann-Whitney sobe para cerca de 51% e o cartão mostra que nem assim o efeito real chegaria a 80% de poder.
3. Frase de fechamento: *"Não rejeitar H₀ nos dados reais não mostra que o bot não tem efeito; mostra que a amostra era pequena demais para enxergá-lo."*

O simulador usa 2.000 coletas por ponto, então os números podem variar até 2 pontos em relação ao G4. Se houver diferença, os valores oficiais são os do G4 e das tabelas.

## Se o professor perguntar sobre tamanho da amostra (seção 6 do enunciado)

| Pergunta | Resposta curta | Onde mostrar |
|---|---|---|
| Qual o poder com a amostra coletada, para o efeito observado? | 13% no Mann-Whitney e 2% no Welch | Seção 5, "E nos dados reais"; linha pontilhada do G4 |
| Quantos PRs para 80% de poder? É viável? | Com o efeito real, nem 200 por grupo bastam (o Mann-Whitney chega a ~51%); com efeito 0,5, ~51 PRs por grupo no Mann-Whitney | Simulador, cartões de cada teste |
| Não significativo quer dizer que não há efeito? | Não: com 13% de poder, a amostra não conseguiria enxergá-lo | Seção 6, "O que isso indica" |
| Com amostras enormes, o que importa mais? | O tamanho do efeito: com 845 PRs o Mann-Whitney já dá significativo, mas a diferença é de minutos | Seção 6, "Importância prática" |
| O n muda qual teste é melhor? | Com dados assimétricos, não: o Mann-Whitney fica à frente em todos os n do simulador | Simulador, gráfico "Poder × n" |
