"""Vẽ lịch tháng (dương + âm lịch Việt Nam) thành BMP 1-bit 480x800 cho màn hình ngủ CrossPoint.

    python tools/render.py [--date YYYY-MM-DD] [--out THU_MUC]

Thuật toán âm lịch: Hồ Ngọc Đức (múi giờ UTC+7).
"""
import argparse
import calendar
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ───────────────────────── Âm lịch ─────────────────────────
TZ = 7
PI = math.pi


def jdn(d, m, y):
    a = (14 - m) // 12
    y, m = y + 4800 - a, m + 12 * a - 3
    return d + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _new_moon(k):
    T = k / 1236.85
    T2, T3, dr = T * T, T * T * T, PI / 180
    jd1 = 2415020.75933 + 29.53058868 * k + 0.0001178 * T2 - 0.000000155 * T3
    jd1 += 0.00033 * math.sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    s = math.sin
    C1 = (0.1734 - 0.000393 * T) * s(M * dr) + 0.0021 * s(2 * dr * M)
    C1 += -0.4068 * s(Mpr * dr) + 0.0161 * s(dr * 2 * Mpr)
    C1 -= 0.0004 * s(dr * 3 * Mpr)
    C1 += 0.0104 * s(dr * 2 * F) - 0.0051 * s(dr * (M + Mpr))
    C1 -= 0.0074 * s(dr * (M - Mpr)) - 0.0004 * s(dr * (2 * F + M))
    C1 -= 0.0004 * s(dr * (2 * F - M)) + 0.0006 * s(dr * (2 * F + Mpr))
    C1 += 0.0010 * s(dr * (2 * F - Mpr)) + 0.0005 * s(dr * (2 * Mpr + M))
    if T < -11:
        dt = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
    else:
        dt = -0.000278 + 0.000265 * T + 0.000262 * T2
    return jd1 + C1 - dt


def _new_moon_day(k):
    return math.floor(_new_moon(k) + 0.5 + TZ / 24)


def _sun_longitude(day):
    T = (day - 0.5 - TZ / 24 - 2451545.0) / 36525
    T2, dr = T * T, PI / 180
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T2 - 0.00000048 * T * T2
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T2
    DL = (1.914600 - 0.004817 * T - 0.000014 * T2) * math.sin(dr * M)
    DL += (0.019993 - 0.000101 * T) * math.sin(dr * 2 * M) + 0.000290 * math.sin(dr * 3 * M)
    L = (L0 + DL) * dr
    L -= PI * 2 * math.floor(L / (PI * 2))
    return math.floor(L / PI * 6)


def _month11(yy):
    k = math.floor((jdn(31, 12, yy) - 2415021) / 29.530588853)
    nm = _new_moon_day(k)
    return _new_moon_day(k - 1) if _sun_longitude(nm) >= 9 else nm


def _leap_offset(a11):
    k = math.floor((a11 - 2415021.076998695) / 29.530588853 + 0.5)
    i, arc = 1, _sun_longitude(_new_moon_day(k + 1))
    while True:
        last, i = arc, i + 1
        arc = _sun_longitude(_new_moon_day(k + i))
        if arc == last or i >= 14:
            return i - 1


def lunar(d, m, y):
    """(ngày, tháng, năm, nhuận) âm lịch của ngày dương d/m/y."""
    day = jdn(d, m, y)
    k = math.floor((day - 2415021.076998695) / 29.530588853)
    start = _new_moon_day(k + 1)
    if start > day:
        start = _new_moon_day(k)
    a11 = b11 = _month11(y)
    if a11 >= start:
        ly, a11 = y, _month11(y - 1)
    else:
        ly, b11 = y + 1, _month11(y + 1)
    diff = math.floor((start - a11) / 29)
    leap, lm = False, diff + 11
    if b11 - a11 > 365:
        off = _leap_offset(a11)
        if diff >= off:
            lm, leap = diff + 10, diff == off
    if lm > 12:
        lm -= 12
    if lm >= 11 and diff < 4:
        ly -= 1
    return day - start + 1, lm, ly, leap


