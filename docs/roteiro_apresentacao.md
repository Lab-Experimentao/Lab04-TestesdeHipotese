# Roteiro da apresentação: 15 perguntas em 7 minutos

Cada resposta tem cerca de 30 segundos de fala. O formato é sempre o mesmo:

- **Mostrar:** onde clicar ou apontar no dashboard (o guia da barra lateral leva direto a cada lugar).
- **Resposta:** o que falar, lendo o que está na tela.
- **Se perguntarem mais:** uma frase de reserva, caso o professor aprofunde.

Os números são os do dashboard (α = 0,05, 10.000 simulações, semente 42). Se as simulações forem refeitas, confiram os valores na tela antes da apresentação.

## Divisão das perguntas

Cada integrante responde pelo menos 4 perguntas, mas o professor pode pedir qualquer uma a qualquer pessoa: todos devem ler o roteiro inteiro.

## Conceitos para ter na ponta da língua

Aparecem em quase todas as respostas. Se o professor perguntar "o que é isso?", a resposta está aqui.

### Os dois grupos e "PRs por grupo"

Um **grupo** é um dos dois conjuntos de PRs que comparamos:

- **Sem bot:** PRs do Ghost criados em out e nov/2024, antes da adoção do CodeRabbit.
- **Com bot:** PRs criados em fev e mar/2025, todos revisados pelo CodeRabbit.

**"PRs por grupo"** é quantos PRs há em cada lado da comparação. Na amostra real são 30 + 30. Nas simulações também são 30, exceto em "Amostra pequena" (10 por grupo) e "Grupos desiguais" (15 e 45). Quanto mais PRs por grupo, mais fácil perceber um efeito, ou seja, mais poder.

### Por que precisamos de dados simulados

Com dados reais **não sabemos a resposta certa**. Se um teste diz "o bot atrasa o merge", não há como saber se ele acertou, porque ninguém sabe o efeito verdadeiro do bot.

Na simulação, **nós decidimos** se o bot tem efeito e de que tamanho:

- **Efeito zero:** H₀ é verdadeira, então toda rejeição é um **alarme falso** (erro tipo I). É o que o G3 mede.
- **Efeito maior que zero:** H₁ é verdadeira, então a proporção de rejeições é o **poder**, a chance de perceber o efeito. É o que o G4 mede.

Repetindo isso 10.000 vezes, medimos com que frequência cada teste acerta e erra.

### Como os dados simulados são feitos

1. **Calibração:** ajustamos a mistura de lognormais aos 845 PRs elegíveis reais, para que os simulados tenham a mesma forma.
2. **Uma coleta simulada:** sorteamos 30 PRs sem bot e 30 com bot dessa mistura. Nos PRs com bot, multiplicamos os tempos pelo efeito escolhido: efeito 0 não muda nada, e efeito 0,5 deixa os merges 3,9 vezes mais lentos.
3. **Os testes:** aplicamos o Welch e o Mann-Whitney a essa coleta e anotamos se deram p < 0,05.
4. **Repetição:** fazemos isso 10.000 vezes para cada situação e cada tamanho de efeito. A proporção de p < 0,05 é o erro tipo I (com efeito zero) ou o poder (com efeito).

As **situações** (normal, outliers, amostra pequena etc.) mudam o passo 2, alterando a forma dos dados, uma coisa de cada vez.

### Por que não usar só os dados reais

Nós usamos os dados reais: a seção 6 aplica os dois testes a eles. Mas eles não bastam para **comparar** os testes, por dois motivos:

- **Um conjunto real dá um resultado só,** e não dá para calcular uma taxa de acerto com uma única observação.
- **Não sabemos a resposta certa.** O próprio dashboard mostra o problema: na amostra de 60 PRs, o Mann-Whitney não rejeita H₀ (p = 0,062) e aponta merge mais lento com bot; com os 845 PRs, ele rejeita (p = 0,032), mas na direção oposta. Com dados reais, não há como dizer qual dos dois está certo.

Por isso, como diz o enunciado, os dados reais servem para **deixar a simulação realista** e para a **aplicação final**; quem decide qual teste é melhor é a simulação.
### O que é uma lognormal

