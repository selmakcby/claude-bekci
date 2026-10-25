"""Denetçinin kural listesi. Hepsi düz regex: model yok, ağ yok, bağımlılık yok.

Kendi kuralını eklemek için ilgili sözlüğe bir satır ekle.
"""
import re

# GİRİŞ: ajanın okuduğu içerikte (web sayfası, dosya, MCP cevabı) talimat kılığına girmiş metin.
ENJEKSIYON = {
    "önceki talimatları yok say": re.compile(
        r"(ignore|disregard|forget)\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts?)"
        r"|önceki\s+(tüm\s+)?(talimatlar|kurallar)\S*\s+(unut|yok\s+say|görmezden\s+gel)",
        re.IGNORECASE,
    ),
    # Ayraç (: , -) şart: "Claude not defteri", "note for the model card" gibi normal metin yakalanmasın.
    "yapay zekaya gizli not": re.compile(
        r"(note|message|instructions?)\s+(to|for)\s+(the\s+)?(ai|assistant|llm|agent|claude)\b[^\n:,\-]{0,30}[:,\-]"
        r"|(yapay\s+zeka|asistan|ajan|claude)\S*\s+(gizli\s+)?(not|talimat|mesaj)\S*\s*:",
        re.IGNORECASE,
    ),
    "kullanıcıdan gizleme": re.compile(
        r"(do\s+not|don't|never)\s+(tell|inform|mention\s+(this\s+)?to)\s+the\s+user"
        r"|kullanıcıya\s+(bundan\s+)?(söyleme|bahsetme)",
        re.IGNORECASE,
    ),
    "rol değiştirme": re.compile(
        r"you\s+are\s+now\s+(a|an|in)\b|new\s+system\s+prompt|<\s*/?\s*system\s*>|artık\s+sen\s+bir",
        re.IGNORECASE,
    ),
    "görünmez karakter": re.compile(r"[\u200b\u200c\u200d\u2060\ufeff\u202e]|[\U000e0000-\U000e007f]"),
}

# ÇIKIŞ: dışarı gitmemesi gereken sırlar.
SIR = {
    "Anthropic anahtarı": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}"),
    "OpenAI anahtarı": re.compile(r"\bsk-(proj-|svcacct-)?[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "AWS erişim anahtarı": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google anahtarı": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"),
    "Slack token": re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"),
    "özel anahtar": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}

# ÇIKIŞ: veriyi dışarı taşıyan komut kalıpları. Aralıklar sınırlı: uzun girdide yavaşlamasın.
_SIRLI = r"(\.env|id_rsa|id_ed25519|\.ssh/|\.aws/|credentials|secrets?/)"
SIZDIRMA = {
    "sır dosyası ağa gidiyor": re.compile(
        _SIRLI + r"[^\n|]{0,200}\|\s*(curl|wget|nc|ncat)\b"
        r"|(curl|wget)\b[^\n]{0,200}?(-d|--data\S*|-F|--form|--upload-file|-T)\s*['\"]?\S{0,40}?" + _SIRLI
        + r"|\$\(\s*cat\s+[^)]{0,100}?" + _SIRLI
        + r"|\b(scp|rsync)\b[^\n]{0,200}?" + _SIRLI
        + r"|" + _SIRLI + r"[^\n]{0,100}?>\s*/dev/(tcp|udp)/",
        re.IGNORECASE,
    ),
    "ortam değişkenleri dışarı paketleniyor": re.compile(
        r"\b(env|printenv|set)\b\s*\|\s*(curl|wget|nc|ncat|base64)\b", re.IGNORECASE
    ),
}

# ÇIKIŞ: engellenmez, kullanıcıya sorulur (meşru kurulum betikleri de böyle çalışır).
SOR = {
    "uzaktan betik çalıştırma": re.compile(
        r"(curl|wget)\s[^\n|]{0,300}\|\s*(sudo\s+)?((ba|z)?sh|python3?|node)\b", re.IGNORECASE
    ),
}


def bul(metin, kurallar):
    """Metinde eşleşen kural adlarını sırayla döndürür (tekrarsız)."""
    if not metin:
        return []
    return [ad for ad, desen in kurallar.items() if desen.search(metin)]
