#!/usr/bin/env python3
"""Buduje slajdy etapu 1 na formatce wydziału (python-pptx).

    python etap1/build_slides.py --source-template ~/Downloads/preznainz.pptx

Z pełnej prezentacji-źródła zostaje tylko wzorzec z układami (zapis do etap1/formatka-wi.pptx,
bez slajdów i multimediów); na nim składane są slajdy. Treść pochodzi z utrwalonego protokołu
(cvbias/protocol.py), z surowych wyników próby uruchomienia (results/pilot) i z rysunków
(etap1/figures). Wzory są renderowane z notacji TeX (matplotlib mathtext) do PNG.

Zakres slajdów = wymagania etapu 1 z karty tematu i kontraktu (ok. 10 minut):
publikacja i problem, pytanie i hipotezy, obciążenie i zmienność + wzór CV, przykład ręczny,
generator / powtórzenia / ocena referencyjna, plan odtworzenia, eksperyment własny,
wykonalność i kontrola poprawności, ograniczenia + źródła + informacja 2A.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from lxml import etree  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cvbias import protocol as P  # noqa: E402

# --- paleta: tekst w odcieniach szarości, akcent granatowy, karty jasnoszare/jasnoniebieskie -----
FONT = "Arial"
INK = RGBColor(0x0B, 0x0B, 0x0B)
INK2 = RGBColor(0x52, 0x51, 0x4E)
MUTED = RGBColor(0x89, 0x87, 0x81)
NAVY = RGBColor(0x1F, 0x3A, 0x5F)
CARD = RGBColor(0xF3, 0xF5, 0xF8)
CARD_NAVY = RGBColor(0xE8, 0xEE, 0xF6)
ARROW = RGBColor(0xC3, 0xC2, 0xB7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ROW_ALT = RGBColor(0xF7, 0xF8, 0xFA)

# Obszar treści na slajdzie 13,333 × 7,5 cala: logotypy u góry, linia stopki na ~6,4 cala.
L, R_EDGE, TOP, BOTTOM = 0.92, 12.42, 1.85, 6.25
W = R_EDGE - L


# ---------------------------------------------------------------- pomocnicze: tekst i kształty
def set_bullet(paragraph, level: int, bullet: bool, indent: float = 0.24) -> None:
    pPr = paragraph._p.get_or_add_pPr()
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    if bullet:
        pPr.set("marL", str(int(Inches(indent * (level + 1)))))
        pPr.set("indent", str(-int(Inches(indent))))
        bu_font = etree.SubElement(pPr, qn("a:buFont"))
        bu_font.set("typeface", "Arial")
        bu_char = etree.SubElement(pPr, qn("a:buChar"))
        bu_char.set("char", "•" if level == 0 else "–")
    else:
        pPr.set("marL", str(int(Inches(indent * level))))
        pPr.set("indent", "0")
        etree.SubElement(pPr, qn("a:buNone"))


def add_text(slide, x, y, w, h, items, size=16, color=INK, anchor="top", line_spacing=1.08,
             space_after=6, align="left"):
    """Pole tekstowe. ``items``: napisy albo słowniki {text|runs, level, bullet, bold, color, size, align,
    space_before, space_after}; ``runs`` to lista (tekst, opcje)."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
    for i, item in enumerate(items):
        if isinstance(item, str):
            item = {"text": item}
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = line_spacing
        p.space_before = Pt(item.get("space_before", 0))
        p.space_after = Pt(item.get("space_after", space_after))
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[item.get("align", align)]
        for text, opts in item.get("runs") or [(item.get("text", ""), {})]:
            run = p.add_run()
            run.text = text
            font = run.font
            font.name = FONT
            font.size = Pt(opts.get("size", item.get("size", size)))
            font.bold = opts.get("bold", item.get("bold", False))
            font.italic = opts.get("italic", item.get("italic", False))
            font.color.rgb = opts.get("color", item.get("color", color))
        set_bullet(p, item.get("level", 0), item.get("bullet", False))
    return box


def add_title(slide, text: str, size: int | None = None) -> None:
    """Tytuł w jednej linii pod logotypami; dłuższe tytuły dostają mniejszy stopień pisma."""
    if size is None:
        size = 30 if len(text) <= 48 else 26
    title = slide.shapes.title
    title.left, title.top, title.width, title.height = Inches(L), Inches(0.8), Inches(W), Inches(0.9)
    tf = title.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.name, run.font.size, run.font.bold = FONT, Pt(size), False
    run.font.color.rgb = INK


