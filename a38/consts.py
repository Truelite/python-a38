# see table at page 26 for the PDF document
# GUIDA ALLA COMPILAZIONE DELLE FATTURE ELETTRONICHE E DELL’ESTEROMETRO
# from AdE (Agenzia Delle Entrate), version 1.6 - 2022/02/04
# https://www.agenziaentrate.gov.it/portale/documents/20143/451259/Guida_compilazione-FE_2021_07_07.pdf/e6fcdd04-a7bd-e6f2-ced4-cac04403a768
# see also:
# - https://agenziaentrate.gov.it/portale/documents/20143/296703/Variazioni+alle+specifiche+tecniche+fatture+elettroniche2021-07-02.pdf  # noqa
# - https://www.agenziaentrate.gov.it/portale/web/guest/schede/comunicazioni/fatture-e-corrispettivi/faq-fe/risposte-alle-domande-piu-frequenti-categoria/compilazione-della-fattura-elettronica  # noqa
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
    "N6.2",  # inversione contabile – cessione di oro e argento ai sensi della
             #                        legge 7/2000 nonché di oreficeria usata ad OPO
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


# Copied from Documentazione valida a partire dal 1 ottobre 2020
# Rappresentazione tabellare del tracciato fattura ordinaria - excel
REGIME_FISCALE = (
    "RF01",  # Ordinario
    "RF02",  # Contribuenti minimi (art.1, c.96-117, L. 244/07)
    "RF04",  # Agricoltura e attività connesse e pesca (artt.34 e 34-bis, DPR 633/72)
    "RF05",  # Vendita sali e tabacchi (art.74, c.1, DPR. 633/72)
    "RF06",  # Commercio fiammiferi (art.74, c.1, DPR  633/72)
    "RF07",  # Editoria (art.74, c.1, DPR  633/72)
    "RF08",  # Gestione servizi telefonia pubblica (art.74, c.1, DPR 633/72)
    "RF09",  # Rivendita documenti di trasporto pubblico e di sosta (art.74, c.1, DPR  633/72)
    "RF10",  # Intrattenimenti, giochi e altre attività di cui alla tariffa
             # allegata al DPR 640/72 (art.74, c.6, DPR 633/72)
    "RF11",  # Agenzie viaggi e turismo (art.74-ter, DPR 633/72)
    "RF12",  # Agriturismo (art.5, c.2, L. 413/91)
    "RF13",  # Vendite a domicilio (art.25-bis, c.6, DPR  600/73)
    "RF14",  # Rivendita beni usati, oggetti d’arte, d’antiquariato o da collezione (art.36, DL 41/95)
    "RF15",  # Agenzie di vendite all’asta di oggetti d’arte, antiquariato o da collezione (art.40-bis, DL 41/95)
    "RF16",  # IVA per cassa P.A. (art.6, c.5, DPR 633/72)
    "RF17",  # IVA per cassa (art. 32-bis, DL 83/2012)
    "RF18",  # Altro
    "RF19",  # Regime forfettario (art.1, c.54-89, L. 190/2014)
)

# Copied from Documentazione valida a partire dal 1 ottobre 2020
# Rappresentazione tabellare del tracciato fattura ordinaria - excel
TIPO_CASSA = (
    "TC01",  # Cassa nazionale previdenza e assistenza avvocati e procuratori legali
    "TC02",  # Cassa previdenza dottori commercialisti
    "TC03",  # Cassa previdenza e assistenza geometri
    "TC04",  # Cassa nazionale previdenza e assistenza ingegneri e architetti liberi professionisti
    "TC05",  # Cassa nazionale del notariato
    "TC06",  # Cassa nazionale previdenza e assistenza ragionieri e periti commerciali
    "TC07",  # Ente nazionale assistenza agenti e rappresentanti di commercio (ENASARCO)
    "TC08",  # Ente nazionale previdenza e assistenza consulenti del lavoro (ENPACL)
    "TC09",  # Ente nazionale previdenza e assistenza medici (ENPAM)
    "TC10",  # Ente nazionale previdenza e assistenza farmacisti (ENPAF)
    "TC11",  # Ente nazionale previdenza e assistenza veterinari (ENPAV)
    "TC12",  # Ente nazionale previdenza e assistenza impiegati dell'agricoltura (ENPAIA)
    "TC13",  # Fondo previdenza impiegati imprese di spedizione e agenzie marittime
    "TC14",  # Istituto nazionale previdenza giornalisti italiani (INPGI)
    "TC15",  # Opera nazionale assistenza orfani sanitari italiani (ONAOSI)
    "TC16",  # Cassa autonoma assistenza integrativa giornalisti italiani (CASAGIT)
    "TC17",  # Ente previdenza periti industriali e periti industriali laureati (EPPI)
    "TC18",  # Ente previdenza e assistenza pluricategoriale (EPAP)
    "TC19",  # Ente nazionale previdenza e assistenza biologi (ENPAB)
    "TC20",  # Ente nazionale previdenza e assistenza professione infermieristica (ENPAPI)
    "TC21",  # Ente nazionale previdenza e assistenza psicologi (ENPAP)
    "TC22",  # INPS
)

# Copied from Documentazione valida a partire dal 1 ottobre 2020
# Rappresentazione tabellare del tracciato fattura ordinaria - excel
MODALITA_PAGAMENTO = (
    "MP01",  # contanti
    "MP02",  # assegno
    "MP03",  # assegno circolare
    "MP04",  # contanti presso Tesoreria
    "MP05",  # bonifico
    "MP06",  # vaglia cambiario
    "MP07",  # bollettino bancario
    "MP08",  # carta di pagamento
    "MP09",  # RID
    "MP10",  # RID utenze
    "MP11",  # RID veloce
    "MP12",  # RIBA
    "MP13",  # MAV
    "MP14",  # quietanza erario
    "MP15",  # giroconto su conti di contabilità speciale
    "MP16",  # domiciliazione bancaria
    "MP17",  # domiciliazione postale
    "MP18",  # bollettino di c/c postale
    "MP19",  # SEPA Direct Debit
    "MP20",  # SEPA Direct Debit CORE
    "MP21",  # SEPA Direct Debit B2B
    "MP22",  # Trattenuta su somme già riscosse
    "MP23",  # PagoPA
)

# Copied from Documentazione valida a partire dal 1 ottobre 2020
# Rappresentazione tabellare del tracciato fattura ordinaria - excel
TIPO_RITENUTA = (
    "RT01",  # ritenuta persone fisiche
    "RT02",  # ritenuta persone giuridiche
    "RT03",  # contributo INPS
    "RT04",  # contributo ENASARCO
    "RT05",  # contributo ENPAM
    "RT06",  # altro contributo previdenziale
)