É uma distribuição típica de **tempos**: a maioria dos valores é pequena e alguns poucos são enormes, formando uma cauda longa à direita. O nome vem de que o **logaritmo** dos tempos tem a forma de sino de uma normal. Por isso o G1 usa eixo em escala log: só assim cabem na mesma figura os merges de minutos e os de semanas.

No nosso caso, uma lognormal só não bastava, porque os PRs têm **dois perfis**. Usamos uma **mistura de duas lognormais**: 49% de merges rápidos (mediana de ~8 minutos, a equipe mergeando o próprio PR) e 51% de merges lentos (mediana de ~8,5 horas, esperando revisão).

### O que é o t de Welch

É um teste **paramétrico** que compara as **médias** dos dois grupos. Ele divide a diferença entre as médias pela incerteza dessa diferença; o resultado é o t. Quanto mais longe de zero, mais forte a evidência de que as médias diferem. É uma versão do t de Student que **não exige que os grupos tenham a mesma variância**.

O ponto fraco: ele supõe que a média de cada grupo se comporta como uma normal. Isso vale com dados simétricos ou amostras grandes, mas falha com assimetria forte e poucos dados, porque **um único PR muito lento puxa a média e infla a variância**.

### O que é o Mann-Whitney

É um teste **não paramétrico**. Imagine juntar todos os PRs e colocá-los numa fila, do mais rápido ao mais lento: o teste verifica se os PRs com bot tendem a ficar mais para o fim da fila. Ele usa só a **ordem** (os postos), não o valor em horas, então um PR de uma semana ou de um ano conta igual: é simplesmente "o mais lento".

Por isso ele quase não sofre com assimetria e outliers. O preço: ele não diz nada sobre a média em horas, que às vezes é o que interessa (por exemplo, o tempo total de espera).

### Efeito 0,5 = merges 3,9 vezes mais lentos

É o efeito de exemplo usado nas seções 3, 5 e no simulador. O "efeito" mede quantas vezes os tempos com bot ficam maiores: 0,25 deixa os merges 2 vezes mais lentos, 0,5 os deixa 3,9 vezes, e 1 os deixa 15 vezes. O efeito observado nos dados reais é de só 0,16, cerca de 1,5 vez.

---

## Seção 1 · Cenário

### 1. Qual é o cenário de vocês e o que H₀ e H₁ afirmam, em palavras simples?

**Mostrar:** seção 1, a pergunta em destaque e os dois quadros H₀ e H₁.

**Resposta:** Queremos saber se um bot de revisão automática muda o tempo até o merge dos PRs. H₀ diz que não muda nada: o tempo tem a mesma distribuição com e sem bot. H₁ diz que muda, para mais ou para menos. Embaixo de cada hipótese está o que cada teste verifica: o t de Welch compara as médias, e o Mann-Whitney verifica se um PR com bot tende a demorar mais que um sem bot.

**Se perguntarem mais:** os dois testes não testam exatamente a mesma coisa. O Welch fala de médias; o Mann-Whitney, de P(X com bot > X sem bot) = ½.

### 2. O teste de vocês é unicaudal ou bicaudal? Por quê?

**Mostrar:** seção 1, item "Teste bicaudal"; depois, no G2 (seção 3), as duas pontas em rosa.

**Resposta:** Bicaudal. O bot pode acelerar o merge, com feedback imediato, ou atrasá-lo, com mais comentários para resolver antes da aprovação. As duas direções interessam e não tínhamos motivo para descartar nenhuma antes de ver os dados. Isso aparece visualmente nas curvas do G2, na seção 3 e tambem mostra os 5% de α divididos entre os dois lados, 2,5% em cada um.

**Se perguntarem mais:** num teste unicaudal, os 5% ficariam todos numa ponta, e não poderíamos concluir nada se o bot acelerasse o merge.

---

## Seção 2 · Os dados (G1)

### 3. Como os dados reais foram coletados, e o que eles mostraram sobre a forma da distribuição?

**Mostrar:** seção 1, item "Dados reais"; depois o G1 (painéis da esquerda, "Reais") e a tabela "Conjuntos do G1".