def add_card(slide, x, y, w, h, fill=CARD):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = 0.07
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_arrow(slide, x, y, w, h, direction="right"):
    kind = MSO_SHAPE.RIGHT_ARROW if direction == "right" else MSO_SHAPE.DOWN_ARROW
    shape = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = ARROW
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_table(slide, data, x, y, w, col_widths, row_h=0.36, size=12, align=None, bold_last=False):
    """Tabela z granatowym nagłówkiem i naprzemiennym tłem wierszy; ``align`` to lista wyrównań kolumn."""
    rows, cols = len(data), len(data[0])
    shape = slide.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(row_h * rows))
    table = shape.table
    table.first_row, table.horz_banding = True, False
    for j, cw in enumerate(col_widths):
        table.columns[j].width = Inches(cw)
    for i in range(rows):
        table.rows[i].height = Inches(row_h)
        for j in range(cols):
            cell = table.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY if i == 0 else (WHITE if i % 2 else ROW_ALT)
            p = cell.text_frame.paragraphs[0]
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[(align or ["l"] * cols)[j]]
            run = p.add_run()
            run.text = str(data[i][j])
            run.font.name, run.font.size = FONT, Pt(size)
            run.font.bold = i == 0 or (bold_last and i == rows - 1)
            run.font.color.rgb = WHITE if i == 0 else INK
    return shape


def formula_png(tex: str, path: Path, fontsize: int = 30, color: str = "#0b0b0b") -> Path:
    """Renderuje wzór TeX do przezroczystego PNG (matplotlib mathtext, czcionka Computer Modern)."""
    plt.rcParams["mathtext.fontset"] = "cm"
    fig = plt.figure(figsize=(0.1, 0.1), dpi=300)
    fig.patch.set_alpha(0)
    fig.text(0, 0, f"${tex}$", fontsize=fontsize, color=color)
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    return path


def add_formula(slide, tex: str, x, y, h, build_dir: Path, name: str, fontsize: int = 30):
    path = formula_png(tex, build_dir / f"{name}.png", fontsize)
    return slide.shapes.add_picture(str(path), Inches(x), Inches(y), height=Inches(h))


def add_notes(slide, text: str) -> None:
    slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------- formatka
def make_blank_template(source: Path, target: Path) -> None:
    """Zostawia z prezentacji-źródła tylko wzorzec i układy (slajdy i multimedia znikają przy zapisie)."""
    prs = Presentation(str(source))
    sld_id_lst = prs.slides._sldIdLst
    for sld_id in list(sld_id_lst):
        prs.part.drop_rel(sld_id.rId)
        sld_id_lst.remove(sld_id)
    prs.save(str(target))


def pct(v: float) -> str:
    return f"{100 * v:.1f} %".replace(".", ",")


def num(v: float, nd: int = 3) -> str:
    return f"{v:.{nd}f}".replace(".", ",")


def signed(v: float, nd: int = 3) -> str:
    return ("+" if v >= 0 else "−") + num(abs(v), nd)


