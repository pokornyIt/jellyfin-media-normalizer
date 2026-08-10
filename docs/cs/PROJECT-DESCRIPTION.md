# POPIS PROJEKTU

[English](../en/PROJECT-DESCRIPTION.md) | [Čeština](PROJECT-DESCRIPTION.md)

## Cíl

Cílem projektu je sjednotit a normalizovat rozsáhlou knihovnu médií uloženou na zařízení Synology NAS tak, aby byla
čistá, konzistentní a připravená pro spolehlivé použití v Jellyfinu.

Knihovna obsahuje více než 9 000 videosouborů v přibližně 1 000 složkách a zahrnuje filmy i televizní seriály.
Hlavním účelem projektu je standardizovat názvy souborů a složek, zlepšit identifikaci médií a připravit knihovnu
na řízené dávkové přejmenování bez zbytečného nepořádku v podobě metadat na disku.

Projekt nepoužívá soubory `.nfo`. Identifikace v Jellyfinu bude místo toho vycházet z jediného ID poskytovatele
uloženého v názvu hlavní složky filmu nebo seriálu ve formátu podporovaném Jellyfinem, například `[imdbid-tt...]`,
`[tmdbid-...]` nebo `[tvdbid-...]`.

## Rozsah

Projekt zahrnuje:

- skenování a inventarizaci stávající knihovny médií;
- klasifikaci položek na filmy, televizní seriály a neznámé či problematické soubory;
- normalizaci názvů do jednotného schématu;
- ověřování parsovaných informací o médiích;
- vyhledání ID poskytovatele pro každý film nebo televizní seriál;
- vytvoření plánu přejmenování;
- řízené dávkové přejmenování v logických skupinách;
- kontrolní sestavy pro nejednoznačné a nevyřešené položky.

Projekt nezahrnuje:

- generování souborů `.nfo`;
- vkládání metadat do mediálních souborů;
- ukládání ID na úrovni epizod;
- ukládání ID do názvů souborů epizod;
- automatické přejmenování bez ověření;
- plnou automatizaci nejistých shod.

## Konvence názvů

### Filmy

Názvy souborů filmů používají následující formát:

- `Czech Title (Year) - CZ.ext`
- `Czech Title (Year) - EN (tit. CZ).ext`

Název složky filmu obsahuje jediné ID poskytovatele:

- `Czech Title (Year) [imdbid-tt1234567]`
- `Czech Title (Year) [tmdbid-12345]`

Uloží se pouze jedno ID podle vybraného doporučení poskytovatele.

### Televizní seriály

Název kořenové složky seriálu používá následující formát:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

V názvu složky seriálu nebude uveden rok, protože by mohl být zavádějící nebo matoucí.

Názvy souborů epizod neobsahují žádné ID poskytovatele:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Jazykové značky používají standardní dvoupísmenné kódy: `CZ`, `EN`, `DE`, `SK`, `FR`, `IT`, `ES`.

## Strategie metadat

Projekt nepoužívá místní doprovodné soubory s metadaty, například `.nfo`, aby souborový systém při přímém procházení
úložiště zůstal čitelný a přehledný.

Identifikace v Jellyfinu se místo toho zlepší přidáním jediného ID poskytovatele pouze do názvu hlavní složky filmu
nebo seriálu.

Priority poskytovatelů:

- Filmy: primární vyhledání přes TMDb; do názvu složky se uloží jedno konečné vybrané ID.
- Televizní seriály: online vyhledání nejprve přes TMDb TV a poté TVDB; do složky seriálu se uloží jedno konečné ID.
- Epizody: bez vyhledání ID poskytovatele a bez ID v názvu souboru.

## Principy návrhu

- Žádné soubory `.nfo`.
- Jedno ID poskytovatele pro film nebo televizní seriál; žádná ID na úrovni epizod.
- Žádné přejmenování bez ověřeného plánu.
- Žádné dávkové přejmenování bez vytvořeného manifestu.
- Výchozím režimem spuštění je dry-run.
- Vedlejší účinky jsou izolovány ve vrstvě executorů.
- Nejednoznačné položky a položky s nízkou mírou jistoty vždy směřují ke kontrole a nikdy se nezpracují automaticky.
- Prioritou je čitelná struktura souborového systému.

