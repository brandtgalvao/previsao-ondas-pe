-- Schema Supabase para o sistema-piloto de alertas de ondas.
-- Rode este arquivo inteiro uma vez no SQL Editor do seu projeto Supabase
-- (Project > SQL Editor > New query > colar e rodar).
--
-- Nenhuma credencial fica aqui. O front-end so usa a "anon key" (publica por
-- design no Supabase, protegida pelas policies de RLS abaixo). O pipeline
-- Python usa a "service_role key" (secreta, nunca exposta ao navegador) para
-- ler assinantes ativos e gravar o log de alertas enviados.

create extension if not exists pgcrypto; -- gen_random_uuid()

-- ---------------------------------------------------------------------
-- subscribers: cadastro de quem quer receber alerta
-- ---------------------------------------------------------------------
create table if not exists subscribers (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  nome text not null,
  email text,
  telefone text,
  place_id text not null,          -- mesma chave usada em PLACES (pipeline/config.py) e no forecast.json
  nivel text not null check (nivel in ('grande_extrema', 'extrema')),
  canal_email boolean not null default false,
  canal_sms boolean not null default false,
  consentimento boolean not null default false,
  ativo boolean not null default true,
  unsubscribe_token uuid not null default gen_random_uuid(),
  constraint pelo_menos_um_canal check (canal_email or canal_sms),
  constraint consentimento_obrigatorio check (consentimento = true),
  constraint pelo_menos_um_contato check (
    (canal_email and email is not null) or (canal_sms and telefone is not null)
  )
);

create index if not exists idx_subscribers_place_ativo on subscribers (place_id) where ativo = true;

-- ---------------------------------------------------------------------
-- place_state: ultima classe conhecida por local (deteccao de evento)
-- ---------------------------------------------------------------------
create table if not exists place_state (
  place_id text primary key,
  last_class smallint not null default 0,  -- indice 0..4 (muito_baixa..extrema)
  last_event_id uuid,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- sent_alerts: log de alertas enviados (auditoria + evita duplicidade)
-- ---------------------------------------------------------------------
create table if not exists sent_alerts (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  subscriber_id uuid not null references subscribers(id),
  place_id text not null,
  event_id uuid not null,
  classe text not null,             -- 'grande' ou 'extrema'
  valid_time timestamptz not null,
  hs_m numeric not null,
  energy_j_m2 numeric not null,
  power_kw_m numeric not null,
  model_run text not null,
  canal text not null,              -- 'email' ou 'sms'
  status text not null default 'enviado'  -- 'enviado' | 'falhou'
);

create index if not exists idx_sent_alerts_subscriber_event on sent_alerts (subscriber_id, event_id);

-- ---------------------------------------------------------------------
-- RLS: por padrao ninguem le/edita nada. So abrimos o minimo necessario
-- para o front-end publico (chave anon); todo o resto usa service_role
-- (que sempre ignora RLS) a partir do pipeline.
-- ---------------------------------------------------------------------
alter table subscribers enable row level security;
alter table place_state enable row level security;
alter table sent_alerts enable row level security;

-- Cadastro publico: qualquer visitante pode inserir sua propria inscricao.
-- Nao ha policy de SELECT/UPDATE/DELETE publica em subscribers -> o anon
-- nunca consegue listar ou ler cadastros (dos outros nem do proprio).
drop policy if exists public_insert_subscribers on subscribers;
create policy public_insert_subscribers on subscribers
  for insert to anon
  with check (true);

-- ---------------------------------------------------------------------
-- Descadastro: funcao dedicada (nao uma policy de UPDATE direta na
-- tabela), para nao dar ao anon permissao geral de escrita. So permite
-- desativar (ativo=false) quem sabe o id + unsubscribe_token exatos
-- (ambos vao no link enviado por e-mail/SMS).
-- ---------------------------------------------------------------------
create or replace function unsubscribe(p_id uuid, p_token uuid)
returns boolean
language sql
security definer
set search_path = public
as $$
  update subscribers
  set ativo = false
  where id = p_id and unsubscribe_token = p_token and ativo = true
  returning true;
$$;

revoke all on function unsubscribe(uuid, uuid) from public;
grant execute on function unsubscribe(uuid, uuid) to anon;
