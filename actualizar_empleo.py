#!/usr/bin/env python3
"""Descarga la ENE desde SIMEL (INE, SDMX) y arma los archivos de datos del dashboard (serie completa desde 2010).

Uso:  python3 actualizar_empleo.py [--descargar] [--cache DIR] [--salida DIR] [--previo serie.json] [--ic AAAA-MM=inf,sup ...]
--previo conserva los márgenes de error de una serie anterior; --ic agrega o corrige el de un trimestre (inicio AAAA-MM).
Sin --descargar usa los CSV ya guardados en --cache.
Salidas (JSON, cada uno {"rows": [...]}): serie.json, regiones_t.json, sectores_t.json
"""
import argparse, json, os, subprocess, sys
import pandas as pd

BASE = "https://sdmx.ine.gob.cl/rest/data/CL01,DF_{}"
FLUJOS = ["TDES_SEXO", "OCU_SEXO", "DES_SEXO", "TOCU_SEXO", "TP_SEXO", "OCUINF_SEXO", "OCURAMA_RAMA_SEXO"]

REGIONES = [  # (codigo SIMEL, nombre, orden geografico norte->sur)
    ("15", "Arica y Parinacota", 1), ("01", "Tarapacá", 2), ("02", "Antofagasta", 3), ("03", "Atacama", 4),
    ("04", "Coquimbo", 5), ("05", "Valparaíso", 6), ("13", "Metropolitana", 7), ("06", "O'Higgins", 8),
    ("07", "Maule", 9), ("16", "Ñuble", 10), ("08", "Biobío", 11), ("09", "La Araucanía", 12),
    ("14", "Los Ríos", 13), ("10", "Los Lagos", 14), ("11", "Aysén", 15), ("12", "Magallanes", 16)]

RAMAS = {
    "A": "Agricultura y pesca", "B": "Minería", "C": "Industria manufacturera", "D": "Electricidad y gas",
    "E": "Agua y residuos", "F": "Construcción", "G": "Comercio", "H": "Transporte", "I": "Alojamiento y comidas",
    "J": "Información y comunicaciones", "K": "Finanzas y seguros", "L": "Inmobiliarias",
    "M": "Servicios profesionales", "N": "Servicios administrativos", "O": "Administración pública",
    "P": "Enseñanza", "Q": "Salud", "R": "Artes y entretenimiento", "S": "Otros servicios"}

MES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESL = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
        "noviembre", "diciembre"]

# Intervalos de confianza al 95 % publicados por el INE en sus notas estadísticas (no vienen en SIMEL).
IC_OH = {"2026-03": (8.8, 11.7), "2026-04": (9.2, 11.8), "2026-05": (9.2, 11.9),
         "2026-06": (9.5, 12.2), "2026-07": (9.6, 12.4)}


def descargar(cache):
    os.makedirs(cache, exist_ok=True)
    for f in FLUJOS:
        r = subprocess.run(["curl", "-sS", "-m", "300", BASE.format(f) + ",1.0?format=csv", "-o",
                            os.path.join(cache, f + ".csv"), "-w", "%{http_code}"], capture_output=True, text=True)
        if r.stdout.strip() != "200":
            sys.exit("Fallo la descarga de %s: %s %s" % (f, r.stdout, r.stderr))


def leer(cache, f):
    d = pd.read_csv(os.path.join(cache, f + ".csv"), dtype=str,
                    usecols=lambda c: c in ["AREA_REF", "SEXO", "RAMA", "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS"])
    d["v"] = d.OBS_VALUE.astype(float)
    d["t"] = d.TIME_PERIOD.str[:7]
    return d


