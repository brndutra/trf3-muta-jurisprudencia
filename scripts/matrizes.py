#!/usr/bin/env python3
"""Modelos-matriz por tipo de julgamento (espécie × resultado × pronunciamento).

Para cada tipo da fase atual (Turma Regional de MS), separa o voto (ou a decisão
monocrática) nas posições do gerador do gabinete e identifica os parágrafos
ESTRUTURAIS — os que o gabinete repete no tipo em várias matérias diferentes.
Variações de um mesmo parágrafo viram VERSÕES alternativas (com a situação que as
distingue); parágrafos presentes em parte das decisões viram OPCIONAIS. O que é
próprio da matéria ou do caso vira {{campo}}.

Saídas:
  modelos/matrizes.json(.gz)      — para a Central (faceta III, modo Matriz)
  modelos/matrizes_gabA.json      — registros no formato Modelo-matriz do gerador
Uso: python3 scripts/matrizes.py
"""
import collections, gzip, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelos as MD

RAIZ = MD.RAIZ
FASE = 'TRMS'
MIN_TIPO, MIN_SLOT, MIN_MAT = 12, 0.10, 3

POS_VOTO = [('admiss', '01 · Admissibilidade recursal'), ('prelim', '02 · Preliminares'), ('trans', '03 · Transição após preliminares'),
            ('contro', '04 · Delimitação da controvérsia'), ('jurid', '05 · Fundamentação jurídica'), ('fatos', '06 · Introdução fática'),
            ('provas', '07 · Exame fático-probatório'), ('aplic', '08 · Aplicação ao caso'), ('concl', '09 · Conclusão'),
            ('consec', '10 · Efeitos financeiros e providências'), ('honor', '11 · Custas e honorários'),
            ('complem', '12 · Questões complementares'), ('disp', '13 · Dispositivo'), ('fecho', '14 · Fecho do voto')]
POS_MONO = [('rel', 'Relatório'), ('prelim', 'Preliminares'), ('fund', 'Fundamentação'), ('honor', 'Honorários'), ('disp', 'Dispositivo'), ('fecho', 'Fecho')]
CAMPO = {'jurid': '{{moldura jurídica da matéria — normas e teses aplicáveis (use o modelo da matéria)}}',
         'fatos': '{{Na espécie, … — fatos relevantes com a fonte (ID)}}',
         'provas': '{{exame das provas: documentos, laudo, prova oral — com ID}}',
         'aplic': '{{aplicação ao caso: subsunção dos fatos à moldura jurídica}}',
         'contro': '{{delimitação da controvérsia devolvida}}',
         'concl': '{{conclusão da questão}}',
         'fund': '{{fundamentação: enquadramento, matéria e caso concreto}}',
         'rel': '{{relatório: decisão recorrida (ID), razões, contrarrazões}}'}

