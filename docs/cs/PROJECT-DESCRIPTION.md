# POPIS PROJEKTU

[English](../en/PROJECT-DESCRIPTION.md) | [Čeština](PROJECT-DESCRIPTION.md)

## Cíl

Cílem projektu je sjednotit a normalizovat rozsáhlou knihovnu médií uloženou na zařízení Synology NAS tak, aby byla
čistá, konzistentní a připravená pro spolehlivé použití v Jellyfinu.

Knihovna obsahuje více než 9 000 videosouborů v přibližně 1 000 složkách a zahrnuje filmy i televizní seriály.
Hlavním účelem projektu je standardizovat názvy souborů a složek, zlepšit identifikaci médií a připravit knihovnu
na řízené dávkové přejmenování bez zbytečného nepořádku v podobě metadat na disku.

Projekt nepoužívá soubory `.nfo`. Identifikace v Jellyfinu bude místo toho vycházet z jediného ID poskytovatele
uloženého v názvu souboru filmu nebo složky seriálu ve formátu podporovaném Jellyfinem, například
`[imdbid-tt...]`, `[tmdbid-...]` nebo `[tvdbid-...]`.

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

## Rozložení a klasifikace knihovny

Aplikace skenuje jeden nakonfigurovaný kořen knihovny, který může obsahovat filmy i televizní seriály. Kořen knihovny
je neutrální kontejner a neklasifikuje se jako jeden z typů médií. Soubor filmu nebo složka seriálu přímo v kořeni
zůstává zpracovatelná a může být připravena k plánování, ale obdrží neblokující varování, protože smíšený kořen není
vhodným cílovým rozložením knihovny Jellyfinu.

Složky pod kořenem se podle obsahu klasifikují jako filmové kolekce, kolekce seriálů, televizní seriály, sezóny nebo
nekompatibilní složky. Klasifikovaná filmová kolekce nesmí obsahovat podstrom seriálu a klasifikovaná kolekce seriálů
nesmí obsahovat filmové soubory. Název složky může přispět jako indicie, ale klasifikaci určuje obsah a struktura.

Skenování sestupuje nejvýše pět adresářových úrovní pod nakonfigurovaný kořen. Kořen má hloubku nula a soubor
nepřidává adresářovou úroveň. Obsah za tímto limitem se oznámí jako nekompatibilní, místo aby se tiše vynechal.

Normalizované rozložení seriálu je striktní:

```text
Series Name [provider-id]/
└── Season 01/
    └── Episode Title S01E01 - CZ.ext
```

Složka seriálu obsahuje pouze normalizované složky sezón a složka sezóny obsahuje soubory epizod a jejich podporované
související soubory bez další adresářové úrovně. Soubory epizod přímo ve vstupní složce seriálu lze opravit:
jednoznačné `SxxExx` určí sezónu, zatímco číslo epizody bez sezóny navrhne `Season 01` a vyžádá kontrolu. Nejednoznačné
číslování epizod vyžaduje kontrolu bez automatického plánu. Vnořené složky sezón a smíšený obsah filmů a seriálů jsou
nekompatibilní a obdrží doporučení k nápravě.

Položka, kterou lze bezpečně seskupit, ale má nejistá metadata, směřuje ke kontrole. Položka, jejíž vlastnictví nebo
strukturální roli nelze určit, je nekompatibilní a nesmí vstoupit do výběru poskytovatele, schválení ani manifestu
přejmenování. Soubory `.nfo` se vždy ignorují a nikdy nevstupují do doménového modelu ani samostatné operace se
souborovým systémem. Smí se přesunout pouze jako obsah přejmenované nadřazené složky.

## Konvence názvů

### Filmy

Názvy souborů filmů používají následující formát:

- `Czech Title (Year) [imdbid-tt1234567] - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - EN (tit. CZ).ext`

Film je videosoubor a nevyžaduje ani nevytváří vlastní filmovou složku. Organizační složky pro žánry a kolekce
zůstávají čitelné a nedostávají ID poskytovatele. Podporovaný související soubor používá stejný základ názvu jako
vlastnící video a přejmenuje se spolu s ním.

Oficiální `Part 1` nebo `Part 2` v názvu filmu zůstává součástí zobrazovaného názvu, pokud mají vydání odlišné identity
poskytovatele. Jeden film fyzicky rozdělený do více souborů místo toho používá koncovou značku části:

- `Czech Title (Year) [tmdbid-12345] - CD1 - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - CD2 - CZ.ext`

Číslování částí musí začínat jedničkou a být souvislé. Samotná značka `Part` nikdy nedokazuje, že soubory patří k
jednomu filmu; části se od samostatných vydání musí odlišit identitou poskytovatele nebo explicitním potvrzením
operátora.

Alternativní verze zůstávají samostatnými soubory pod jednou entitou filmu a jedním vybraným ID poskytovatele. Jejich
řízené označení edice předchází jazykové značce, například:

- `Czech Title (Year) [tmdbid-12345] - Director's Cut - CZ.ext`
- `Czech Title (Year) [tmdbid-12345] - Theatrical - EN (tit. CZ).ext`

Více souborů se stejným názvem, rokem a poskytovatelem vyžaduje kontrolu před označením jako části, alternativní verze,
duplicity nebo různé filmy.

### Televizní seriály

Název složky seriálu používá následující formát:

- `Series Name [tvdbid-12345]`
- `Series Name [tmdbid-12345]`

Normalizovaná složka seriálu nikdy neobsahuje rok vydání ani první premiéry. Koncový rok ve vstupní složce se použije
pro vyhledávání a kontrolu a odstraní se až po výběru a schválení identity poskytovatele. Remaky se stejným
zobrazovaným názvem rozlišuje ID poskytovatele.

Čísla, která jsou součástí skutečného názvu, například `1899`, `1923`, `11.22.63` nebo `Catch-22`, zůstávají beze
změny. Nejednoznačné číslo vyžaduje kontrolu. Roky se nikdy nepřidávají do složek sezón ani názvů souborů epizod.

Názvy složek sezón používají `Season XX`, například `Season 01`.

Seriálové speciály používají `Season 00` a `S00E##`. Patří seriálu a nikdy nedostávají ID poskytovatele. Jeden soubor
obsahující více epizod používá explicitní rozsah, například `S01E01-E02`. Vícedílné příběhy uložené jako samostatně
číslované epizody zůstávají samostatnými epizodami; `Part 1` a `Part 2` zůstávají v jejich zobrazovaných názvech.

Názvy souborů epizod neobsahují žádné ID poskytovatele:

- `Czech Episode Title S01E02 - CZ.ext`
- `Czech Episode Title S01E02 - EN (tit. CZ).ext`

Jazykové značky používají standardní dvoupísmenné kódy: `CZ`, `EN`, `DE`, `SK`, `FR`, `IT`, `ES`.

### Zobrazované názvy

Zobrazovaný název se vybírá v tomto pořadí: operátorem schválený název, český lokalizovaný název vybraného
poskytovatele, existující název ze souborového systému a původní název poskytovatele. Poslední možnost vyžaduje
kontrolu.

Zobrazovaný název zachovává diakritiku, členy, interpunkci a pořadí slov vybraného zdroje. Normalizace pro vyhledávání
zobrazovaný text nikdy nepřepisuje. Ručně schválený název přetrvá další skeny, zatímco změna vybraného poskytovatele
znovu otevře kontrolu názvu.

### Související soubory

První vydání podporuje soubory titulků s příponami `.srt`, `.ass`, `.ssa`, `.vtt` a `.sub`. Titulky patří k videu,
pokud používají stejný základ názvu nebo přidávají pouze rozpoznané jazykové a titulkové příznaky, například `cs`,
`en`, `forced`, `sdh`, `cc` nebo `default`. Příznaky se při přejmenování zachovají. Osiřelé titulky a kolize cílových
názvů vyžadují kontrolu.

Ostatní typy souborů se jako samostatné položky ignorují a při přejmenování nadřazené složky v ní zůstanou. Soubor
`.nfo` se nikdy samostatně nečte, neparsuje, nemodeluje, nevytváří, nemění, nemaže ani necílí operací manifestu. Smí
se přesunout pouze jako ignorovaný obsah přejmenované nadřazené složky.

Video rozpoznané jako bonus nebo extra vyžaduje kontrolu. Operátor je může klasifikovat jako film, seriálový speciál
nebo ignorovaný obsah. Ignorované bonusy nedostanou ID poskytovatele ani samostatnou operaci manifestu a smějí se
přesunout pouze jako obsah přejmenované nadřazené složky.

