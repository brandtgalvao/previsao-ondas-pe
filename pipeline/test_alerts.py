"""Testes sinteticos da logica de alertas (secao 7 do pedido), sem
depender de credenciais reais do Supabase/Resend/Twilio - usa um
Supabase falso em memoria e verifica so a maquina de estados/regras de
disparo. Rodar com: python pipeline/test_alerts.py
"""
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import alerts  # noqa: E402


class FakeSupabase:
    def __init__(self):
        self.place_state = {}
        self.subscribers = []
        self.sent_alerts = []

    def get(self, table, params):
        if table == "place_state":
            place_id = params["place_id"].split("eq.")[1]
            row = self.place_state.get(place_id)
            return [{"last_class": row["last_class"]}] if row else []
        if table == "subscribers":
            place_id = params["place_id"].split("eq.")[1]
            return [s for s in self.subscribers if s["place_id"] == place_id and s["ativo"]]
        raise ValueError(table)

    def insert(self, table, rows):
        if table == "sent_alerts":
            self.sent_alerts.extend(rows)
        else:
            raise ValueError(table)

    def upsert(self, table, rows, on_conflict):
        if table == "place_state":
            for r in rows:
                self.place_state[r["place_id"]] = r
        else:
            raise ValueError(table)


def entry(hs, power, hours_from_now=3.0):
    vt = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    return {
        "valid_time": vt.strftime("%Y-%m-%dT%H:%MZ"),
        "hs_m": hs,
        "power_kw_m": power,
        "energy_j_m2": 628 * hs ** 2,
    }


# valores de referencia por classe (Hs e Pw ambos na mesma classe, p/ simplificar)
NORMAL = (1.50, 8.0)
GRANDE = (1.90, 13.0)
EXTREMA = (2.30, 20.0)

PLACE = "recife_boa_viagem"
LABEL = "Recife"
MODEL_RUN = "2026-09-19 12:00:00"

failures = []
total_checks = 0


def check(desc, cond):
    global total_checks
    total_checks += 1
    status = "OK" if cond else "FALHOU"
    print(f"[{status}] {desc}")
    if not cond:
        failures.append(desc)


def alerted_classes(sb):
    return [r["classe"] for r in sb.sent_alerts]


def with_default_subscriber(sb):
    sb.subscribers.append({
        "id": "padrao", "place_id": PLACE, "ativo": True, "nivel": "grande_extrema",
        "canal_email": True, "canal_sms": False, "email": "padrao@example.com", "telefone": None,
    })
    return sb


# --- 1. entrada em Grande -------------------------------------------------
sb = with_default_subscriber(FakeSupabase())
alerts.process_place(sb, PLACE, LABEL, [entry(*GRANDE)], MODEL_RUN)
check("1. entrada em Grande dispara alerta 'grande'", alerted_classes(sb) == ["grande"])
check("1. estado do local atualizado para classe 3 (grande)", sb.place_state[PLACE]["last_class"] == 3)

# --- 2. permanencia em Grande: sem duplicar -------------------------------
sb.sent_alerts.clear()
alerts.process_place(sb, PLACE, LABEL, [entry(*GRANDE)], MODEL_RUN)
check("2. permanencia em Grande nao reenvia", alerted_classes(sb) == [])

# --- 3. agravamento Grande -> Extrema --------------------------------------
sb.sent_alerts.clear()
alerts.process_place(sb, PLACE, LABEL, [entry(*EXTREMA)], MODEL_RUN)
check("3. agravamento para Extrema dispara alerta 'extrema'", alerted_classes(sb) == ["extrema"])
check("3. estado atualizado para classe 4 (extrema)", sb.place_state[PLACE]["last_class"] == 4)

# --- 4. entrada direta em Extrema (local novo, sem passar por Grande) -----
sb2 = with_default_subscriber(FakeSupabase())
alerts.process_place(sb2, PLACE, LABEL, [entry(*EXTREMA)], MODEL_RUN)
check("4. entrada direta em Extrema dispara so 'extrema' (nao 'grande' antes)",
      alerted_classes(sb2) == ["extrema"])