def mes_mas(t, n):
    k = int(t[:4]) * 12 + (int(t[5:]) - 1) + n
    return "%04d-%02d" % (k // 12, k % 12 + 1)


def etiquetas(t):
    """Nombres del trimestre móvil en español: periodo (jul–sep 2026), corto (jul–sep 26), largo (julio–septiembre 2026)."""
    fin = mes_mas(t, 2)
    iy, fy = int(t[:4]), int(fin[:4])
    m0, m2 = int(t[5:]) - 1, int(fin[5:]) - 1
    if iy == fy:
        return ("%s–%s %d" % (MES[m0], MES[m2], fy), "%s–%s %02d" % (MES[m0], MES[m2], fy % 100),
                "%s–%s %d" % (MESL[m0], MESL[m2], fy))
    return ("%s %d–%s %d" % (MES[m0], iy, MES[m2], fy), "%s %02d–%s %02d" % (MES[m0], iy % 100, MES[m2], fy % 100),
            "%s %d–%s %d" % (MESL[m0], iy, MESL[m2], fy))


def r1(x):
    return None if pd.isna(x) else round(float(x), 1)


def ri(x):
    return None if pd.isna(x) else int(round(float(x)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--descargar", action="store_true")
    ap.add_argument("--cache", default="cache_sdmx")
    ap.add_argument("--salida", default="docs/data")
    ap.add_argument("--previo", default="docs/data/serie.json")
    ap.add_argument("--ic", action="append", default=[])
    a = ap.parse_args()
    if a.previo and os.path.exists(a.previo):
        for r in json.load(open(a.previo, encoding="utf-8"))["rows"]:
            if r.get("ic_lo") is not None and r["id"] not in IC_OH:
                IC_OH[r["id"]] = (r["ic_lo"], r["ic_hi"])
    for x in a.ic:
        k, v = x.split("=")
        lo, hi = v.split(",")
        IC_OH[k] = (float(lo), float(hi))
    if a.descargar:
        descargar(a.cache)
    os.makedirs(a.salida, exist_ok=True)

    TD = leer(a.cache, "TDES_SEXO"); OC = leer(a.cache, "OCU_SEXO"); DE = leer(a.cache, "DES_SEXO")
    TO = leer(a.cache, "TOCU_SEXO"); TP = leer(a.cache, "TP_SEXO"); IN = leer(a.cache, "OCUINF_SEXO")
    RA = leer(a.cache, "OCURAMA_RAMA_SEXO")

    def s(d, area, sexo="AS", rama=None):
        x = d[(d.AREA_REF == area) & (d.SEXO == sexo)]
        if rama is not None:
            x = x[x.RAMA == rama]
        return x.drop_duplicates("t").set_index("t").v

    ultimo = TD.t.max()
    periodos = sorted(TD[TD.AREA_REF == "06"].t.unique())

    S = {k: s(*v) for k, v in {
        "td_oh": (TD, "06"), "td_n": (TD, "_T"), "td_oh_f": (TD, "06", "F"), "td_oh_m": (TD, "06", "M"),
        "td_n_f": (TD, "_T", "F"), "td_n_m": (TD, "_T", "M"), "oc_oh": (OC, "06"), "oc_n": (OC, "_T"),
        "de_oh": (DE, "06"), "de_n": (DE, "_T"), "to_oh": (TO, "06"), "to_n": (TO, "_T"),
        "tp_oh": (TP, "06"), "tp_n": (TP, "_T"), "in_oh": (IN, "06"), "in_n": (IN, "_T"),
        "con_oh": (RA, "06", "AS", "F"), "con_n": (RA, "_T", "AS", "F")}.items()}

    def g(k, t):
        return S[k].get(t, float("nan"))

    serie = []
    for t in periodos:
        periodo, corto, largo = etiquetas(t)
        ic = IC_OH.get(t)
        oc_oh, oc_n = g("oc_oh", t), g("oc_n", t)
        serie.append({
            "id": t, "periodo": periodo, "corto": corto, "largo": largo,
            "tasa_oh": r1(g("td_oh", t)), "tasa_nac": r1(g("td_n", t)),
            "tasa_oh_f": r1(g("td_oh_f", t)), "tasa_oh_m": r1(g("td_oh_m", t)),
            "tasa_nac_f": r1(g("td_n_f", t)), "tasa_nac_m": r1(g("td_n_m", t)),
            "ic_lo": ic[0] if ic else None, "ic_hi": ic[1] if ic else None,
            "ocu_oh": ri(oc_oh), "ocu_nac": ri(oc_n), "des_oh": ri(g("de_oh", t)), "des_nac": ri(g("de_n", t)),
            "tocu_oh": r1(g("to_oh", t)), "tocu_nac": r1(g("to_n", t)),
            "tpar_oh": r1(g("tp_oh", t)), "tpar_nac": r1(g("tp_n", t)),
            "inf_oh": r1(g("in_oh", t) / oc_oh * 100), "inf_nac": r1(g("in_n", t) / oc_n * 100),
            "con_oh": ri(g("con_oh", t)), "con_nac": ri(g("con_n", t)),
        })

    # --- regiones x trimestre (una fila por región y trimestre, con todos los indicadores)
    regiones = []
    for cod, nom, geo in REGIONES:
        td, tf, tm = s(TD, cod), s(TD, cod, "F"), s(TD, cod, "M")
        oc, de, to, tp, inf = s(OC, cod), s(DE, cod), s(TO, cod), s(TP, cod), s(IN, cod)
        rf = RA[(RA.AREA_REF == cod) & (RA.SEXO == "AS") & (RA.RAMA == "F")].drop_duplicates("t").set_index("t")
        ro = s(RA, cod, "AS", "_T")
        for t in periodos:
            if t not in td.index:
                continue
            g_ = lambda x: x.get(t, float("nan"))
            o_ = g_(oc)
            fila = {"id": "%s|%s" % (cod, t), "t": t, "cod": cod, "region": nom, "geo": geo, "tasa": r1(td[t]),
                    "tasa_f": r1(g_(tf)), "tasa_m": r1(g_(tm)), "ocu": ri(o_), "des": ri(g_(de)),
                    "tocu": r1(g_(to)), "tpar": r1(g_(tp)), "inf": r1(g_(inf) / o_ * 100)}
            if t in rf.index:
                est = rf.OBS_STATUS.get(t)
                fila.update({"con_ocu": ri(rf.v[t]), "con_peso": r1(rf.v[t] / ro[t] * 100) if t in ro.index else None,
                             "con_est": est if isinstance(est, str) else ""})
            regiones.append(fila)

    # --- ramas de actividad por región x trimestre (formato ancho: 19 ramas en el orden de RAMAS)
    sectores = []
    claves = list(RAMAS)
    RA1 = RA[RA.SEXO == "AS"].drop_duplicates(["AREA_REF", "RAMA", "t"])
    idx = RA1.set_index(["AREA_REF", "RAMA", "t"])
    for area, cod in [("_T", "00")] + [(c, c) for c, _, _ in REGIONES]:   # "00" = país
        for t in periodos:
            if (area, "_T", t) not in idx.index:
                continue
            o, e = [], ""
            hay = False
            for k in claves:
                if (area, k, t) in idx.index:
                    v = idx.at[(area, k, t), "v"]
                    st = idx.at[(area, k, t), "OBS_STATUS"]
                    if pd.isna(v):
                        o.append(None); e += "."
                    else:
                        o.append(ri(v)); hay = True
                        e += st if isinstance(st, str) and st else "."
                else:
                    o.append(None); e += "."
            if hay:
                sectores.append({"id": "%s|%s" % (cod, t), "t": t, "cod": cod, "tot": ri(idx.at[(area, "_T", t), "v"]), "o": o, "e": e})

    for nombre, rows in (("serie", serie), ("regiones_t", regiones), ("sectores_t", sectores)):
        json.dump({"rows": rows}, open(os.path.join(a.salida, nombre + ".json"), "w", encoding="utf-8"),
                  ensure_ascii=False, separators=(",", ":"))
    print("ok", ultimo, "serie", len(serie), "regiones", len(regiones), "sectores", len(sectores))


if __name__ == "__main__":
    main()