RX_POS = [
    ('fecho', re.compile(r'^(É como voto|Publique-se|Intime-se|Oportunamente|Após,? baixem|Observadas as formalidades)', re.I)),
    ('disp', re.compile(r'^(Ante o exposto|Pelo exposto|Em face do exposto|Diante do exposto|Isto posto|Por estes fundamentos)', re.I)),
    ('honor', re.compile(r'sucumb[êe]ncia recursal|honor[áa]rios (advocat[íi]cios )?recursais|artigo 85, § ?11|condena[çc][ãa]o adicional', re.I)),
    ('consec', re.compile(r'^(Quanto aos consect[áa]rios|Os consect[áa]rios|A corre[çc][ãa]o monet[áa]ria|Os juros de mora|Correção monetária e juros)', re.I)),
    ('trans', re.compile(r'^(No m[ée]rito,|Superada[s]? a[s]? preliminar|Passa-se (ao|à an[áa]lise do) m[ée]rito|Quanto ao m[ée]rito)', re.I)),
    ('admiss', re.compile(r'pressupostos de admissibilidade|^Conhe[çc]o|n[ãa]o conhe[çc]o|deser[çc][ãa]o|tempestiv|efeito suspensivo|preparo|artigo 932|Segundo a Corte Superior|julgamento sob tais par[âa]metros', re.I)),
    ('prelim', re.compile(r'^(Preliminarmente|Inicialmente, (quanto|no tocante) [àa] preliminar|Rejeita-se a preliminar|A preliminar)|cerceamento de defesa|nulidade da senten[çc]a', re.I)),
    ('fatos', re.compile(r'^(Na esp[ée]cie|No caso|No caso concreto|In casu|Na hip[óo]tese)', re.I)),
    ('concl', re.compile(r'^(Em suma|Assim,|Logo,|Portanto,|Desse modo|Dessa forma|Como se observa|Nada colhe|Assim, nada)', re.I)),
    ('contro', re.compile(r'^Senhores Desembargadores,|controv[ée]rsia|discute-se|cinge-se|a quest[ãa]o (em discuss[ãa]o|devolvida)', re.I)),
    ('provas', re.compile(r'\blaudo\b|per[íi]cia|prova testemunhal|testemunh|\(IDs? ?[\d\[]', re.I)),
]
MAP_MONO = {'admiss': 'fund', 'prelim': 'prelim', 'trans': 'fund', 'contro': 'fund', 'jurid': 'fund', 'fatos': 'fund', 'provas': 'fund',
            'aplic': 'fund', 'concl': 'fund', 'consec': 'fund', 'honor': 'honor', 'complem': 'fund', 'disp': 'disp', 'fecho': 'fecho'}
IDRX = [(re.compile(r'\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b'), '{{nº do processo}}'),
        (re.compile(r'\bIDs?\s*\d{6,}(?:\s*(?:,|e)\s*\d{6,})*(?:,?\s*(?:fls?|f)\.\s*[\d/\-e ]+\d)?', re.I), 'ID {{nº}}')]


def lit_campos(s):
    for rx, rep in IDRX:
        s = rx.sub(rep, s)
    return s


def classif(l, i, n):
    for k, rx in RX_POS:
        if rx.search(l):
            return k
    return 'jurid' if i < n * 0.6 else 'aplic'


def voto(r, tipo):
    """parágrafos do voto (acórdão) ou da decisão (monocrática), sem relatório, ementa e acórdão"""
    linhas = MD.estrutura(r['inteiro_teor'])
    out, dentro = [], tipo == 'monocrática'
    for tp, l in linhas:
        u = re.sub(r'\s', '', l).upper()
        if tp == 'secao':
            if u.startswith(('VOTO', 'DECIDO')):
                dentro = True
            elif u.startswith(('EMENTA', 'ACÓRDÃO', 'ACORDAO')):
                dentro = False
            elif u.startswith(('ÉORELATÓRIO', 'EORELATORIO')) and tipo == 'monocrática':
                out = []  # monocrática: descarta o relatório
            continue
        if re.match(r'^(É o relatório|DECIDO)\.?$', l, re.I):
            out = [] if tipo == 'monocrática' else out
            dentro = True
            continue
        if re.match(r'^O Desembargador Federal .*\(Relator\):?$', l):
            dentro = True
            continue
        if dentro and len(l) >= 25:
            out.append(l)
    return out


def blocos_secao(r, nome):
    """linhas da ementa (itens numerados) ou do acórdão"""
    t = r['inteiro_teor'] or ''
    if nome == 'ementa':
        e = MD.sem_cabecalho(r.get('ementa') or '')
        return [l.strip() for l in e.split('\n') if len(l.strip()) >= 20]
    m = re.search(r'\n\s*A\s?C\s?[ÓO]\s?R\s?D\s?[ÃA]\s?O\s*\n([\s\S]+)$', t)
    return [l.strip() for l in (m.group(1) if m else '').split('\n') if l.strip().startswith('Vistos')]


