import pandas as pd

PLIK_CSV = "refurbed_prices.csv"


def wczytaj_dane(nazwa_pliku=PLIK_CSV):
    df = pd.read_csv(nazwa_pliku)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    if "cena_liczbowo" in df.columns:
        df["cena_liczbowo"] = pd.to_numeric(df["cena_liczbowo"], errors="coerce")

    if "prog_alertu" in df.columns:
        df["prog_alertu"] = pd.to_numeric(df["prog_alertu"], errors="coerce")

    return df


def policz_braki(df):
    return df.isna().sum().sort_values(ascending=False).to_dict()


def policz_pelne_duplikaty(df):
    if df.empty:
        return 0
    return int(df.duplicated(keep=False).sum())


def _dostepne_klucze(df, kandydaci):
    return [kolumna for kolumna in kandydaci if kolumna in df.columns]


def znajdz_duplikaty_w_tym_samym_pomiarze(df):
    kandydaci = [
        "data", "typ", "model", "kolor", "pamiec",
        "stan", "cena_liczbowo", "dostepnosc"
    ]
    klucze = _dostepne_klucze(df, kandydaci)

    if len(klucze) < 2:
        return pd.DataFrame(columns=df.columns)

    maska = df.duplicated(subset=klucze, keep=False)
    wynik = df.loc[maska].copy()

    if not wynik.empty:
        wynik = wynik.sort_values(klucze)

    return wynik


def znajdz_duplikaty_glownego_produktu(df):
    if "typ" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    glowny = df[df["typ"] == "glowny_produkt"].copy()
    if glowny.empty:
        return pd.DataFrame(columns=df.columns)

    kandydaci = ["data", "typ", "model", "cena_liczbowo", "url"]
    klucze = _dostepne_klucze(glowny, kandydaci)

    if len(klucze) < 2:
        return pd.DataFrame(columns=df.columns)

    maska = glowny.duplicated(subset=klucze, keep=False)
    wynik = glowny.loc[maska].copy()

    if not wynik.empty:
        wynik = wynik.sort_values(klucze)

    return wynik


def znajdz_duplikaty_sugerowanych_konfiguracji(df):
    if "typ" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    sugerowane = df[df["typ"] == "sugerowana_konfiguracja"].copy()
    if sugerowane.empty:
        return pd.DataFrame(columns=df.columns)

    kandydaci = [
        "data", "model", "kolor", "pamiec",
        "stan", "cena_liczbowo", "dostepnosc"
    ]
    klucze = _dostepne_klucze(sugerowane, kandydaci)

    if len(klucze) < 2:
        return pd.DataFrame(columns=df.columns)

    maska = sugerowane.duplicated(subset=klucze, keep=False)
    wynik = sugerowane.loc[maska].copy()

    if not wynik.empty:
        wynik = wynik.sort_values(klucze)

    return wynik



def znajdz_duplikaty_biznesowe(df):
    """
    Funkcja kompatybilności dla app.py v0.1.
    Zwraca duplikaty wykryte w ramach tego samego pomiaru.
    """
    return znajdz_duplikaty_w_tym_samym_pomiarze(df)

def policz_typy_rekordow(df):
    if "typ" not in df.columns:
        return {}

    return (
        df["typ"]
        .fillna("BRAK_TYPU")
        .astype(str)
        .value_counts()
        .to_dict()
    )


def znajdz_bledne_ceny(df, minimum=500, maksimum=5000):
    if "cena_liczbowo" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    maska = (
        df["cena_liczbowo"].isna()
        | (df["cena_liczbowo"] <= 0)
        | (df["cena_liczbowo"] < minimum)
        | (df["cena_liczbowo"] > maksimum)
    )

    return df.loc[maska].copy()