# --- 5. retorno a Normal e novo evento Grande posterior --------------------
sb.sent_alerts.clear()
alerts.process_place(sb, PLACE, LABEL, [entry(*NORMAL)], MODEL_RUN)
check("5a. retorno a Normal nao dispara alerta", alerted_classes(sb) == [])
check("5a. estado volta para classe 2 (normal)", sb.place_state[PLACE]["last_class"] == 2)
sb.sent_alerts.clear()
alerts.process_place(sb, PLACE, LABEL, [entry(*GRANDE)], MODEL_RUN)
check("5b. novo evento Grande dispara de novo apos ter voltado a Normal",
      alerted_classes(sb) == ["grande"])

# --- 6. filtro por nivel do assinante (Grande+Extrema vs so Extrema) ------
sb3 = FakeSupabase()
sb3.subscribers = [
    {"id": "u1", "place_id": PLACE, "ativo": True, "nivel": "grande_extrema",
     "canal_email": True, "canal_sms": False, "email": "amplo@example.com", "telefone": None},
    {"id": "u2", "place_id": PLACE, "ativo": True, "nivel": "extrema",
     "canal_email": True, "canal_sms": False, "email": "so_extrema@example.com", "telefone": None},
]
alerts.process_place(sb3, PLACE, LABEL, [entry(*GRANDE)], MODEL_RUN)
emails_notificados = {r["subscriber_id"] for r in sb3.sent_alerts}
check("6a. em evento Grande, so o assinante 'grande_extrema' e notificado",
      emails_notificados == {"u1"})
sb3.sent_alerts.clear()
alerts.process_place(sb3, PLACE, LABEL, [entry(*EXTREMA)], MODEL_RUN)
emails_notificados = {r["subscriber_id"] for r in sb3.sent_alerts}
check("6b. em evento Extrema, os dois assinantes sao notificados",
      emails_notificados == {"u1", "u2"})

# --- 8/9. formatacao de mensagem + envio sem credenciais (nao deve lancar) -
subject, body = alerts.format_alert(LABEL, "grande", entry(*GRANDE, hours_from_now=20))
check("8. assunto no formato esperado", subject == "ALERTA DE ONDAS GRANDES — PERNAMBUCO")
check("8. corpo contem 'Classificação das ondas: GRANDE'", "Classificação das ondas: GRANDE" in body)
check("8. corpo contem Energia em J/m² (nao kJ/m²)", "J/m²" in body and "kJ/m²" not in body)
lower_body = body.lower()
check("8. mensagem nao usa termos de aviso oficial",
      not any(w in lower_body for w in alerts.FORBIDDEN_WORDS))

# sem RESEND_API_KEY/Twilio no ambiente de teste -> deve retornar False, sem lancar excecao
os.environ.pop("RESEND_API_KEY", None)
os.environ.pop("TWILIO_ACCOUNT_SID", None)
ok_email = alerts.send_email(subject, body, "teste@example.com")
ok_sms = alerts.send_sms(body, "+5581999999999")
check("9. send_email sem credenciais retorna False sem lancar excecao", ok_email is False)
check("9. send_sms sem credenciais retorna False sem lancar excecao", ok_sms is False)

# --- classificacao pura (limiares) ----------------------------------------
check("limiares Hs: 1.74 e Normal, 1.75 e Grande, 2.15 e Extrema",
      alerts.classify_hs(1.74) == 2 and alerts.classify_hs(1.75) == 3 and alerts.classify_hs(2.15) == 4)
check("limiares Potencia: 11.40 e Normal, 11.41 e Grande, 18.24 e Extrema",
      alerts.classify_power(11.40) == 2 and alerts.classify_power(11.41) == 3 and alerts.classify_power(18.24) == 4)

print()
if failures:
    print(f"{len(failures)} teste(s) falharam:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print(f"Todos os {total_checks} testes sinteticos passaram.")
    print("Pendente de credenciais reais: cadastro->Supabase, envio real de e-mail (Resend) e SMS (Twilio), "
          "e o fluxo de descadastro via RPC do Postgres (nao coberto aqui por depender de um projeto Supabase real).")