# ---------------------------------------------------------------- slajdy
def build(template: Path, out: Path, results: Path, figures: Path, build_dir: Path) -> None:
    prs = Presentation(str(template))
    lay = {layout.name: layout for layout in prs.slide_layouts}
    folds = pd.read_csv(results / "reproduction_folds.csv")
    summary = pd.read_csv(results / "reproduction_summary.csv")
    own_folds = pd.read_csv(results / "own_folds.csv")
    meta = json.loads((results / "meta.json").read_text(encoding="utf-8"))
    fits = P.planned_fits()
    gen, gen_imb = P.GENERATORS["balanced"], P.GENERATORS["imbalanced"]

    def new_slide(title: str):
        slide = prs.slides.add_slide(lay["Tylko tytuł"])
        add_title(slide, title)
        return slide

    # 1. Tytuł ------------------------------------------------------------------------------
    s = prs.slides.add_slide(lay["Slajd tytułowy"])
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(1.2), Inches(1.5), Inches(10.9), Inches(2.0)
    p = t.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "Obciążenie i zmienność oceny\nprzez walidację krzyżową"
    r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(44), INK
    sub = s.placeholders[1]
    sub.left, sub.top, sub.width, sub.height = Inches(1.2), Inches(3.75), Inches(10.9), Inches(2.4)
    tf = sub.text_frame
    lines = [
        ("Etap 1 — prezentacja tematu  ·  temat 06, obszar: metodologia eksperymentów", 18, INK2),
        ("R. Kohavi, A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection, IJCAI 1995", 15, MUTED),
        ("", 10, MUTED),
        ("Dariusz Salzburg (103931)  ·  Filip Sejud (103928)", 20, INK),
        ("Rozpoznawanie wzorców, studia II stopnia, 2026/2027, grupa 2  ·  29.10.2026", 15, INK2),
    ]
    for i, (text, size, color) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = text
        r.font.name, r.font.size, r.font.color.rgb = FONT, Pt(size), color
        set_bullet(p, 0, False)
    add_notes(s, "Temat 06 z karty tematów. Odtwarzamy pytanie z pracy Kohaviego (1995) w adaptacji: własny generator danych "
                 "i modele ze scikit-learn. Ok. 10 minut.")

    # 2. Publikacja i problem ----------------------------------------------------------------
    s = new_slide("Publikacja i problem")
    add_card(s, L, TOP, 6.6, 4.2)
    add_text(s, L + 0.2, TOP + 0.15, 6.2, 3.9, [
        {"text": "Kohavi (IJCAI 1995)", "bold": True, "size": 17, "color": NAVY, "space_after": 8},
        {"text": "Pytanie: jak dobrze walidacja krzyżowa (CV) i bootstrap szacują trafność klasyfikatora?", "bullet": True, "size": 15},
        {"text": "C4.5 i Naive‑Bayes na 7 zbiorach UCI, 50 powtórzeń; „prawdziwa” trafność z holdoutu na reszcie zbioru", "bullet": True, "size": 15},
        {"text": "CV zaniża trafność (pesymizm) — najbardziej dla k = 2 i 5; dla k = 10–20 prawie bez obciążenia", "bullet": True, "size": 15},
        {"text": "Największa wariancja dla k = 2; stratyfikacja zmniejsza obciążenie i wariancję", "bullet": True, "size": 15},
        {"text": "Zalecenie: 10‑krotna stratyfikowana CV", "bullet": True, "size": 15, "bold": True},
    ])
    add_text(s, L + 6.9, TOP, 4.6, 0.4, [{"text": "Co odtwarzamy, a co zmieniamy", "bold": True, "size": 15, "color": NAVY}])
    rows = [
        ["", "Kohavi", "My"],
        ["Pytanie", "obciążenie i wariancja CV vs k", "to samo"],
        ["Dane", "7 zbiorów UCI", "generator syntetyczny"],
        ["Modele", "C4.5, Naive‑Bayes", "CART, GaussianNB"],
        ["Odniesienie", "holdout, 50 powt.", "test N = 10 000, 30 powt."],
        ["k", "2, 5, 10, 20, LOO, bootstrap", "2, 5, 10"],
        ["Stratyfikacja", "klasy zbalansowane", "klasa rzadka 10 %"],
    ]
    add_table(s, rows, L + 6.9, TOP + 0.45, 4.6, [1.15, 1.9, 1.55], row_h=0.42, size=11.5)
    add_notes(s, "Kohavi mierzył trafność; my mierzymy błąd = 1 − trafność. Zamiana danych i modeli to adaptacja — cel "
                 "metodologiczny bez zmian.")

    # 3. Pytanie i hipotezy ------------------------------------------------------------------
    s = new_slide("Pytanie badawcze i hipotezy")
    add_text(s, L, TOP, W, 0.75, [
        {"text": "Jak liczba części walidacji krzyżowej wpływa na obciążenie i zmienność szacowanego błędu oraz co zmienia stratyfikacja przy niezbalansowanych klasach?", "size": 17, "bold": True, "color": NAVY},
    ])
    cards = [
        ("P1 · liczba foldów k = 2, 5, 10", [
            "H1: ê_CV zawyża błąd (pesymizm) najbardziej dla k = 2, bo model w foldzie uczy się tylko na n/2 obiektów; dla k = 10 obciążenie bliskie zera.",
            "H1′: zmienność ê_CV jest największa dla k = 2.",
            "H1″: efekty silniejsze dla CART (model niestabilny) niż dla GaussianNB (stabilny).",
        ]),
        ("P2 · stratyfikacja przy klasie rzadkiej (10 %)", [
            "H2: stratyfikowane 5‑foldowe CV ma mniejszą zmienność niż zwykłe i nie daje foldów bez klasy rzadkiej.",
            "H2′: obciążenie podobne — rozmiar treningu w foldzie jest taki sam.",
        ]),
    ]
    for i, (head, bullets) in enumerate(cards):
        x = L + i * 5.9
        add_card(s, x, TOP + 1.0, 5.6, 3.2, CARD if i == 0 else CARD_NAVY)
        items = [{"text": head, "bold": True, "size": 16, "color": NAVY, "space_after": 8}]
        items += [{"text": b, "size": 14.5, "bullet": True, "space_after": 8} for b in bullets]
        add_text(s, x + 0.2, TOP + 1.12, 5.2, 3.0, items)
    add_notes(s, "Hipotezy wynikają z krzywej uczenia (mniej danych → większy błąd) i z niestabilności modelu. "
                 "Wynik negatywny nie obniża oceny, jeśli procedura jest poprawna.")

    # 4. Obciążenie i zmienność ------------------------------------------------------------------
    s = new_slide("Obciążenie i zmienność estymatora błędu")
    add_card(s, L, TOP, W, 1.15)
    add_text(s, L + 0.2, TOP + 0.08, 3.5, 0.4, [{"text": "Błąd prawdziwy modelu C", "bold": True, "size": 15, "color": NAVY}])
    add_formula(s, r"e(C) = P\left(C(X) \neq Y\right)", L + 0.25, TOP + 0.5, 0.42, build_dir, "f_true", 26)
    add_text(s, L + 4.3, TOP + 0.05, W - 4.5, 1.05, [
        {"text": "Prawdopodobieństwo pomyłki na nowym obiekcie z tego samego rozkładu. Nieznane — przybliżamy je błędem e_test modelu na dużym, niezależnym teście T (N = 10 000).", "size": 14, "color": INK2},
    ], anchor="middle")
    add_card(s, L, TOP + 1.3, W, 1.4, CARD_NAVY)
    add_text(s, L + 0.2, TOP + 1.38, 5.0, 0.4, [{"text": "Estymator ê_CV: obciążenie i zmienność", "bold": True, "size": 15, "color": NAVY}])
    add_formula(s, r"\mathrm{bias} = \mathrm{E}[\hat e_{CV}] - e_{test}, \qquad \mathrm{sd} = \sqrt{\mathrm{Var}[\hat e_{CV}]}",
                L + 0.25, TOP + 1.82, 0.5, build_dir, "f_bias_sd", 26)
    add_text(s, L + 6.6, TOP + 1.35, W - 6.8, 1.3, [
        {"text": "Obciążenie: błąd systematyczny — dodatnie = CV zawyża błąd (pesymizm). Zmienność: rozrzut ê_CV między powtórzeniami. Jedno nie wynika z drugiego.", "size": 14, "color": INK2},
    ], anchor="middle")
    add_text(s, L, TOP + 2.85, W, 1.3, [
        {"runs": [("Skąd pesymizm: ", {"bold": True}), ("model w foldzie uczy się na n(k−1)/k obiektów, nie na n (k = 2: 100, k = 5: 160, k = 10: 180 z 200). Mniej danych → większy błąd.", {})], "size": 14, "bullet": True, "space_after": 5},
        {"runs": [("Skąd zmienność: ", {"bold": True}), ("losowy zbiór treningowy i losowy podział na foldy.", {})], "size": 14, "bullet": True, "space_after": 5},
        {"runs": [("Jak liczymy: ", {"bold": True}), ("30 niezależnych zbiorów D_r → 30 różnic ê_CV,r − e_test,r; ich średnia = obciążenie, odchylenie standardowe = zmienność.", {})], "size": 14, "bullet": True},
    ])
    add_notes(s, "Pytanie kontrolne: czy niższa wariancja oznacza mniejsze obciążenie? Nie — to dwie różne składowe błędu "
                 "estymatora (MSE = bias² + wariancja). U Kohaviego bootstrap .632 ma niską wariancję i duże obciążenie.")

    # 5. Wzór CV i symbole -------------------------------------------------------------------
    s = new_slide("k‑krotna walidacja krzyżowa: wzór i symbole")
    add_formula(s, r"\hat e_{CV} = \frac{1}{k}\sum_{j=1}^{k} e_j, \qquad e_j = \frac{m_j}{|D_j|}",
                L + 0.3, TOP, 0.85, build_dir, "f_cv", 30)
    symbols = [
        ["Symbol", "Znaczenie"],
        ["D = D_1 ∪ … ∪ D_k", "zbiór treningowy (n = 200) podzielony losowo na k równych, rozłącznych części (foldów)"],
        ["C_−j", "model nauczony na wszystkich foldach poza j‑tym, czyli na n(k−1)/k obiektach"],
        ["m_j, e_j", "liczba pomyłek modelu C_−j na odłożonym foldzie D_j i ich odsetek e_j = m_j / |D_j|"],
        ["ê_CV", "średnia błędów foldów; przy równych foldach = wszystkie pomyłki / n"],
        ["e_test", "odsetek pomyłek modelu nauczonego na całym D, zmierzony na teście T (N = 10 000)"],
    ]
    add_table(s, symbols, L, TOP + 1.05, W, [2.3, W - 2.3], row_h=0.4, size=13)
    add_card(s, L, TOP + 3.6, W, 0.75, CARD_NAVY)
    add_text(s, L + 0.2, TOP + 3.62, W - 0.4, 0.7, [
        {"runs": [("Foldy nie są niezależnymi pomiarami: ", {"bold": True}), ("zbiory uczące C_−1 i C_−2 mają wspólne (k−2)/(k−1) obiektów (k = 10: 8 z 9). Dlatego powtórzeniem badania jest cały niezależny zbiór D_r, a nie fold.", {})], "size": 14, "color": INK},
    ], anchor="middle")
    add_notes(s, "Każdy obiekt jest dokładnie raz w foldzie testowym. k foldów = k dopasowań modelu. "
                 "Pytanie kontrolne 1: dziesięć foldów nie daje dziesięciu niezależnych pomiarów, bo zbiory uczące nakładają się w 8/9.")

    # 6. Przykład ręczny ---------------------------------------------------------------------
    ex = folds[(folds.rep == 1) & (folds.model == "gnb") & (folds.k == 5) & (folds.cv_type == "kfold")].sort_values("fold")
    ex_sum = summary[(summary.rep == 1) & (summary.model == "gnb") & (summary.k == 5)].iloc[0]
    s = new_slide("Przykład ręczny: średnia błędów foldów (D₁, GaussianNB, k = 5)")
    rows = [["Fold j", "Obiektów w foldzie", "Pomyłek", "e_j = pomyłki / obiekty"]]
    for _, row in ex.iterrows():
        rows.append([str(int(row.fold)), str(int(row.n_test)), str(int(row.n_errors)), f"{int(row.n_errors)} / {int(row.n_test)} = {num(row.error)}"])
    total_err, total_n = int(ex.n_errors.sum()), int(ex.n_test.sum())
    rows.append(["Razem", str(total_n), str(total_err), f"{total_err} / {total_n} = {num(total_err / total_n)}"])
    add_table(s, rows, L, TOP, 6.4, [1.0, 1.8, 1.3, 2.3], row_h=0.42, size=14, align=["c", "c", "c", "c"], bold_last=True)
    terms = " + ".join(num(e) for e in ex.error)
    add_card(s, L + 6.7, TOP, 4.8, 2.95, CARD_NAVY)
    add_text(s, L + 6.9, TOP + 0.12, 4.4, 2.8, [
        {"text": "Rachunek", "bold": True, "size": 16, "color": NAVY, "space_after": 8},
        {"runs": [("ê_CV = (", {}), (terms, {}), (f") / 5 = {num(ex_sum.e_cv)}", {"bold": True})], "size": 14, "space_after": 10},
        {"runs": [("e_test = ", {}), (num(ex_sum.e_test, 4), {"bold": True}), (" — GaussianNB nauczony na całym D₁ (200 obiektów), sprawdzony na T (10 000 obiektów)", {})], "size": 14, "space_after": 10},
        {"runs": [("ê_CV − e_test = ", {}), (signed(ex_sum["diff"], 4), {"bold": True}), ("  (tu: optymizm)", {"color": INK2})], "size": 14},
    ])
    add_text(s, L, TOP + 3.1, W, 1.1, [
        {"text": "Jedna różnica nic nie mówi — zależy od losowego D₁ i losowego podziału. Dopiero średnia i rozrzut 30 takich różnic (po jednej na zbiór D_r) dają obciążenie i zmienność.", "size": 14.5, "color": INK2, "bullet": True, "space_after": 6},
        {"text": f"Liczby z próby uruchomienia (results/pilot, {meta['timestamp'][:10]}). Błąd Bayesa generatora: 15,9 % — niżej zejść się nie da.", "size": 14.5, "color": INK2, "bullet": True},
    ])
    add_notes(s, "Do weryfikacji ustnej: policzyć średnią pięciu ułamków i pokazać, że 29/200 daje to samo. Ujemna różnica w jednym "
                 "zbiorze nie przeczy pesymistycznemu obciążeniu — obciążenie to średnia po wielu zbiorach.")

    # 7. Generator, powtórzenia, ocena referencyjna --------------------------------------------
    s = new_slide("Generator danych, powtórzenia i ocena referencyjna")
    add_formula(s, r"X \mid y \sim \mathcal{N}(\mu_y, I_{10}),\quad \mu_1 = -\mu_0 = \frac{\delta}{2}\,u,\quad u = \frac{1}{\sqrt{5}}(1,1,1,1,1,0,0,0,0,0),\quad \delta = 2",
                L + 1.3, TOP - 0.05, 0.5, build_dir, "f_gen", 28)
    img_h = 2.6
    img_w = img_h * 12.0 / 4.2    # proporcje rysunku z make_figures.py
    s.shapes.add_picture(str(figures / "generator.png"), Inches(L + (W - img_w) / 2), Inches(TOP + 0.5), height=Inches(img_h))
    add_text(s, L, TOP + 0.5 + img_h + 0.08, W, 1.1, [
        {"runs": [("Generator: ", {"bold": True}), (f"dwie klasy normalne, 5 cech informacyjnych + 5 szumu; błąd Bayesa Φ(−δ/2) = {pct(gen.bayes_error())} (π₁ = 0,5), {pct(gen_imb.bayes_error())} dla klasy rzadkiej (π₁ = 0,1).", {})], "size": 14, "bullet": True, "space_after": 5},
        {"runs": [("Powtórzenia: ", {"bold": True}), ("R = 30 niezależnych zbiorów D_r po n = 200 obiektów (ziarno 1000 + r).", {})], "size": 14, "bullet": True, "space_after": 5},
        {"runs": [("Ocena referencyjna: ", {"bold": True}), ("jeden zbiór testowy T, N = 10 000, osobne ziarno — służy tylko do oceny estymatora.", {})], "size": 14, "bullet": True},
    ])
    add_notes(s, "Parametry generatora ustalone a priori (znany błąd Bayesa), nie według testu. GaussianNB jest tu dobrze "
                 "wyspecyfikowany (stabilny), CART musi przybliżać granicę ukośną (niestabilny). Zmiana δ: większe δ → mniejszy błąd.")

    # 8. Plan odtworzenia (schemat) ---------------------------------------------------------
    s = new_slide("Plan odtworzenia: estymata CV kontra duży test")
    bx_h = 0.85
    row1_y, row2_y = TOP, TOP + 1.4

    def box(x, y, w, h, head, body, fill=CARD):
        add_card(s, x, y, w, h, fill)
        add_text(s, x + 0.12, y + 0.06, w - 0.24, h - 0.1, [
            {"text": head, "bold": True, "size": 13, "color": NAVY, "space_after": 2},
            {"text": body, "size": 11.5, "color": INK2},
        ])

    box(L, row1_y, 2.2, bx_h, "Generator", "ziarno 1000 + r dla D_r; ziarno 90001 dla T")
    add_arrow(s, L + 2.25, row1_y + 0.28, 0.35, 0.3)
    box(L + 2.65, row1_y, 2.3, bx_h, "D_r, r = 1…30", "n = 200 obiektów, klasy 50/50", CARD_NAVY)
    add_arrow(s, L + 5.0, row1_y + 0.28, 0.35, 0.3)
    box(L + 5.4, row1_y, 3.1, bx_h, "CV, k ∈ {2, 5, 10}", "KFold(shuffle, ziarno 2000 + r); te same podziały dla obu modeli")
    add_arrow(s, L + 8.55, row1_y + 0.28, 0.35, 0.3)
    box(L + 8.95, row1_y, 2.55, bx_h, "ê_CV,r,k", "średnia błędów k foldów", CARD_NAVY)
    add_arrow(s, L + 3.65, row1_y + bx_h + 0.04, 0.3, 0.46, "down")
    box(L + 2.65, row2_y, 2.3, bx_h, "Model na całym D_r", "jedno dopasowanie, 200 obiektów")
    add_arrow(s, L + 5.0, row2_y + 0.28, 0.35, 0.3)
    box(L + 5.4, row2_y, 3.1, bx_h, "Test T", "N = 10 000, ten sam generator; tylko do oceny")
    add_arrow(s, L + 8.55, row2_y + 0.28, 0.35, 0.3)
    box(L + 8.95, row2_y, 2.55, bx_h, "e_test,r", "odsetek pomyłek na T", CARD_NAVY)
    add_arrow(s, L + 10.1, row2_y + bx_h + 0.05, 0.3, 0.38, "down")
    add_card(s, L, row2_y + bx_h + 0.48, W, 0.8, CARD_NAVY)
    add_text(s, L + 0.2, row2_y + bx_h + 0.5, W - 0.4, 0.76, [
        {"runs": [("Δ_r = ê_CV,r − e_test,r", {"bold": True}), ("   →   dla każdego k i modelu 30 wartości Δ: średnia = obciążenie, odchylenie standardowe = zmienność", {})], "size": 14},
    ], anchor="middle")
    add_text(s, L, row2_y + bx_h + 1.4, W, 0.8, [
        {"runs": [("Modele: ", {"bold": True}), ("GaussianNB() i CART = DecisionTreeClassifier(random_state=0), parametry domyślne scikit‑learn 1.8.0. ", {}),
                  ("Metryka: ", {"bold": True}), ("odsetek pomyłek. ", {}), ("Ziarna, rozmiary i k utrwalone w ", {}), ("cvbias/protocol.py", {"bold": True}), (".", {})], "size": 14, "color": INK2},
    ])
    add_notes(s, "Czego nie wolno wybierać według dużego testu: parametrów modeli, generatora ani wariantu CV — T służy tylko do oceny. "
                 "Wskazanie w kodzie: experiment.run_series.")

    # 9. Eksperyment własny ----------------------------------------------------------------
    s = new_slide("Eksperyment własny: stratyfikacja przy klasie rzadkiej (≈ 10 %)")
    add_card(s, L, TOP, 5.6, 4.3)
    add_text(s, L + 0.2, TOP + 0.15, 5.2, 4.1, [
        {"text": "Plan", "bold": True, "size": 16, "color": NAVY, "space_after": 8},
        {"text": "Ten sam generator z π₁ = 0,1: ok. 20 obiektów klasy rzadkiej na 200; osobne 30 zbiorów D_r i osobny test T′ (N = 10 000).", "size": 14.5, "bullet": True, "space_after": 8},
        {"text": "Na tym samym D_r: KFold(5) i StratifiedKFold(5) z tym samym ziarnem — różni się tylko przydział obiektów do foldów.", "size": 14.5, "bullet": True, "space_after": 8},
        {"text": "Miary: odsetek pomyłek, czułość klasy rzadkiej, liczba foldów bez klasy rzadkiej.", "size": 14.5, "bullet": True, "space_after": 8},
        {"text": "Fold bez klasy rzadkiej → czułość nieokreślona: zapisujemy jako brak wyniku z powodem.", "size": 14.5, "bullet": True, "bold": True},
    ])
    own1 = own_folds[(own_folds.rep == 1) & (own_folds.model == "gnb")]
    kf = own1[own1.cv_type == "kfold"].sort_values("fold")
    st = own1[own1.cv_type == "stratified"].sort_values("fold")
    rows = [["Fold", "KFold: klasa rzadka w foldzie", "Stratified: klasa rzadka w foldzie"]]
    for (_, a), (_, b) in zip(kf.iterrows(), st.iterrows()):
        rows.append([str(int(a.fold)), str(int(a.n_test_class1)), str(int(b.n_test_class1))])
    n_rare_d1 = int(own1.n_train_class1.iloc[0] + own1.n_test_class1.iloc[0])
    add_text(s, L + 5.9, TOP, 5.6, 0.5, [{"text": f"Próba uruchomienia, D₁ ({n_rare_d1} obiektów klasy rzadkiej na 200), foldy po 40", "size": 13, "color": INK2}])
    add_table(s, rows, L + 5.9, TOP + 0.55, 5.6, [0.8, 2.4, 2.4], row_h=0.4, size=13, align=["c", "c", "c"])
    n_missing = int(own_folds[own_folds.cv_type == "kfold"].missing_class_test.sum())
    n_missing_s = int(own_folds[own_folds.cv_type == "stratified"].missing_class_test.sum())
    add_text(s, L + 5.9, TOP + 3.05, 5.6, 1.2, [
        {"text": f"Już w 3 zbiorach próby: zwykły KFold dał fold bez klasy rzadkiej ({n_missing} raz), stratyfikowany — {n_missing_s} razy.", "size": 13.5, "color": INK2, "bullet": True},
    ])
    add_notes(s, "Stratyfikacja nie zmienia rozmiaru treningu, więc obciążenie podobne; usuwa losowość udziału klas między foldami, "
                 "więc zmniejsza zmienność. Czułość dodajemy, bo przy 10 % klasy rzadkiej błąd 0/1 jest zdominowany przez klasę większościową.")

    # 10. Wykonalność i kontrola poprawności ------------------------------------------------
    s = new_slide("Wykonalność: próba uruchomienia i kontrola poprawności")
    tiles = [
        (str(meta["fits_performed"]), "dopasowań w próbie", "3 zbiory, oba eksperymenty"),
        (f"{num(meta['elapsed_seconds'], 2)} s", "czas próby na CPU", "zwykły laptop, bez GPU"),
        (f"{fits['total']} / {fits['budget']}", "dopasowań w pełnej serii", "budżet z karty tematu"),
    ]
    for i, (big, label, sub) in enumerate(tiles):
        x = L + i * 3.9
        add_card(s, x, TOP, 3.7, 1.4, CARD_NAVY)
        add_text(s, x + 0.15, TOP + 0.08, 3.4, 0.7, [{"text": big, "size": 32, "bold": True, "color": NAVY, "align": "center"}], anchor="middle")
        add_text(s, x + 0.15, TOP + 0.78, 3.4, 0.6, [
            {"text": label, "size": 12, "color": INK2, "align": "center", "space_after": 0},
            {"text": sub, "size": 12, "color": MUTED, "align": "center", "space_after": 0},
        ])
    add_text(s, L, TOP + 1.6, 5.6, 2.7, [
        {"text": "Środowisko i uruchomienie", "bold": True, "size": 15, "color": NAVY, "space_after": 5},
        {"text": f"Python {meta['versions']['python']}, numpy {meta['versions']['numpy']}, scikit‑learn {meta['versions']['scikit-learn']}", "size": 14, "bullet": True, "space_after": 5},
        {"text": "python run_experiment.py --reps 3 --out results/pilot", "size": 13, "bullet": True, "color": INK2, "space_after": 5},
        {"text": "Zapisujemy: błąd i skład klas każdego foldu (CSV), podsumowania, meta.json z wersjami, ziarnami i liczbą dopasowań", "size": 14, "bullet": True, "space_after": 5},
        {"text": "Kod i wyniki: github.com/FylyppS/rozpoznawanie-wzorcow", "size": 14, "bullet": True},
    ])
    add_text(s, L + 5.9, TOP + 1.6, 5.6, 2.7, [
        {"text": "Kontrola poprawności", "bold": True, "size": 15, "color": NAVY, "space_after": 5},
        {"text": "Duży test tylko do oceny estymatora — nie dobieramy według niego parametrów modeli ani generatora", "size": 14, "bullet": True, "space_after": 5},
        {"text": "Te same zbiory D_r i te same podziały dla wszystkich wariantów CV i obu modeli", "size": 14, "bullet": True, "space_after": 5},
        {"text": "Ziarna, rozmiary, k, metryki utrwalone przed badaniem (cvbias/protocol.py)", "size": 14, "bullet": True, "space_after": 5},
        {"text": "Brak przecieku: model w foldzie widzi tylko D ∖ D_j; T ma osobne ziarno", "size": 14, "bullet": True},
    ])
    add_notes(s, "Mała próba potwierdza działający generator, kod i budżet. Pełna seria to sekundy — ryzykiem nie jest obliczenie, "
                 "lecz poprawność protokołu.")

    # 11. Ograniczenia, źródła, informacja o AI ---------------------------------------------
    s = new_slide("Ograniczenia planu, źródła i informacja o AI")
    add_card(s, L, TOP, 5.6, 4.3)
    add_text(s, L + 0.2, TOP + 0.15, 5.2, 4.1, [
        {"text": "Ograniczenia", "bold": True, "size": 16, "color": NAVY, "space_after": 8},
        {"text": "Dane syntetyczne o rozkładzie zgodnym z założeniami GaussianNB — wyniki dla NB mogą być „zbyt ładne”.", "size": 14, "bullet": True, "space_after": 7},
        {"text": "Jeden wspólny test T dla wszystkich powtórzeń (słaba korelacja e_test,r; mała przy N = 10 000).", "size": 14, "bullet": True, "space_after": 7},
        {"text": "R = 30 → błąd standardowy obciążenia ≈ sd/√30 (≈ 0,5 p.p.); małe efekty mogą być nieodróżnialne od zera.", "size": 14, "bullet": True, "space_after": 7},
        {"text": "U Kohaviego „prawdziwa” trafność z holdoutu i próbki z jednego zbioru też nie są bez wad — nasz test z generatora jest czystszy.", "size": 14, "bullet": True},
    ])
    add_card(s, L + 5.9, TOP, 5.6, 4.3, CARD_NAVY)
    add_text(s, L + 6.1, TOP + 0.15, 5.2, 4.1, [
        {"text": "Źródła", "bold": True, "size": 16, "color": NAVY, "space_after": 6},
        {"text": "R. Kohavi, A Study of Cross-Validation and Bootstrap for Accuracy Estimation and Model Selection, IJCAI 1995 — ai.stanford.edu/~ronnyk/accEst.pdf", "size": 13, "bullet": True, "space_after": 5},
        {"text": "scikit-learn 1.8.0: KFold, StratifiedKFold, GaussianNB, DecisionTreeClassifier", "size": 13, "bullet": True, "space_after": 5},
        {"text": "Karta tematu 06 i kontrakt przedmiotu (Moodle PO)", "size": 13, "bullet": True, "space_after": 12},
        {"text": "Informacja o AI (załącznik 2A, wariant 1)", "bold": True, "size": 16, "color": NAVY, "space_after": 6},
        {"text": "Poziom 2 — AI jako wsparcie pracy. Narzędzie: Claude (Anthropic) w Claude Code — pomoc w analizie publikacji, szkic protokołu i kodu, redakcja slajdów. Kod uruchomiony i sprawdzony przez nas; liczby pochodzą z faktycznych obliczeń. Pełna informacja w załączonym PDF.", "size": 13, "color": INK2},
    ])
    add_notes(s, "Praca autora (Kohavi): pytanie, definicje, schemat porównania. Nasz wkład: generator, protokół, kod, eksperyment własny.")

    # 12. Zapas: pytania kontrolne ------------------------------------------------------------
    s = new_slide("Slajd zapasowy: pytania kontrolne z karty tematu")
    qa = [
        ("Dlaczego dziesięć foldów nie daje dziesięciu niezależnych pomiarów?",
         "Zbiory uczące kolejnych foldów pokrywają się w 8/9; każdy obiekt współtworzy 9 z 10 modeli, więc błędy foldów są skorelowane. Niezależne są dopiero powtórzenia na osobnych zbiorach D_r."),
        ("Czy niższa wariancja oznacza mniejsze obciążenie?",
         "Nie. To osobne składowe błędu estymatora (MSE = obciążenie² + wariancja). Bootstrap .632 u Kohaviego: niska wariancja, obciążenie do 9,8 p.p.; leave-one-out: prawie nieobciążone, wysoka wariancja."),
        ("Czego nie wolno wybierać według dużego testu?",
         "Parametrów modeli, parametrów generatora ani wariantu CV. Duży test ocenia estymator; każdy wybór „pod” T zamieniłby ocenę referencyjną w zbiór walidacyjny i zaniżył mierzony błąd."),
    ]
    for i, (q, a) in enumerate(qa):
        y = TOP + i * 1.5
        add_card(s, L, y, W, 1.35, CARD if i % 2 == 0 else CARD_NAVY)
        add_text(s, L + 0.2, y + 0.08, W - 0.4, 1.25, [
            {"text": q, "bold": True, "size": 15, "color": NAVY, "space_after": 3},
            {"text": a, "size": 13.5, "color": INK2},
        ])
    add_notes(s, "Slajd na pytania po prezentacji.")

    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    print(f"zapisano {out} ({len(prs.slides)} slajdów)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-template", type=Path, default=None, help="pełna prezentacja z formatką (np. ~/Downloads/preznainz.pptx)")
    parser.add_argument("--template", type=Path, default=ROOT / "etap1/formatka-wi.pptx")
    parser.add_argument("--out", type=Path, default=ROOT / "etap1/slajdy-etap1.pptx")
    parser.add_argument("--results", type=Path, default=ROOT / "results/pilot")
    parser.add_argument("--figures", type=Path, default=ROOT / "etap1/figures")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/slides")
    args = parser.parse_args()

    args.build_dir.mkdir(parents=True, exist_ok=True)
    if args.source_template is not None or not args.template.exists():
        source = args.source_template or Path.home() / "Downloads/preznainz.pptx"
        make_blank_template(source, args.template)
        print(f"formatka bez slajdów: {args.template}")
    build(args.template, args.out, args.results, args.figures, args.build_dir)


if __name__ == "__main__":
    main()
