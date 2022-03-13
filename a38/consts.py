# see table at page 26 for the PDF document
# GUIDA ALLA COMPILAZIONE DELLE FATTURE ELETTRONICHE E DELL’ESTEROMETRO
# from AdE (Agenzia Delle Entrate), version 1.6 - 2022/02/04
# https://www.agenziaentrate.gov.it/portale/documents/20143/451259/Guida_compilazione-FE_2021_07_07.pdf/e6fcdd04-a7bd-e6f2-ced4-cac04403a768
# see also:
# - https://agenziaentrate.gov.it/portale/documents/20143/296703/Variazioni+alle+specifiche+tecniche+fatture+elettroniche2021-07-02.pdf
# - https://www.agenziaentrate.gov.it/portale/web/guest/schede/comunicazioni/fatture-e-corrispettivi/faq-fe/risposte-alle-domande-piu-frequenti-categoria/compilazione-della-fattura-elettronica
NATURA_IVA = (
    "N1",
    "N2",
    "N2.1",  # non soggette ad IVA ai sensi degli artt. da 7 a 7-septies del D.P.R. n. 633/72
    "N2.2",  # non soggette - altri casi
    "N3",
    "N3.1",  # non imponibili - esportazioni
    "N3.2",  # non imponibili - cessioni intracomunitarie
    "N3.3",  # non imponibili - cessioni verso San Marino
    "N3.4",  # non imponibili - operazioni assimilate alle cessioni all'esportazione
    "N3.5",  # non imponibili - a seguito di dichiarazioni d'intento
    "N3.6",  # non imponibili - altre operazioni
    "N4",
    "N5",
    "N6",
    "N6.1",  # inversione contabile - cessione di rottami e altri materiali di recupero
    "N6.2",  # inversione contabile – cessione di oro e argento ai sensi della legge 7/2000 nonché di oreficeria usata ad OPO
    "N6.3",  # inversione contabile - subappalto nel settore edile
    "N6.4",  # inversione contabile - cessione di fabbricati
    "N6.5",  # inversione contabile - cessione di telefoni cellulari
    "N6.6",  # inversione contabile - cessione di prodotti elettronici
    "N6.7",  # inversione contabile - prestazioni comparto edile e settori connessi
    "N6.8",  # inversione contabile - operazioni settore energetico
    "N6.9",  # inversione contabile - altri casi
    "N7",
)

# see pages 1 to 25 for the PDF document
# GUIDA ALLA COMPILAZIONE DELLE FATTURE ELETTRONICHE E DELL’ESTEROMETRO
# from AdE (Agenzia Delle Entrate), version 1.6 - 2022/02/04
# https://www.agenziaentrate.gov.it/portale/documents/20143/451259/Guida_compilazione-FE_2021_07_07.pdf/e6fcdd04-a7bd-e6f2-ced4-cac04403a768
TIPO_DOCUMENTO = (
    "TD01",  # FATTURA
    "TD02",  # ACCONTO/ANTICIPO SU FATTURA
    "TD03",  # ACCONTO/ANTICIPO SU PARCELLA
    "TD04",  # NOTA DI CREDITO
    "TD05",  # NOTA DI DEBITO
    "TD06",  # PARCELLA
    "TD07",  # FATTURA SEMPLIFICATA
    "TD08",  # NOTA DI CREDITO SEMPLIFICATA
    "TD09",  # NOTA DI DEBITO SEMPLIFICATA
    "TD16",  # INTEGRAZIONE FATTURA DA REVERSE CHARGE INTERNO
    "TD17",  # INTEGRAZIONE/AUTOFATTURA PER ACQUISTO SERVIZI DALL'ESTERO
    "TD18",  # INTEGRAZIONE PER ACQUISTO DI BENI INTRACOMUNITARI
    "TD19",  # INTEGRAZIONE/AUTOFATTURA PER ACQUISTO DI BENI EX ART. 17 C.2 D.P.R. 633/72
    "TD20",  # AUTOFATTURA PER REGOLARIZZAZIONE E INTEGRAZIONE DELLE FATTURE
             # (EX ART. 6 COMMI 8 E 9-BIS D. LGS. 471/97 O ART. 46 C.5 D.L. 331/93)
    "TD21",  # AUTOFATTURA PER SPLAFONAMENTO
    "TD22",  # ESTRAZIONE BENI DA DEPOSITO IVA
    "TD23",  # ESTRAZIONE BENI DA DEPOSITO IVA CON VERSAMENTO DELL'IVA
    "TD24",  # FATTURA DIFFERITA DI CUI ALL'ART. 21, COMMA 4, TERZO PERIODO, LETT. A), DEL D.P.R. N. 633/72
    "TD25",  # FATTURA DIFFERITA DI CUI ALL'ART. 21, COMMA 4, TERZO PERIODO LETT. B), DEL D.P.R. N. 633/72
    "TD26",  # CESSIONE DI BENI AMMORTIZZABILI E PER PASSAGGI INTERNI (EX ART. 36 D.P.R. 633/72)
    "TD27",  # FATTURA PER AUTOCONSUMO O PER CESSIONI GRATUITE SENZA RIVALSA
)