## Implementace

### Architektura

Projekt je uspořádán do samostatných vrstev. Každá vrstva má jedinou odpovědnost:

```text
src/jellyfin_media_normalizer/
├── constants.py            — řetězcové a n-ticové konstanty celého projektu
├── settings.py             — běhová konfigurace pomocí proměnných prostředí
├── main.py                 — vstupní bod aplikace
├── cli/
│   └── app.py              — příkazy CLI (scan, parse, report-scan, ...)
├── models/
│   ├── media_item.py       — nezpracovaná položka nalezeného souboru
│   ├── media_type.py       — výčet movie / tv_episode / unknown
│   ├── parsed_media_item.py — úplně parsovaná a ověřená položka
│   ├── parsed_name.py      — strukturovaná data názvu získaná ze jména souboru
│   ├── provider_match.py   — vybrané ID poskytovatele s jistotou a zdůvodněním
│   ├── scan_result.py      — souhrn výsledku skenování
│   ├── validation_result.py — chyby a varování ověření
│   ├── validation_status.py — výčet passed / review_needed / failed
│   └── confidence_level.py — výčet high / medium / low
├── scanners/
│   └── library_scanner.py  — skenování souborového systému a inventář souborů
├── parsers/
│   ├── patterns.py         — sdílené zkompilované regulární výrazy
│   ├── filename_cleaner.py — odstranění značek vydání a normalizace oddělovačů
│   ├── classifier.py       — klasifikace názvu souboru jako film nebo epizoda
│   ├── movie_name_parser.py — získání názvu, roku a jazyka filmu
│   ├── tv_episode_parser.py — získání seriálu, řady, epizody a jazyka
│   ├── media_parser.py     — koordinace čištění, klasifikace a parsování
│   └── provider_id_extractor.py — nalezení vložených ID poskytovatelů v názvech složek
├── validators/
│   ├── structure_validator.py   — ověření povinných polí parsovaných položek
│   ├── confidence_scorer.py     — výpočet úrovně jistoty
│   ├── consistency_validator.py — ověření vnitřní konzistence mezi položkami
│   └── validation_service.py   — koordinace ověřovacího procesu
├── providers/
│   ├── provider_clients.py      — HTTP klienti pro API TMDb a TVDB
│   ├── provider_id_cache.py     — místní JSON mezipaměť nalezených ID poskytovatelů
│   ├── online_provider_resolver.py — online vyhledání přes TMDb a TVDB
│   └── provider_resolver_chain.py  — řetězec resolverů (mezipaměť → online)
├── services/
│   ├── scan_service.py          — spuštění a vrácení výsledků skenování
│   ├── parse_service.py         — koordinace parsování, ověření a vyhledání poskytovatele
│   └── provider_lookup_service.py — nalezení ID poskytovatelů pro všechny parsované položky
├── reporters/
│   ├── json_reporter.py         — úplná JSON sestava všech parsovaných položek
│   ├── review_reporter.py       — sestava položek vyžadujících kontrolu
│   └── unresolved_reporter.py   — sestava položek bez nalezeného ID poskytovatele
└── utils/
    ├── logging.py               — LoggingMixin a pomocné funkce nastavení
    └── paths.py                 — pomocné funkce pro rozlišení cest
```

### Zjišťování ID poskytovatele

ID poskytovatelů se zjišťují v tomto pořadí:

1. **Vložené ID** — pokud už název složky obsahuje `[imdbid-tt...]`, `[tmdbid-...]` nebo `[tvdbid-...]`,
   toto ID se použije přímo a další vyhledávání neproběhne.
2. **Mezipaměť** — nejprve se zkontroluje místní JSON mezipaměť v
   `data/workspace/cache/provider_ids.json` podle odpovídajícího vyhledávacího klíče.
3. **Online API** — pokud mezipaměť neobsahuje shodu a jsou nastavené API klíče, klienti se dotazují v tomto pořadí:
   - `movie`: TMDb;
   - `tv_episode` (vyhledání na úrovni seriálu): TMDb TV, poté TVDB.

Položky klasifikované jako `unknown` se zcela přeskočí.