**Resposta:** Coletamos pela API do GitHub os PRs mergeados do repositório do Ghost (uma plataforma open-source de newsletters com centenas de PRs por mês). A partir de fevereiro de 2025, o CodeRabbit passou a revisar todos os PRs; comparamos os dois meses antes da adoção com os dois meses depois. Dos 845 PRs elegíveis que conseguimos pegar, sorteamos 30 de cada período. No G1, em escala log, a forma é muito assimétrica: a mediana fica abaixo de 1 hora (13 e 27 minutos), mas há PRs de dias. A tabela mostra assimetria de 3,6 a 3,9, muito acima de zero, que seria o simétrico, e 13% a 17% de PRs muito mais lentos que o normal do grupo (os outliers).

**Se perguntarem mais:** o eixo do G1 é logarítmico porque, em escala normal, quase todos os PRs ficariam espremidos no primeiro intervalo.

### 4. Como os dados reais ajudaram a escolher os parâmetros da simulação?

**Mostrar:** seção 2, itens "Parâmetros da simulação" e "Real × simulado"; tabelas "Parâmetros da mistura" e "Ajuste aos 845 elegíveis".

**Resposta:** Os dados reais definiram a forma e os números da simulação, em três passos.

1. **De onde tiramos os números:** usamos os 845 PRs elegíveis, e não só os 60 da amostra. Por acaso, a amostra quase não pegou PRs muito lentos: o mais demorado dela levou 138 horas, enquanto entre os elegíveis há um de 10.807 horas.
2. **Que forma usar:** os dados mostram dois tipos de PR, os que a equipe mergeia em minutos e os que esperam revisão por horas. Por isso simulamos uma mistura de duas lognormais, uma para cada tipo: 49% de merges rápidos (mediana de uns 8 minutos) e 51% de lentos (mediana de 8,5 horas), como mostra a tabela "Parâmetros da mistura".
3. **Como sabemos que a forma acerta:** a tabela "Ajuste aos 845 elegíveis" compara os PRs mais lentos. Nos dados reais, 90% dos PRs são mergeados em até 83 horas (o P90); a mistura dá 62 horas, perto disso, e uma lognormal simples daria só 17, subestimando muito os PRs lentos.

**Se perguntarem mais:** se usássemos só a amostra de 60, a simulação herdaria o acaso dela e teria quase nenhum PR muito lento. Os dados simulados ficariam mais "comportados" do que a realidade, justamente o tipo de dado em que o t de Welch vai melhor.

---

## Seção 3 · Como os testes funcionam (G2)

### 5. O que cada um dos dois testes compara de fato?

**Mostrar:** seção 3, item "O que cada teste compara"; tabela "Conjunto de exemplo", linha "Estatística no exemplo".

**Resposta:** O t de Welch compara médias: pergunta se a média com bot é diferente da média sem bot, e mede essa diferença na estatística t. O Mann-Whitney compara postos, ou seja, a ordem: forma os 900 pares possíveis entre um PR com bot e um sem e conta em quantos o PR com bot demorou mais. Esse total é o U. Se o bot não mudasse nada, o esperado seria metade, 450.

**Se perguntarem mais:** no exemplo, U = 600,5: o PR com bot foi mais lento em cerca de dois terços dos pares.

### 6. No G2: o que é a distribuição da estatística sob H₀, e por que a região de rejeição fica onde fica?

**Mostrar:** o G2, as curvas coloridas e as pontas rosa; item "Região de rejeição".

**Resposta:** A curva mostra os valores que a estatística costuma ter quando o bot não muda nada, só pelo acaso de quais PRs caíram na amostra. No Welch, ela fica em volta de zero, porque sem efeito as médias tendem a ser iguais. No Mann-Whitney, fica em volta de 450, porque sem efeito o PR com bot seria o mais lento em metade dos 900 pares. A região de rejeição fica nas pontas porque ali estão os 5% de resultados mais extremos, raros demais para serem só acaso; como o teste é bicaudal, são 2,5% em cada ponta. Se o resultado cair numa ponta, o teste **rejeita H₀**, ou seja, conclui que o bot muda o tempo de merge. Se cair no meio, **não rejeita**: não há evidência suficiente de diferença. Na prática, o Welch rejeita quando t passa de +2,04 ou fica abaixo de −2,04, e o Mann-Whitney quando U fica abaixo de 317 ou acima de 583.

