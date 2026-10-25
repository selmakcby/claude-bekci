#!/usr/bin/env python3
"""ÇIKIŞ DENETÇİSİ — PreToolUse ve Stop hook.

PreToolUse: ajan bir komut çalıştırmadan, bir URL'ye gitmeden ya da bir MCP aracına
(Slack, mail, GitHub...) bir şey göndermeden önce argümanlar buradan geçer.
İçinde sır ya da sızdırma kalıbı varsa araç hiç çalışmaz.

Stop: ajan cevabını bitirdiğinde son mesajında sır varsa durmasına izin verilmez,
sırrı maskeleyip yeniden yazması istenir.

Sözleşme: her zaman exit 0. Temizse hiçbir şey basmaz.
"""
import json
import sys

try:
    from denetci.kurallar import SIR, SIZDIRMA, SOR, bul
    from denetci.kayit import yaz
except ImportError:  # hook olarak doğrudan çalıştırıldığında
    sys.path.insert(0, __file__.rsplit("/denetci/", 1)[0])
    from denetci.kurallar import SIR, SIZDIRMA, SOR, bul
    from denetci.kayit import yaz


def arac_karari(girdi):
    arac = girdi.get("tool_name", "?")
    metin = json.dumps(girdi.get("tool_input", {}), ensure_ascii=False)
    bulunan = bul(metin, SIR) + bul(metin, SIZDIRMA)
    if not bulunan:
        return _sor_karari(girdi, arac, metin)
    yaz(girdi.get("cwd"), {"denetci": "cikis", "arac": arac, "kurallar": bulunan})
    return {
        "systemMessage": f"🛡️ Çıkış denetçisi: {arac} engellendi ({', '.join(bulunan)})",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"ÇIKIŞ DENETÇİSİ: bu {arac} çağrısı dışarı veri taşıyor ({', '.join(bulunan)}). "
                "Engellendi. Başka bir yoldan deneme; kullanıcıya ne istendiğini ve neden durduğunu anlat."
            ),
        },
    }


def _sor_karari(girdi, arac, metin):
    bulunan = bul(metin, SOR)
    if not bulunan:
        return None
    yaz(girdi.get("cwd"), {"denetci": "cikis", "arac": arac, "kurallar": bulunan, "karar": "sor"})
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": f"ÇIKIŞ DENETÇİSİ: {', '.join(bulunan)}. Kaynağa güveniyorsan onayla.",
        },
    }


def son_mesaj_karari(girdi):
    if girdi.get("stop_hook_active"):
        return None  # bir kez geri yolladık, sonsuz döngüye girmeyelim
    mesaj = girdi.get("last_assistant_message")
    bulunan = bul(mesaj, SIR) if isinstance(mesaj, str) else []
    if not bulunan:
        return None
    yaz(girdi.get("cwd"), {"denetci": "cikis", "arac": "son-mesaj", "kurallar": bulunan})
    return {
        "decision": "block",
        "reason": (
            f"ÇIKIŞ DENETÇİSİ: son mesajında sır var ({', '.join(bulunan)}). "
            "Cevabını sırrın kendisini yazmadan, ilk ve son 4 karakteri dışında maskeleyerek yeniden yaz."
        ),
    }


def karar(girdi):
    olay = girdi.get("hook_event_name")
    if olay == "PreToolUse":
        return arac_karari(girdi)
    if olay == "Stop":
        return son_mesaj_karari(girdi)
    return None


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(girdi, dict):
        return 0
    try:
        cikti = karar(girdi)
    except Exception:  # denetçi hatası ajanı düşürmez
        return 0
    if cikti:
        print(json.dumps(cikti, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
