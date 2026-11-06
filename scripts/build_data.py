#!/usr/bin/env python3
"""
Builds src/data/questions.json from the exam (5 variants x 20 questions).

The source PDF text is in a Latin-letter Georgian font encoding (e.g. "Semdegi" = "შემდეგი").
Text outside $...$ is converted to real Georgian Unicode; text inside $...$ is LaTeX (kept as-is).
Correct answers follow the highlighted answers in the exam PDF. Where a highlight contradicted
the mathematically correct answer, the correct one is used and the question is listed in the
printed report (see DISPUTED below).
"""
import json
import os
import re
import sys

MAP = {
    "a": "ა", "b": "ბ", "g": "გ", "d": "დ", "e": "ე", "v": "ვ", "z": "ზ", "T": "თ",
    "i": "ი", "k": "კ", "l": "ლ", "m": "მ", "n": "ნ", "o": "ო", "p": "პ", "J": "ჟ",
    "r": "რ", "s": "ს", "t": "ტ", "u": "უ", "f": "ფ", "q": "ქ", "R": "ღ", "y": "ყ",
    "S": "შ", "C": "ჩ", "c": "ც", "Z": "ძ", "w": "წ", "W": "ჭ", "x": "ხ", "j": "ჯ", "h": "ჰ",
}


def geo(s: str) -> str:
    parts = s.split("$")
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # inside $...$ -> LaTeX
            out.append("$" + part + "$")
        else:
            res = []
            for ch in part:
                if ch.isalpha():
                    if ch not in MAP:
                        raise ValueError(f"No mapping for {ch!r} in {s!r}")
                    res.append(MAP[ch])
                else:
                    res.append(ch)
            out.append("".join(res))
    return "".join(out)


LETTERS = "abgd"
CURRENT = []


def Q(prompt, opts, correct, disputed=None):
    assert len(opts) == 4, prompt
    CURRENT.append({
        "prompt": prompt, "opts": opts, "correct": LETTERS.index(correct), "disputed": disputed,
    })


# ---------- reusable formulas ----------
UNI = r"$X := a+(b-a)\gamma$"
LNPROD = r"$X=-\frac{1}{\lambda m}\cdot\ln\left[\prod_{i=1}^{m}\gamma_i\right]$"
FLOOR = r"$X := m+\lfloor\gamma(n-m+1)\rfloor$"
POIS = r"$X=\min\left\{i:\prod_{j=1}^{i}\gamma_j<e^{-\lambda}\right\}$"
SUMSEQ = r"$X=i \Leftrightarrow \sum_{j=1}^{i}\gamma_j\le 1\le\sum_{j=1}^{i+1}\gamma_j$"
BM = r"$X_1 := \sqrt{-2\ln\gamma_1}\cdot\cos(2\pi\gamma_2),\ \ X_2 := \sqrt{-2\ln\gamma_1}\cdot\sin(2\pi\gamma_2)$"
POLAR = (r"$X_1 := \eta_1 Y,\ X_2 := \eta_2 Y,\ Y := \sqrt{(-2\ln\xi)/\xi},\ "
         r"\xi=\eta_1^2+\eta_2^2,\ \eta_i=2\gamma_i-1$")

CHI = r"$\frac{k}{n}\sum_{j=1}^{k}\left(f_i-\frac{n}{k}\right)^{2}$"
CHI_NOK = r"$\sum_{j=1}^{k}\left(f_i-\frac{n}{k}\right)^{2}$"
CHI_2N = r"$\frac{k}{n}\sum_{j=1}^{k}\left(f_i-\frac{n}{k}\right)^{2n}$"
CHI_2N_NOK = r"$\sum_{j=1}^{k}\left(f_i-\frac{n}{k}\right)^{2n}$"
SER_D = (r"$\frac{k^d}{n}\sum_{j_1=1}^{k}\sum_{j_2=1}^{k}\cdots\sum_{j_d=1}^{k}"
         r"\left(f_{j_1,j_2,\dots,j_d}-\frac{n}{k^d}\right)^{2}$")
SER_BAD = (r"$\frac{k}{n}\sum_{j_1=1}^{k}\sum_{j_2=1}^{k}\cdots\sum_{j_d=1}^{k}"
           r"\left(f_{j_1,j_2,\dots,j_d}-\frac{n}{k}\right)^{2}$")
RUNS_A = r"$\frac{1}{n}\sum_{i=1}^{6}\sum_{j=1}^{6}a_{ij}(r_i-nb_i)(r_j-nb_j)$"
RUNS_NOA = r"$\frac{1}{n}\sum_{i=1}^{6}\sum_{j=1}^{6}(r_i-nb_i)(r_j-nb_j)$"