def materia(r, tipo):
    if tipo == 'acórdão':
        e = MD.sem_cabecalho(r.get('ementa') or '')
        segs = [s.strip() for s in re.split(r'\.\s', e.split('\n')[0]) if s.strip()]
        segs = [s for s in segs if not re.match(r'^(DIREITO|APELA|EMBARG|REMESSA|AGRAVO|RECURSO)', s, re.I)]
        return ' '.join(segs[:2]).upper()[:80]
    m = re.search(r'Trata-se de [^.]{0,200}', r['inteiro_teor'] or '')
    return ' '.join(MD.norm(m.group(0)).split()[3:12]) if m else ''


RAMOS = [('previdenciário', r'previdenci|INSS|benefício|aposentadoria|auxílio|LOAS|assistencial'),
         ('tributário', r'tribut|PIS|COFINS|imposto|contribuição social|IRPJ|CSLL|execução fiscal|crédito tributário'),
         ('penal', r'\bpenal|crime|réu |denúncia|habeas'),
         ('administrativo', r'servidor|licita|improbidade|FIES|militar|concurso|administrativ'),
         ('civil', r'contrato|SFH|indenização|dano moral|responsabilidade civil|CEF|Caixa Econômica')]


def ramo(r):
    t = (r.get('ementa') or '')[:400] + ' ' + (r.get('inteiro_teor') or '')[:1500]
    for nome, rx in RAMOS:
        if re.search(rx, t, re.I):
            return nome
    return 'outro'


