# Acervo jurisprudencial — Des. Fed. Carlos Muta (TRF3)

Decisões monocráticas e acórdãos em que o Desembargador Federal **Luís Carlos Hiroki Muta** figura como relator (ou relator para o acórdão), extraídos da **base pública de jurisprudência do TRF3** e organizados para consulta, pesquisa e verificação de integridade.

**Central Paradigmas · Acervo · Minutas:** **https://brndutra.github.io/trf3-muta-jurisprudencia/central/**
- **I · Paradigmas**: pesquisa, leitura, citação e verificação das 33.207 decisões do gabinete.
- **II · Acervo**: importa os relatórios do PJe/BI (só no navegador, nada é enviado) e cruza cada processo com o banco: paradigmas próprios (decisões do gabinete no próprio processo), paradigmas similares e modelos sugeridos.
- **III · Minutas**: 752 modelos extraídos do acervo (`modelos/`), em modo **Texto-modelo** (a decisão-base da matéria, com campos) ou **Matriz** (modelo-matriz do *tipo de julgamento* — espécie × resultado —, com fórmulas fixas, versões alternativas escolhidas conforme a situação do caso e trechos opcionais; o conteúdo da matéria entra na fundamentação a partir dos blocos do modelo aberto); relatório estruturado (Forma A/B e espécies próprias); **editor** da minuta; **painel de diretrizes** com indicadores de correção. O painel usa o *Padrão Muta* (regras de redação, normas, diretrizes e roteiros do gabinete), que **não é publicado** neste repositório: é carregado pelo usuário a partir do arquivo `padrao_muta.json` e fica guardado apenas no navegador.

**Painel de consulta (somente jurisprudência):** https://brndutra.github.io/trf3-muta-jurisprudencia/consulta/

O código do painel está em [`consulta/index.html`](consulta/index.html). Também pode ser aberto direto do arquivo, lendo os dados deste repositório, ou com uma cópia local (⚙ › *Abrir pasta local*). Links diretos para uma decisão: `…/consulta/#id=A00001`.

## Conteúdo

| Conjunto | Registros | Período | Texto |
|---|---:|---|---|
| Decisões monocráticas | 7.157 | 05/2016 – 10/2026 | inteiro teor em todas |
| Acórdãos — integral | 12.694 | 2016 – 2026 | relatório, voto e acórdão |
| Acórdãos — ementa + acórdão | 11.751 | 1999 – 2017 | ementa e parágrafo do acórdão (a base não oferece relatório/voto) |
| Acórdãos — só ementa | 1.605 | 1999 – 2011 | apenas ementa |
| **Total** | **33.207** | | |

Faltam **162 acórdãos** da base (os mais antigos, c. 1999–2001, em regra só com ementa): o servidor do TRF3 recusou as últimas requisições da coleta. A lacuna está registrada no `MANIFESTO.json`.

Critérios de busca na base: Monocráticas, `relator: CARLOS MUTA`; Acórdãos, `relator | relator para o acórdão: CARLOS MUTA`. Coleta em 30/10/2026.

## Estrutura

```
consulta/index.html          painel de consulta (HTML único, sem dependências)
dados/indice.json.gz         índice compacto (metadados, prévia, resultado) — 33.207 linhas
dados/acordaos/AAAA.json.gz      acórdãos por ano de julgamento
dados/monocraticas/AAAA.json.gz  monocráticas por ano da decisão
MANIFESTO.json               hashes SHA-256 de cada arquivo e de cada registro + contagens
SHA256SUMS                   hashes dos arquivos (formato `sha256sum -c`)
scripts/organizar.py         gera dados/, MANIFESTO e SHA256SUMS a partir dos JSON exportados
scripts/modelos.py           extrai os modelos (arquétipos) de monocráticas e acórdãos → modelos/
central/index.html           central tripartite: Paradigmas · Acervo · Minutas
modelos/sugestoes.json(.gz)  752 sugestões de modelo por fase do gabinete (extração automática), com texto-base rastreável
scripts/matrizes.py          extrai a estrutura por tipo de julgamento → modelos/tipos-julgamento*.json
modelos/tipos-julgamento.json(.gz)  20 tipos de julgamento (fase TRMS): posições, parágrafos-fórmula, versões e situação
modelos/tipos-julgamento_gabA.json  os mesmos, no formato “Modelo-matriz” do gerador (esqueletoModelo/paragrafosModelo)
modelos/trechos.json         trechos vinculados por matéria (voto ↔ relatório ↔ ementa), curadoria do gabinete
modelos/indice.json          lista dos modelos-matriz que a Central carrega (matriz e rascunhos)
modelos/matriz/<id>.json     um arquivo por modelo-matriz verificado
modelos/rascunhos/<id>.json  um arquivo por rascunho de modelo-matriz (em elaboração)
modelos/modelos-matriz.json  reserva: os modelos-matriz num arquivo só, lido apenas se faltar o índice
```