## Strategie metadat

Projekt nepoužívá místní doprovodné soubory s metadaty, například `.nfo`, aby souborový systém při přímém procházení
úložiště zůstal čitelný a přehledný.

Identifikace v Jellyfinu se místo toho zlepší přidáním jediného ID poskytovatele do názvu souboru filmu nebo složky
seriálu.

Priority poskytovatelů:

- Filmy: primární vyhledání přes TMDb; do názvu videosouboru se uloží jedno konečné vybrané ID.
- Televizní seriály: online vyhledání nejprve přes TMDb TV a poté TVDB; do složky seriálu se uloží jedno konečné ID.
- Epizody: bez vyhledání ID poskytovatele a bez ID v názvu souboru.

### Zásady výběru poskytovatele

Kandidáti poskytovatele se skórují nezávisle na jistotě parseru a skupiny entity. Automatický výběr je povolen jen
pro strukturálně platnou entitu s vysokou jistotou, odpovídajícím typem média, ID platným pro poskytovatele a bez
konfliktu s vloženým nebo ručně schváleným výběrem. Platné vložené ID a explicitní ruční výběr mají před skórováním
kandidátů přednost.

Při spolehlivém zdrojovém roku používá skóre kandidáta 80 % podobnosti normalizovaného názvu a 20 % shody roku.
Přesný rok má hodnotu `1.0`, rozdíl jednoho roku `0.5` a větší rozdíl nebo chybějící rok kandidáta `0.0`. Filmy pro
automatický výběr vyžadují přesný rok. Seriály vyžadují přesný vstupní rok, pokud byl spolehlivě parsován; bez něj
odpovídá jejich běžné skóre podobnosti názvu.

Automatický výběr vyžaduje skóre `0.92`, podobnost názvu `0.90` a náskok `0.08` před druhým kandidátem stejného
poskytovatele. Jediný kandidát vyžaduje skóre i podobnost názvu `0.97`. Pořadí API, popularita, grafika, dostupnost
přehledu a úplnost metadat nepřispívají ke skóre identity.

Seriál bez roku může použít názvy epizod od poskytovatele jako další důkaz, pokud nestačí skórování samotného názvu.
Deterministicky se vyberou až tři vhodné epizody jako první, prostřední a poslední použitelná epizoda, pokud možno
z různých řad. Jsou potřeba alespoň dva vzorky s použitelnými názvy epizod. Speciály, `Season 00`, vícedílné soubory,
soubory s více epizodami a nerozpoznatelné epizody se vynechají.

Každá vybraná kombinace řady a epizody musí u kandidáta existovat a každý název musí mít podobnost alespoň `0.85`
s lokalizovaným nebo původním názvem epizody od poskytovatele. Potvrzené skóre používá 75 % podobnosti názvu seriálu
a 25 % průměrné podobnosti názvů epizod. Vyžaduje podobnost názvu seriálu `0.85`, konečné skóre `0.92`, běžný náskok
`0.08` a žádný konflikt ve vzorku. Vyhledání epizod poskytuje pouze důkaz identity seriálu a nikdy nevytváří ID
poskytovatele na úrovni epizody.

Automatický výběr poskytovatele vytvoří stav `ready_for_approval`, nikoli schválení přejmenování. Ruční změny jsou
explicitní a auditovatelné. Prahy jsou pojmenované a verzované konstanty zásad, které operátor v prvním vydání
nemůže snížit. Výběry z mezipaměti lze automaticky znovu použít jen tehdy, pokud byly dříve schváleny podle stejné
verze zásad a vstupy identity se nezměnily; ostatní výsledky vyžadují nové skórování nebo kontrolu.

## Principy návrhu

- Žádné samostatné zpracování souborů `.nfo` ani operace manifestu pro ně.
- Jedno ID poskytovatele pro film nebo televizní seriál; žádná ID na úrovni epizod.
- Žádné přejmenování bez ověřeného plánu.
- Žádné dávkové přejmenování bez vytvořeného manifestu.
- Výchozím režimem spuštění je dry-run.
- Vedlejší účinky jsou izolovány ve vrstvě executorů.
- Nejednoznačné položky a položky s nízkou mírou jistoty vždy směřují ke kontrole a nikdy se nezpracují automaticky.
- Prioritou je čitelná struktura souborového systému.
- Symbolické odkazy se vždy odmítnou a nikdy se nenásledují, nemodelují, neplánují ani nepřejmenovávají.

