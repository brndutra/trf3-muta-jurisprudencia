#!/usr/bin/env python3
"""Extrai modelos (arquétipos) de decisões monocráticas e acórdãos do acervo.

Método
1. Divide cada inteiro teor em parágrafos e normaliza os elementos variáveis
   (número de processo, IDs, datas, valores, números).
2. Em cada fase do gabinete (3ª Turma 2020-23, 1ª Turma 2023-24, Turma Regional
   de MS 2026), marca como "bloco padronizado" o parágrafo normalizado que se
   repete em pelo menos MIN_BLOCO decisões.
3. Agrupa as decisões pela semelhança (Jaccard) do conjunto de blocos que usam,
   separadas por tipo e espécie recursal.
4. Em cada grupo com pelo menos MIN_GRUPO decisões, escolhe a decisão mais típica
   (medoide, preferindo a mais recente) e monta o modelo: blocos recorrentes no
   grupo ficam no texto literal; trechos próprios do caso viram [campos].

Nada é inventado: todo texto fixo do modelo é transcrito de decisão real do acervo,
cujo id fica registrado em `fonte_modelo`.
Uso: python3 scripts/modelos.py   (gera modelos/modelos.json e modelos/MODELOS.md)
"""
import collections, glob, gzip, json, math, os, re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIN_BLOCO, MIN_GRUPO, LIMIAR, UNIVERSAL = 5, 5, 0.34, 0.12
FASES = {'TRMS': 'Turma Regional de Mato Grosso do Sul (2026)', '1T': '1ª Turma (2023–2024)', '3T': '3ª Turma (2020–2023)'}


def carregar(tipo):
    R = []
    for f in sorted(glob.glob(os.path.join(RAIZ, 'dados', tipo, '*.json.gz'))):
        R += json.load(gzip.open(f))['registros']
    return R


def fase(r):
    o = r.get('orgao_julgador') or ''
    y = (r.get('data_julgamento_iso') or r.get('data_decisao_iso') or '0000')[:4]
    if 'Mato Grosso do Sul' in o or y >= '2025':
        return 'TRMS'
    if o.startswith('1ª Turma') or y == '2024':
        return '1T'
    if '2020' <= y <= '2023':
        return '3T'
    return None