Os arquivos são JSON compactados com gzip (`zcat dados/acordaos/2021.json.gz | jq '.registros[0]'`).

## Campos

**Comuns:** `id` (`A…` acórdão, `M…` monocrática), `seq` (posição na lista da base), `numero_processo`, `classe_sigla`, `classe`, `relator`, `orgao_julgador`, `publicacao_veiculo`, `data_publicacao`, `inteiro_teor`, `link_pje`, `link_impressao`, `sha256_inteiro_teor`, `conteudo_texto`.

**Acórdãos:** `data_julgamento(_iso)`, `ementa`, `sha256_ementa`, `numero_classe_legado`, `publicacao_complemento`, `relator_no_documento`, `partes`, `resultado_colegiado`, `atuacao_muta`, `possui_inteiro_teor`, `link_pdf`, `link_integra_externa`.

**Monocráticas:** `data_decisao(_iso)`, `dispositivo`, `orgao_julgador_fonte`, `caracteres`.

### Fonte × derivado

- **Reproduzido da base, sem alteração de conteúdo** (apenas espaços e quebras de linha repetidos normalizados): inteiro teor, ementa, número, classe, relator, órgão julgador dos acórdãos, datas, veículo de publicação e links.
- **Extraído automaticamente** (útil para filtrar, nunca para citar): `dispositivo`, `resultado_colegiado`, `partes`, `atuacao_muta`, `conteudo_texto`, `orgao_julgador` das monocráticas (só quando consta do cabeçalho do documento) e os campos de prévia do índice.

## Autenticidade e verificação

A base de jurisprudência é um serviço de consulta, **não a publicação oficial**. O texto autêntico é o documento assinado no PJe e a publicação no DJEN/e-DJF3/DJU. A base já não traz formatação (negritos, tabelas) nem assinatura, e eventuais falhas dela estão reproduzidas aqui.

O que este repositório garante é **integridade e rastreabilidade desde a extração**:

1. `MANIFESTO.json` traz o SHA-256 do inteiro teor e da ementa de cada registro e de cada arquivo, além dos hashes dos arquivos exportados originalmente.
2. `sha256sum -c SHA256SUMS` confere todos os arquivos de `dados/`.
3. No painel, **Verificar autenticidade** recalcula no navegador o hash do texto exibido e o compara com o manifesto.
4. Cada registro mantém os links para o PJe, para a versão de impressão do TRF3 e, nos acórdãos antigos, para a íntegra no site anterior.
5. O histórico do Git registra qualquer alteração posterior.

## Reprocessar

```bash
python3 scripts/organizar.py muta_monocraticas_TRF3.json muta_acordaos_TRF3_*.json
sha256sum -c SHA256SUMS
```

O `.gz` é gerado com `mtime=0`; portanto a mesma entrada produz os mesmos bytes.

## Modelos

`scripts/modelos.py` identifica, em cada fase do gabinete (3ª Turma 2020–23, 1ª Turma 2023–24, Turma Regional de MS 2026), os parágrafos repetidos literalmente em várias decisões e agrupa as decisões que compartilham o mesmo conjunto desses blocos. Para cada grupo com 5 ou mais decisões, o modelo reproduz a decisão mais típica (`fonte_modelo`), mantendo o texto fixo — inclusive precedentes citados com suas datas — e trocando por `[campos]` apenas o que varia entre os casos (`[trecho próprio do caso]`, `ID [nº]`, `[dispositivo]` etc.). Nenhum trecho é redigido pelo algoritmo.

