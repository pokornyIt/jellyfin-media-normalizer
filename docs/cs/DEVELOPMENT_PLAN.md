# Plán vývoje

[English](../en/DEVELOPMENT_PLAN.md) | [Čeština](DEVELOPMENT_PLAN.md)

Tento dokument sleduje stav implementace a další kroky projektu `jellyfin-media-normalizer`.

Má se průběžně aktualizovat a sloužit jako praktický kontrolní seznam pro realizaci následujících fází.

## Snímek aktuálního stavu (2026-07-19)

Ověřeno jako implementované a stabilní:

- proces skenování a inventarizace souborového systému;
- proces parsování a klasifikace filmů, televizních epizod a neznámých položek;
- proces ověřování struktury, konzistence a míry jistoty;
- vyhledání poskytovatele v pořadí vložené ID -> mezipaměť -> řetězec online resolverů;
- sestavy: kontrolní JSON, JSON nevyřešených položek, kontrolní HTML a HTML nevyřešených položek;
- bezpečné výchozí běhové nastavení včetně dry-run;
- místní kontroly kvality: Ruff, Pyright, pytest a pre-commit hooky.

Ověřený stav kvality:

- `uv run pytest -q`: 466 testů prošlo;
- `uv run ruff check src tests`: prošlo;
- `uv run pyright`: 0 chyb.

Hlavní chybějící schopnost produktu:

- Plánování a provádění přejmenování dosud nejsou implementovány jako plnohodnotné vrstvy.

Další riziko rozsahu a použitelnosti:

- Samotné CLI a ruční úpravy souborů nebudou dobře škálovat pro velké dávky se stovkami až tisíci souborů.

## Neměnná omezení

Všechny vývojové úkoly musí zachovat tato pravidla:

- Nikdy samostatně nečíst, neparsovat, nevytvářet, neměnit, nemazat ani necílit na soubory `.nfo`. Soubor `.nfo` se
  smí přesunout pouze jako ignorovaný obsah přejmenované nadřazené složky.
- Právě jedno ID poskytovatele pro entitu filmu nebo televizního seriálu.
- Nikdy nepřejmenovávat bez ověřeného plánu.
- Nikdy neprovádět dávkové přejmenování bez vytvořeného manifestu.
- Dry-run musí zůstat výchozím režimem spuštění.

## Stav fází

| Fáze | Oblast                                | Stav                         |
| ---- | ------------------------------------- | ---------------------------- |
| 1    | Inventarizace a skenování             | Hotovo                       |
| 2    | Klasifikace                           | Hotovo                       |
| 3    | Normalizace názvů                     | Hotovo                       |
| 4    | Ověření                               | Hotovo                       |
| 5    | Vyhledání ID poskytovatele            | Hotovo                       |
| 6    | Plánování přejmenování (manifest)     | Nezahájeno                   |
| 7    | Dávkové provedení přejmenování        | Nezahájeno                   |
| 8    | Exporty kontrolního workflow          | Částečně (HTML ano, CSV ne)  |

## Směr UX a produktu pro velké knihovny

Rozhodnutí k implementaci:

- Zachovat CLI jako zdroj pravdy pro automatizaci a dávkové operace.
- Přidat lehkou webovou aplikační vrstvu (FastAPI a HTML vykreslované na serveru) pro hromadnou kontrolu a schvalování.

Odůvodnění:

- Současný přístup je provozně robustní, ale neefektivní při třídění tisíců nejednoznačných položek.
- Webové UI může nabídnout filtrování, hromadné schválení či zamítnutí a bezpečnější workflow s účastí člověka.

Architektonická omezení UI:

- UI nesmí obcházet bezpečnostní brány planneru a executoru.
- Akce UI musí zapisovat do manifestu nebo stavu kontroly a následně spouštět stejný ověřený proces jako CLI.
- Dry-run zůstává výchozí pro všechny exekuční akce spuštěné z UI.
- UI musí dodržet pravidlo jediného ID poskytovatele na film či seriál a zákaz souborů `.nfo`.

## Fronta implementace

## P0 – Kritická cesta blokující vydání

### 1. Přidat modely přejmenování

Cíl:

- Zavést sdílené datové kontrakty pro plánování a provádění.

Výstupy:

- model `RenameEntry`;
- model `RenameManifest`;
- stabilní pole schématu: zdrojová cesta, cílová cesta, důvod, jistota, vazba na poskytovatele a metadata dávky.

Akceptační kritéria:

- Modely jsou plně typované a ověřované.
- Modely používají plannery, executory i výstupní sestavy a souhrny.