**Se perguntarem mais:**
- **Não rejeitar não prova que o bot não muda nada:** só quer dizer que a diferença observada cabe no que o acaso produziria. É como um julgamento: "não culpado" não é o mesmo que "inocente".
- **As curvas têm nome:** a do Welch é uma t de Student, e a do Mann-Whitney é uma normal. São as distribuições que cada teste usa como referência para calcular o p-valor.
- **As barras cinza** são 10.000 coletas simuladas sem efeito. No Mann-Whitney, elas seguem a curva; no Welch, formam dois morros perto de ±1, e é por isso que ele é conservador (pergunta 9).

### 7. O que significa o p-valor do exemplo mostrado no G2? E o que ele não significa?

**Mostrar:** o G2, as áreas hachuradas e as linhas do valor observado; item "P-valor do exemplo".

**Resposta:** O exemplo é uma coleta simulada em que nós colocamos o efeito: o bot deixa os merges 3,9 vezes mais lentos. A linha preta marca o resultado dessa coleta, e a área hachurada, que vai dessa linha até a ponta da curva dos dois lados, é o p-valor: a chance de ver um resultado tão extremo quanto este se o bot não mudasse nada. A regra é comparar com os 5% de α. No Mann-Whitney, o p-valor é 2,7%, menor que 5%: ele rejeita H₀ e acerta, porque sabemos que o efeito existe. No Welch, é 19,3%, maior que 5%: ele não rejeita e comete um erro tipo II. O p-valor **não** é a chance de H₀ ser verdadeira, nem mede o tamanho do efeito.

**Se perguntarem mais:**
- **O erro comum:** p = 2,7% **não** quer dizer "2,7% de chance de o bot não fazer nada". Quer dizer: "se o bot não fizesse nada, só 2,7% das coletas dariam um resultado tão extremo quanto este".
- **Por que o p-valor não mede o tamanho do efeito:** na tabela "Conjunto de exemplo", o tamanho do efeito é parecido nos dois testes (g = 0,34 e r = 0,33), mas os p-valores são muito diferentes (19,3% e 2,7%). O p-valor depende também do teste e do tamanho da amostra.

---

## Seção 4 · Erro tipo I (G3)

### 8. No cenário de vocês, o que seria um erro tipo I e um erro tipo II? Qual dos dois seria mais grave?

**Mostrar:** seção 4, item "Erro tipo I e tipo II".

**Resposta:** Erro tipo I é concluir que o bot muda o tempo de merge quando ele não muda: um alarme falso. Erro tipo II é não perceber um atraso real causado pelo bot. Para nós o tipo II é mais grave: um alarme falso leva, no máximo, a reconfigurar um bot que não fazia diferença, mas um atraso não percebido continua custando tempo em todos os PRs, todos os dias.

**Se perguntarem mais:** o G3 mede o erro tipo I; o G4 mede o poder, que é 1 menos a chance de erro tipo II.

### 9. No G3, algum teste se afastou de 5%? Ele ficou liberal ou conservador, e por quê?

**Mostrar:** o G3 (pontos fora da faixa cinza) e a tabela "Erro tipo I por situação", coluna "Diagnóstico".

**Resposta:** Cada linha do G3 é uma situação, que é basicamente uma versão da simulação que muda uma coisa só: na de outliers, 5% dos PRs viram "esquecidos", muito mais lentos que os outros; na de amostra pequena, são só 10 PRs por grupo; e o controle normal é o caso ideal para o Welch, que serve de comparação. Assim, se um teste piora, sabemos o que causou isso. O Mann-Whitney ficou perto de 5% em todas as situações, de 4,3% a 5,5%. O t de Welch se afastou e ficou conservador com dados assimétricos: 1,1% no cenário principal, 1,2% na lognormal e 0,5% com amostra pequena. Isso acontece porque um único PR muito lento infla a variância do grupo, o t fica pequeno e raramente chega à região de rejeição, como os dois morros do G2 mostram.

**Se perguntarem mais:** em "Grupos desiguais", os 4,1% do Welch parecem bons, mas 99% das rejeições apontam para o mesmo lado (merge mais lento com bot), quando deveriam se dividir entre os dois.

