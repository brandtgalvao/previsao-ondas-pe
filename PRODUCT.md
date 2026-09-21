# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Público multifacetado e majoritariamente profissional/técnico que precisa de condição
de mar em Pernambuco para tomar uma decisão prática:

- Gerenciamento de risco portuário e operações marítimas (decisões operacionais)
- Comandantes de navios / navegação comercial
- Cientistas e pesquisadores (oceanografia, clima de ondas)
- Mergulhadores
- Pescadores
- Surfistas e outros watermen (surf, vela) decidindo se vale ir pra praia
- Público costeiro geral (moradores, turistas) querendo maré/condição do mar de forma simples

A superfície precisa servir tanto uma consulta rápida ("dá pra sair hoje?") quanto uma
leitura técnica aprofundada (séries de energia/potência, direção, período, referência
histórica) — não é um público único e não pode ser tratado como "app de praia".

## Product Purpose

Previsão de ondas, vento, temperatura e maré para a costa de Pernambuco (12 praias/
municípios), com classificação da condição do mar em relação à série histórica
(Escala de Ondas em Pernambuco) e alertas automáticos por e-mail/SMS quando a condição
prevista entra em Grande/Extrema. Nasceu como produto "bônus" de uma tese de doutorado
em oceanografia (clima de ondas na costa de PE) e está em produção pública desde o
início da colaboração.

## Positioning

Rigor científico e transparência de fonte, não previsão de caixa-preta: dados de fonte
primária (ECMWF Open Data HRES/IFS-WAM, Tábua de Maré da Marinha/DHN), com a física
explicada (fórmulas de energia/potência de onda, mesmo período de energia "mwp" oficial
do ECMWF) e a classificação da condição ancorada numa referência histórica real (P2/ERA5,
1940–2025) em vez de uma escala arbitrária. Feito por quem pesquisa isso na prática
(tese de doutorado em oceanografia). Esse rigor é o que diferencia de concorrentes como
o Surfguru — não densidade de dados por si só, mas a credibilidade de que os números
vêm de metodologia auditável.

## Operating Context

- Site público, sem login, consumido em desktop e mobile
- Dados atualizados 2x/dia via pipeline automatizado (GitHub Actions + ECMWF Open Data)
- Usuário técnico pode acompanhar séries temporais completas (7 dias) por praia;
  usuário de decisão rápida pode olhar só o card de "condição atual"
- Cadastro de alertas por e-mail/SMS é uma jornada secundária (opt-in), não o ponto
  de entrada principal

## Capabilities and Constraints

- 12 praias/municípios de PE, cada uma mapeada pro ponto de grade offshore mais próximo
  (praias próximas podem compartilhar o mesmo ponto — resolução do modelo global)
- Variáveis: altura/período/direção de onda, energia (J/m²) e potência (kW/m) de onda,
  vento (nós + direção), temperatura de água e ar, maré (gráfico e tabela)
- Escala de Ondas em Pernambuco: 5 classes (Muito baixa/Baixa/Normal/Grande/Extrema)
  por percentil (P5/P25/P75/P95) da série histórica offshore P2/ERA5, aplicada a Hs e
  Potência — energia sempre exibida em J/m², nunca kJ/m²
- Sistema de alertas: detecção de evento (entrada/agravamento pra Grande/Extrema, sem
  duplicar), envio via Resend (e-mail) e Twilio (SMS, opcional/não configurado ainda)
- Stack: HTML/CSS/JS vanilla no front (`site/`), sem framework — constraint técnico
  deliberado, não pendência
- IDs/classes usados por `app.js`/`alerts.js` são contrato vivo do JS — qualquer
  redesign de HTML/CSS precisa preservar os hooks que o JS referencia

## Brand Commitments

- Nome do produto: "Previsão de Ondas — Pernambuco", domínio mardeondas.com.br
- Crédito visível ao autor: Daniel Brandt Galvão / UFPE (contato daniel.brandt@ufpe.br)
- Rótulo "piloto de pesquisa acadêmica" é intencional e deve permanecer legível — não
  é um MVP disfarçado, é uma característica de identidade (contraponto à leitura de
  "produto comercial")
- Paleta navy/cyan (`--bg: #0a1a28`, `--accent: #5bd0f0`) e tipografia Fraunces
  (display) + Inter (corpo) são a identidade estabelecida ao longo da colaboração —
  redesign pode evoluir a aplicação da paleta, mas não a substitui sem conversar

## Evidence on Hand

- Implementação incumbente completa em `site/` (HTML/CSS/JS), com dados reais
  servidos por `site/data/forecast.json`
- Metodologia e fórmulas documentadas no rodapé do site (`site/index.html`)
- Concorrente de referência: Surfguru (posicionamento por contraste, não por cópia
  de layout)

## Product Principles

1. Densidade de dados é uma feature, não uma dívida — o redesign não pode "limpar"
   o site a ponto de esconder as séries técnicas que diferenciam o produto.
2. A credibilidade científica precisa ser visualmente legível — layout e hierarquia
   devem comunicar rigor/precisão, não estética de app de praia.
3. Serve dois modos de leitura ao mesmo tempo: decisão rápida (card de condição atual)
   e leitura técnica profunda (séries completas) — ambos precisam de hierarquia clara
   na mesma página, sem forçar o usuário rápido a rolar por tudo.
4. O rótulo de "piloto acadêmico" e o crédito ao autor são parte da identidade, não
   um detalhe a minimizar.
5. Qualquer mudança estrutural em HTML/CSS preserva os IDs/classes que `app.js` e
   `alerts.js` referenciam — funcionalidade nunca quebra por causa de estética.