PP_A = r"$t_i := t_{i-1}-\frac{1}{\lambda}\ln\gamma$"
PP_B = r"$t_i := t_{i-1}-\frac{1}{\lambda m}\cdot\ln\left[\prod_{i=1}^{m}\gamma_i\right]$"
PP_G = r"$t_i := t_{i-1}-\frac{1}{\lambda}\ln\gamma(i-1)$"
PP_D = r"$t_i := t_{i-1}-\frac{n}{\lambda}\ln\gamma$"

T_STUD = r"$t=\frac{Y}{\sqrt{X}}\sqrt{m},\ Y\sim N(0;1),\ X=\chi^{2}(m)$"
T_12 = r"$t=\sum_{i=1}^{12}\gamma_i-6$"
CHI2 = r"$X=Y_1^2+Y_2^2+\dots+Y_m^2,\ Y_1,Y_2,\dots,Y_m\sim N(0,1)$"
T_LN = r"$t=-\frac{1}{\lambda m}\cdot\ln\left[\prod_{i=1}^{m}\gamma_i\right]$"
T_MIN = r"$t=\min\left\{i:\prod_{j=1}^{i}\gamma_j<e^{-\lambda}\right\}$"

LEH_A = r"$z_i=(az_{i-1}+c)\pmod m,\quad i=1,2,\dots$"
LEH_B = r"$z_i=(az_{i-1})\pmod m+c,\quad i=1,2,\dots$"
LEH_G = r"$z_i=(az_{i-1}^{2}+c)\pmod m,\quad i=1,2,\dots$"
LEH_D = r"$z_i=(az_{i-1}^{2}+bz_{i-1}+c)\pmod m,\quad i=1,2,\dots$"

MON_5_6 = r"$z_i=(5z_{i-1}+3)\pmod{16},\quad z_0=6$"
MON_5_7 = r"$z_i=(5z_{i-1}+3)\pmod{16},\quad z_0=7$"
MON_7_6 = r"$z_i=(7z_{i-1}+3)\pmod{16},\quad z_0=6$"
MON_7_7 = r"$z_i=(7z_{i-1}+3)\pmod{16},\quad z_0=7$"

MR_16807_OK = r"$m=2^{31}-1,\ a=16\,807$"
MR_630_OK = r"$m=2^{31}-1,\ a=630\,360\,016$"
MR_630_P1 = r"$m=2^{31}+1,\ a=630\,360\,016$"
MR_630_P0 = r"$m=2^{31},\ a=630\,360\,016$"
MR_16807_P0 = r"$m=2^{31},\ a=16\,807$"

INV_EXP = [
    r"$x=-\frac{1}{\lambda}\ln(1+\gamma)$",
    r"$x=-\frac{1}{\lambda+1}\ln\gamma$",
    r"$x=-\frac{1}{\lambda}\ln\gamma$",
    r"$x=\frac{1}{\lambda}\ln\gamma$",
]

STD_DETAIL = "sistemis kvlevis miznidan gamomdinare faqtorebisa da mdgomareobebis gansazRvra-SeTanxmeba "
EXP_NORMAL_UNI_BIN = ["eqsponencialuri;", "normaluri;", "Tanabari;", "binomialuri."]
TEST_STAT_SERIES = "generatorebis statistikuri testirebiT Semowmeba seriebis kriteriumiT mravalganzomilebian Tanabrobaze gulisxmobs Semdegi statistikis gamoTvlas:"
TEST_STAT_RUNS = "generatorebis statistikuri testirebiT zrdadi seriebis kriteriumiT Semowmeba damoukideblobaze gulisxmobs Semdegi kriteriumis gamoTvlas:"
TEST_STAT_UNI = "generatorebis statistikuri testirebiT Semowmeba Tanabar ganawilebaze gulisxmobs Semdegi kriteriumis gamoTvlas:"
SIM_ASPECTS = "simulaciuri modelebis klasifikaciis sam aspeqts miekuTvneba:"
CRYPTO = "farTod visi generatori gamoiyeneba kriptografiaSi?"
NORMAL = "normaluri ganawileba generirdeba formuliT:"
POISSON = "puasonis ganawileba generirdeba formuliT:"
BINOM = "binomialuri ganawileba generirdeba:"
BINOM_OPTS = [
    "puasonis SemTxveviTi sidideebis naxveviT;",
    "bernulis SemTxveviTi sidideebis naxveviT;",
    "bernulis SemTxveviTi sidideebis kompoziciiT;",
    "puasonis SemTxveviTi sidideebis kompoziciiT.",
]
BINOM_OPTS_5 = [
    "bernulis SemTxveviTi sidideebis naxveviT;",
    "puasonis SemTxveviTi sidideebis naxveviT;",
    "bernulis SemTxveviTi sidideebis kompoziciiT;",
    "puasonis SemTxveviTi sidideebis kompoziciiT.",
]

