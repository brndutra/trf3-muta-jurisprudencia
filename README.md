# Acervo jurisprudencial — Des. Fed. Carlos Muta (TRF3)

Decisões monocráticas e acórdãos em que o Desembargador Federal **Luís Carlos Hiroki Muta** figura como relator (ou relator para o acórdão), extraídos da **base pública de jurisprudência do TRF3** e organizados para consulta, pesquisa e verificação de integridade.

**Central Paradigmas · Acervo · Minutas:** **https://brndutra.github.io/trf3-muta-jurisprudencia/central/**
- **I · Paradigmas**: pesquisa, leitura, citação e verificação das 33.207 decisões do gabinete.
- **II · Acervo**: importa os relatórios do PJe/BI (só no navegador, nada é enviado) e cruza cada processo com o banco: paradigmas próprios (decisões do gabinete no próprio processo), paradigmas similares e modelos sugeridos.
- **III · Minutas**: 752 modelos extraídos do acervo (`modelos/`), em modo **Padrão** (modelo com campos) ou **Matriz** (blocos fixos e opcionais do grupo, com o percentual de uso); relatório estruturado (Forma A/B e espécies próprias); **editor** da minuta; **painel de diretrizes** com indicadores de correção. O painel usa o *Padrão Muta* (regras de redação, normas, diretrizes e roteiros do gabinete), que **não é publicado** neste repositório: é carregado pelo usuário a partir do arquivo `padrao_muta.json` e fica guardado apenas no navegador.

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
modelos/modelos.json(.gz)    752 modelos por fase do gabinete, com texto-base rastreável e blocos da matriz
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
