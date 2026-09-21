# Previsão de Ondas — Pernambuco (piloto)

## Contexto
Produto "bônus" derivado da tese de doutorado em oceanografia de Daniel
Brandt Galvão sobre o clima de ondas na costa de Pernambuco (projeto irmão
em `C:\TESE_DANIEL`, separado deste). Site público de previsão de ondas
para a costa de PE, em produção desde o início da colaboração.

- **Site**: https://mardeondas.com.br (domínio próprio; o link antigo
  `brandtgalvao.github.io/previsao-ondas-pe/` redireciona automaticamente)
- **Repositório**: `brandtgalvao/previsao-ondas-pe` (GitHub)
- **Hospedagem**: GitHub Pages, deploy via GitHub Actions
  (`.github/workflows/update-forecast.yml`), cron 2x/dia (09:15 e 21:15 UTC)
  + `workflow_dispatch` manual

## Arquitetura
- `pipeline/` (Python, ambiente conda `ondas_pe`): busca dados do
  **ECMWF Open Data** (HRES/IFS-WAM), calcula energia/potência de onda,
  parseia tábuas de maré da Marinha (PDF), monta `site/data/forecast.json`,
  e roda o sistema de alertas (`pipeline/alerts.py`)
- `site/` (HTML/CSS/JS vanilla, sem framework): consome o `forecast.json`
  e renderiza os gráficos/painéis. `app.js` é o núcleo (gráficos, escala de
  ondas); `alerts.js` é o formulário de cadastro de alertas (fala direto
  com o Supabase via REST, usando a anon key pública)
- `db/schema.sql`: schema do Supabase (assinantes de alerta, log de
  eventos, RLS) — rodar manualmente no SQL Editor do Supabase quando mudar

## Funcionalidades já implementadas
1. **Previsão de ondas/vento/temperatura/maré** por praia (12 praias/
   municípios de PE), com gráficos de altura/período/direção, energia/
   potência, resumo semanal
2. **Escala de Ondas em Pernambuco**: classificação Muito baixa/Baixa/
   Normal/Grande/Extrema por percentil (P5/P25/P75/P95) da série histórica
   offshore P2/ERA5 (1940–2025), aplicada a Hs e Potência. Painel oculto
   por padrão ("Mostrar escala"), com bloco "Classificação das ondas"
   (energia sempre em J/m², nunca kJ/m²)
2. **Sistema de alertas por e-mail/SMS**: cadastro público no site,
   detecção de evento (entrada/agravamento pra Grande/Extrema, sem
   duplicar), envio via Resend (e-mail, domínio `mardeondas.com.br`
   verificado) e Twilio (SMS, ainda não configurado — opcional). Testado
   de ponta a ponta com assinante real
3. **Domínio próprio** `mardeondas.com.br` apontado pro GitHub Pages
   (nota técnica: nesse modo de deploy via Actions, o arquivo `CNAME`
   sozinho NÃO configura o domínio customizado — precisa
   `gh api repos/.../pages -X PUT -f cname=...` explicitamente)
4. **Redesign visual v1** (em andamento): direção acordada é "dashboard
   funcional com toque editorial" — mantém a densidade de dados (não vira
   minimalista) mas ganha refinamento tipográfico/institucional (não vira
   um app pop de praia). V1 trocou tipografia (Fraunces pros títulos/
   números de destaque, Inter pro resto, tabular-nums), criou um hero no
   cabeçalho, refinou paineis. Feedback do usuário: "ainda muito parecido
   com o original" — falta trabalho mais estrutural (grid, hierarquia de
   cores, layout que não seja só painéis empilhados)

## Ferramenta de design disponível
**Impeccable** (`.claude/skills/impeccable/`, instalado via
`npx impeccable install`) — skill de design pra agentes de IA, com
comandos tipo `polish`, `audit`, `critique`, `bolder`, `layout`, `typeset`
etc. Invocar via `Skill({skill: "impeccable", args: "<comando>"})`. Rodar
`init` primeiro (se ainda não tiver `PRODUCT.md`/`DESIGN.md` no projeto)
pra capturar contexto de produto antes de qualquer trabalho de design.

## Convenções e cuidados importantes
- Identidade visual: navy/cyan (`--bg: #0a1a28`, `--accent: #5bd0f0`)
  como base histórica — redesigns podem evoluir isso, mas não descartar
  sem conversar, é a identidade que o usuário escolheu ao longo da sessão
- **Nunca alterar IDs/classes que `app.js`/`alerts.js` referenciam**
  (a lista é longa — checar com Grep antes de renomear qualquer coisa)
- Antes de mudanças estruturais grandes, criar uma tag git de segurança
  (padrão já usado: `pre-escala-ondas-pe`, `pre-alertas-ondas-pe`,
  `pre-redesign-layout`)
- Testar sempre local (`.claude/launch.json` já tem o servidor `site` em
  `localhost:8000`) em desktop E mobile (375px) antes de publicar
- Deploy: `git push` sozinho NÃO redeploya (o workflow só roda por
  agenda ou `workflow_dispatch`) — depois de commitar, rodar
  `gh workflow run "Atualizar previsão"` e acompanhar com `gh run watch`
- `gh` CLI perde autenticação entre sessões às vezes — se der erro de
  auth, usar `gh auth login --hostname github.com --git-protocol https
  --web` (device flow, pede um código pro usuário autorizar no
  navegador) e depois `gh auth refresh -h github.com -s workflow` se
  precisar do scope de workflow
- Segredos (Supabase service key, Resend/Twilio API keys) ficam só como
  secrets do GitHub Actions — nunca pedir pro usuário colar eles no chat;
  a chave "anon" do Supabase é pública por design e pode ficar exposta
  em `site/alerts-config.js`

## Fora de escopo aqui
Qualquer trabalho da tese em si (figuras, capítulos, dados científicos)
pertence exclusivamente à sessão/pasta `C:\TESE_DANIEL` e não deve ser
misturado a este projeto.