def jacc(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / len(A | B) if A and B else 0


PAL = re.compile(r'[A-Za-zÀ-ÿ0-9/]{3,}')
STOPT = set('que dos das com para pela pelo não por nos nas aos uma seu sua ser são foi está deve ante exposto artigo cpc '.split())


def titulo_versao(txt, base):
    a = {w.lower() for w in PAL.findall(txt)} - STOPT
    b = {w.lower() for w in PAL.findall(base)} - STOPT
    dif = [w for w in PAL.findall(txt) if w.lower() in a - b][:5]
    return ', '.join(dict.fromkeys(dif)) or 'variante'


RX_FECHO = re.compile(r'^(Comunique-se|Publique-se|Intimem-se|Campo Grande|Oportunamente|Dê-se ciência|Após, |Decorrido o prazo)')
POS_IDS = set()
RX_LEI = re.compile(r'^\s*[“"]?\s*(Art\.|§|[IVXLC]+\s*[-–]|[a-z]\)|Parágrafo único)')


def slug(t):
    return re.sub(r'[^a-z]', '', unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower())


def sobrepoe(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / min(len(A), len(B)) if A and B else 0


AGLUT = re.compile(r'\b(embargos|recurso|apelação|sentença|acórdão|artigo|Na|No|De)(de|da|do|espécie|caso)\b')


def chave_grafia(t):
    return re.sub(r'[\s.,;:]', '', MD.norm(t)).lower()


def versoes_de(lits, n_tipo, n_grupo, formula=True):
    """versões de um parágrafo: funde variações só de grafia; mantém as que mudam o sentido;
    quando a cauda varia caso a caso, preserva a fórmula inicial + {{complemento}}"""
    por_grafia = collections.defaultdict(collections.Counter)
    for lt, c in lits.items():
        por_grafia[chave_grafia(lt)][lt] += c
    cands = []
    for k, cs in por_grafia.items():
        # entre grafias equivalentes, prefere a sem aglutinação (mais palavras) e depois a mais usada
        melhor = max(cs, key=lambda t: (not AGLUT.search(t), len(t.split()), cs[t]))
        cands.append([melhor, sum(cs.values())])
    cands.sort(key=lambda x: -x[1])
    top_share = cands[0][1] / n_grupo
    vers = []
    if formula and top_share < 0.3 and len(cands) > 3:
        # fórmula fixa com cauda variável: maior prefixo comum a >= 60% das ocorrências
        toks = [c[0].split() for c in cands]
        pref = []
        for i in range(min(map(len, toks))):
            cont = collections.Counter(t[i] for t in toks if len(t) > i and t[:i] == pref)
            w, q = cont.most_common(1)[0]
            if sum(c[1] for c, t in zip(cands, toks) if t[:i + 1] == pref + [w]) < n_grupo * 0.6:
                break
            pref.append(w)
        if len(pref) >= 5:
            vers.append({'texto': lit_campos(' '.join(pref)) + ' {{complemento conforme o caso}}', 'uso': round(n_grupo / n_tipo, 3), 'titulo': 'fórmula + complemento'})
            return vers
    base = cands[0][0]
    for lt, c in cands:
        if c < max(2, n_grupo * 0.06) and vers:
            continue
        if any(sobrepoe(' '.join(MD.norm(v['_lit']).split()), ' '.join(MD.norm(lt).split())) >= 0.92 and abs(len(lt) - len(v['_lit'])) < 25 for v in vers):
            continue  # diferença mínima de redação: não é alternativa
        vers.append({'texto': lit_campos(lt), 'uso': round(c / n_tipo, 3), 'titulo': 'padrão' if not vers else titulo_versao(lt, base), '_lit': lt})
        if len(vers) == 4:
            break
    for v in vers:
        v.pop('_lit', None)
    return vers


SITUACOES = [
    ('parte', 'autora', r'\ba autora\b|da autora\b'), ('parte', 'autor', r'\bo autor\b|do autor\b'),
    ('parte', 'ré', r'\ba ré\b|autarquia|\bINSS\b|da ré\b'), ('parte', 'União', r'\bUnião\b|Fazenda Nacional'),
    ('parte', 'impetrante', r'impetrante'), ('parte', 'embargante', r'embargante'),
    ('gratuidade', 'sim', r'gratuidade'), ('sumula111', 'sim', r'Súmula 111'),
    ('oficio', 'sim', r'de ofício'), ('retorno', 'sim', r'retorno dos autos'),
    ('extincao', 'sim', r'extinto|sem resolução do mérito'), ('tema1059', 'sim', r'Tema 1\.059'),
]
ROT_SIT = {'gratuidade': 'gratuidade', 'sumula111': 'Súmula 111', 'oficio': 'correção de ofício', 'retorno': 'retorno à origem',
           'extincao': 'extinção sem mérito', 'tema1059': 'Tema 1.059'}


def situacao(t):
    tags = {}
    for k, v, rx in SITUACOES:
        if k not in tags and re.search(rx, t):
            tags[k] = v
    return tags


def titulo_sit(tags):
    partes = [('recorrente: ' + tags['parte'])] if 'parte' in tags else []
    partes += [ROT_SIT[k] for k in tags if k in ROT_SIT]
    return ' · '.join(partes)


def fundir_slots(slots):
    """parágrafos da mesma posição e ordem próxima, com texto sobreposto, são alternativas de um só ponto"""
    out = []
    for s in sorted(slots, key=lambda s: (s['posicao'], s['ordem'])):
        alvo = next((o for o in out if o['posicao'] == s['posicao'] and abs(o['ordem'] - s['ordem']) <= 0.12
                     and sobrepoe(' '.join(MD.norm(o['versoes'][0]['texto']).split()), ' '.join(MD.norm(s['versoes'][0]['texto']).split())) >= 0.6), None)
        if alvo:
            for v in s['versoes']:
                if len(alvo['versoes']) < 5:
                    alvo['versoes'].append({**v, 'titulo': v['titulo'] if v['titulo'] != 'padrão' else titulo_versao(v['texto'], alvo['versoes'][0]['texto'])})
            alvo['uso'] = round(min(1, alvo['uso'] + s['uso']), 3); alvo['opcional'] = alvo['uso'] < 0.5
            alvo['materias'] = max(alvo['materias'], s['materias'])
        else:
            out.append(s)
    for o in out:
        for v in o['versoes']:
            v['situacao'] = situacao(v['texto'])
        sits = [titulo_sit(v['situacao']) for v in o['versoes']]
        if len(set(sits)) > 1:  # quando as versões diferem pela situação, ela vira o título
            vistos = collections.Counter()
            for v, t in zip(o['versoes'], sits):
                if t:
                    vistos[t] += 1
                    v['titulo'] = t + ('' if vistos[t] == 1 else f' · redação {vistos[t]}')
        o['versoes'].sort(key=lambda v: -v['uso'])
        for i, v in enumerate(o['versoes']):
            if i == 0:
                v['titulo'] = 'padrão' if v['titulo'] in ('padrão', 'variante') else v['titulo']
    return out


TEMATICAS = ('admiss', 'prelim', 'trans', 'contro', 'jurid', 'fatos', 'provas', 'aplic', 'concl', 'fund')
RAMO_DOC = []
RAMO_TIPO_DOM = 0


def slots_de(seqs, n_tipo, materias, posicao_de):
    """seqs: lista (por decisão) de [(pos, literal)] → slots com versões"""
    fam = collections.defaultdict(lambda: {'docs': set(), 'mat': set(), 'pos': collections.Counter(), 'ord': [], 'var': collections.Counter(), 'lit': collections.defaultdict(collections.Counter), 'ramo': collections.Counter()})
    for d, seq in enumerate(seqs):
        tot = max(1, len(seq))
        for i, (pos, l) in enumerate(seq):
            nk = ' '.join(MD.norm(l).split())
            pk = ' '.join(nk.split()[:4])
            f = fam[pk]
            f['docs'].add(d); f['ramo'][RAMO_DOC[d] if d < len(RAMO_DOC) else 'outro'] += 1; f['mat'].add(materias[d]); f['pos'][pos] += 1; f['ord'].append(i / tot)
            f['var'][nk] += 1; f['lit'][nk][' '.join(l.split())] += 1
    slots = []
    for pk, f in fam.items():
        if len(f['docs']) < max(3, n_tipo * MIN_SLOT) or len(f['mat']) < MIN_MAT:
            continue
        # agrupa variantes do mesmo parágrafo (sobreposição alta de palavras, inclusive quando uma contém a outra)
        grupos = []
        for nk, c in f['var'].most_common():
            g = next((g for g in grupos if sobrepoe(g['top'], nk) >= 0.8), None)
            if g:
                g['vars'].append((nk, c)); g['n'] += c
            else:
                grupos.append({'top': nk, 'vars': [(nk, c)], 'n': c})
        for g in grupos:
            if g['n'] < max(3, n_tipo * MIN_SLOT):
                continue
            lits = collections.Counter()
            for nk, c in g['vars']:
                for lt, k in f['lit'][nk].items():
                    lits[lt] += k
            versoes = versoes_de(lits, n_tipo, g['n'], posicao_de(f['pos'].most_common(1)[0][0]) not in ('honor', 'disp', 'fecho', 'consec'))
            uso = g['n'] / n_tipo
            dom = f['ramo'].most_common(1)[0][1] / max(1, sum(f['ramo'].values()))
            slots.append({'posicao': posicao_de(f['pos'].most_common(1)[0][0]), 'ordem': round(sum(f['ord']) / len(f['ord']), 3),
                          'uso': round(min(1, uso), 3), 'opcional': uso < 0.5, 'materias': len(f['mat']), 'versoes': versoes})
    # texto de lei transcrito e fundamentação temática pertencem ao modelo de matéria, não ao tipo de julgamento
    slots = [x for x in slots if x['versoes'] and not RX_LEI.match(x['versoes'][0]['texto'])
             and not (x['posicao'] in TEMATICAS and x['uso'] < 0.3 and len(x['versoes'][0]['texto']) > 130)]
    for x in slots:  # prequestionamento (art. 1.025) fecha a fundamentação, antes do dispositivo
        if 'complem' in POS_IDS and re.search(r'artigo 1\.025|prequestionamento', x['versoes'][0]['texto']) and x['posicao'] not in ('disp', 'contro'):
            x['posicao'] = 'complem'
    for x in slots:  # fórmulas de encerramento ficam no fecho, onde quer que tenham sido lidas
        if RX_FECHO.match(x['versoes'][0]['texto']) and x['posicao'] not in ('disp',):
            x['posicao'] = 'fecho' if 'fecho' in POS_IDS else x['posicao']
            if x['versoes'][0]['texto'].startswith('Campo Grande'):
                x['ordem'] = 2
    return fundir_slots(slots)


def main():
    acs = [r for r in MD.carregar('acordaos') if r['conteudo_texto'] == 'integral' and MD.fase(r) == FASE]
    mon = [r for r in MD.carregar('monocraticas') if MD.fase(r) == FASE]
    tipos = collections.defaultdict(list)
    for r in acs:
        tipos[('acórdão', MD.especie(r), MD.resultado(r, 'acordaos'))].append(r)
    for r in mon:
        tipos[('monocrática', MD.especie(r), MD.resultado(r, 'monocraticas'))].append(r)
    saida = []
    for (tipo, esp, res), R in sorted(tipos.items(), key=lambda kv: -len(kv[1])):
        if len(R) < MIN_TIPO or res == 'outro':
            continue
        mono = tipo == 'monocrática'
        POS = POS_MONO if mono else POS_VOTO
        mats = [materia(r, tipo) for r in R]
        global RAMO_DOC
        RAMO_DOC = [ramo(r) for r in R]
        global RAMO_TIPO_DOM
        RAMO_TIPO_DOM = collections.Counter(RAMO_DOC).most_common(1)[0][1] / len(R)
        seqs = []
        for r in R:
            v = voto(r, tipo)
            seqs.append([(classif(l, i, len(v)), l) for i, l in enumerate(v)])
        global POS_IDS
        POS_IDS = {p[0] if isinstance(p, (list, tuple)) else p for p in POS}
        slots = slots_de(seqs, len(R), mats, (lambda p: MAP_MONO.get(p, 'fund')) if mono else (lambda p: p))
        # presença de conteúdo próprio por posição (para os campos {{ }})
        pres = collections.Counter()
        for seq in seqs:
            for p in {(MAP_MONO.get(p, 'fund') if mono else p) for p, _ in seq}:
                pres[p] += 1
        posicoes = []
        for pid, tit in POS:
            ss = sorted([s for s in slots if s['posicao'] == pid], key=lambda s: s['ordem'])
            base = CAMPO.get(pid, '') if pres[pid] >= len(R) * 0.3 else ''
            if not ss and not base:
                continue
            posicoes.append({'id': pid, 'titulo': tit, 'base': base, 'slots': ss})
        extra = {}
        if not mono:
            for nome in ('ementa', 'acordao'):
                sq = [[(nome, l) for l in blocos_secao(r, nome)] for r in R]
                extra[nome] = sorted([s for s in slots_de(sq, len(R), mats, lambda p: p)], key=lambda s: s['ordem'])
        rot_esp = {'ED': 'Embargos de declaração', 'AI': 'Agravo de instrumento', 'RemNec': 'Remessa necessária', 'CC': 'Conflito de competência',
                   'SUSPAPEL': 'Pedido de efeito suspensivo'}.get(esp, esp)
        rid = f"MATRIZ-{FASE}-{'M' if mono else 'A'}-{slug(rot_esp).upper()[:8]}-{slug(res)[:14]}"
        saida.append({'id': rid, 'fase': FASE, 'pronunciamento': 'Decisão monocrática terminativa' if mono else 'Voto',
                      'tipo': tipo, 'especie': rot_esp, 'resultado': res, 'decisoes': len(R), 'materias': len(set(mats)),
                      'periodo': [min(r.get('data_julgamento_iso') or r.get('data_decisao_iso') for r in R), max(r.get('data_julgamento_iso') or r.get('data_decisao_iso') for r in R)],
                      'exemplos': [r['id'] for r in sorted(R, key=lambda r: r.get('data_julgamento_iso') or r.get('data_decisao_iso') or '', reverse=True)[:10]],
                      'posicoes': posicoes, **({'ementa': extra['ementa'], 'acordao': extra['acordao']} if not mono else {})})
    ids = collections.Counter()
    for m in saida:
        ids[m['id']] += 1
        if ids[m['id']] > 1:
            m['id'] += f"-{ids[m['id']]}"
    dados = {'gerado_por': 'scripts/matrizes.py', 'fase': FASE, 'criterios': {'min_decisoes_tipo': MIN_TIPO, 'min_uso_slot': MIN_SLOT, 'min_materias': MIN_MAT},
             'total': len(saida), 'matrizes': saida}
    os.makedirs(os.path.join(RAIZ, 'modelos'), exist_ok=True)
    with open(os.path.join(RAIZ, 'modelos', 'matrizes.json'), 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
    with open(os.path.join(RAIZ, 'modelos', 'matrizes.json.gz'), 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as gz:
        gz.write(json.dumps(dados, ensure_ascii=False, separators=(',', ':')).encode())
    exportar_gabA(saida)
    for m in saida:
        print(f"{m['decisoes']:4d} {m['materias']:4d}m  {m['id']:38s} posições={len(m['posicoes'])} parágrafos={sum(len(p['slots']) for p in m['posicoes'])} versões={sum(len(s['versoes']) for p in m['posicoes'] for s in p['slots'])}")


def exportar_gabA(saida):
    """registros no formato Modelo-matriz do gerador do gabinete (gabA.modelos)"""
    regs = []
    for m in saida:
        mono = m['tipo'] == 'monocrática'
        esq = {'_estrutura': 'matriz', '_topicos': [{'id': p['id'], 'titulo': p['titulo'].split(' · ')[-1], 'opcional': all(s['opcional'] for s in p['slots']) and not p['base'], 'livres': True} for p in m['posicoes']]}
        pars = []
        for p in m['posicoes']:
            esq[p['id']] = {'texto': p['base'], 'ativo': bool(p['base']) or any(not s['opcional'] for s in p['slots'])}
            for o, s in enumerate(p['slots'], 1):
                for v, ver in enumerate(s['versoes'], 1):
                    pars.append({'posicao': p['id'], 'ordem': o, 'versao': v,
                                 'titulo': f"{'opcional · ' if s['opcional'] else ''}{ver['titulo']} ({round(ver['uso'] * 100)}%)",
                                 'texto': ver['texto'], 'cit': '', 'citTipo': '', 'citRef': ''})
        regs.append({'id': m['id'].lower(), 'processo': m['id'], 'tipo': 'Modelo', 'formatoModelo': 'Modelo-matriz', 'pronunciamento': m['pronunciamento'],
                     'classe': m['especie'], 'resultado': m['resultado'], 'assunto': '(estrutural — qualquer matéria)',
                     'fonte': f"Extraído de {m['decisoes']} decisões da Turma Regional de MS ({m['materias']} matérias), {m['periodo'][0]} a {m['periodo'][1]}",
                     'esqueletoModelo': json.dumps(esq, ensure_ascii=False), 'paragrafosModelo': json.dumps(pars, ensure_ascii=False)})
    with open(os.path.join(RAIZ, 'modelos', 'matrizes_gabA.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema': 'gabA.modelos', 'schema_versao': 1, 'descricao': 'Modelos-matriz por tipo de julgamento, extraídos do acervo do gabinete (Turma Regional de MS). Identificadores MATRIZ não representam processos judiciais.',
                   'registros': regs}, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