VAR = [
    (re.compile(r'\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b'), '[nº do processo]', '‹PROC›'),
    (re.compile(r'\bIDs?\s*\d{6,}(?:\s*(?:,|e)\s*\d{6,})*(?:,?\s*(?:fls?|f)\.\s*[\d/\-e ]+\d)?', re.I), 'ID [nº]', '‹ID›'),
    (re.compile(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b'), '[data]', '‹DATA›'),
    (re.compile(r'R\$\s*[\d.,]+'), 'R$ [valor]', '‹VALOR›'),
]
NUM = re.compile(r'\b\d+(?:[.,]\d+)*\b')


def norm(p):
    s = ' '.join(p.split())
    for rx, _, tok in VAR:
        s = rx.sub(tok, s)
    return NUM.sub('‹N›', s)


def campos(p):
    """Texto literal, com os elementos variáveis do caso trocados por [campos]."""
    s = ' '.join(p.split())
    for rx, rep, _ in VAR:
        s = rx.sub(rep, s)
    return s


CAB = re.compile(r'^(PODER JUDICI|Tribunal Regional Federal|Turma Regional de|Rua |Avenida |https?://|\d+ª Turma$|'
                 r'[A-ZÇÃÕÁÉÍÓÚÂÊÔ /()\-]{3,}\s*\(\d+\)\s*N[ºo°]|RELATOR|OUTROS PARTICIPANTES)', re.I)
PARTE = re.compile(r'^[A-ZÇÃÕÁÉÍÓÚÂÊÔ][A-Za-zçãõáéíóúâêôÇÃÕÁÉÍÓÚÂÊÔ ()./\-]{2,60}:\s')
SECAO = re.compile(r'^(R\s?E\s?L\s?A\s?T\s?[ÓO]\s?R\s?I\s?O|V\s?O\s?T\s?O|E\s?M\s?E\s?N\s?T\s?A|A\s?C\s?[ÓO]\s?R\s?D\s?[ÃA]\s?O|'
                   r'D\s?E\s?C\s?I\s?S\s?[ÃA]\s?O|DECIDO\.?|É o relatório\.?)\s*$', re.I)


def estrutura(txt):
    """Separa cabeçalho (descartado) do corpo; devolve lista de (tipo, texto)."""
    linhas = [l.strip() for l in (txt or '').split('\n') if l.strip()]
    corpo, iniciou = [], False
    for l in linhas:
        if not iniciou:
            if SECAO.match(l) or l.startswith(('Vistos', 'Trata-se', 'Cuida-se')):
                iniciou = True
            else:
                continue
        if SECAO.match(l):
            corpo.append(('secao', l))
        elif re.match(r'^(CARLOS MUTA|Desembargador Federal|Relator|Juiz|Juíza)\b', l) or re.match(r'^(São Paulo|Campo Grande),', l):
            corpo.append(('assinatura', l))
        else:
            corpo.append(('par', l))
    return corpo


def especie(r):
    c = (r.get('classe_sigla') or '').upper()
    t = (r.get('inteiro_teor') or '')[:6000]
    if re.search(r'embargos\s*de\s*declara', t[:4000], re.I) and re.search(r'Trata-se de embargos\s*de\s*declara', t, re.I):
        return 'ED'
    if c in ('AI',):
        return 'AI'
    if c in ('REMNECCIV', 'REENEC', 'RENEC'):
        return 'RemNec'
    if c in ('APCIV', 'AP', 'APELREMNEC', 'APREENEC'):
        return 'Apelação'
    if c in ('CCCIV',):
        return 'CC'
    return c or 'outros'


ROT_ESP = {'ED': 'Embargos de declaração', 'AI': 'Agravo de instrumento', 'RemNec': 'Remessa necessária',
           'Apelação': 'Apelação', 'CC': 'Conflito de competência', 'SUSPAPEL': 'Pedido de efeito suspensivo à apelação',
           'AR': 'Ação rescisória', 'MSCIV': 'Mandado de segurança', 'AGEXFIS': 'Agravo em execução fiscal'}


def resultado(r, tipo):
    s = ((r.get('resultado_colegiado') if tipo == 'acordaos' else r.get('dispositivo')) or '').lower()
    for k, v in [('não conhe', 'não conhecimento'), ('prejudicad', 'prejudicado'), ('homolog', 'homologação'),
                 ('parcial provimento', 'parcial provimento'), ('acolh', 'acolhimento'), ('rejeit', 'rejeição'),
                 ('negou provimento', 'desprovimento'), ('negar provimento', 'desprovimento'), ('nego provimento', 'desprovimento'),
                 ('deu provimento', 'provimento'), ('dar provimento', 'provimento'), ('dou provimento', 'provimento'),
                 ('extin', 'extinção'), ('incompet', 'declínio de competência'), ('indefer', 'indeferimento'),
                 ('defiro', 'deferimento'), ('defer', 'deferimento')]:
        if k in s:
            return v
    return 'outro'


STOP = set('''de da do das dos e em a o as os para por com sem no na nos nas ao aos à às que se um uma ou não art lei
cpc cf nº n recurso recursal apelação agravo instrumento embargos declaração remessa necessária provimento desprovida
desprovido provida provido negado direito processual civil administrativo tributário previdenciário caso exame questão
discussão razões decidir dispositivo tese acórdão sentença parcial'''.split())


RE_TIT_EMENTA = re.compile(r'^\s*E\s?M\s?E\s?N\s?T\s?A\s*$', re.I | re.M)


def sem_cabecalho(e):
    m = RE_TIT_EMENTA.search(e or '')
    return (e[m.end():] if m else (e or '')).strip()


def tema(ementas, fundo):
    c = collections.Counter()
    for e in map(sem_cabecalho, ementas):
        cab = re.split(r'\n|\bI\.\s*Caso em exame|\b1\.\s', e or '', maxsplit=1)[0]
        for t in re.split(r'[.;]\s*', cab.upper()):
            t = t.strip(' ."')
            if 3 < len(t) < 70 and t.lower() not in STOP and not re.match(r'^(DIREITO|PROCESSUAL|APELA|AGRAVO|EMBARGOS|REMESSA|RECURSO)', t):
                c[t] += 1
    if not c:
        return None
    pont = sorted(c.items(), key=lambda kv: -kv[1] * (1.0 / (1 + fundo.get(kv[0], 0) / max(1, len(ementas)))))
    return ' · '.join(k.capitalize() for k, _ in pont[:3])


PAL = re.compile(r"[A-Za-zÀ-ÿ]{5,}")
STOP2 = set('''artigo artigos sobre quando conforme assim ainda porque também entre desde mesmo outro outros outra
sendo forma termos tendo pelos pelas pela pelo deste desta neste nesta presente decisão recurso recursos relator
monocrática código processo civil seguinte seguintes inciso incisos parte partes autos sentença julgado julgados
jurisprudência superior tribunal corte federal turma regional região apelação agravo instrumento remessa
necessária embargos declaração provimento conhecer exposto fundamento acórdão sentido razão razões questão
matéria pedido caso legal legislação aplicação hipótese análise tratando tratar trata-se'''.split())


def palavras(t):
    return [w.lower() for w in PAL.findall(t) if w.lower() not in STOP2]


def chaves(nucleo, idf, n=4):
    tf = collections.Counter()
    for b in nucleo:
        tf.update(set(palavras(b)))
    pont = sorted(tf, key=lambda w: -tf[w] * idf.get(w, 0))
    return pont[:n]


def jacc(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def agrupar(docs):
    """docs: lista de (id, frozenset blocos). Agrupamento guloso por Jaccard ao representante."""
    grupos = []
    for did, s in sorted(docs, key=lambda d: -len(d[1])):
        melhor, mj = None, 0
        for g in grupos:
            j = jacc(s, g['rep'])
            if j > mj:
                melhor, mj = g, j
        if melhor and mj >= LIMIAR:
            melhor['ids'].append(did); melhor['cont'].update(s)
        else:
            grupos.append({'rep': s, 'ids': [did], 'cont': collections.Counter(s)})
    for g in grupos:  # representante passa a ser o núcleo (blocos em ≥ 50% do grupo)
        n = len(g['ids'])
        g['nucleo'] = frozenset(b for b, c in g['cont'].items() if c >= max(2, n * 0.5))
    return grupos


RE_FIM_REL = re.compile(r'^(É o relatório\.?|DECIDO\.?|V\s?O\s?T\s?O)\s*$', re.I)
RE_DISP = re.compile(r'^(Ante o exposto|Em face do exposto|Diante do exposto|Pelo exposto|Por estes fundamentos)', re.I)


def matriz(membros, pars, blocos, literal, nucleo):
    """Blocos do grupo para o modo matriz: fixos (>= 50% das decisões) e opcionais (>= 15%),
    na ordem média em que aparecem e com a seção (relatório, fundamentação, dispositivo)."""
    n = len(membros)
    cont, pos, sec = collections.Counter(), collections.defaultdict(list), collections.defaultdict(collections.Counter)
    for r in membros:
        ps = [(tp, l) for tp, l in estrutura(r['inteiro_teor']) if tp in ('par', 'secao')]
        tot = max(1, len(ps))
        estado, vistos = 'relatorio', set()
        for i, (tp, l) in enumerate(ps):
            if tp == 'secao' or RE_FIM_REL.match(l):
                u = re.sub(r'\s', '', l).upper()
                if u.startswith('EMENTA'):
                    estado = 'ementa'
                elif u.startswith(('ACÓRDÃO', 'ACORDAO')):
                    estado = 'acordao'
                elif u.startswith(('VOTO', 'DECIDO', 'ÉORELATÓRIO', 'EORELATORIO')):
                    estado = 'fundamentacao'
                continue
            b = norm(l)
            if b not in blocos or len(l) < 60 or b in vistos:
                continue
            vistos.add(b)
            cont[b] += 1
            pos[b].append(i / tot)
            st = 'acordao' if l.startswith('Vistos e relatados') else estado
            if st == 'fundamentacao' and RE_DISP.match(l):
                st = 'dispositivo'
            sec[b][st] += 1
    out = []
    for b, c in cont.items():
        if c < max(2, n * 0.15):
            continue
        var = collections.Counter(literal[r['id']][b] for r in membros if b in literal[r['id']])
        lit, k = var.most_common(1)[0]
        texto = lit if k >= max(2, sum(var.values()) * 0.6) else campos(lit)
        out.append({'texto': texto, 'uso': round(c / n, 2), 'fixo': c >= n * 0.5 or b in nucleo,
                    'secao': sec[b].most_common(1)[0][0], 'ordem': round(sum(pos[b]) / len(pos[b]), 3)})
    out.sort(key=lambda x: ({'relatorio': 0, 'fundamentacao': 1, 'dispositivo': 2, 'ementa': 3, 'acordao': 4}[x['secao']], x['ordem']))
    return out[:60]


def montar(r, nucleo_norm, prefixos, literais=None):
    linhas = []
    for tp, l in estrutura(r['inteiro_teor']):
        if tp == 'secao':
            linhas.append(l.upper() if len(l) < 25 else l)
        elif tp == 'assinatura':
            continue
        elif norm(l) in nucleo_norm:
            # texto fixo: se o parágrafo se repete literalmente no grupo (inclusive datas e números de
            # precedentes citados), mantém-se o literal; só o que varia entre decisões vira [campo]
            var = (literais or {}).get(norm(l))
            lit = ' '.join(l.split())
            if var and var.most_common(1)[0][0] == lit and var[lit] >= max(2, sum(var.values()) * 0.6):
                linhas.append(lit)
            else:
                linhas.append(campos(l))
        else:
            n = norm(l)
            pref = next((p for p in prefixos if n.startswith(p)), None)
            if pref:
                k = len(' '.join(l.split()[:len(pref.split())]))
                linhas.append(campos(l[:k]).rstrip(',;:') + ' [complementar conforme o caso].')
            else:
                rot = 'citação de precedente' if re.match(r'^[A-Z][A-Za-z ]{1,25}\s[\d.]+|^(AgInt|AgRg|REsp|RE|AI|ApCiv|EDcl|ARE|MS|RMS)\b', l) else 'trecho próprio do caso'
                if not linhas or linhas[-1] != f'[{rot}]':
                    linhas.append(f'[{rot}]')
    while linhas and linhas[-1].startswith('['):
        linhas.pop()
    if not any(re.match(r'(Ante o exposto|Em face do exposto|Diante do exposto|Pelo exposto)', l) for l in linhas[-3:]):
        linhas.append('[dispositivo]')
    while len(linhas) > 1 and linhas[1].startswith('[') and linhas[0] in ('DECISÃO', 'D E C I S Ã O', 'RELATÓRIO'):
        linhas.pop(1)
    return '\n\n'.join(linhas)


def main():
    saida, fundo = [], collections.Counter()
    for tipo in ('monocraticas', 'acordaos'):
        regs = [r for r in carregar(tipo) if r.get('inteiro_teor') and (tipo == 'monocraticas' or r['conteudo_texto'] == 'integral')]
        for r in regs:
            for t in re.split(r'[.;]\s*', (r.get('ementa') or '')[:400].upper()):
                fundo[t.strip(' ."')] += 1
        for fz in FASES:
            G = [r for r in regs if fase(r) == fz]
            freq = collections.Counter()
            pars = {}
            literal = {}
            for r in G:
                lits = {norm(l): ' '.join(l.split()) for tp, l in estrutura(r['inteiro_teor']) if tp == 'par' and len(l) >= 60}
                ps = set(lits)
                literal[r['id']] = lits
                pars[r['id']] = ps
                freq.update(ps)
            blocos = {p for p, c in freq.items() if c >= MIN_BLOCO}
            universais = {p for p in blocos if freq[p] >= len(G) * UNIVERSAL}
            distintivos = blocos - universais
            por_id = {r['id']: r for r in G}
            df = collections.Counter()
            for b in blocos:
                df.update(set(palavras(b)))
            idf = {w: math.log((1 + len(blocos)) / (1 + c)) for w, c in df.items()}
            por_esp = collections.defaultdict(list)
            for r in G:
                por_esp[especie(r)].append((r['id'], frozenset(pars[r['id']] & distintivos)))
            for esp, docs in por_esp.items():
                docs = [d for d in docs if d[1]]
                for g in agrupar(docs):
                    if len(g['ids']) < MIN_GRUPO or len(g['nucleo']) < 2:
                        continue
                    nucleo_total = g['nucleo'] | {u for u in universais if sum(u in pars[i] for i in g['ids']) >= len(g['ids']) * 0.5}
                    membros = [por_id[i] for i in g['ids']]
                    # medoide: maior Jaccard médio ao núcleo, desempate pela data mais recente
                    def chave(r):
                        s = pars[r['id']] & distintivos
                        return (round(jacc(s, g['nucleo']), 2), r.get('data_julgamento_iso') or r.get('data_decisao_iso') or '')
                    med = max(membros, key=chave)
                    # aberturas recorrentes de trechos próprios ("Trata-se de agravo de instrumento à decisão que")
                    pc = collections.Counter()
                    for r in membros:
                        for p in pars[r['id']] - g['nucleo']:
                            w = p.split()
                            if len(w) >= 8:
                                pc[' '.join(w[:7])] += 1
                    prefixos = [p for p, c in pc.items() if c >= max(3, len(membros) * 0.3)]
                    blocos_mx = matriz(membros, pars, blocos, literal, g['nucleo'] | nucleo_total)
                    res = collections.Counter(resultado(r, tipo) for r in membros).most_common(1)[0][0]
                    datas = sorted(r.get('data_julgamento_iso') or r.get('data_decisao_iso') for r in membros)
                    classes = collections.Counter(r.get('classe_sigla') for r in membros)
                    ementas = [r.get('ementa') for r in membros] if tipo == 'acordaos' else \
                        [next((l for tp, l in estrutura(r['inteiro_teor']) if tp == 'par' and l.startswith(('Trata-se', 'Cuida-se'))), '') for r in membros]
                    saida.append({
                        'tipo': 'acórdão' if tipo == 'acordaos' else 'monocrática', 'fase': fz, 'fase_nome': FASES[fz],
                        'especie': ROT_ESP.get(esp, esp), 'resultado': res,
                        'tema': tema(ementas, fundo) if tipo == 'acordaos' else None,
                        'abertura': campos(ementas[membros.index(med)])[:260] if tipo == 'monocraticas' else None,
                        'frequencia': len(membros), 'periodo': [datas[0], datas[-1]],
                        'classes': dict(classes.most_common()),
                        'blocos_fixos': len(nucleo_total),
                        'fonte_modelo': med['id'], 'processo_modelo': med['numero_processo'],
                        'exemplos': [r['id'] for r in sorted(membros, key=lambda r: r.get('data_julgamento_iso') or r.get('data_decisao_iso') or '', reverse=True)[:12]],
                        'ementa_modelo': campos(sem_cabecalho(med.get('ementa'))) if tipo == 'acordaos' else None,
                        'modelo': montar(med, nucleo_total, prefixos, {b: collections.Counter(literal[i][b] for i in g['ids'] if b in literal[i]) for b in nucleo_total}),
                        'palavras_chave': chaves(g['nucleo'], idf),
                        'blocos': blocos_mx,
                    })
    saida.sort(key=lambda m: ({'TRMS': 0, '1T': 1, '3T': 2}[m['fase']], m['tipo'] != 'monocrática', -m['frequencia']))
    for i, m in enumerate(saida, 1):
        m['id'] = f"MOD-{m['fase']}-{'M' if m['tipo'] == 'monocrática' else 'A'}-{i:03d}"
        m['nome'] = ' · '.join(x for x in [m['especie'], m['resultado'], m['tema'] or ', '.join(m['palavras_chave'])] if x)
    os.makedirs(os.path.join(RAIZ, 'modelos'), exist_ok=True)
    with open(os.path.join(RAIZ, 'modelos', 'modelos.json'), 'w', encoding='utf-8') as f:
        json.dump({'gerado_por': 'scripts/modelos.py', 'parametros': {'min_bloco': MIN_BLOCO, 'min_grupo': MIN_GRUPO, 'jaccard': LIMIAR},
                   'total': len(saida), 'modelos': saida}, f, ensure_ascii=False, indent=1)
    dados = {'gerado_por': 'scripts/modelos.py', 'parametros': {'min_bloco': MIN_BLOCO, 'min_grupo': MIN_GRUPO, 'jaccard': LIMIAR},
             'total': len(saida), 'modelos': saida}
    with open(os.path.join(RAIZ, 'modelos', 'modelos.json.gz'), 'wb') as raw, \
            gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=9, mtime=0) as gz:
        gz.write(json.dumps(dados, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    c = collections.Counter((m['fase'], m['tipo']) for m in saida)
    print(len(saida), dict(c))
    cobre = collections.Counter()
    for m in saida:
        cobre[(m['fase'], m['tipo'])] += m['frequencia']
    print('decisões cobertas', dict(cobre))


if __name__ == '__main__':
    main()