### 2. Implementovat vrstvu plannerů

Cíl:

- Vytvořit balíček plannerů pro generování ověřených manifestů přejmenování.

Výstupy:

- modul plannerů se službou pro sestavení manifestu;
- serializace schématu manifestu do `data/workspace/manifests`;
- ověřovací brána před označením manifestu za spustitelný.

Akceptační kritéria:

- Planner přijímá parsované a ověřené položky médií.
- Výstup planneru je deterministický a plně serializovatelný.
- Planner odmítá neplatné, nejednoznačné a nevyřešené položky.

### 3. Implementovat vrstvu executorů

Cíl:

- Vytvořit balíček executorů pro bezpečné dávkové přejmenování pouze z manifestu.

Výstupy:

- executor dry-run jako výchozí chování;
- režim skutečných změn s explicitním přihlášením;
- protokol pro vrácení každé provedené operace v dávce;
- kontroly kolizí a existence cíle.

Akceptační kritéria:

- Žádná cesta přejmenování neobchází vstupní manifest.
- Dry-run nemění souborový systém.
- Chyby se protokolují s dostatkem kontextu pro opakování nebo ruční vrácení změn.

### 4. Přidat příkazy CLI pro workflow přejmenování

Cíl:

- Vyjádřit v CLI explicitní tok parse -> plan -> execute.

Výstupy:

- příkaz `plan-rename`;
- příkaz `execute-rename`;
- volitelný příkaz `validate-manifest`.

Akceptační kritéria:

- `execute-rename` okamžitě skončí chybou, pokud manifest chybí nebo je neplatný.
- Skutečné provedení vyžaduje explicitní přepínač a ve výchozím stavu není možné.
- Příkazy vypisují srozumitelné souhrny pro uživatele a cesty k výstupům.

### 5. Definovat architektonický kontrakt CLI a UI (ADR)

Cíl:

- Před implementací webové vrstvy ustálit integrační hranice.

Výstupy:

- ADR popisující odpovědnosti CLI a UI;
- jasná rozhraní služeb použitelná z CLI i webové aplikace;
- bezpečnostní model místního nasazení včetně autentizace, zásad CSRF a předpokladů důvěryhodné sítě.

Akceptační kritéria:

- Vstupní body CLI a UI neduplikují obchodní logiku.
- Planner a executor zůstávají jediným zdrojem pravdy pro změny.
- Model hrozeb a provozní předpoklady jsou explicitně zdokumentované.

## P1 – Důležité následné práce

### 5. Dokončit exporty sestav

Cíl:

- Rozšířit výstupy sestav pro provoz a kontrolu.

Výstupy:

- CSV reportér pro kontrolní a nevyřešené datové sady;
- volitelný formát souhrnu provedení manifestu, nejprve JSON a případně CSV.

Akceptační kritéria:

- Exportní příkazy vytvářejí platné soubory ze stejné zdrojové datové sady.
- Výstup jasně označuje nevyřešené položky a položky vyžadující ruční kontrolu.

### 6. Zlepšit provozní protokolování dlouhých běhů

Cíl:

- Posílit pozorovatelnost při zpracování velkých knihoven.

Výstupy:

- strukturované události začátku a konce příkazu s uplynulým časem;
- korelační ID běhu v kontextu protokolu;
- volitelný zápis protokolu do `data/workspace/logs` vedle standardního výstupu.

Akceptační kritéria:

- Dlouhé běhy lze sledovat od začátku do konce podle jediného identifikátoru.
- Operátor může protokoly prohlédnout i po skončení příkazu bez historie terminálu.

### 7. Zlepšit přívětivost CLI

Cíl:

- Zlepšit ergonomii příkazů a kvalitu zpětné vazby.

Výstupy:

- jednotná nápověda s praktickými příklady hlavních příkazů;
- dokumentované návratové kódy pro úspěch, režim varování ověření a fatální chybu;
- volitelné přepínače `--no-html` a `--no-json` pro sestavy příkazu `parse`.

Akceptační kritéria:

- Běžný operátorský postup je pochopitelný pouze z výstupu `--help`.
- Chování generování sestav je explicitní a konfigurovatelné.

### 8. Implementovat webové UI pro kontrolu a schválení

Cíl:

- Umožnit škálovatelnou ruční kontrolu a schválení velkého množství rozhodnutí o přejmenování.

Výstupy:

- aplikace FastAPI se stránkami položek vyžadujících kontrolu a nevyřešených položek;
- hledání, filtrování, řazení a stránkování velkých datových sad;
- hromadné akce: schválit, zamítnout, odložit a přidat poznámku či důvod;
- náhled manifestu s cestami před a po změně, ID poskytovatele, jistotou a rizikovými příznaky;
- endpointy spouštějící planner a dry-run executoru.

Akceptační kritéria:

- Operátor zpracuje rozsáhlé kontrolní sady výrazně rychleji než úpravami jednotlivých souborů.
- Každá akce je auditovatelná a trvale uložená včetně toho, kdo, kdy a co změnil.
- UI nikdy neprovede skutečné přejmenování bez explicitního potvrzení a bezpečnostních kontrol.

## P2 – Údržba a konzistence

### 9. Sjednotit pojmenování struktury testů

Cíl:

- Odstranit nesoulad v názvu adresáře testů.

Výstupy:

- sladit `tests/parses` s názvem `src/parsers`;
- zachovat stabilní importy a vyhledávání testů.

Akceptační kritéria:

- Cesty testů a zdrojů si zřetelně odpovídají.
- Nedojde k regresi při sběru testů.

### 10. Postupně zpřísnit zásady kontroly typů

Cíl:

- Bezpečně zvýšit přísnost Pyrightu.

Výstupy:

- nejprve znovu posoudit hlášení neznámých typů v nových modulech plannerů a executorů;
- doplnit cílené anotace ve slabších místech nalezených během implementace.

Akceptační kritéria:

- Nové kritické moduly mají silnější typové pokrytí.
- Typové chyby zůstávají relevantní a bez zbytečného šumu.

### 11. Úplnost dokumentace pro operátory

Cíl:

- Zajistit soulad dokumentace se skutečným workflow a usnadnit první použití.

Výstupy:

- po dokončení fází 6 a 7 doplnit dokumentaci workflow přejmenování;
- doplnit řešení potíží s klíči poskytovatelů, mezipamětí a nevyřešenými shodami;
- doplnit ukázkovou posloupnost scan -> parse -> plan -> execute dry-run;
- doplnit příručku webového UI pro místní spuštění, kontrolní workflow a bezpečnostní model.

Akceptační kritéria:

- Nový operátor zvládne podle dokumentace bezpečný workflow bez dohadů.
- Dokumentace odpovídá současným příkazům CLI a výstupům sestav.

## Doporučené pořadí implementace

1. Modely a schéma přejmenování.
2. Služba planneru a generování manifestu.
3. Služba executoru s výchozím dry-run.
4. Integrace příkazů plan a execute do CLI.
5. Architektonický ADR pro CLI a UI.
6. Testovací sada planneru a executoru.
7. Rozšíření sestav o CSV.
8. Zlepšení protokolování a UX CLI.
9. Kontrolní webové UI FastAPI a HTML.
10. Závěrečná aktualizace dokumentace workflow přejmenování a provozu UI.

## Strategie testování zbývajících fází

Požadované testy funkcí planneru a executoru:

- vytvoření platného manifestu z čistých parsovaných vstupů;
- odmítnutí manifestu s nevyřešenými nebo konfliktními položkami;
- potvrzení nulových změn souborového systému při dry-run příkazu `execute-rename`;
- tvrdé selhání `execute-rename` bez explicitního přepínače provedení;
- protokolování selhání dávky a integrita protokolu pro vrácení změn;
- koncový test CLI nad testovací knihovnou;
- integrační testy UI pro schvalovací akce a přechody stavů manifestu;
- test toku UI do dry-run executoru bez změn souborového systému.

## Definice dokončení workflow přejmenování

Workflow přejmenování je dokončen až po splnění všech následujících bodů:

- Generování manifestu existuje a je před provedením povinné.
- Přejmenování používá ve výchozím stavu dry-run.
- Skutečné provedení vyžaduje explicitní přihlášení.
- Pro každý běh dávky vzniká protokol pro vrácení změn.
- Příkazy CLI pro plánování a provedení jsou zdokumentované a otestované.
- Koncové testy ověřují bezpečné chování při selhání.

## Rutina provozní aktualizace

Při zahájení úkolu:

- Přesuňte jej v tomto souboru nebo souvisejícím systému úkolů do stavu Rozpracováno.
- Připojte odkazy na implementační pull requesty a související testy.

Po dokončení úkolu:

- Označte jej jako Hotovo a doplňte krátké poznámky k ověření.
- Následný technický dluh zaznamenejte jako nový úkol fronty s prioritou.

Tento soubor udržujte jako jediný praktický plán realizace vývoje.
