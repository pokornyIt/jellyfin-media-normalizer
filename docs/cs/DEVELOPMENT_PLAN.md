# Plán vývoje

[English](../en/DEVELOPMENT_PLAN.md) | [Čeština](DEVELOPMENT_PLAN.md)

Tento dokument sleduje stav implementace a další kroky projektu `jellyfin-media-normalizer`.

Má se průběžně aktualizovat a sloužit jako praktický kontrolní seznam pro realizaci následujících fází.

## Snímek aktuálního stavu (2026-07-19)

Ověřeno jako implementované a stabilní:

- proces skenování a inventarizace souborového systému;
- proces parsování a klasifikace filmů, televizních epizod a neznámých položek;
- proces ověřování struktury, konzistence a míry jistoty;
- základní přenos vyhledání poskytovatele v pořadí vložené ID -> mezipaměť -> řetězec online resolverů;
- sestavy: kontrolní JSON, JSON nevyřešených položek, kontrolní HTML a HTML nevyřešených položek;
- bezpečné výchozí běhové nastavení včetně dry-run;
- místní kontroly kvality: Ruff, Pyright, pytest a pre-commit hooky.

Ověřený stav kvality:

- `uv run pytest -q`: 466 testů prošlo;
- `uv run ruff check src tests`: prošlo;
- `uv run pyright`: 0 chyb.

Hlavní chybějící schopnosti produktu:

- Vyhledání poskytovatele stále přijímá první online výsledek s pevnou jistotou. Kandidáti ke kontrole,
  vysvětlitelné skórování, prahy nejednoznačnosti, potvrzení názvy epizod a důvěryhodný původ mezipaměti nejsou
  implementované.
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
| 5    | Vyhledání ID poskytovatele            | Částečně                     |
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
- Akce UI musí zapisovat do trvalého stavu kontroly nebo manifestu a používat stejné aplikační služby jako CLI.
- První UI může spustit dry-run, ale nemá endpoint skutečného přejmenování; provedení zůstává pouze v CLI.
- UI musí dodržet pravidlo jediného ID poskytovatele na film či seriál a zákaz souborů `.nfo`.
- První UI je neautentizované, naslouchá na konfigurovatelné adrese s výchozí hodnotou `0.0.0.0` a je podporované
  pouze na důvěryhodném počítači nebo privátní LAN. Vystavení veřejnému internetu není podporované.

Kontrakt vydání kontejneru:

- sestavovat, kontrolovat smoke testem a publikovat pouze obrazy `linux/amd64` pro prostředí WSL a cílová zařízení
  Synology DS925+ a DS723+;
- v prvním vydání nepublikovat ARM, 32bitové ani multi-platformní manifesty obrazů;
- nenastavovat v Compose `platform`, aby nepodporované hostitele selhaly místo skrytého použití emulace;
- zachovat Dockerfile přiměřeně přenositelný a přidat pokročilé příklady nativního a cross-buildu, jasně označené
  jako best-effort a nepodporované.
- dlouhodobé službě `app` ponechat média explicitně pouze ke čtení; přidat samostatný jednorázový `executor` v profilu
  `execution` s explicitním zapisovatelným mountem, bez sítě, webového portu a restartu;
- zakázat proměnný režim mountu médií a vedle aktivace profilu vyžadovat explicitní přepínač CLI a globální execution
  lock ve workspace.

## Fronta implementace

## P0 – Kritická cesta blokující vydání

### 1. Implementovat kontrolovatelný výběr kandidáta poskytovatele

Cíl:

- Nahradit párování prvního výsledku přijatými deterministickými zásadami výběru poskytovatele.

Výstupy:

- odpovědi s více kandidáty poskytovatele, původem výběru a vysvětlením skóre;
- verzované konstanty zásad pro běžné skóre, podobnost názvu, náskok kandidáta a práh jediného kandidáta;
- brány přesného roku filmu a spolehlivého vstupního roku seriálu;
- deterministické potvrzení první, prostřední a poslední epizodou pro způsobilé seriály bez roku;
- opětovné použití mezipaměti podle verze zásad, které odliší schválené výběry od neprokázaných kandidátů;
- trvalý stav `ready_for_approval` bez implicitního schválení přejmenování.

Akceptační kritéria:

- Pořadí výsledků API samo nikdy neurčuje výběr poskytovatele.
- Testy pokrývají hranice prahů, neshodu roku, těsné kandidáty, jediného kandidáta, záložního poskytovatele, potvrzení
  epizodami a chybějící kombinace řady a epizody.
