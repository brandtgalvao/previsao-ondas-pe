"""Sistema-piloto de alertas de ondas (classes Grande/Extrema).

Le assinantes ativos no Supabase, verifica a previsao das proximas 48h
de cada local, detecta ENTRADA/AGRAVAMENTO de classe (evento) e dispara
e-mail/SMS. Nao depende de nenhuma credencial para o resto do pipeline
funcionar: se SUPABASE_URL/SUPABASE_SERVICE_KEY nao estiverem configuradas,
`run_alerts` simplesmente nao faz nada (loga um aviso e retorna).

Classificacao usa os MESMOS limiares P2/ERA5 da Escala de Ondas em
Pernambuco ja publicada no site (site/app.js) - nao inventa nem
recalibra nada aqui, so replica em Python pra decidir o disparo.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import requests

WAVE_SCALE_CLASSES = ["muito_baixa", "baixa", "normal", "grande", "extrema"]
WAVE_SCALE_LABELS = {
    "muito_baixa": "Muito baixa",
    "baixa": "Baixa",
    "normal": "Normal",
    "grande": "GRANDE",
    "extrema": "EXTREMA",
}
GRANDE_IDX = WAVE_SCALE_CLASSES.index("grande")

# [P5, P25, P75, P95] - identicos ao site (site/app.js: WAVE_SCALE_THRESHOLDS)
HS_THRESHOLDS_M = [1.21, 1.38, 1.75, 2.15]
POWER_THRESHOLDS_KW_M = [4.95, 6.81, 11.41, 18.24]
ENERGY_THRESHOLDS_J_M2 = [914, 1204, 1914, 2900]

ALERT_WINDOW_HOURS = 48
SITE_BASE_URL = "https://brandtgalvao.github.io/previsao-ondas-pe"

FORBIDDEN_WORDS = ["perigo", "risco alto", "não navegar", "nao navegar", "aviso oficial"]


def classify_scale(value: float, thresholds: list[float]) -> int:
    p5, p25, p75, p95 = thresholds
    if value < p5:
        return 0
    if value < p25:
        return 1
    if value < p75:
        return 2
    if value < p95:
        return 3
    return 4


def classify_hs(hs_m: float) -> int:
    return classify_scale(hs_m, HS_THRESHOLDS_M)


def classify_power(power_kw_m: float) -> int:
    return classify_scale(power_kw_m, POWER_THRESHOLDS_KW_M)


def overall_class_idx(hs_m: float, power_kw_m: float) -> int:
    """Classificacao geral = maior classe entre Hs e Potencia (Energia fica
    de fora por ser derivada diretamente de Hs^2)."""
    return max(classify_hs(hs_m), classify_power(power_kw_m))


class SupabaseError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self, url: str, service_key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    def get(self, table: str, params: dict) -> list[dict]:
        r = requests.get(f"{self.base}/{table}", headers=self.headers, params=params, timeout=20)
        if not r.ok:
            raise SupabaseError(f"GET {table} falhou: {r.status_code} {r.text}")
        return r.json()

    def insert(self, table: str, rows: list[dict]) -> None:
        headers = {**self.headers, "Prefer": "return=minimal"}
        r = requests.post(f"{self.base}/{table}", headers=headers, json=rows, timeout=20)
        if not r.ok:
            raise SupabaseError(f"INSERT {table} falhou: {r.status_code} {r.text}")

    def upsert(self, table: str, rows: list[dict], on_conflict: str) -> None:
        headers = {**self.headers, "Prefer": "resolution=merge-duplicates,return=minimal"}
        r = requests.post(
            f"{self.base}/{table}", headers=headers, json=rows, timeout=20,
            params={"on_conflict": on_conflict},
        )
        if not r.ok:
            raise SupabaseError(f"UPSERT {table} falhou: {r.status_code} {r.text}")


def get_place_state(sb: SupabaseClient, place_id: str) -> int:
    rows = sb.get("place_state", {"place_id": f"eq.{place_id}", "select": "last_class"})
    if not rows:
        return 0
    return int(rows[0]["last_class"])


def set_place_state(sb: SupabaseClient, place_id: str, new_class_idx: int, event_id: str) -> None:
    sb.upsert(
        "place_state",
        [{
            "place_id": place_id,
            "last_class": new_class_idx,
            "last_event_id": event_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }],
        on_conflict="place_id",
    )


def get_active_subscribers(sb: SupabaseClient, place_id: str) -> list[dict]:
    return sb.get("subscribers", {"place_id": f"eq.{place_id}", "ativo": "eq.true", "select": "*"})


def peak_in_window(forecast: list[dict], window_hours: int = ALERT_WINDOW_HOURS) -> tuple[int, dict] | None:
    """Acha, dentre os passos nas proximas `window_hours`, o primeiro passo
    que atinge a maior classe geral encontrada na janela. Retorna
    (classe_idx, entrada_do_forecast) ou None se a janela nao tiver dados."""
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=window_hours)
    in_window = []
    for f in forecast:
        vt = datetime.fromisoformat(f["valid_time"].replace("Z", "+00:00"))
        if now <= vt <= end:
            in_window.append((vt, f))
    if not in_window:
        return None
    best_class = -1
    best_entry = None
    for vt, f in in_window:
        c = overall_class_idx(f["hs_m"], f["power_kw_m"])
        if c > best_class:
            best_class = c
            best_entry = f
    return best_class, best_entry


def _sanitize(text: str) -> str:
    lowered = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in lowered:
            raise ValueError(f"Mensagem de alerta contem termo proibido: '{word}'")
    return text


def format_alert(place_label: str, class_key: str, entry: dict) -> tuple[str, str]:
    """Monta (assunto, corpo) da mensagem, no formato pedido, sem termos de
    aviso meteorologico oficial (a escala e uma classificacao tecnica)."""
    vt = datetime.fromisoformat(entry["valid_time"].replace("Z", "+00:00")) - timedelta(hours=3)
    quando = f"{vt.day:02d}/{vt.month:02d} às {vt.hour:02d}h"
    classe_label = WAVE_SCALE_LABELS[class_key]
    titulo = "GRANDES" if class_key == "grande" else "EXTREMAS"

    subject = f"ALERTA DE ONDAS {titulo} — PERNAMBUCO"
    body = (
        f"{subject}\n\n"
        f"Local: {place_label}\n"
        f"Previsão: {quando}\n\n"
        f"Classificação das ondas: {classe_label}\n\n"
        f"Hs: {entry['hs_m']:.2f} m\n"
        f"Energia: {entry['energy_j_m2']:.0f} J/m²\n"
        f"Potência: {entry['power_kw_m']:.1f} kW/m\n\n"
        f"Referência: Escala de Ondas em Pernambuco — P2/ERA5."
    )
    return _sanitize(subject), _sanitize(body)


def unsubscribe_url(subscriber: dict) -> str:
    return f"{SITE_BASE_URL}/unsubscribe.html?id={subscriber['id']}&token={subscriber['unsubscribe_token']}"


def with_unsubscribe_footer(body: str, subscriber: dict) -> str:
    return f"{body}\n\nPara cancelar o recebimento: {unsubscribe_url(subscriber)}"


def send_email(subject: str, body: str, to_email: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY")
    from_addr = os.environ.get("RESEND_FROM", "alertas@previsao-ondas-pe.dev")
    if not api_key:
        print(f"  [email nao enviado - RESEND_API_KEY ausente] para {to_email}: {subject}")
        return False
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [to_email],
                "subject": subject,
                "text": body,
            },
            timeout=20,
        )
        if not r.ok:
            print(f"  [email FALHOU] {to_email}: {r.status_code} {r.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"  [email FALHOU] {to_email}: {e}")
        return False


def send_sms(body: str, to_phone: str) -> bool:
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_FROM_NUMBER")
    if not (sid and token and from_number):
        print(f"  [sms nao enviado - credenciais Twilio ausentes] para {to_phone}")
        return False
    try:
        r = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
            auth=(sid, token),
            data={"From": from_number, "To": to_phone, "Body": body},
            timeout=20,
        )
        if not r.ok:
            print(f"  [sms FALHOU] {to_phone}: {r.status_code} {r.text}")
            return False
        return True
    except requests.RequestException as e:
        print(f"  [sms FALHOU] {to_phone}: {e}")
        return False


def process_place(sb: SupabaseClient, place_id: str, place_label: str, forecast: list[dict],
                   model_run: str, dry_run: bool = False) -> None:
    result = peak_in_window(forecast)
    if result is None:
        return
    new_class_idx, entry = result
    if new_class_idx < GRANDE_IDX:
        # Mar tranquilo (Muito baixa/Baixa/Normal): nao e condicao de alerta.
        # Ainda assim registramos o estado, pra permitir um "novo evento
        # Grande" caso a condicao suba de novo depois.
        if not dry_run:
            set_place_state(sb, place_id, new_class_idx, str(uuid.uuid4()))
        return

    last_class_idx = 0 if dry_run else get_place_state(sb, place_id)
    if new_class_idx <= last_class_idx:
        return  # mesma classe ou downgrade dentro de Grande/Extrema: sem reenvio

    class_key = WAVE_SCALE_CLASSES[new_class_idx]
    event_id = str(uuid.uuid4())
    subject, body = format_alert(place_label, class_key, entry)

    subscribers = [] if dry_run else get_active_subscribers(sb, place_id)
    for sub in subscribers:
        wants_it = sub["nivel"] == "grande_extrema" or (sub["nivel"] == "extrema" and class_key == "extrema")
        if not wants_it:
            continue
        personal_body = with_unsubscribe_footer(body, sub) if "unsubscribe_token" in sub else body
        if sub.get("canal_email") and sub.get("email"):
            ok = send_email(subject, personal_body, sub["email"])
            sb.insert("sent_alerts", [_alert_log_row(sub, place_id, event_id, class_key, entry, model_run, "email", ok)])
        if sub.get("canal_sms") and sub.get("telefone"):
            ok = send_sms(personal_body, sub["telefone"])
            sb.insert("sent_alerts", [_alert_log_row(sub, place_id, event_id, class_key, entry, model_run, "sms", ok)])

    if not dry_run:
        set_place_state(sb, place_id, new_class_idx, event_id)


def _alert_log_row(sub: dict, place_id: str, event_id: str, class_key: str, entry: dict,
                    model_run: str, canal: str, ok: bool) -> dict:
    return {
        "subscriber_id": sub["id"],
        "place_id": place_id,
        "event_id": event_id,
        "classe": class_key,
        "valid_time": entry["valid_time"],
        "hs_m": entry["hs_m"],
        "energy_j_m2": entry["energy_j_m2"],
        "power_kw_m": entry["power_kw_m"],
        "model_run": model_run,
        "canal": canal,
        "status": "enviado" if ok else "falhou",
    }


def run_alerts(places_out: dict, points_out: dict, model_run: str) -> None:
    """Chamado pelo build_forecast.py apos publicar o forecast.json. Nunca
    lanca excecao para fora - uma falha aqui nao pode derrubar a publicacao
    da previsao (que e a funcao critica do pipeline)."""
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not (url and service_key):
        print("Alertas: SUPABASE_URL/SUPABASE_SERVICE_KEY nao configurados - pulando etapa de alertas.")
        return

    try:
        sb = SupabaseClient(url, service_key)
        for place_id, place in places_out.items():
            gp = points_out[place["grid_point"]]
            process_place(sb, place_id, place["label"], gp["forecast"], model_run)
        print("Alertas: verificacao concluida.")
    except Exception as e:  # noqa: BLE001 - alertas nao podem derrubar o pipeline
        print(f"Alertas: erro nao fatal durante o processamento ({e}); previsao publicada normalmente.")