def znajdz_bledne_alerty(df):
    wymagane = {"cena_liczbowo", "prog_alertu", "alert"}
    if not wymagane.issubset(df.columns):
        return pd.DataFrame(columns=df.columns)

    roboczy = df.dropna(subset=["cena_liczbowo", "prog_alertu"]).copy()
    if roboczy.empty:
        return pd.DataFrame(columns=df.columns)

    roboczy["oczekiwany_alert"] = roboczy.apply(
        lambda wiersz: (
            "TAK"
            if wiersz["cena_liczbowo"] < wiersz["prog_alertu"]
            else "NIE"
        ),
        axis=1
    )

    maska = (
        roboczy["alert"].astype(str)
        != roboczy["oczekiwany_alert"].astype(str)
    )

    return roboczy.loc[maska].copy()


def znajdz_bledne_daty(df):
    if "data" not in df.columns:
        return pd.DataFrame(columns=df.columns)

    return df[df["data"].isna()].copy()


def policz_wynik_jakosci(df):
    if df.empty:
        return 0.0

    liczba_komorek = max(len(df) * max(len(df.columns), 1), 1)

    braki = int(df.isna().sum().sum())
    duplikaty_run = len(znajdz_duplikaty_w_tym_samym_pomiarze(df))
    bledne_ceny = len(znajdz_bledne_ceny(df))
    bledne_alerty = len(znajdz_bledne_alerty(df))
    bledne_daty = len(znajdz_bledne_daty(df))

    kara = braki + duplikaty_run + bledne_ceny + bledne_alerty + bledne_daty
    wynik = 100 - (kara / liczba_komorek * 100)

    return round(max(0.0, min(100.0, wynik)), 2)


def raport_jakosci(df):
    duplikaty_run = znajdz_duplikaty_w_tym_samym_pomiarze(df)
    duplikaty_glowny = znajdz_duplikaty_glownego_produktu(df)
    duplikaty_sugerowane = znajdz_duplikaty_sugerowanych_konfiguracji(df)

    return {
        "liczba_rekordow": int(len(df)),
        "liczba_kolumn": int(len(df.columns)),
        "typy_rekordow": policz_typy_rekordow(df),
        "pelne_duplikaty": policz_pelne_duplikaty(df),
        "duplikaty_w_tym_samym_pomiarze": int(len(duplikaty_run)),
        "duplikaty_biznesowe": int(len(duplikaty_run)),
        "duplikaty_glownego_produktu": int(len(duplikaty_glowny)),
        "duplikaty_sugerowanych_konfiguracji": int(len(duplikaty_sugerowane)),
        "braki": policz_braki(df),
        "bledne_ceny": int(len(znajdz_bledne_ceny(df))),
        "bledne_alerty": int(len(znajdz_bledne_alerty(df))),
        "bledne_daty": int(len(znajdz_bledne_daty(df))),
        "wynik_jakosci": policz_wynik_jakosci(df),
    }


def podsumowanie_jakosci(nazwa_pliku=PLIK_CSV):
    df = wczytaj_dane(nazwa_pliku)
    raport = raport_jakosci(df)

    print("--- RAPORT JAKOŚCI DANYCH v0.2 ---")
    print(f"Rekordy: {raport['liczba_rekordow']}")
    print(f"Kolumny: {raport['liczba_kolumn']}")
    print(f"Typy rekordów: {raport['typy_rekordow']}")
    print(f"Pełne duplikaty: {raport['pelne_duplikaty']}")
    print(f"Duplikaty w tym samym pomiarze: {raport['duplikaty_w_tym_samym_pomiarze']}")
    print(f"Duplikaty głównego produktu: {raport['duplikaty_glownego_produktu']}")
    print(f"Duplikaty sugerowanych konfiguracji: {raport['duplikaty_sugerowanych_konfiguracji']}")
    print(f"Błędne ceny: {raport['bledne_ceny']}")
    print(f"Błędne alerty: {raport['bledne_alerty']}")
    print(f"Błędne daty: {raport['bledne_daty']}")
    print(f"Wynik jakości: {raport['wynik_jakosci']}/100")


if __name__ == "__main__":
    podsumowanie_jakosci()
