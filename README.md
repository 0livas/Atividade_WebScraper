# Atividade WebScraper

Implementação das duas atividades de coleta de dados propostas durante as aulas de ciência de dados. Os programas usam `requests`, `BeautifulSoup`, tratamento de erros, paginação e gravação de CSV em UTF-8, conforme instruções específicas das atividades.

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Atividade 1 - Fundação Bradesco

Extrai automaticamente todos os cursos do catálogo, visita a página de cada
curso e salva título, área/tema, descrição, carga horária, nível, link,
conteúdo e detalhes.

```bash
python atividade_1_fundacao_bradesco/scraper_cursos.py
```

Saída padrão: `atividade_1_fundacao_bradesco/saida/cursos_fundacao_bradesco.csv`.

## Atividade 2 - Mini Atividade 1

### 1. Sucupira (500 programas)

O portal atual é uma aplicação JavaScript. O programa consulta a mesma API
pública usada pelo portal e enriquece os 500 registros com os detalhes de cada
programa.

```bash
python atividade_2_mini_atividade_1/scraper_sucupira.py
```

Por padrão o programa coleta 500 registros, mas isso poder ser alterado com --limite "quantidade" junto do comando python ou alterando a variável global "QUANTIDADE" presente no código.

### 2. Duas URLs para dois CSVs

Esse extrator genérico registra metadados, títulos, parágrafos, itens de lista,
links e tabelas de cada página. Para rodar, informe exatamente duas URLs e duas saídas:

```bash
python atividade_2_mini_atividade_1/extrair_duas_urls.py \
  --url https://www.ev.org.br/cursos \
  --url https://xkcd.com/ \
  --saida saida/url_1.csv \
  --saida saida/url_2.csv
```

### 3. XKCD

Por padrão, inicia na página atual e segue `Previous Comic` até a primeira.
Use `--limite` para testar sem baixar todo o acervo.

```bash
python atividade_2_mini_atividade_1/baixar_xkcd.py --limite 3
python atividade_2_mini_atividade_1/baixar_xkcd.py
```