## Modelos-matriz por tipo de julgamento

`scripts/matrizes.py` agrupa as decisões da Turma Regional de MS (2026) por **tipo de julgamento** — pronunciamento (voto/monocrática) × espécie × resultado — e, em cada tipo com 12 ou mais decisões, distribui os parágrafos pelas posições do voto (admissibilidade, preliminares, controvérsia, fundamentação, fatos, provas, aplicação, conclusão, efeitos, honorários, complemento, dispositivo, fecho). Um parágrafo entra na matriz quando é **fórmula do tipo**, e não da matéria: aparece em ao menos 10% das decisões do tipo e em 3 ou mais matérias; transcrições de lei e exposições temáticas ficam para o modelo da matéria.

- **Fixo**: presente em metade ou mais das decisões do tipo. **Opcional**: entre 10% e 50%, pode ser omitido.
- **Versões**: redações alternativas do mesmo ponto (variações só de grafia são fundidas). Cada versão traz a **situação** que a distingue — recorrente (autor, autora, ré/INSS, União), gratuidade, Súmula 111, correção de ofício, retorno à origem — e a Central sugere a versão conforme o relatório preenchido.
- **Fórmula + complemento**: quando a cauda do parágrafo varia caso a caso, guarda-se o trecho fixo seguido de `{{complemento conforme o caso}}`.
- Nada é redigido pelo algoritmo: todo texto é transcrição de decisões do gabinete, com o percentual de uso no tipo.

## Trechos vinculados (voto ↔ relatório ↔ ementa)

`modelos/trechos.json` reúne, por matéria, os trechos que o gabinete acrescenta ao voto conforme o caso. Cada trecho declara o texto do **voto** e o que ele exige no **relatório** e na **ementa**; na Central (Minutas › Matriz › *Trechos vinculados*), marcar o trecho insere as três partes de uma vez, nas posições indicadas.

- **Voto** (`pos`): `contro`, `jurid`, `provas`, `aplic`, `concl`, `honor`, `disp` — em `honor` e `disp` o trecho substitui as fórmulas da matriz.
- **Relatório** (`pos`): `apos_recurso` (parágrafo após as razões), `contrarrazoes` (complemento da frase das contrarrazões), `antes_mpf`.
- **Ementa** (`pos`): `cabecalho` (termos), `caso`, `questao` (oração no infinitivo; com duas ou mais, “Há … questões em discussão: (i) …; e (ii) …”), `razoes`, `dispositivo` (substitui o da matriz).
- **Opções da matéria**: `[?id:texto]` entra só com a opção (ou o trecho) `id` marcada; `[?!id:texto]`, só com ela desmarcada. Uma mesma opção acende o texto correspondente nas três seções (ex.: *habilitação de herdeiros* no voto, nas contrarrazões e na questão em discussão). Opções com `situacao` seguem o relatório (ex.: gratuidade).
- `{{campo}}` = dado dos autos a preencher; aparece como `[campo]` na minuta.
- O caso em exame da ementa passa a ser montado a partir do relatório (espécie, contexto e resultado da decisão recorrida).
- Diferentemente dos modelos e matrizes, este arquivo não é extraído por algoritmo: é texto curado do gabinete. Primeira matéria: 28,86% (cumprimento da ACP 0005019-15.1997.4.03.6000).

## Visualizações dos precedentes

Na aba Precedentes, abaixo do total de resultados, a mesma página troca de forma sem perder os filtros à esquerda nem a busca: **Lista**, **Infográfico** (totais, ramos, resultados, anos, classes e órgãos), **Mapa mental**, **Tópicos** (abre já com os ramos e as subáreas), **Mosaico** (área proporcional ao número de decisões), **Matriz** (ramo × resultado), **Linha do tempo** e **Fluxo** (ramo → acórdão/monocrática → resultado). Clicar num ramo, subárea, célula ou resultado recorta a página; o recorte aparece ao lado dos botões e se desfaz no ✕. Ramo, assunto e subassunto vêm do índice temático (que os chama de área, subárea e tema); sem ele, o ramo vem do cabeçalho da ementa. O resultado é extraído automaticamente do índice e deve ser conferido no documento oficial.

