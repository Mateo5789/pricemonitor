import pandas as pd

PLIK_CSV = "refurbed_prices.csv"


def wczytaj_dane(nazwa_pliku=PLIK_CSV):
    """
    Wczytuje dane z CSV i przygotowuje podstawowe typy kolumn.
    """
    df = pd.read_csv(nazwa_pliku)

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    if "cena_liczbowo" in df.columns:
        df["cena_liczbowo"] = pd.to_numeric(
            df["cena_liczbowo"],
            errors="coerce"
        )

    if "prog_alertu" in df.columns:
        df["prog_alertu"] = pd.to_numeric(
            df["prog_alertu"],
            errors="coerce"
        )

    return df


def filtruj_glowny_produkt(df):
    """
    Zwraca tylko poprawne pomiary głównego produktu.
    """
    wymagane_kolumny = {"typ", "data", "cena_liczbowo"}

    if not wymagane_kolumny.issubset(df.columns):
        brakujace = wymagane_kolumny - set(df.columns)
        raise ValueError(
            f"Brakuje wymaganych kolumn: {', '.join(sorted(brakujace))}"
        )

    glowny = df[df["typ"] == "glowny_produkt"].copy()

    glowny = glowny.dropna(
        subset=["data", "cena_liczbowo"]
    )

    glowny = glowny.sort_values("data")

    return glowny


def pobierz_aktualny_pomiar(glowny):
    """
    Zwraca najnowszy pomiar głównego produktu.
    """
    if glowny.empty:
        return None

    return glowny.iloc[-1]


def pobierz_poprzedni_pomiar(glowny):
    """
    Zwraca poprzedni pomiar głównego produktu.
    """
    if len(glowny) < 2:
        return None

    return glowny.iloc[-2]


def policz_statystyki(glowny):
    """
    Liczy podstawowe statystyki cenowe dla głównego produktu.
    """
    if glowny.empty:
        return {
            "aktualna_cena": None,
            "poprzednia_cena": None,
            "zmiana_ceny": None,
            "zmiana_procentowa": None,
            "minimalna_cena": None,
            "maksymalna_cena": None,
            "srednia_cena": None,
            "liczba_pomiarow": 0,
            "aktualny_alert": None,
            "prog_alertu": None,
        }

    aktualny = pobierz_aktualny_pomiar(glowny)
    poprzedni = pobierz_poprzedni_pomiar(glowny)

    aktualna_cena = float(aktualny["cena_liczbowo"])

    if poprzedni is not None:
        poprzednia_cena = float(poprzedni["cena_liczbowo"])
        zmiana_ceny = round(
            aktualna_cena - poprzednia_cena,
            2
        )

        if poprzednia_cena != 0:
            zmiana_procentowa = round(
                (zmiana_ceny / poprzednia_cena) * 100,
                2
            )
        else:
            zmiana_procentowa = None
    else:
        poprzednia_cena = None
        zmiana_ceny = None
        zmiana_procentowa = None

    alert = (
        aktualny.get("alert")
        if "alert" in aktualny.index
        else None
    )

    prog_alertu = (
        aktualny.get("prog_alertu")
        if "prog_alertu" in aktualny.index
        else None
    )

    if pd.isna(prog_alertu):
        prog_alertu = None
    elif prog_alertu is not None:
        prog_alertu = float(prog_alertu)

    return {
        "aktualna_cena": aktualna_cena,
        "poprzednia_cena": poprzednia_cena,
        "zmiana_ceny": zmiana_ceny,
        "zmiana_procentowa": zmiana_procentowa,
        "minimalna_cena": float(glowny["cena_liczbowo"].min()),
        "maksymalna_cena": float(glowny["cena_liczbowo"].max()),
        "srednia_cena": float(glowny["cena_liczbowo"].mean()),
        "liczba_pomiarow": int(len(glowny)),
        "aktualny_alert": alert,
        "prog_alertu": prog_alertu,
    }


def przygotuj_historie_cen(glowny):
    """
    Przygotowuje dane do wykresu historii cen.
    """
    if glowny.empty:
        return pd.DataFrame(
            columns=["data", "cena_liczbowo"]
        )

    return glowny[
        ["data", "cena_liczbowo"]
    ].copy()


def przygotuj_ostatnie_pomiary(glowny, limit=10):
    """
    Zwraca ostatnie pomiary w formie wygodnej do tabeli w dashboardzie.
    """
    if glowny.empty:
        return pd.DataFrame()

    kolumny = [
        kolumna for kolumna in [
            "data",
            "model",
            "cena_liczbowo",
            "alert",
            "prog_alertu",
            "dostepnosc",
            "url",
        ]
        if kolumna in glowny.columns
    ]

    return (
        glowny
        .sort_values("data", ascending=False)
        [kolumny]
        .head(limit)
        .copy()
    )


def podsumowanie_analityczne(nazwa_pliku=PLIK_CSV):
    """
    Funkcja pomocnicza do szybkiego testu modułu w terminalu.
    """
    df = wczytaj_dane(nazwa_pliku)
    glowny = filtruj_glowny_produkt(df)
    statystyki = policz_statystyki(glowny)

    print("--- PODSUMOWANIE ANALITYCZNE ---")
    print(f"Liczba pomiarów: {statystyki['liczba_pomiarow']}")
    print(f"Aktualna cena: {statystyki['aktualna_cena']} zł")
    print(f"Poprzednia cena: {statystyki['poprzednia_cena']} zł")
    print(f"Zmiana ceny: {statystyki['zmiana_ceny']} zł")
    print(f"Zmiana procentowa: {statystyki['zmiana_procentowa']}%")
    print(f"Minimum: {statystyki['minimalna_cena']} zł")
    print(f"Maksimum: {statystyki['maksymalna_cena']} zł")
    print(f"Średnia: {statystyki['srednia_cena']:.2f} zł")
    print(f"Alert: {statystyki['aktualny_alert']}")
    print(f"Próg alertu: {statystyki['prog_alertu']} zł")


if __name__ == "__main__":
    podsumowanie_analityczne()