---

## Seção 5 · Poder (G4)

### 10. No G4, qual teste tem mais poder? A diferença entre eles muda conforme o tamanho do efeito?

**Mostrar:** o G4 (painel "Mistura") e a tabela "Poder com efeito 0,5"; se der tempo, o simulador.

**Resposta:** O Mann-Whitney, em todas as violações. No cenário principal, com merges 3,9 vezes mais lentos, ele detecta o efeito em 59% das coletas, contra 5% do Welch, que não passa de 33% nem com o maior efeito. A diferença cresce com o efeito: a curva do Mann-Whitney sobe rápido e a do Welch sobe muito devagar. Só no controle normal o Welch passa à frente, e por no máximo 3 pontos, porque sem PRs extremos a média aproveita quanto cada PR demorou, e não só a ordem. 

No simulador dá para ver isso ao vivo: com os mesmos 30 PRs por grupo, ao subir o efeito de 0,5 para 0,7 (merges 6,7 vezes mais lentos), o Mann-Whitney vai de 59% para 82% e passa dos 80% de poder, ou seja, perceberia o efeito em 8 de cada 10 coletas, o padrão usado em pesquisa; o Welch fica em 10%.

**Se perguntarem mais:**
- Na tabela "Efeito necessário para 80% de poder", o Mann-Whitney chega a 80% com efeito 0,70 (merges 6,6 vezes mais lentos); o Welch não chega no cenário principal.
- **"Mas o efeito real não é 0,16?"** Sim, e é por isso que usamos outros valores aqui. O 0,5 e o 0,7 são efeitos **hipotéticos**: a pergunta é "*se* o bot tivesse um efeito desse tamanho, qual teste perceberia?". Com o efeito real de 0,16 e 30 PRs por grupo, nenhum teste percebe quase nada (13% e 2% de poder), as curvas mal se separam e não dá para comparar os testes. Por isso o enunciado pede efeitos crescentes, começando em zero.

### 11. Que violação de pressuposto vocês simularam, e por que ela afeta mais um teste do que o outro?

**Mostrar:** tabela "Situações da simulação" na seção 2 (coluna "O que viola no Welch"); depois o G4, comparando "Normal (controle)" com "Mistura".

**Resposta:** O Welch supõe que a média representa bem cada grupo, o que exige dados simétricos. A principal violação que simulamos é a **assimetria**, a forma real dos PRs. Ela afeta mais o Welch porque um PR muito lento distorce a média: quatro PRs de minutos e um de 30 dias dão média de cerca de 6 dias. Para o Mann-Whitney, esse PR é só "o mais lento da fila". No G4, os dois empatam no controle normal, e o Welch despenca na mistura.

**Se perguntarem mais:**
- **Situações simuladas:** controle normal, mistura, lognormal, outliers, amostra pequena, grupos desiguais e variâncias diferentes, uma mudança por vez.
- **Em "Outliers" as curvas andam juntas** (33% × 38%) porque só 5% dos PRs são extremos e o resto é simétrico: o que derruba o Welch é a assimetria do conjunto inteiro, não alguns outliers.

### 12. Se vocês usassem α = 0,01 em vez de 0,05, o que mudaria no G3 e no G4?

**Mostrar:** trocar o seletor para α = 0,01 no G3 e no G4; itens "Com α = 0,01" e a tabela "α = 0,05 × 0,01", que aparece abaixo do G4.

**Resposta:** No G3, a referência passa de 5% para 1% de alarmes falsos. O Mann-Whitney acompanha, de 0,67% a 0,97%, e o Welch fica ainda mais conservador: 0,04% no cenário principal. No G4, os dois perdem poder porque exigem mais evidência: no controle, caem de cerca de 5 para 2 em cada 10 coletas. Mas com dados assimétricos o Welch quase some, de 5% para 0,2%, enquanto o Mann-Whitney ainda detecta em 33%. Quanto mais rigoroso o α, mais a escolha do teste pesa.

**Se perguntarem mais:** é a troca entre os dois erros: um α menor reduz o erro tipo I, mas aumenta o erro tipo II.

---

## Seção 7 · Conclusão (pergunta 13) e Seção 6 · Dados reais (pergunta 14)