### Fáze implementace

| #   | Fáze                                  | Stav              |
| --- | ------------------------------------- | ----------------- |
| 1   | Inventarizace a skenování             | ✅ Implementováno |
| 2   | Klasifikace                           | ✅ Implementováno |
| 3   | Normalizace názvů                     | ✅ Implementováno |
| 4   | Ověření                               | ✅ Implementováno |
| 5   | Vyhledání ID poskytovatele            | ✅ Implementováno |
| 6   | Plánování přejmenování (manifest)     | ⏳ Plánováno      |
| 7   | Dávkové provedení přejmenování        | ⏳ Plánováno      |
| 8   | Kontrolní workflow (HTML/CSV sestavy) | ⏳ Plánováno      |

#### Fáze 1 — Inventarizace a skenování

Prohledá knihovnu médií a shromáždí cesty k souborům, strukturu složek a vzory názvů. Zjistí podporované přípony videa.
Výsledkem je plochý seznam objektů `MediaItem`, který slouží jako vstup všech dalších fází.

#### Fáze 2 — Klasifikace

Každá položka se klasifikuje jako `movie`, `tv_episode` nebo `unknown`.

Klasifikace vychází ze vzorů názvů souborů: rok v závorkách značí film, značka `SxxExx` nebo její ekvivalent značí
epizodu seriálu. Položky, které neodpovídají ani jednomu vzoru, se označí jako `unknown`.

#### Fáze 3 — Normalizace názvů

Normalizované názvy se parsují do strukturovaných objektů `ParsedName` s názvem, rokem, řadou či epizodou, jazykovým
kódem a příznaky titulků. Před parsováním se odstraní značky vydání, například kodeky, rozlišení a kvalita.

#### Fáze 4 — Ověření

Všechny parsované položky se ověří z hlediska strukturální úplnosti a vnitřní konzistence. Každá položka dostane
`ValidationStatus` (`passed`, `review_needed` nebo `failed`) a `ConfidenceLevel` (`high`, `medium` nebo `low`). Položky
s vysokou jistotou postupují automaticky, ostatní se označí ke kontrole.

#### Fáze 5 — Vyhledání ID poskytovatele

Po ověření se každá položka kromě `unknown` spáruje s jediným ID poskytovatele. Vyhledávání probíhá podle řetězce
popsaného výše v části [Zjišťování ID poskytovatele](#zjišťování-id-poskytovatele).

Výsledkem každé nalezené položky je objekt `ProviderMatch` obsahující `provider`, `provider_id`, `confidence`, `reason`
a `lookup_key`. Položky bez shody se zapíší do sestavy nevyřešených položek.

#### Fáze 6 — Plánování přejmenování *(plánováno)*

Před jakoukoli změnou souborového systému se vytvoří manifest přejmenování. Bude obsahovat původní cestu, typ média,
normalizovaná data názvu, vybrané ID poskytovatele, jistotu, navrženou novou cestu a stav akce.

Výchozím režimem bude dry-run. Skutečné provedení bude vyžadovat explicitní přepínač.

#### Fáze 7 — Dávkové provedení přejmenování *(plánováno)*

Přejmenování se provede v logických dávkách, tedy filmy po složkách a seriály po jednotlivých pořadech, až po kontrole
manifestu. Executor bude podporovat protokolování, detekci kolizí a možnost vrácení změn.

#### Fáze 8 — Kontrolní workflow *(plánováno)*

Položky označené ke kontrole se exportují také do formátů HTML a CSV, aby je bylo možné ručně prohlížet mimo JSON.
Tato fáze nemá žádné vedlejší účinky na souborový systém.

## Očekávaný výsledek

Po dokončení by knihovna médií měla mít:

- konzistentní a čitelné názvy souborů a složek;
- lepší rozpoznávání v Jellyfinu pomocí vložených ID poskytovatelů;
- opakovatelný workflow pro budoucí přírůstky knihovny;
- bezpečný proces dávkového přejmenování s možností vrácení změn;
- minimální nepořádek v souborovém systému — bez doprovodných souborů a vložených metadat;
- řízené zpracování všech nejistých a nejednoznačných případů.