## Modelos-matriz verificados × modelos sugeridos

A aba Minutas (Modelos) separa três listas: **✓ Matriz** (modelos-matriz verificados), **✎ Rascunhos** (modelos-matriz em elaboração — criados do zero ou convertidos de sugestões; o estado é o mesmo nos dois casos) e **Sugestões** (extração automática). Um rascunho passa a Matriz quando é marcado como verificado.

- **✓ Modelos-matriz** (`modelos/matriz/`, verificados; rascunhos em `modelos/rascunhos/`): modelos-matriz conferidos pelo gabinete. O tipo de julgamento e a matéria são fixados pelo próprio modelo; não há busca por similaridade. Cada **bloco** reúne o texto do voto e o que ele exige no relatório, na ementa e no acórdão, e é *fixo*, *opcional* ou *alternativo* (um por grupo). No preenchimento, o relatório é montado pelo formulário e os blocos/opções são marcados — as opções que seguem o relatório (ex.: gratuidade) são acesas automaticamente.
- **Sugeridos** (`modelos/sugestoes.json.gz`): extração automática pela recorrência dos trechos nas decisões, como antes. Num modelo sugerido, **⇢ Converter em modelo-matriz** gera um rascunho na lista Rascunhos (parágrafos do voto agrupados por posição, ementa distribuída por seção, acórdão), para o curador organizar em blocos.

**Edição.** Em um modelo-matriz, **✎ Editar modelo** abre o editor em forma de **esqueleto da minuta** — relatório (pontos que o formulário não cobre), voto (11 posições), ementa (cabeçalho, caso em exame, questão, razões, dispositivo, dispositivos e jurisprudência citados) e acórdão. Cada texto fica no lugar em que entra; “+ texto aqui…” cria o texto naquele ponto, em bloco novo ou vinculado a um bloco existente. Os textos do mesmo bloco têm a mesma cor e são destacados juntos. **⇄ alternativa** cria outra redação para o mesmo bloco (cópia de todos os seus textos, para reescrever em paralelo); as alternativas aparecem lado a lado em cada ponto e, no preenchimento, entra uma. As alterações ficam no navegador até **⤓ Exportar modelos (.zip)**: o arquivo traz a pasta `modelos/` com `indice.json`, `matriz/` e `rascunhos/` (um arquivo por modelo). Descompacte e arraste a pasta `modelos/` para a raiz do repositório (Add file › Upload files). A Central só carrega o que o índice lista; quando um rascunho é verificado, o arquivo passa de `rascunhos/` para `matriz/` — apague a cópia antiga. Sintaxe dos textos: `{{campo}}` = dado dos autos; `[?id:texto]` entra com a opção ou o bloco `id` marcado; `[?!id:texto]`, com ele desmarcado.

**Prévia formatada.** O editor da minuta tem a vista *Prévia* (títulos, ementa no padrão CNJ, citações recuadas, campos grifados): clique num campo para preenchê-lo; duplo clique num parágrafo leva ao ponto correspondente na vista *Texto*.

**Lote 28,86% (A1–A7).** Os sete modelos do lote 28,86% (ACP 0005019-15.1997.4.03.6000) estão em `modelos/rascunhos/` (`mm-2886-a1…a7`), montados a partir do inteiro teor dos acórdãos-paradigma da sessão de 05/10/2026: texto transcrito, dados do caso trocados por `{{campos}}`, condicionais `[?id:…]` para prescrição, herdeiros, recurso adesivo, gratuidade e honorários. Pontos a conferir estão na `nota` do modelo ou do bloco (marcados [VALIDAR]). Passam a Matriz depois de conferidos pelo gabinete.

No modo Matriz dos sugeridos, o tipo de julgamento também passa a ser fixado pelo modelo (sem aproximação por outra espécie ou resultado), e as versões são marcadas a partir do relatório preenchido.
