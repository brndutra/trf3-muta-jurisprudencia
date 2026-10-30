#!/usr/bin/env python3
"""Organiza o acervo extraído da base de jurisprudência do TRF3 (Des. Fed. Carlos Muta).

Entrada: os JSON exportados do navegador (monocráticas + acórdãos por período).
Saída (em ./dados):
  monocraticas/AAAA.json.gz   decisões monocráticas por ano da decisão
  acordaos/AAAA.json.gz       acórdãos por ano do julgamento
  indice.json.gz              índice compacto para o painel de consulta
  ../MANIFESTO.json           hashes SHA-256 de cada arquivo e de cada registro
  ../SHA256SUMS               hashes no formato do `sha256sum -c`

Nenhum texto de origem é alterado: o script só acrescenta `id` e os hashes
SHA-256 do inteiro teor e da ementa, e redistribui os registros por ano.

Uso: python3 scripts/organizar.py ARQUIVO.json [ARQUIVO.json ...]
"""
import gzip, hashlib, json, os, re, sys
from collections import defaultdict
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, 'dados')


def sha(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest() if s else None


def sha_arquivo(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def resumo(s, n):
    if not s:
        return None
    s = ' '.join(s.split())
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0] + '…'


RE_REL = re.compile(r'^\s*R\s?E\s?L\s?A\s?T\s?[ÓO]\s?R\s?I\s?O\b', re.I | re.M)
RE_VOTO = re.compile(r'^\s*V\s?O\s?T\s?O\b', re.I | re.M)
RE_EMENTA_TIT = re.compile(r'^\s*E\s?M\s?E\s?N\s?T\s?A\s*$', re.I | re.M)
RE_RESULT = re.compile(r'(por unanimidade|por maioria)(.*?)(?:,?\s*nos termos d|$)', re.I | re.S)
ORDINAIS = {'PRIMEIRA': '1ª', 'SEGUNDA': '2ª', 'TERCEIRA': '3ª', 'QUARTA': '4ª', 'QUINTA': '5ª', 'SEXTA': '6ª',
            'SÉTIMA': '7ª', 'SETIMA': '7ª', 'OITAVA': '8ª', 'NONA': '9ª', 'DÉCIMA': '10ª', 'DECIMA': '10ª'}


def conteudo_texto(r):
    """Classifica o que a base efetivamente entrega no campo inteiro_teor."""
    it = r.get('inteiro_teor')
    if not it:
        return 'apenas_ementa'
    if RE_REL.search(it) and RE_VOTO.search(it):
        return 'integral'
    if RE_REL.search(it) and len(it) > 3000:
        return 'integral'
    return 'apenas_acordao'


def orgao_normalizado(o):
    if not o:
        return None
    s = ' '.join(o.split())
    m = re.match(r'^(\S+)\s+(TURMA|SEÇÃO|SECAO)$', s, re.I)
    if m and m.group(1).upper() in ORDINAIS:
        return f"{ORDINAIS[m.group(1).upper()]} {'Turma' if m.group(2).upper() == 'TURMA' else 'Seção'}"
    if re.match(r'^[OÓ]RG[AÃ]O ESPECIAL$', s, re.I):
        return 'Órgão Especial'
    return s


def previa(r, tipo):
    """Trecho de leitura rápida, sem o cabeçalho do PJe."""
    if tipo == 'acordaos':
        e = r.get('ementa') or ''
        m = RE_EMENTA_TIT.search(e)
        return e[m.end():] if m else e
    it = r.get('inteiro_teor') or ''
    m = re.search(r'(Trata-se|Cuida-se|Vistos[.,])', it)
    return it[m.start():] if m else it


def resultado_curto(r, tipo):
    if tipo == 'monocraticas':
        return r.get('dispositivo')
    s = r.get('resultado_colegiado') or ''
    m = RE_RESULT.search(s)
    return (m.group(1) + m.group(2)).strip(' ,') if m else (s or None)


def gravar_gz(p, obj):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    # mtime=0 torna o .gz reprodutível byte a byte
    with open(p, 'wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', compresslevel=9, mtime=0) as gz:
        gz.write(data)


def main(arquivos):
    fontes, mono, acor = [], [], []
    meta_mono, meta_acor = None, []
    for p in arquivos:
        d = json.load(open(p, encoding='utf-8'))
        nome = re.sub(r'^[0-9a-f]{8}-', '', os.path.basename(p))  # remove prefixo de upload
        fontes.append({'arquivo': nome, 'bytes': os.path.getsize(p), 'sha256': sha_arquivo(p),
                       'registros': len(d.get('decisoes') or d.get('acordaos'))})
        if 'decisoes' in d:
            mono += d['decisoes']; meta_mono = d['metadados']
        else:
            acor += d['acordaos']; meta_acor.append(d['metadados'])

    por_ano = {'monocraticas': defaultdict(list), 'acordaos': defaultdict(list)}
    indice, registros_hash = [], []
    for tipo, regs, campo_data in (('monocraticas', mono, 'data_decisao_iso'), ('acordaos', acor, 'data_julgamento_iso')):
        pref = 'M' if tipo == 'monocraticas' else 'A'
        for r in sorted(regs, key=lambda x: (x.get(campo_data) or '', x['seq'])):
            r = {'id': f"{pref}{r['seq']:05d}", **r}
            r['sha256_inteiro_teor'] = sha(r.get('inteiro_teor'))
            if tipo == 'acordaos':
                r['sha256_ementa'] = sha(r.get('ementa'))
                r['conteudo_texto'] = conteudo_texto(r)
                r['possui_inteiro_teor'] = r['conteudo_texto'] == 'integral'
            else:
                r['conteudo_texto'] = 'integral'
            ano = (r.get(campo_data) or '0000')[:4]
            por_ano[tipo][ano].append(r)
            registros_hash.append({'id': r['id'], 'arquivo': f'dados/{tipo}/{ano}.json.gz',
                                   'sha256_inteiro_teor': r['sha256_inteiro_teor'],
                                   **({'sha256_ementa': r['sha256_ementa']} if tipo == 'acordaos' else {})})
            indice.append({
                'id': r['id'], 't': pref, 'n': r['numero_processo'], 'c': r.get('classe_sigla'),
                'cl': r.get('classe'), 'o': orgao_normalizado(r.get('orgao_julgador')), 'd': r.get(campo_data),
                'p': r.get('data_publicacao'), 'v': r.get('publicacao_veiculo'),
                'a': r.get('atuacao_muta', 'relator'), 'k': r['conteudo_texto'],
                'e': resumo(previa(r, tipo), 380),
                'r': resumo(resultado_curto(r, tipo), 240),
                'y': ano,
            })

    arquivos_saida = []
    for tipo, anos in por_ano.items():
        for ano, regs in sorted(anos.items()):
            p = os.path.join(DADOS, tipo, f'{ano}.json.gz')
            gravar_gz(p, {'tipo': tipo, 'ano': ano, 'total': len(regs), 'registros': regs})
            arquivos_saida.append(p)
    gravar_gz(os.path.join(DADOS, 'indice.json.gz'), indice)
    arquivos_saida.append(os.path.join(DADOS, 'indice.json.gz'))

    contagem = {t: {a: len(v) for a, v in sorted(anos.items())} for t, anos in por_ano.items()}
    manifesto = {
        'gerado_em': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'fonte': 'TRF3 — Base de Jurisprudência (web.trf3.jus.br/jurisprudencia), coleções Monocráticas e TRF3/Acórdãos',
        'criterios': {'monocraticas': meta_mono and meta_mono.get('criterio'),
                      'acordaos': meta_acor and meta_acor[0].get('criterio')},
        'coleta_original': {'monocraticas': meta_mono and meta_mono.get('data_coleta'),
                            'acordaos': meta_acor and meta_acor[0].get('data_coleta')},
        'totais': {'monocraticas': len(mono), 'acordaos': len(acor),
                   'acordaos_na_base': meta_acor and meta_acor[0].get('total_acervo_na_base'),
                   'acordaos_nao_coletados': meta_acor and meta_acor[0].get('nao_coletados'),
                   'acordaos_por_conteudo_texto': dict(sorted(
                       __import__('collections').Counter(x['k'] for x in indice if x['t'] == 'A').items()))},
        'contagem_por_ano': contagem,
        'arquivos_de_entrada': fontes,
        'arquivos': [{'arquivo': os.path.relpath(p, RAIZ), 'bytes': os.path.getsize(p), 'sha256': sha_arquivo(p)}
                     for p in arquivos_saida],
        'registros': registros_hash,
    }
    with open(os.path.join(RAIZ, 'MANIFESTO.json'), 'w', encoding='utf-8') as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=1)
    with open(os.path.join(RAIZ, 'SHA256SUMS'), 'w') as f:
        for a in manifesto['arquivos']:
            f.write(f"{a['sha256']}  {a['arquivo']}\n")
    print(json.dumps({k: manifesto[k] for k in ('totais', 'contagem_por_ano')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
