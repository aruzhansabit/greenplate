import sys, json, re
import pdfplumber

DAY_MAP = {
    "PAZARTESİ": "Monday",
    "SALI": "Tuesday",
    "ÇARŞAMBA": "Wednesday",
    "PERŞEMBE": "Thursday",
    "CUMA": "Friday",
}

def clean(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def main(pdf_path: str, out_path: str):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    lines = [clean(x) for x in text.split("\n") if clean(x)]

    # Находим индексы заголовков дней
    idx = []
    for i, ln in enumerate(lines):
        up = ln.upper()
        for tr_day in DAY_MAP.keys():
            if up == tr_day:
                idx.append((i, tr_day))
    idx = sorted(idx, key=lambda x: x[0])

    # Если заголовки не нашлись, пробуем “мягкий поиск” (иногда заголовки идут с пробелами/декором)
    if not idx:
        for i, ln in enumerate(lines):
            up = ln.upper()
            for tr_day in DAY_MAP.keys():
                if tr_day in up and len(up) <= len(tr_day) + 6:
                    idx.append((i, tr_day))
        idx = sorted(idx, key=lambda x: x[0])

    days = {DAY_MAP[k]: [] for k in DAY_MAP.keys()}

    # Режем текст на блоки по дням и вытаскиваем блюда
    for j, (start_i, tr_day) in enumerate(idx):
        end_i = idx[j+1][0] if j+1 < len(idx) else len(lines)
        block = lines[start_i+1:end_i]

        # фильтруем мусор
        filtered = []
        for item in block:
            u = item.upper()
            if "ÖĞRENCİ" in u or "YEMEKHANE" in u: 
                continue
            if u.startswith("NOT:") or "DEĞİŞİKLİK" in u:
                continue
            if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}", item):
                continue
            filtered.append(item)

        # В твоём PDF по каждому дню обычно 6 строк (суп, основное, гарнир, овощ, салат, десерт/фрукт)
        # Берём первые 6 “адекватных” строк
        meals = [x for x in filtered if len(x) > 2][:6]

        days[DAY_MAP[tr_day]] = meals

    data = {
        "updated_at": None,
        "pdf_filename": "menu.pdf",
        "note": "Auto-updated and parsed from the official PDF (Mon–Fri).",
        "days": days
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