- Vyhledání epizod nikdy nevytváří ID poskytovatele na úrovni epizody.
- Ruční změny zůstávají explicitní a auditovatelné; staré nebo neprokazatelné záznamy mezipaměti vyžadují nové
  skórování nebo kontrolu.

### 2. Přidat modely přejmenování

Cíl:

- Zavést sdílené datové kontrakty pro plánování a provádění.

Výstupy:

- model `RenameEntry`;
- model `RenameManifest`;
- stabilní pole schématu: zdrojová cesta, cílová cesta, otisk zdroje, důvod, jistota, vazba na poskytovatele a metadata
  dávky;
- kanonická serializace manifestu s SHA-256 digestem.

Akceptační kritéria:

- Modely jsou plně typované a ověřované.
- Modely používají plannery, executory i výstupní sestavy a souhrny.
- Symbolické odkazy nelze reprezentovat jako spustitelné zdroje přejmenování.

### 3. Implementovat vrstvu plannerů

Cíl:

- Vytvořit balíček plannerů pro generování ověřených manifestů přejmenování.

Výstupy:

- modul plannerů se službou pro sestavení manifestu;
- serializace schématu manifestu do `data/workspace/manifests`;
- ověřovací brána před označením manifestu za spustitelný;
- otisky souborů z relativní cesty, typu položky, velikosti a času změny;
- stromové digesty složek zahrnující neprůhledné členství ignorovaných potomků bez jejich otevření či modelování.

Akceptační kritéria:

- Planner přijímá parsované a ověřené položky médií.
- Výstup planneru je deterministický a plně serializovatelný.
- Planner odmítá neplatné, nejednoznačné a nevyřešené položky.
- Planner odmítá každý symbolický odkaz a každou plánovanou složku, která jej obsahuje.

### 4. Implementovat vrstvu executorů

Cíl:

- Vytvořit balíček executorů pro bezpečné dávkové přejmenování pouze z manifestu.

Výstupy:

- executor dry-run jako výchozí chování;
- režim skutečných změn s explicitním přihlášením;
- trvalý audit každé operace s potvrzenými úspěšnými, neúspěšnými, čekajícími a nejistými stavy;
- generování neměnného JSON manifestu rollbacku z potvrzených úspěšných operací v opačném pořadí provedení;
- kontroly kolizí a existence cíle;
- kontroly otisků zdrojů při dry-run, před každou dávkou a před každou operací;
- stabilní chybové kódy změněného zdroje a vazba úspěšného dry-run na přesný digest manifestu;
- položky rollbacku propojené s původními operacemi s obrácenými cestami, otisky, očekávanými nepřítomnými cíli,
  pořadím a důvody obnovy;
- globální execution lock ve workspace sdílený skutečným přejmenováním a rollbackem.

Akceptační kritéria:

- Žádná cesta přejmenování neobchází vstupní manifest.
- Dry-run nemění souborový systém.
- Chyby se protokolují s dostatkem kontextu pro opakování nebo ruční vrácení změn.
- Každý rozdíl zdroje zastaví celý běh provádění a vyžaduje nové schválené workflow od skenování po dry-run;
  executor nikdy neobnovuje otisky na místě.
- Bezpečnost cíle se nezávisle kontroluje při plánování, dry-run a bezprostředně před provedením.
- První selhání operace zastaví celý běh bez automatického rollbacku.
- Rollback používá běžný executor, povinný dry-run, explicitní potvrzení, zákaz přepsání a samostatný audit; provedení
  nikdy nemění manifest rollbacku.
- Souběžné skutečné přejmenování nebo rollback selže před první změnou souborového systému.

### 5. Přidat příkazy CLI pro workflow přejmenování

Cíl:

- Vyjádřit v CLI explicitní tok parse -> plan -> execute.

Výstupy:

- příkaz `plan-rename`;
- příkaz `execute-rename`;
- volitelný příkaz `validate-manifest`;
- CLI workflow pro kontrolu, dry-run a explicitní provedení vytvořených manifestů rollbacku stejným executorem.

Akceptační kritéria:

- `execute-rename` okamžitě skončí chybou, pokud manifest chybí nebo je neplatný.
- Skutečné provedení vyžaduje explicitní přepínač a ve výchozím stavu není možné.
- Příkazy vypisují srozumitelné souhrny pro uživatele a cesty k výstupům.
- Výstup při selhání označí manifest rollbacku a rozliší dokončenou, neúspěšnou, čekající a nejistou práci.

### 6. Definovat architektonický kontrakt CLI a UI (ADR)

Cíl:

- Před implementací webové vrstvy ustálit integrační hranice.

Výstupy:

- ADR popisující odpovědnosti CLI a UI;
- jasná rozhraní služeb použitelná z CLI i webové aplikace;
- kontrakt počátečního nasazení zahrnující konfigurovatelné naslouchání, předpoklad důvěryhodné privátní sítě,
  upozornění při naslouchání mimo loopback a absenci endpointu skutečného provedení v UI;
- hranice pro pozdější nadstavbu autentizace a zabezpečení vzdáleného přístupu.

Akceptační kritéria:

- Vstupní body CLI a UI neduplikují obchodní logiku.
- Planner a executor zůstávají jediným zdrojem pravdy pro změny.
- Předpoklady počáteční důvěryhodné sítě a nepodporované veřejné vystavení jsou explicitně zdokumentované.

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
- Každá akce je trvale uložená a auditovatelná s časem, změnou a aktérem jediného místního operátora.
- UI zpřístupňuje akce planneru a dry-run, ale nemá endpoint skutečného provedení přejmenování.
- Konfigurovatelná adresa naslouchání má výchozí hodnotu `0.0.0.0` a spuštění mimo loopback zobrazí upozornění.

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
- doplnit příručku webového UI pro místní spuštění, kontrolní workflow a bezpečnostní model;
- v rychlém začátku pro operátory dokumentovat podporovaný obraz AMD64 a nepodporované příklady nativního sestavení
  a sestavení ze zdrojů přes `buildx` umístit do pokročilé dokumentace;
- dokumentovat běžné spuštění Compose pouze ke čtení odděleně od explicitního jednorázového příkazu profilu
  `execution`.

Akceptační kritéria:

- Nový operátor zvládne podle dokumentace bezpečný workflow bez dohadů.
- Dokumentace odpovídá současným příkazům CLI a výstupům sestav.
- Dokumentace nikdy neprezentuje netestovanou architekturu jako podporovanou.
- Běžný rychlý začátek nelze zaměnit za nasazení se zapisovatelnými médii.

### 12. Přidat autentizované nasazení pro vzdálený přístup

Cíl:

- Po dokončení funkčního UI pro jediného operátora zabezpečit vzdálený přístup.

Možný rozsah:

- autentizace jediného operátora, session a ochrana CSRF;
- návod k HTTPS reverse proxy a zacházení s důvěryhodnou proxy;
- volitelná širší podpora účtů nebo rolí, pokud vznikne konkrétní potřeba;
- volitelná integrace se Synology účtem jako nepovinné rozšíření.

Akceptační kritéria:

- Nadstavba se nestane závislostí UI pro důvěryhodnou privátní síť.
- Každý nově podporovaný režim vzdáleného přístupu má explicitní bezpečnostní a provozní dokumentaci.

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
11. Volitelné zabezpečení autentizovaného vzdáleného přístupu.

## Strategie testování zbývajících fází

Požadované testy funkcí planneru a executoru:

- vytvoření platného manifestu z čistých parsovaných vstupů;
- odmítnutí manifestu s nevyřešenými nebo konfliktními položkami;
- determinismus manifestu a digestu složky při opakovaných skenech nezměněných fixtur;
- odmítnutí symbolických odkazů bez následování jejich cílů;
- detekce změněných cest, typů položek, velikostí, časů změny a členství ve složce;
- odmítnutí výsledku dry-run vytvořeného pro jiný digest manifestu;
- odmítnutí souběžného provedení, pokud je globální execution lock ve workspace obsazený;
- potvrzení nulových změn souborového systému při dry-run příkazu `execute-rename`;
- tvrdé selhání `execute-rename` bez explicitního přepínače provedení;
- zastavení při chybě, trvalé stavy auditu, pořadí manifestu rollbacku a integrita manifestu rollbacku;
- odmítnutí rollbacku při změně otisku jeho zdroje nebo existujícím cíli;
- koncový test CLI nad testovací knihovnou;
- integrační testy UI pro schvalovací akce a přechody stavů manifestu;
- test toku UI do dry-run executoru bez změn souborového systému.
- testy tras UI prokazující, že první vydání nemá endpoint skutečného provedení přejmenování.

## Definice dokončení workflow přejmenování

Workflow přejmenování je dokončen až po splnění všech následujících bodů:

- Generování manifestu existuje a je před provedením povinné.
- Přejmenování používá ve výchozím stavu dry-run.
- Skutečné provedení vyžaduje explicitní přihlášení.
- První chyba zastaví běh a vytvoří trvalý audit a neměnný manifest rollbacku pro potvrzené úspěšné operace.
- Rollback vyžaduje vlastní úspěšný dry-run a explicitní přihlášení přes běžný executor.
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