VARIANTS = []


def variant(n, fn):
    CURRENT.clear()
    fn()
    assert len(CURRENT) == 20, (n, len(CURRENT))
    VARIANTS.append((n, list(CURRENT)))


# =========================== VARIANT 1 ===========================
def v1():
    Q("ra aris sistemis detalizacia?", [
        STD_DETAIL + "sistemis menejerisa da modelis proeqtis avtorebis mier;",
        STD_DETAIL + "sistemis menejerisa da saxelmwifo samsaxurebis mier;",
        STD_DETAIL + "modelis proeqtis avtorebisa da saxelmwifo samsaxurebis mier;",
        STD_DETAIL + "sistemis direqtoratis mier.",
    ], "a")
    Q("masobrivi momsaxureobis sistemaSi (momsaxureobis erTi kvanZiT) momdevno moTxovnebis dadgomebs Soris dros ra tipis albaTuri ganawileba aqvs?",
      EXP_NORMAL_UNI_BIN, "a")
    Q(SIM_ASPECTS, ["statikuri Tu dinamikuri;", "statistikuri Tu stoqasturi;",
                    "uwyveti Tu warmoebadi;", "deterministuli Tu stacionaluri."], "a")
    Q("ra aris statistikuri mTvlelebi?", [
        "cvladebi, romlebSic inaxeba sistemis maxasiaTeblebze statistikuri informacia;",
        "cvladebi, romlebSic inaxeba sistemis mdgomareobaze statikuri an dinamikuri informacia;",
        "cvladebi, romlebSic inaxeba statistikuri informacia sistemis warsuli funqcionirebidan;",
        "cvladebi, romlebSic inaxeba statistikuri informacia sistemis modelis avtorebis Sesaxeb.",
    ], "a")
    Q("romeli qveprograma asrulebs sistemis mTvlelebis ganaxlebas?", [
        "sinqronizaciis programa;", "xdomilebaTa damuSavebis programa;",
        "inicializaciis programa;", "ZiriTadi programa."], "b")
    Q("romeli qveprograma asrulebs angariSebis Seqmnas?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "inicializaciis programa;", "arc erTi aq CamoTvlili."], "d")
    Q("ra aris sinqronizaciis programa?", [
        "qveprograma, romelsac simulaciuri modeli moyavs sawyis, nulovan mdgomareobaSi;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs nulovan mdgomareobaSi.",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs axali xdomilebis dadgomis droze;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdgar xdomilebebs da anaxlebs sistemis mdgomareobas."], "g")
    Q("lemeris generatoria:", [LEH_A, LEH_B, LEH_G, LEH_D], "a")
    Q("wanacvlebuli wkg-is gamoTvlebSi mamravlis pirdapiri gadamravlebis operacia icvleba:", [
        "bitebze moqmedi marjvniv Zvrisa da Sekrebis operaciebiT;",
        "mTeli ricxvebis gadavsebisa da gamravlebis operaciebiT;",
        "bitebze moqmedi marcxniv Zvrisa da Sekrebis operaciebiT;",
        "arc erTi aq CamoTvlili."], "g")
    Q("ratom ar aqvs multiplikatiur generators sruli periodi? radgan", [
        r"$m>0,\ c>0$", r"$m>0,\ c\ge 0$", r"$m>0,\ c=0$", "arc erTi aq CamoTvlili."], "g")
    Q("rodis miiRweva sruli periodi wrfiv kongruentul generatorSi?", [
        "Tu periodis sigrZe emTxveva wanacvlebas;", "Tu periodis sigrZe emTxveva moduls;",
        "Tu periodis sigrZe emTxveva mamravls;", "Tu periodis sigrZe emTxveva moduls minus erTi."], "b")
    Q("risi tolia periodis maqsimaluri mniSvneloba multiplikatiur generatorSi?",
      [r"$m$", r"$a-1$", r"$a$", r"$m-1$"], "d")
    Q(r"$b_i=(b_{i-r}+b_{i-q})\pmod 2$", [
        "esaa lekiueris generatori;", "esaa tausvortis generatori;",
        "esaa bleqbernis generatori;", "esaa marsesa da robertsis generatori;"], "b")
    Q(TEST_STAT_RUNS, [RUNS_A, CHI, SER_D, RUNS_NOA], "a")
    Q("sarekomendacio mniSvnelobebi marsesa da robertsis multiplikatiur wkg-Si:",
      [MR_16807_OK, MR_630_P1, MR_16807_P0, MR_630_P0], "a")
    Q("Sebrunebuli gardaqmnis algoriTmiT eqsponencialurad ganawilebuli SemTxveviTi sididis generireba gamoiTvleba formuliT:",
      INV_EXP, "g")
    Q(NORMAL, [UNI, LNPROD, POLAR, POIS], "g")
    Q("puasonis martivi procesi modelireba Semdegi formuliT:", [PP_A, PP_B, PP_G, PP_D], "a")
    Q("puasonis ganawileba miekuTvneba ganawilebis Semdeg tips:",
      ["uwyveti;", "diskretuli;", "dinamikuri;", "statikuri."], "b")
    Q(NORMAL, [LNPROD, FLOOR, SUMSEQ, BM], "d")


# =========================== VARIANT 2 ===========================
def v2():
    Q("masobrivi momsaxureobis sistemaSi (momsaxureobis erTi kvanZiT) moTxovnis momsaxureobis dros ra tipis albaTuri ganawileba aqvs?",
      EXP_NORMAL_UNI_BIN, "a")
    Q("ra aris xdomilebaTa sia?", [
        "sia, romelic Seicavs rigSi mdgomi moTxovnebis dadgomis dros;",
        "sia, romelic Seicavs rigSi mdgomi moTxovnebis momsaxureobaze gadasvlis drois momentebs;",
        "sia, romelic Seicavs yoveli Semdegi gansxvavebuli tipis xdomilebis dadgomis dros;",
        "sia, romelic Seicavs moTxovnebis momsaxureobidan gasvlis momentebs."], "g")
    Q(SIM_ASPECTS, ["deterministuli Tu stacionaluri;", "statistikuri Tu stoqasturi;",
                    "uwyveti Tu warmoebadi.", "deterministuli Tu stoqasturi;"], "d")
    Q("ra aris inicializaciis programa?", [
        "qveprograma, romelsac simulaciuri modeli moyavs saboloo, damamTavrebel mdgomareobaSi;",
        "qveprograma, romelsac simulaciuri modeli moyavs sawyis, nulovan mdgomareobaSi;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs axali xdomilebis dadgomis droze;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs nulovan mdgomareobaSi."], "b")
    Q("ra aris biblioTekuri programa?", [
        "qveprogramaTa krebuli, romelsac simulaciuri modeli moyavs sawyis, nulovan mdgomareobaSi;",
        "qveprogramaTa krebuli, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs axali xdomilebis dadgomis droze.",
        "qveprogramaTa krebuli, romelic gamoiyeneba SemTxveviTi dakvirvebaTa generaciisaTvis (romlebic gamoiyenebian simulaciur modelSi);",
        "qveprogramaTa krebuli, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs nulovan mdgomareobaSi."], "g")
    Q("romeli qveprograma asrulebs moTxovnis SefasebaTa gamoTvlas?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "inicializaciis programa;", "arc erTi aq CamoTvlili."], "d")
    Q("pirobebi parametrebze lemeris generatorSi:", [
        r"$m>0,\ \ m>a,\ \ m>c,\ \ m>z_0$",
        r"$m>0,\ \ m>a,\ \ m\le c,\ \ m>z_0$",
        r"$m>0,\ \ m\le a,\ \ m>c,\ \ m>z_0$",
        r"$m\ge 0,\ \ m>a,\ \ m>c,\ \ m>z_0$"], "a",
      disputed="PDF highlight was (d) m>=0; correct condition is m>0 (also highlighted as (a) in variant 4)")
    Q("romeli qveprograma asrulebs statistikuri mTvlelebis drois generirebas da maTi xdomilebaTa siaSi damatebas?", [
        "xdomilebaTa damuSavebis programa;", "sinqronizaciis programa;",
        "inicializaciis programa;", "ZiriTadi programa."], "a")
    Q("monahanis wkg-ia:", [MON_5_6, MON_7_7, MON_7_6, MON_5_7], "d")
    Q("sarekomendacio mniSvnelobebi marsesa da robertsis multiplikatiur wkg-Si:",
      [MR_630_OK, MR_630_P1, MR_630_P0, MR_16807_P0], "a")
    Q(r"$z_i=(z_{1i}-z_{2i})\pmod m$", [
        "esaa tausvortis generatori;", "esaa lekiueris generatori;",
        "esaa marsesa da robertsis generatori;", "esaa manCesteris generatori;"], "b")
    Q("marsesa da robertsis multiplikatiuri generatoris gamoTvlebSi pirdapiri gayofis nacvlad gamoiyeneba:", [
        "mTeli ricxvebis gadavsebis operacia;", "bitebze moqmedi marjvniv Zvris operacia;",
        "simulaciuri gayofa;", "arc erTi aq CamoTvlili."], "g")
    Q(CRYPTO, ["lekiueris;", "marsesa da robertsis;", "tausvortis;", "marselis."], "g")
    Q(TEST_STAT_UNI, [CHI_2N, CHI_NOK, CHI, CHI_2N_NOK], "g")
    Q(r"$X=Y_1+Y_2+\dots+Y_m$", [
        "aseTi sidide generirdeba kompoziciis meTodis algoriTmiT;",
        "aseTi sidide generirdeba Sebrunebuli gardaqmnis algoriTmiT;",
        "aseTi sidide generirdeba naxvevis meTodis algoriTmiT;",
        "aseTi sidide ar generirdeba arc erTi aq CamoTvliliT."], "a")
    Q(NORMAL, [BM, LNPROD, FLOOR, SUMSEQ], "a")
    Q(TEST_STAT_SERIES, [CHI, SER_BAD, SER_D, CHI_NOK], "g")
    Q(BINOM, BINOM_OPTS, "g")
    Q("stiudentis ganawilebis generireba xdeba formuliT:", [T_LN, T_STUD, T_12, T_MIN], "b")
    Q(POISSON, [UNI, LNPROD, FLOOR, POIS], "d")


# =========================== VARIANT 3 ===========================
def v3():
    Q("ra xdeba mds-is Cvenebaze?", [
        "drois Cveneba gadadis eqspertis mier miTiTebuli xdomilebis warmoqmnis droze;",
        "drois Cveneba gadadis sistemidan gasuli moTxovnis drois Cvenebaze;",
        "drois Cveneba gadadis Semdegi uaxloesi xdomilebis warmoqmnis droze;",
        "drois Cveneba gadadis sistemis muSaobis dasasrulze."], "g")
    Q("ra aris xdomilebaTa sia?", [
        "sia, romelic Seicavs yoveli Semdegi gansxvavebuli tipis xdomilebis dadgomis dros;",
        "sia, romelic Seicavs rigSi mdgomi moTxovnebis dadgomis dros;",
        "sia, romelic Seicavs rigSi mdgomi moTxovnebis momsaxureobaze gadasvlis drois momentebs;",
        "sia, romelic Seicavs moTxovnebis momsaxureobidan gasvlis momentebs."], "a")
    Q(SIM_ASPECTS, ["deterministuli Tu stacionaluri;", "statistikuri Tu stoqasturi;",
                    "uwyveti Tu diskretuli;", "uwyveti Tu warmoebadi."], "g")
    Q("romeli qveprograma asrulebs sistemis mdgomareobis ganaxlebas?", [
        "sinqronizaciis programa;", "inicializaciis programa;",
        "ZiriTadi programa.", "xdomilebaTa damuSavebis programa;"], "d")
    Q("romeli qveprograma asrulebs SemTxveviTi sidideebis generirebas?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "sinqronizaciis programa;", "inicializaciis programa."], "a")
    Q("ra aris angariSebis generatori?", [
        "qveprograma, romelic iTvlis statistikuri mTvlelebidan sistemis muSaobis kriteriumebis Sefasebebs da iZleva modelirebis dasrulebis angariSs;",
        "qveprograma, romelic periodulad iTvlis statistikuri mTvlelebidan sistemis muSaobis kriteriumebis Sefasebebs da iZleva modelirebis qronologiur angariSs;",
        "qveprograma, romelic iTvlis xdomilebaTa siaSi moTxovnebis dadgomis momentebs da iZleva Sesabamis angariSs;",
        "qveprograma, romelic iTvlis qveprogramaTa mimarTvebs da modelirebis dasrulebis Semdeg programis efeqturobaze iZleva angariSs."], "a")
    Q("romeli qveprograma asrulebs modeluri drois saaTis gadayvanas?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "sinqronizaciis programa;", "inicializaciis programa."], "g")
    Q("romelia yvelaze grZeli operacia wkg-Si?", [
        "mamravlze gamravleba;", "modulze gayofa da naSTis miReba;",
        "wanacvlebaze mimateba;", "arc erTi aq CamoTvlili."], "b")
    Q("gayofis swrafi Catarebis mizniT ra warmoadgens modulis karg arCevans wanacvlebuli wkg-Si?",
      [r"$m=2^{b}-1$", r"$m=2^{b-1}$", r"$m=2^{b}$", r"$m=2^{b}-2$"], "g")
    Q("wkg-is gamoyenebiT generirebuli SemTxveviTi ricxvebi Rebuloben mxolod Semdeg racionalur mniSvnelobebs:", [
        r"$0,\ \frac{1}{m},\ \frac{2}{m},\ \dots,\ \frac{m-1}{m}$",
        r"$0,\ \frac{1}{m},\ \frac{2}{m},\ \dots,\ \frac{m}{m}\equiv 1$",
        r"$\frac{1}{m},\ \frac{2}{m},\ \dots,\ \frac{m-1}{m}$",
        r"$\frac{1}{m},\ \frac{2}{m},\ \dots,\ \frac{m}{m}\equiv 1$"], "a")
    Q("rodis aris wkg multiplikatiuri generatori? roca",
      [r"$(c=0)$", r"$(c\ge 0)$", r"$(c\ne 0)$", "arc erTi aq CamoTvlili."], "a")
    Q("lekiueris rTul generatorSi periodi aRwevs Semdeg rigs:",
      [r"$2^{19}$", r"$2^{191}$", r"$2^{991}$", r"$2^{1991}$"], "b")
    Q(TEST_STAT_SERIES, [CHI, SER_BAD, SER_D, CHI_NOK], "g")
    Q(TEST_STAT_RUNS, [RUNS_A, CHI, SER_D, RUNS_NOA], "a",
      disputed="PDF highlight was (d), the formula without a_ij; the runs-up test statistic includes a_ij (as in variant 1)")
    Q("marsesa da robertsis multiplikatiuri generatoris gamoTvlebSi modulis rolSi iReben Semdeg gamosaxulebas:",
      [r"$2^{b}$", r"$2^{b}+m$", r"$2^{b}+a$", r"$2^{b}-q,\ q\in\mathbb{N}$"], "d")
    Q(r"$F(x)=\sum_{k=1}^{N}p_jF_j(x)$", [
        "aseTi ganawileba generirdeba Sebrunebuli gardaqmnis algoriTmiT;",
        "aseTi ganawileba generirdeba kompoziciis meTodis algoriTmiT;",
        "aseTi ganawileba generirdeba naxvevis meTodis algoriTmiT;",
        "aseTi ganawileba ar generirdeba arc erTi aq CamoTvliliT."], "b")
    Q("“xi-kvadrat”- ganawilebis generireba xdeba formuliT:", [UNI, LNPROD, CHI2, POIS], "g")
    Q("stiudentis ganawilebis generireba xdeba formuliT:", [T_LN, T_12, T_MIN, T_STUD], "d")
    Q("puasonis ganawileba miekuTvneba ganawilebis Semdeg tips:",
      ["diskretuli;", "uwyveti;", "statikuri;", "dinamikuri."], "a")
    Q("normaluri ganawilebis simulaciis miaxloebiTi meTodis generirebis formulaa:",
      [UNI, LNPROD, T_12.replace("t=", "x="), POIS], "g")


# =========================== VARIANT 4 ===========================
def v4():
    Q("masobrivi momsaxureobis sistemaSi (momsaxureobis erTi kvanZiT) momdevno moTxovnebis dadgomebs Soris dros ra tipis albaTuri ganawileba aqvs?",
      ["normaluri;", "eqsponencialuri;", "Tanabari;", "binomialuri."], "b")
    Q("ra aris statistikuri mTvlelebi?", [
        "cvladebi, romlebSic inaxeba sistemis mdgomareobaze statikuri an dinamikuri informacia;",
        "cvladebi, romlebSic inaxeba statistikuri informacia sistemis warsuli funqcionirebidan;",
        "cvladebi, romlebSic inaxeba sistemis maxasiaTeblebze statistikuri informacia;",
        "cvladebi, romlebSic inaxeba statistikuri informacia sistemis modelis avtorebis Sesaxeb."], "g")
    Q("diskretuli-xdomilebiTi modelirebis Sesrulebisas droSi sistemis mdgomareoba icvleba:",
      ["uwyvetad;", "TandaTanobiT;", "monotonurad.", "myisierad;"], "d")
    Q("ra aris sinqronizaciis programa?", [
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs axali xdomilebis dadgomis droze;",
        "qveprograma, romelsac simulaciuri modeli moyavs sawyis, nulovan mdgomareobaSi;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs nulovan mdgomareobaSi.",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdgar xdomilebebs da anaxlebs sistemis mdgomareobas."], "a")
    Q("romeli qveprograma asrulebs Semdegi tipis xdomilebis gansazRvras?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "sinqronizaciis programa;", "inicializaciis programa."], "g")
    Q("romeli qveprograma asrulebs moTxovnis SefasebaTa gamoTvlas?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "inicializaciis programa;", "arc erTi aq CamoTvlili."], "d")
    Q("pirobebi parametrebze lemeris generatorSi:", [
        r"$m>0,\ \ m>a,\ \ m>c,\ \ m>z_0$",
        r"$m>0,\ \ m>a,\ \ m\le c,\ \ m>z_0$",
        r"$m>0,\ \ m\le a,\ \ m>c,\ \ m>z_0$",
        r"$m\ge 0,\ \ m>a,\ \ m>c,\ \ m>z_0$"], "a")
    Q("ra aris angariSebis generatori?", [
        "qveprograma, romelic periodulad iTvlis statistikuri mTvlelebidan sistemis muSaobis kriteriumebis Sefasebebs da iZleva modelirebis qronologiur angariSs;",
        "qveprograma, romelic iTvlis xdomilebaTa siaSi moTxovnebis dadgomis momentebs da iZleva Sesabamis angariSs;",
        "qveprograma, romelic iTvlis statistikuri mTvlelebidan sistemis muSaobis kriteriumebis Sefasebebs da iZleva modelirebis dasrulebis angariSs;",
        "qveprograma, romelic iTvlis qveprogramaTa mimarTvebs da modelirebis dasrulebis Semdeg programis efeqturobaze iZleva angariSs."], "g")
    Q("rodis aris wkg wanacvlebuli generatori? roca",
      [r"$a>0$", r"$c>0$", r"$c>a$", r"$m>c$"], "b")
    Q("wanacvlebuli wkg-is gamoTvlebSi mamravlis pirdapiri gadamravlebis operaciis Sesrulebia icvleba:", [
        "bitebze moqmedi marcxniv Zvrisa da Sekrebis operaciebiT;",
        "bitebze moqmedi marjvniv Zvrisa da Sekrebis operaciebiT;",
        "mTeli ricxvebis gadavsebisa da gamravlebis operaciebiT;",
        "arc erTi aq CamoTvlili."], "a")
    Q("marsesa da robertsis multiplikatiuri generatoris gamoTvlebSi modulis rolSi iReben Semdeg gamosaxulebas:",
      [r"$2^{b}$", r"$2^{b}-q,\ q\in\mathbb{N}$", r"$2^{b}+m$", r"$2^{b}+a$"], "b")
    Q("wanacvlebuli wkg-is gamoTvlebSi modulze pirdapiri gayofis Sesrulebis operacia icvleba:", [
        "arc erTi aq CamoTvlili.", "bitebze moqmedi marjvniv Zvris operaciiT;",
        "mTeli ricxvebis gadavsebis operaciiT;", "bitebze moqmedi logikuri an-operaciiT."], "g")
    Q("lekiueris rTuli generatoria?", [
        r"$z_i=(z_{1i}-z_{2i})\pmod m$", r"$z_i=(z_{1i}+z_{2i})\pmod m$",
        r"$z_i=(z_{1i}\bullet z_{2i})\pmod m$", r"$z_i=(z_{1i}\div z_{2i})\pmod m$"], "a")
    Q(TEST_STAT_UNI, [CHI, CHI_2N, CHI_NOK, CHI_2N_NOK], "a")
    Q("intervalze uwyveti Tanabrad ganawilebuli SemTxveviTi sidide generirdeba formuliT:",
      [LNPROD, FLOOR, UNI, SUMSEQ], "g")
    Q("intervalze diskretuli Tanabrad ganawilebuli SemTxveviTi sidide generirdeba formuliT:",
      [UNI, LNPROD, FLOOR, SUMSEQ], "g")
    Q(CRYPTO, ["lekiueris;", "blumebisa da Subas;", "neskeensis;", "marsesa da robertsis."], "b")
    Q("“xi-kvadrat”- ganawilebis generireba xdeba formuliT:", [UNI, LNPROD, CHI2, POIS], "g")
    Q("erlangis ganawileba miekuTvneba ganawilebis Semdeg tips:",
      ["diskretuli;", "statikuri;", "uwyveti;", "dinamikuri."], "g")
    Q(NORMAL, [UNI, LNPROD, POLAR, POIS], "g",
      disputed="PDF highlight was (d), the Poisson formula; the Box-Muller polar method (g) generates the normal distribution")


# =========================== VARIANT 5 ===========================
def v5():
    Q("ra aris sistemis detalizacia?", [
        STD_DETAIL + "sistemis menejerisa da modelis proeqtis avtorebis mier;",
        STD_DETAIL + "sistemis menejerisa da saxelmwifo samsaxurebis mier;",
        STD_DETAIL + "modelis proeqtis avtorebisa da saxelmwifo samsaxurebis mier;",
        STD_DETAIL + "sistemis direqtoratis mier."], "a")
    Q("masobrivi momsaxureobis sistemaSi (momsaxureobis erTi kvanZiT) moTxovnis momsaxureobis dros ra tipis albaTuri ganawileba aqvs?",
      ["normaluri;", "Tanabari;", "binomialuri.", "eqsponencialuri;"], "d")
    Q("modeluri drois mimdinareobis ori midgomaa:", [
        "xdomilebidan xdomilebamde drois mimdinareoba da drois mimdinareoba uwyvetad;",
        "xdomilebidan xdomilebamde drois mimdinareoba da drois mimdinareoba mudmivi bijiT;",
        "xdomilebidan xdomilebamde drois mimdinareoba da drois mimdinareoba cvladi bijiT;",
        "xdomilebidan xdomilebamde drois mimdinareoba da drois mimdinareoba monotonuri bijiT;"], "b")
    Q("ra aris inicializaciis programa?", [
        "qveprograma, romelsac simulaciuri modeli moyavs sawyis, nulovan mdgomareobaSi;",
        "qveprograma, romelsac simulaciuri modeli moyavs saboloo, damamTavrebel mdgomareobaSi;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs axali xdomilebis dadgomis droze;",
        "qveprograma, romelic xdomilebaTa siaSi eZebs Semdeg xdomilebas da mds-s Cveneba gadayavs nulovan mdgomareobaSi."], "a")
    Q("romeli qveprograma asrulebs statistikuri mTvlelebis drois generirebas da maTi xdomilebaTa siaSi damatebas?", [
        "xdomilebaTa damuSavebis programa;", "sinqronizaciis programa;",
        "inicializaciis programa;", "ZiriTadi programa."], "a")
    Q("romeli qveprograma asrulebs Semdegi tipis xdomilebis gansazRvras?", [
        "biblioTekis programebi;", "xdomilebaTa damuSavebis programa;",
        "sinqronizaciis programa;", "inicializaciis programa."], "g")
    Q("lemeris generatoria:", [LEH_B, LEH_A, LEH_G, LEH_D], "b")
    Q("romeli qveprograma asrulebs sistemis mdgomareobis ganaxlebas?", [
        "xdomilebaTa damuSavebis programa;", "sinqronizaciis programa;",
        "inicializaciis programa;", "ZiriTadi programa."], "a")
    Q("monahanis wkg-ia:", [MON_5_6, MON_5_7, MON_7_7, MON_7_6], "b")
    Q("gayofis swrafi Catarebis mizniT ra warmoadgens modulis karg arCevans wanacvlebuli wkg-Si?",
      [r"$m=2^{b}$", r"$m=2^{b}-1$", r"$m=2^{b-1}$", r"$m=2^{b}-2$"], "a")
    Q("marsesa da robertsis multiplikatiuri generatoris gamoTvlebSi pirdapiri gayofis nacvlad gamoiyeneba:", [
        "mTeli ricxvebis gadavsebis operacia;", "simulaciuri gayofa;",
        "bitebze moqmedi marjvniv Zvris operacia;", "arc erTi aq CamoTvlili."], "b")
    Q("romelia yvelaze grZeli operacia wkg-Si?", [
        "mamravlze gamravleba;", "wanacvlebaze mimateba;",
        "arc erTi aq CamoTvlili.", "modulze gayofa da naSTis miReba;"], "d")
    Q(CRYPTO, ["lekiueris;", "tausvortis;", "marsesa da robertsis.", "fabregasis."], "b")
    Q(TEST_STAT_RUNS, [CHI, SER_D, RUNS_A, RUNS_NOA], "g",
      disputed="PDF highlight was (b), the multidimensional series statistic; the runs-up test statistic is the one with a_ij (as in variant 1)")
    Q("uwyveti Tanabari ganawileba Sualedze generirdeba formuliT:", [UNI, LNPROD, FLOOR, SUMSEQ], "a")
    Q(r"$b_i=(b_{i-r}+b_{i-q})\pmod 2$", [
        "esaa tausvortis generatori;", "esaa lekiueris generatori;",
        "esaa robertos generatori;", "esaa marsesa da robertsis generatori;"], "a")
    Q(POISSON, [UNI, LNPROD, FLOOR, SUMSEQ], "d")
    Q(BINOM, BINOM_OPTS_5, "g")
    Q("puasonis martivi procesi modelireba Semdegi formuliT:", [PP_B, PP_G, PP_A, PP_D], "g")
    Q(POISSON, [UNI, LNPROD, FLOOR, POIS], "d")


for n, fn in enumerate([v1, v2, v3, v4, v5], start=1):
    variant(n, fn)

# ---------- emit ----------
out = {"course": geo("modelireba da simulacia"), "variants": []}
disputed_report = []
for n, qs in VARIANTS:
    vq = []
    for i, q in enumerate(qs, start=1):
        item = {
            "id": f"v{n}-q{i}",
            "n": i,
            "prompt": geo(q["prompt"]),
            "options": [geo(o) for o in q["opts"]],
            "correct": q["correct"],
        }
        if q["disputed"]:
            disputed_report.append(f"Variant {n}, Q{i}: {q['disputed']}")
        vq.append(item)
    out["variants"].append({"id": n, "title": f"Variant {n}", "questions": vq})

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = os.path.join(root, "src", "data", "questions.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

total = sum(len(v["questions"]) for v in out["variants"])
print(f"Wrote {total} questions to {path}")
if disputed_report:
    print("Answer-key corrections (PDF highlight vs correct answer):")
    for line in disputed_report:
        print(" -", line)
