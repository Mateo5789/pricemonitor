import streamlit as st
import pandas as pd

from analytics import (
    wczytaj_dane,
    filtruj_glowny_produkt,
    policz_statystyki,
    przygotuj_historie_cen,
    przygotuj_ostatnie_pomiary,
)

from data_quality import (
    raport_jakosci,
    znajdz_duplikaty_w_tym_samym_pomiarze,
    znajdz_duplikaty_glownego_produktu,
    znajdz_duplikaty_sugerowanych_konfiguracji,
    znajdz_bledne_ceny,
    znajdz_bledne_alerty,
)


PLIK_RAW = "refurbed_prices.csv"
PLIK_CLEAN = "refurbed_prices_clean.csv"


st.set_page_config(
    page_title="Refurbed Price Tracker 2.0",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Refurbed Price Tracker 2.0")
st.caption(
    "Automatyczny monitoring cen, analiza historii i kontrola jakości danych."
)


@st.cache_data
def zaladuj_raw():
    return wczytaj_dane(PLIK_RAW)


@st.cache_data
def zaladuj_clean():
    return wczytaj_dane(PLIK_CLEAN)


try:
    df_raw = zaladuj_raw()
except FileNotFoundError:
    st.error(
        f"Nie znaleziono pliku {PLIK_RAW}. "
        "Umieść go w tym samym folderze co app.py."
    )
    st.stop()
except Exception as e:
    st.error(f"Błąd podczas wczytywania RAW: {e}")
    st.stop()

try:
    df_clean = zaladuj_clean()
except FileNotFoundError:
    st.error(
        f"Nie znaleziono pliku {PLIK_CLEAN}. "
        "Najpierw uruchom: py data_cleaning.py"
    )
    st.stop()
except Exception as e:
    st.error(f"Błąd podczas wczytywania CLEAN: {e}")
    st.stop()


if df_raw.empty:
    st.warning("Plik RAW nie zawiera danych.")
    st.stop()

if df_clean.empty:
    st.warning("Plik CLEAN nie zawiera danych.")
    st.stop()


zakladka1, zakladka2, zakladka3, zakladka4 = st.tabs(
    [
        "📊 Dashboard",
        "📱 Konfiguracje",
        "🧹 Data Quality",
        "📋 Dane",
    ]
)


with zakladka1:
    st.subheader("Podsumowanie cen")

    glowny = filtruj_glowny_produkt(df_clean)
    statystyki = policz_statystyki(glowny)

    if statystyki["liczba_pomiarow"] == 0:
        st.warning("Brak poprawnych pomiarów głównego produktu.")
    else:
        col1, col2, col3, col4 = st.columns(4)

        delta = None
        if statystyki["zmiana_ceny"] is not None:
            delta = f"{statystyki['zmiana_ceny']:.2f} zł"

        col1.metric(
            "Aktualna cena",
            f"{statystyki['aktualna_cena']:.2f} zł",
            delta
        )

        col2.metric(
            "Najniższa cena",
            f"{statystyki['minimalna_cena']:.2f} zł"
        )

        col3.metric(
            "Najwyższa cena",
            f"{statystyki['maksymalna_cena']:.2f} zł"
        )

        col4.metric(
            "Średnia cena",
            f"{statystyki['srednia_cena']:.2f} zł"
        )

        st.write(
            f"**Liczba pomiarów głównego produktu:** "
            f"{statystyki['liczba_pomiarow']}"
        )

        if statystyki["zmiana_procentowa"] is not None:
            st.write(
                f"**Zmiana względem poprzedniego pomiaru:** "
                f"{statystyki['zmiana_procentowa']:.2f}%"
            )

        st.subheader("Historia ceny")

        historia = przygotuj_historie_cen(glowny)

        if historia.empty:
            st.info("Brak danych do wykresu.")
        else:
            st.line_chart(
                historia.set_index("data")["cena_liczbowo"]
            )

        st.subheader("Alert cenowy")

        alert = statystyki["aktualny_alert"]
        prog = statystyki["prog_alertu"]

        if alert == "TAK":
            if prog is not None:
                st.error(
                    f"🚨 Cena spadła poniżej progu {prog:.2f} zł."
                )
            else:
                st.error("🚨 Alert cenowy jest aktywny.")
        elif alert == "NIE":
            if prog is not None:
                st.success(
                    f"Cena jest powyżej progu {prog:.2f} zł."
                )
            else:
                st.success("Alert cenowy nie jest aktywny.")
        else:
            st.warning("Brak jednoznacznego statusu alertu.")

        st.subheader("Ostatnie pomiary")

        ostatnie = przygotuj_ostatnie_pomiary(
            glowny,
            limit=10
        )

        st.dataframe(
            ostatnie,
            use_container_width=True,
            hide_index=True
        )


with zakladka2:
    st.subheader("Analiza sugerowanych konfiguracji")

    konfiguracje = df_clean[
        df_clean["typ"] == "sugerowana_konfiguracja"
    ].copy()

    if konfiguracje.empty:
        st.info("Brak danych o sugerowanych konfiguracjach.")
    else:
        kol1, kol2, kol3, kol4 = st.columns(4)

        kol1.metric(
            "Liczba rekordów CLEAN",
            len(konfiguracje)
        )

        kol2.metric(
            "Najniższa cena",
            f"{konfiguracje['cena_liczbowo'].min():.2f} zł"
        )

        kol3.metric(
            "Najwyższa cena",
            f"{konfiguracje['cena_liczbowo'].max():.2f} zł"
        )

        kol4.metric(
            "Średnia cena",
            f"{konfiguracje['cena_liczbowo'].mean():.2f} zł"
        )

        pamieci = ["Wszystkie"] + sorted(
            konfiguracje["pamiec"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        stany = ["Wszystkie"] + sorted(
            konfiguracje["stan"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        kolory = ["Wszystkie"] + sorted(
            konfiguracje["kolor"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        f1, f2, f3 = st.columns(3)

        wybrana_pamiec = f1.selectbox("Pamięć", pamieci)
        wybrany_stan = f2.selectbox("Stan", stany)
        wybrany_kolor = f3.selectbox("Kolor", kolory)

        widok = konfiguracje.copy()

        if wybrana_pamiec != "Wszystkie":
            widok = widok[
                widok["pamiec"].astype(str) == wybrana_pamiec
            ]

        if wybrany_stan != "Wszystkie":
            widok = widok[
                widok["stan"].astype(str) == wybrany_stan
            ]

        if wybrany_kolor != "Wszystkie":
            widok = widok[
                widok["kolor"].astype(str) == wybrany_kolor
            ]

        st.write(
            f"**Liczba rekordów po filtrach:** {len(widok)}"
        )

        if not widok.empty:
            historia_konf = (
                widok[
                    ["data", "cena_liczbowo"]
                ]
                .dropna()
                .sort_values("data")
            )

            if not historia_konf.empty:
                st.line_chart(
                    historia_konf.set_index("data")[
                        "cena_liczbowo"
                    ]
                )

            kolumny_tabeli = [
                kolumna for kolumna in [
                    "data",
                    "model",
                    "kolor",
                    "pamiec",
                    "stan",
                    "cena_liczbowo",
                    "alert",
                ]
                if kolumna in widok.columns
            ]

            st.dataframe(
                widok.sort_values(
                    "data",
                    ascending=False
                )[kolumny_tabeli],
                use_container_width=True,
                hide_index=True
            )


with zakladka3:
    st.subheader("Kontrola jakości danych RAW")

    raport = raport_jakosci(df_raw)

    q1, q2, q3, q4 = st.columns(4)

    q1.metric(
        "Wynik jakości RAW",
        f"{raport['wynik_jakosci']}/100"
    )

    q2.metric(
        "Duplikaty w tym samym pomiarze",
        raport["duplikaty_w_tym_samym_pomiarze"]
    )

    q3.metric(
        "Błędne ceny",
        raport["bledne_ceny"]
    )

    q4.metric(
        "Błędne alerty",
        raport["bledne_alerty"]
    )

    st.write(f"**Rekordy RAW:** {len(df_raw)}")
    st.write(f"**Rekordy CLEAN:** {len(df_clean)}")
    st.write(
        f"**Usunięte / odfiltrowane rekordy:** "
        f"{len(df_raw) - len(df_clean)}"
    )

    typy = raport.get("typy_rekordow", {})

    if typy:
        st.write("**Typy rekordów RAW:**")
        for typ, liczba in typy.items():
            st.write(f"- {typ}: {liczba}")

    st.write(
        f"**Duplikaty głównego produktu:** "
        f"{raport['duplikaty_glownego_produktu']}"
    )
    st.write(
        f"**Duplikaty sugerowanych konfiguracji:** "
        f"{raport['duplikaty_sugerowanych_konfiguracji']}"
    )
    st.write(
        f"**Błędne daty:** {raport['bledne_daty']}"
    )

    st.subheader("Duplikaty sugerowanych konfiguracji")

    duplikaty_sugerowane = (
        znajdz_duplikaty_sugerowanych_konfiguracji(df_raw)
    )

    if duplikaty_sugerowane.empty:
        st.success(
            "Brak duplikatów sugerowanych konfiguracji."
        )
    else:
        st.warning(
            f"W RAW wykryto {len(duplikaty_sugerowane)} "
            "rekordów należących do grup duplikatów."
        )

        st.dataframe(
            duplikaty_sugerowane.head(100),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Podejrzane ceny")

    bledne_ceny = znajdz_bledne_ceny(df_raw)

    if bledne_ceny.empty:
        st.success("Nie wykryto podejrzanych cen.")
    else:
        st.warning(
            f"Wykryto {len(bledne_ceny)} podejrzanych rekordów."
        )

        st.dataframe(
            bledne_ceny.head(100),
            use_container_width=True,
            hide_index=True
        )


with zakladka4:
    st.subheader("Podgląd danych CLEAN")

    typy = ["Wszystkie"]

    if "typ" in df_clean.columns:
        typy += sorted(
            [
                str(x)
                for x in df_clean["typ"].dropna().unique()
            ]
        )

    wybrany_typ = st.selectbox(
        "Filtruj po typie rekordu",
        typy
    )

    widok = df_clean.copy()

    if (
        wybrany_typ != "Wszystkie"
        and "typ" in widok.columns
    ):
        widok = widok[
            widok["typ"].astype(str) == wybrany_typ
        ]

    st.write(
        f"**Liczba widocznych rekordów CLEAN:** {len(widok)}"
    )

    st.dataframe(
        widok.sort_values(
            "data",
            ascending=False
        )
        if "data" in widok.columns
        else widok,
        use_container_width=True,
        hide_index=True
    )