### 13. A simulação confirmou o que o grupo esperava antes de simular? Se não, o que explica a diferença?

**Mostrar:** seção 7, os quadros "Antes de simular" e "Depois de simular"; item "O que não prevíamos".

**Resposta:** Confirmou, e com mais folga do que esperávamos. Antes de simular, apostamos no Mann-Whitney por causa da assimetria e dos outliers; no cenário principal ele detecta 59% contra 5% do Welch. O que não previmos foi como o Welch falha: achávamos que, quando o bot não muda nada, ele daria alarmes falsos demais, mas ele dá de menos, só 1,1% de alarmes falsos em vez de 5%. Essa cautela é justamente o que tira o poder dele.

**Se perguntarem mais:** a expectativa ficou registrada na seção 1 antes das simulações; o histórico de commits do repositório mostra a ordem.

### 14. Nos dados reais, os dois testes chegaram à mesma conclusão? O tamanho do efeito tem importância prática?

**Mostrar:** seção 6, as duas tabelas (amostra e elegíveis) e o item "Importância prática".

**Resposta:** Na amostra de 30 + 30 PRs, nenhum dos dois rejeita H₀, mas de jeitos diferentes: o Mann-Whitney chega perto de rejeitar (p = 0,062, pouco acima de 5%), e o Welch não vê diferença nenhuma (p = 0,977). Com todos os 845 PRs, o Mann-Whitney rejeita (p = 0,032), mas na direção oposta à da amostra: ali o bot parece acelerar o merge. Na prática, o efeito não importa: o PR típico leva 13 contra 27 minutos na amostra, e 35 contra 22 nos elegíveis. São minutos, e a direção até se inverte.

**Se perguntarem mais:** a média dos elegíveis salta de 35 h para 81 h com bot, mas só por causa de 2 PRs abertos por mais de um ano; sem eles, fica em 32 contra 35 h. É um exemplo direto de por que a média engana neste cenário.

### 15. Qual teste vocês recomendam, em que situação mudariam a recomendação, e qual é a principal limitação do estudo?

**Mostrar:** seção 7, itens "Recomendação", "Quando a escolha mudaria" e "E nos dados reais".

**Resposta:** Recomendamos o Mann-Whitney: ele manteve o erro tipo I entre 4,3% e 5,5% em todas as situações e teve mais poder em todas as violações. Mudaríamos para o Welch em dois casos: dados simétricos, sem PRs extremos, como no controle normal da simulação, ou uma pergunta sobre a média em horas, como o tempo total de espera, que o Mann-Whitney não testa. A principal limitação é o desenho antes × depois: outras coisas mudaram entre os períodos, então nenhuma diferença pode ser atribuída só ao bot. E a amostra é pequena: com o efeito real, o Mann-Whitney teria só 13% de chance de percebê-lo.

**Se perguntarem mais:** o dado de 13% está na seção 5, item "E nos dados reais", e na linha pontilhada do G4. Para chegar a 80% de poder com esse efeito, nem 200 PRs por grupo bastariam (o simulador mostra isso).

---

## Se o professor perguntar sobre tamanho da amostra (seção 6 do enunciado)

| Pergunta | Resposta curta | Onde mostrar |
|---|---|---|
| Qual o poder com a amostra coletada, para o efeito observado? | 13% no Mann-Whitney e 2% no Welch | Seção 5, "E nos dados reais"; linha pontilhada do G4 |
| Quantos PRs para 80% de poder? É viável? | Com o efeito real, nem 200 por grupo bastam (o Mann-Whitney chega a ~51%); com efeito 0,5, ~51 PRs por grupo no Mann-Whitney | Simulador, cartões de cada teste |
| Não significativo quer dizer que não há efeito? | Não: com 13% de poder, a amostra não conseguiria enxergá-lo | Seção 6, "O que isso indica" |
| Com amostras enormes, o que importa mais? | O tamanho do efeito: com 845 PRs o Mann-Whitney já dá significativo, mas a diferença é de minutos | Seção 6, "Importância prática" |
| O n muda qual teste é melhor? | Com dados assimétricos, não: o Mann-Whitney fica à frente em todos os n do simulador | Simulador, gráfico "Poder × n" |