CAN = "Giáp Ất Bính Đinh Mậu Kỷ Canh Tân Nhâm Quý".split()
CHI = "Tý Sửu Dần Mão Thìn Tỵ Ngọ Mùi Thân Dậu Tuất Hợi".split()


def canchi_year(ly):
    return f"{CAN[(ly + 6) % 10]} {CHI[(ly + 8) % 12]}"


def canchi_month(lm, ly):
    return f"{CAN[(ly * 12 + lm + 3) % 10]} {CHI[(lm + 1) % 12]}"


def canchi_day(d, m, y):
    j = jdn(d, m, y)
    return f"{CAN[(j + 9) % 10]} {CHI[(j + 1) % 12]}"


def selfcheck():
    assert lunar(17, 2, 2026) == (1, 1, 2026, False)  # Tết Bính Ngọ
    assert lunar(6, 2, 2027) == (1, 1, 2027, False)  # Tết Đinh Mùi
    assert lunar(29, 1, 2025) == (1, 1, 2025, False)  # Tết Ất Tỵ
    assert lunar(25, 7, 2025) == (1, 6, 2025, True)  # nhuận tháng 6/2025
    assert lunar(22, 3, 2023) == (1, 2, 2023, True)  # nhuận tháng 2/2023
    assert lunar(21, 1, 1985) == (1, 1, 1985, False)  # Tết 1985: VN sớm hơn TQ 1 tháng
    assert canchi_year(2026) == "Bính Ngọ" and canchi_day(1, 1, 2000) == "Mậu Ngọ"


# ───────────────────────── Ngày lễ ─────────────────────────
SOLAR_EVENTS = {
    (1, 1): "Tết Dương lịch", (14, 2): "Lễ Tình nhân", (8, 3): "Quốc tế Phụ nữ",
    (30, 4): "Giải phóng miền Nam", (1, 5): "Quốc tế Lao động", (1, 6): "Quốc tế Thiếu nhi",
    (2, 9): "Quốc khánh", (20, 10): "Phụ nữ Việt Nam", (20, 11): "Nhà giáo Việt Nam",
    (22, 12): "Quân đội Nhân dân", (25, 12): "Giáng sinh",
}
LUNAR_EVENTS = {
    (1, 1): "Tết Nguyên Đán", (2, 1): "Mùng 2 Tết", (3, 1): "Mùng 3 Tết",
    (15, 1): "Rằm tháng Giêng", (10, 3): "Giỗ Tổ Hùng Vương", (15, 4): "Phật Đản",
    (5, 5): "Tết Đoan Ngọ", (15, 7): "Vu Lan", (15, 8): "Tết Trung Thu",
    (23, 12): "Ông Công Ông Táo",
}


def event(d, m, y):
    ld, lm, _, leap = lunar(d, m, y)
    return SOLAR_EVENTS.get((d, m)) or (None if leap else LUNAR_EVENTS.get((ld, lm)))


# ───────────────────────── Vẽ ─────────────────────────
W, H, MX = 480, 800, 24
FONTS = Path(__file__).parent / "fonts"
MONTHS = "Một Hai Ba Tư Năm Sáu Bảy Tám Chín Mười,Mười Một,Mười Hai".replace(" ", ",").replace("Mười,Một", "Mười Một").replace("Mười,Hai", "Mười Hai").split(",")
LMONTHS = ["Giêng"] + MONTHS[1:11] + ["Chạp"]
WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def font(weight, size):
    return ImageFont.truetype(str(FONTS / f"BeVietnamPro-{weight}.ttf"), size)