## Bezpečnost stavu zdroje

Každý běžný zdrojový soubor v manifestu přejmenování má povinný otisk obsahující relativní cestu, typ položky,
velikost a čas změny s přesností poskytnutou souborovým systémem. První vydání nehashuje celý obsah médií a jako pole
identity nepoužívá číslo inode, čas vytvoření, vlastníka ani oprávnění.

Přejmenovávaná složka používá stromový SHA-256 digest nad kanonicky seřazenou inventurou. Každý potomek přispívá
relativní cestou a typem položky; spravované běžné soubory také velikostí a časem změny. Ignorovaní potomci včetně
`.nfo` přispívají pouze neprůhledným členstvím a nikdy se neotevírají, neparsují, nemodelují ani nedostávají samostatný
záznam manifestu. Symbolický odkaz je vždy neplatný, nikdy se nenásleduje a svou přítomností vyloučí obsahující složku
z plánování a provedení.

Manifest má samostatný SHA-256 digest kanonické serializace. Dry-run platí pouze pro přesný digest manifestu a shodné
otisky zdrojů. Stav zdrojů se znovu ověřuje při dry-run, bezprostředně před každou dávkou a před každou operací. Každý
rozdíl zastaví celý běh provádění a vyžaduje nové skenování, analýzu, schválení, manifest a dry-run. Existence cílů a
kolize se kontrolují nezávisle při plánování, dry-run i provedení.

## Částečné selhání a rollback

První neúspěšné přejmenování zastaví celý běh provádění. Aplikace se nepokusí o automatický rollback. Trvalý audit
místo toho rozliší potvrzené úspěšné, neúspěšné, čekající a nejisté operace. Pouze potvrzené úspěšné operace se v
opačném pořadí provedení obrátí do neměnného JSON manifestu rollbacku.

Každá položka rollbacku odkazuje na původní operaci a obsahuje současnou zdrojovou cestu, původní cílovou cestu,
otisk zdroje, očekávanou nepřítomnost cíle, pořadí a důvod obnovy. Manifest zaznamenává své schéma a druh, původní běh
a digest manifestu, čas vytvoření a vlastní SHA-256 digest. Ukládá strukturovaná data, nikoli shellové příkazy.

Rollback zpracovává běžný executor manifestu. Stav zdroje a nepřítomnost cíle se znovu ověří, dry-run je povinný,
skutečný rollback vyžaduje explicitní potvrzení a každý výsledek se zapíše do samostatného auditu. Rollback nikdy
nepřepíše existující cestu ani nezmění svůj manifest. Operátor může místo něj zachovat dokončené operace a vytvořit
nové workflow pro zbývající položky.

## Počáteční nasazení webového UI

První webové UI je neautentizovaná aplikace pro jediného operátora na důvěryhodném počítači nebo privátní LAN.
Adresa naslouchání je konfigurovatelná a má výchozí hodnotu `0.0.0.0`, aby prohlížeč Windows dosáhl na aplikaci
spuštěnou ve WSL nebo kontejneru. Naslouchání mimo loopback zobrazí upozornění, ale nebrání spuštění. Dostupná
důvěryhodná zařízení určují pravidla firewallu hostitele a publikování portu v Compose.

Počáteční UI podporuje nastavení, analýzu, kontrolu, opravy, schvalování, náhled manifestu, historii auditu a dry-run.
Nemá endpoint pro skutečné provedení přejmenování. Skutečné změny souborového systému zůstávají pouze v CLI a nadále
vyžadují ověřený manifest, úspěšný dry-run a samostatné explicitní potvrzení. Změnové trasy UI nikdy nepoužívají
metodu `GET`.

Vystavení veřejnému internetu a nedůvěryhodné síti není podporované. Autentizace, účty, role, session, ochrana CSRF,
TLS spravované aplikací, návod k HTTPS reverse proxy a zabezpečení vzdáleného přístupu jsou pozdější nadstavby.
Integrace se Synology účtem je volitelná a první podporované nasazení ji nevyžaduje.

## Podpora architektur kontejneru

Projekt oficiálně sestavuje, kontroluje smoke testem a publikuje kontejnerové obrazy pouze pro `linux/amd64`. Tato
platforma pokrývá vývojové prostředí WSL `x86_64` i obě cílová zařízení NAS: Synology DS925+ s AMD Ryzen V1500B a
Synology DS723+ s AMD Ryzen R1600.

První vydání nepublikuje obrazy ARM, 32bitové ani multi-platformní obrazy. Compose nenastavuje `platform`, takže
nepodporovaný hostitel skončí běžnou chybou Dockeru pro nekompatibilní obraz místo skrytého použití emulace AMD64.

Dockerfile zůstává prakticky přenositelný. Pokročilá dokumentace bude obsahovat příklady nativního `docker build` a
volitelného sestavení jediné platformy přes `docker buildx build` pro uživatele, kteří chtějí vyzkoušet jinou
architekturu. Taková sestavení jsou best-effort, projekt je v release netestuje a oficiálně je nepodporuje ani
nepublikuje.

## Přístup Compose pro zápis

Běžné `docker compose up` spustí pouze dlouhodobou službu `app`. Ta připojí knihovnu médií explicitně jako
`/media:ro` a používá trvalý zapisovatelný `/workspace`. Webová služba nikdy nedostane zapisovatelný přístup k médiím.

Skutečné přejmenování a rollback používají samostatnou jednorázovou službu `executor` v profilu `execution`. Připojí
`/media:rw`, nemá síť ani webový port, používá `restart: "no"` a po dokončení příkazu se odstraní. Dokumentované
spuštění má následující tvar:

```bash
docker compose --profile execution run --rm executor <command> <explicit-execution-flag>
```

Compose uvádí `:ro` a `:rw` přímo; žádná proměnná prostředí nepřepíná režim mountu médií. Před každou změnou executor
získá globální execution lock ve workspace. Zapisovatelný mount ani lock neobcházejí požadavky na integritu manifestu,
otisky zdrojů, bezpečnost cílů, úspěšný dry-run, explicitní potvrzení, zastavení při chybě, rollback ani audit.

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

1. **Vložené ID** — pokud název souboru filmu nebo složky seriálu obsahuje právě jedno syntakticky platné ID
   poskytovatele slučitelné s daným typem média, toto ID se vybere a mezipaměť ani online vyhledávání se nepoužije.
   ID na jiném místě, více ID a ID na úrovni epizody entitu nevyřeší a vyžadují ověření.
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
| 5   | Vyhledání ID poskytovatele            | 🚧 Částečně       |
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

Současný online resolver přijímá první vrácený výsledek s pevnou jistotou. Více kandidátů, vysvětlitelné skórování,
prahy nejednoznačnosti, potvrzení názvy epizod, verzované opětovné použití mezipaměti a trvalý původ výběru je nutné
teprve implementovat, aby tato fáze splnila produktové zásady.

#### Fáze 6 — Plánování přejmenování *(plánováno)*

Před jakoukoli změnou souborového systému se vytvoří manifest přejmenování. Bude obsahovat původní cestu, typ média,
normalizovaná data názvu, vybrané ID poskytovatele, jistotu, navrženou novou cestu a stav akce.

Výchozím režimem bude dry-run. Skutečné provedení bude vyžadovat explicitní přepínač.

#### Fáze 7 — Dávkové provedení přejmenování *(plánováno)*

Přejmenování se provede v logických dávkách, tedy filmy po složkách a seriály po jednotlivých pořadech, až po kontrole
manifestu. Executor bude podporovat audit, detekci kolizí, okamžité zastavení při chybě a explicitní rollback přes
neměnný obrácený manifest. Automatický rollback není podporovaný.

#### Fáze 8 — Kontrolní workflow *(plánováno)*

Položky označené ke kontrole se exportují také do formátů HTML a CSV, aby je bylo možné ručně prohlížet mimo JSON.
Tato fáze nemá žádné vedlejší účinky na souborový systém.

## Očekávaný výsledek

Po dokončení by knihovna médií měla mít:

- konzistentní a čitelné názvy souborů a složek;
- lepší rozpoznávání v Jellyfinu pomocí vložených ID poskytovatelů;
- opakovatelný workflow pro budoucí přírůstky knihovny;
- bezpečný proces dávkového přejmenování s možností vrácení změn;
- minimální nepořádek v souborovém systému — bez generovaných metadatových souborů a změn vložených metadat;
- řízené zpracování všech nejistých a nejednoznačných případů.