def render(today):
    y, m = today.year, today.month
    img = Image.new("1", (W, H), 1)
    g = ImageDraw.Draw(img)

    def text(xy, s, f, anchor="la", fill=0):
        g.text(xy, s, font=f, anchor=anchor, fill=fill)

    # Đầu trang: số tháng thật lớn bên trái, tên tháng / năm / năm âm bên phải
    text((MX - 4, 150), f"{m:02d}", font("ExtraBold", 136), "ls")
    text((W - MX, 62), "THÁNG " + MONTHS[m - 1].upper(), font("SemiBold", 21), "rs")
    text((W - MX, 112), str(y), font("ExtraBold", 46), "rs")
    text((W - MX, 146), "Năm " + canchi_year(lunar(today.day, m, y)[2]), font("Regular", 19), "rs")

    # Dải thứ trong tuần
    top = 178
    g.rounded_rectangle((MX, top, W - MX, top + 34), 8, fill=0)
    cw = (W - 2 * MX) / 7
    for i, name in enumerate(["T2", "T3", "T4", "T5", "T6", "T7", "CN"]):
        text((MX + cw * (i + 0.5), top + 17), name, font("SemiBold", 16), "mm", 1)

    # Lưới ngày
    weeks = calendar.Calendar(0).monthdayscalendar(y, m)
    gy, gh = top + 46, 440
    ch = min(84, gh / len(weeks))
    f_day, f_sun = font("SemiBold", 27), font("ExtraBold", 27)
    f_lun, f_lun1 = font("Regular", 14), font("SemiBold", 14)
    events = []
    for r, week in enumerate(weeks):
        if r:
            for x in range(MX + 4, W - MX - 4, 6):  # đường chấm ngăn tuần
                g.point((x, round(gy + r * ch)), 0)
        for c, d in enumerate(week):
            if not d:
                continue
            x0, y0 = MX + c * cw, gy + r * ch
            cx, cy = x0 + cw / 2, y0 + ch / 2
            ld, lm, _, leap = lunar(d, m, y)
            first = ld == 1 or d == 1
            ltxt = f"{ld}/{lm}{'n' if leap else ''}" if first else str(ld)
            ev = event(d, m, y)
            if ev:
                events.append((d, ev))
            is_today = d == today.day
            box = (x0 + 4, y0 + 5, x0 + cw - 4, y0 + ch - 5)
            if is_today:
                g.rounded_rectangle(box, 10, fill=0)
            elif ev:
                g.rounded_rectangle(box, 10, outline=0, width=2)
            ink = 1 if is_today else 0
            text((cx, cy - 9), str(d), f_sun if c == 6 else f_day, "mm", ink)
            text((cx, cy + 19), ltxt, f_lun1 if first else f_lun, "mm", ink)

    # Chân trang: hôm nay + ngày lễ trong tháng
    fy = round(gy + len(weeks) * ch) + 14
    g.line((MX, fy, W - MX, fy), fill=0, width=2)
    ld, lm, ly, leap = lunar(today.day, m, y)
    text((MX, fy + 14), f"{WEEKDAYS[today.weekday()]}, {today.day} tháng {m}", font("SemiBold", 20))
    text((MX, fy + 44),
         f"{ld} tháng {LMONTHS[lm - 1]}{' nhuận' if leap else ''} âm lịch · ngày {canchi_day(today.day, m, y)}",
         font("Regular", 16))
    ey = fy + 76
    upcoming = [e for e in events if e[0] >= today.day] or events[-1:]
    for d, name in upcoming:
        if ey + 20 > H - 12:
            break
        g.ellipse((MX + 1, ey + 7, MX + 8, ey + 14), fill=0)
        text((MX + 18, ey), f"{d}/{m}", font("SemiBold", 15))
        text((MX + 68, ey), name, font("Regular", 15))
        ey += 23
    return img


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", help="YYYY-MM-DD (mặc định: hôm nay theo giờ Việt Nam)")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    selfcheck()
    day = date.fromisoformat(a.date) if a.date else datetime.now(timezone(timedelta(hours=TZ))).date()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    img = render(day)
    img.save(out / "current.bmp")
    img.save(out / "preview.png")
    print("OK", day, out / "current.bmp")
