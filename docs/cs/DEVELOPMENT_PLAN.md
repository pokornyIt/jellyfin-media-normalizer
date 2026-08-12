# Plán vývoje

[English](../en/DEVELOPMENT_PLAN.md) | [Čeština](DEVELOPMENT_PLAN.md)

Tento dokument sleduje ověřený stav implementace a praktický backlog projektu jellyfin-media-normalizer. Produktová
pravidla určuje [PROJECT-DESCRIPTION.md](PROJECT-DESCRIPTION.md), přijatý směr a zdůvodnění popisuje
[PRODUCT_DEVELOPMENT_BRIEF.md](PRODUCT_DEVELOPMENT_BRIEF.md).

## Přehled aktuálního stavu (2026-07-19)

Ověřené současné schopnosti:

- skenování podporovaných video souborů;
- ploché parsování a klasifikace jednotlivých souborů na film, epizodu seriálu nebo neznámou položku;
- ověření struktury jednotlivého souboru a skórování jistoty;
- základní řetězec vloženého ID, JSON mezipaměti a online resolveru poskytovatele;
- kontrolní sestavy a sestavy nevyřešených položek ve formátech JSON a HTML;
- nastavené kontroly kvality Ruff, Pyright, pytest a pre-commit.

Poslední zaznamenané ověření:

- `uv run pytest -q`: 466 testů prošlo;
- `uv run ruff check src tests`: prošlo;
- `uv run pyright`: 0 chyb.

Tyto datované výsledky dokládají uvedený snapshot, nikoli dokončení cílového produktového workflow.

<!-- markdownlint-disable MD013 -->
| Schopnost                              | Stav                                                   |
| -------------------------------------- | ------------------------------------------------------ |
| Inventarizace a skenování              | Částečně: pouze podporované video soubory              |
| Klasifikace a seskupování entit        | Částečně: pouze plochá klasifikace souborů             |
| Normalizace názvů                      | Částečně: pouze základní parsování názvů souborů       |
| Ověření                                | Částečně: chybí skupinová konzistence                  |
| Vyhledání a výběr poskytovatele        | Částečně: řetězec přijímá první výsledek               |
| Plánování přejmenování                 | Nezahájeno                                             |
| Dávkové přejmenování a rollback        | Nezahájeno                                             |
| Statické kontrolní exporty             | Částečně: JSON a HTML hotové; CSV chybí                |
| Interaktivní kontrolní UI              | Nezahájeno                                             |
<!-- markdownlint-enable MD013 -->

Současné vydání slouží pouze k analýze. Výchozí nastavení dry-run existuje, ale planner ani executor přejmenování
zatím neexistují, takže je nelze prezentovat jako implementovanou bezpečnost přejmenování.

## Nezměnitelná omezení

- Nikdy samostatně nečíst, neparsovat, nevytvářet, neměnit, nemazat ani necílit soubory `.nfo`. Soubor `.nfo` se může
  přesunout pouze jako ignorovaný potomek přejmenované nadřazené složky.
- Ukládat nejvýše jedno vybrané ID poskytovatele pro film nebo seriál a nikdy ID na úrovni epizody.
- Každý symbolický odkaz považovat za nepodporovaný a nekompatibilní. Nikdy jej nenásledovat, nemodelovat, neplánovat
  ani nepřejmenovávat a nepovolit obejití odmítnutí lidskou kontrolou.
- Každé přejmenování musí vycházet ze schváleného, ověřeného a uloženého manifestu.
- Dry-run zůstává výchozí; skutečné provedení vyžaduje explicitní volbu.

## Architektura vydání

- CLI zůstává zdrojem pravdy pro automatizaci a skutečné provedení.
- Odlehčená aplikace FastAPI se serverově vykresleným HTML poskytne hromadnou kontrolu a schvalování.
- UI a CLI používají stejné aplikační služby, přechody stavů a hranice planneru a executoru.
- První UI je bez autentizace, má výchozí adresu `0.0.0.0` a je podporované jen na důvěryhodném počítači nebo privátní
  LAN. Může spouštět plánování a dry-run, ale nemá endpoint pro skutečné provedení.
- SQLite ukládá měnitelný stav workflow. Neměnné manifesty přejmenování a rollbacku zůstávají artefakty JSON.
- Parsery a služby entit zůstávají nezávislé na mediálním serveru. `NamingProfile` validuje kompatibilitu s mediálním
  serverem; `OutputScheme` vykresluje cílové názvy. P0 dodá explicitní implementace Jellyfin s jedním pevným výstupním
  schématem bez dynamického vyhledávání pluginů třetích stran nebo konfigurovatelných šablon.
- Docker Compose je primární cesta operátora. Dlouhodobá aplikace používá `/media:ro`; samostatný jednorázový executor
  v profilu `execution` používá `/media:rw`, nemá síť ani webový port a získává globální execution lock workspace.
- Oficiální obrazy cílí pouze na `linux/amd64` pro WSL, Synology DS925+ a Synology DS723+.

## P0 - Vydání připravené pro operátora

### P0.1 Opravit analytický model a ukládat stav workflow

Cíl:

- Před výběrem poskytovatele nebo plánováním vytvořit důvěryhodné entity a trvalý stav lidských rozhodnutí.

Výstupy:

- Inventarizovat složky, podporovaná videa a titulky, ignorované členství, překročení hloubky a symbolické odkazy bez
  otevírání ignorovaných souborů.
- Přidat typované entity filmu, seriálu, epizody a souvisejícího souboru a klasifikaci rolí složek.
- Udržet parsovaná a seskupená pole entit nezávislá na formátu cílových názvů Jellyfin.
- Seskupit soubory do entit a zapojit ověření skupinové konzistence do produkčního workflow.
- Vynutit přijatá pravidla smíšeného kořene, striktního seriálového layoutu, vícedílných médií, verzí, titulků a
  nekompatibilních složek.
- Přidat SQLite pro běhy, entity, kandidáty, opravy, schválení, poznámky, přechody workflow a metadata auditu s
  verzovanými migracemi.
- S implementací schématu a hranic migrací zaznamenat zaměřené ADR perzistence.

Kritéria přijetí:

- Každá nalezená cesta je spravovaná, ignorovaná s neprůhledným členstvím nebo nahlášená jako nekompatibilní.
- Neúspěšné, nejednoznačné, nekompatibilní entity a entity s nízkou jistotou nelze implicitně schválit.
- Stav přežije restart a operátor nemusí přímo editovat generovaná data JSON, YAML ani SQLite.
- Testy pokrývají seskupování, smíšený obsah, maximální hloubku, upozornění v rootu, titulky a symbolické odkazy.

### P0.2 Implementovat základní kontrolovatelný výběr poskytovatele

Cíl:

- Nahradit první výsledek přijatou deterministickou politikou prvního vydání.

Výstupy:

- Více kandidátů poskytovatele s původem a vysvětlením skóre.
- Verzované konstanty pro skóre, podobnost názvu, náskok, jediného kandidáta a brány roku.
- Přesný rok filmu, spolehlivý vstupní rok seriálu, priorita vloženého a ručního výběru a fallback TMDb/TVDB.
- Opětovné použití mezipaměti podle politiky a uložený stav `ready_for_approval` bez implicitního schválení.
- Seriály bez roku, které neprojdou samotným názvem, zůstávají ke kontrole; potvrzení epizodami není součástí P0.

Kritéria přijetí:

- Pořadí API, popularita, grafika ani úplnost metadat nikdy nerozhodují identitu.
- Projdou testy hranic, konfliktů roku, blízkých a jediných kandidátů, fallbacku a původu mezipaměti.
- Ruční změny jsou explicitní a auditovatelné a nevzniká ID poskytovatele na úrovni epizody.

### P0.3 Implementovat minimální UI pro kontrolu člověkem

Cíl:

- Zajistit praktickou trvalou kontrolu před zavedením plánování přejmenování.

Výstupy:

- Stránky FastAPI pro fronty `review_required`, `ready_for_approval` a nevyřešené položky.
- Vyhledávání, filtrování, řazení a stránkování velkých knihoven.
- Opravy, výběr poskytovatele, schválení, zamítnutí, odložení, poznámky a hlídané hromadné akce.
- Viditelné upozornění důvěryhodné sítě a žádný endpoint pro skutečné změny souborového systému.
- Zaměřené ADR hranic UI a služeb vytvořené s implementovanými rozhraními.

Kritéria přijetí:

- Každá změna stavu používá sdílené služby, je ověřená, trvalá po restartu a auditovatelná.
- Hromadné akce odmítnou smíšený nebo nezpůsobilý výběr a neobcházejí pravidla položek.
- Testy tras prokážou, že první UI nemá operaci skutečného provedení.

### P0.4 Přidat sdílený manifest a planner přejmenování

Cíl:

- Vytvářet deterministické kontrolovatelné plány pouze ze schválených entit.

Výstupy:

- Verzované modely `RenameManifest` a `RenameEntry` pro druhy manifestu `rename` a `rollback`.
- Pluggable kontrakty `NamingProfile` a `OutputScheme` s explicitními registry, `JellyfinNamingProfile` a jedním
  pevným `JellyfinDefaultOutputScheme`. Parsery nesmějí vykreslovat výstupní cesty; nastavitelné šablony zůstávají P3.
- Kanonická serializace JSON a SHA-256 digest.
- Otisky zdrojových souborů a stromové digesty složek s neprůhledným členstvím ignorovaných položek.
- Deterministické cíle pro složky, videa, podporované titulky, části vícedílných médií a verze.
- Trvalé neměnné manifesty a čitelný náhled v UI seskupený podle logických dávek. Náhled zobrazí současné a navržené
  cesty, související soubory, identitu poskytovatele, upozornění, chyby validace a přesný schvalovaný digest; surový
  JSON je artefakt ke stažení, nikoli hlavní kontrolní pohled.

Kritéria přijetí:

- Planner odmítne nevyřešené, neschválené, neplatné, nekompatibilní či konfliktní vstupy a symbolické odkazy.
- Opakované plánování nad nezměněným schváleným stavem vytvoří ekvivalentní položky a digest.
- Každý cíl splňuje přijatá pravidla názvů a struktury pro Jellyfin.
- Manifest ukládá identifikátory a verze profilu názvů i výstupního schématu a vykreslený výstup projde společným
  ověřením cest, kolizí, ID poskytovatele, `.nfo` a bezpečnosti.

### P0.5 Implementovat bezpečné provedení a rollback

Cíl:

- Provádět pouze ověřené manifesty s explicitním řízením a obnovitelnými důkazy částečného selhání.

Výstupy:

- Výchozí dry-run a explicitní režim skutečného provedení.
- Kontroly integrity manifestu, otisků, kolizí, nepřítomnosti cíle a globálního locku na určených hranicích.
- Trvalé stavy úspěšných, neúspěšných, čekajících a nejistých operací se zastavením při první chybě.
- Neměnný manifest rollbacku jen z potvrzených úspěšných operací ve sdíleném schématu, s obráceným pořadím seznamu,
  odkazem na původní operaci, současným otiskem zdroje a vlastním digestem.
- Samostatný dry-run, potvrzení a audit rollbacku; žádný automatický rollback ani manifest shellových příkazů.
- Zaměřené ADR bezpečnosti provedení vytvořené s konkrétním návrhem locku a auditu.

Kritéria přijetí:

- Žádná změna neobchází ověřený manifest a dry-run nic nezapisuje.
- Změněné zdroje, existující cíle, kolize, neplatné digesty a souběžné provedení selžou před nebezpečnou změnou.
- Provedení nikdy nemění vstupní manifest ani nepřepisuje existující cestu.
- Testy chyb prokážou klasifikaci auditu a bezpečnou tvorbu manifestu rollbacku.

### P0.6 Integrovat operace workflow do CLI a UI

Cíl:

- Zpřístupnit sdílené služby planneru a executoru v jasném workflow operátora.

Výstupy:

- Příkazy CLI pro plán, validaci, dry-run a explicitní provedení manifestů přejmenování a rollbacku.
- Náhled manifestu a schválení přesného digestu, spuštění planneru, výsledky dry-run a historie auditu v UI.
- Jasné souhrny, cesty artefaktů, kódy selhání a vazby mezi původními běhy a rollbackem.

Kritéria přijetí:

- Skutečné provedení zůstává jen v CLI a vyžaduje explicitní přepínač.
- CLI a UI vytvářejí konzistentní stavy a výsledky přes sdílené služby.
- End-to-end testy pokrývají analýzu, schválení, plán, dry-run, chybu provedení a dry-run rollbacku.

### P0.7 Zabalit podporované nasazení Compose

Cíl:

- Poskytnout podporované nasazení pro jediného operátora bez oslabení bezpečnosti souborového systému.

Výstupy:

- Produkční Dockerfile bez root uživatele, `.dockerignore`, Compose, healthcheck a příklad prostředí.
- Dlouhodobá aplikace s médii pouze pro čtení a trvalým workspace.
- Jednorázová služba profilu execution s explicitně zapisovatelnými médii, bez sítě, webového portu a restartu.
- Reprodukovatelný build `linux/amd64`, smoke test, metadata obrazu a release workflow.
- Zaměřené ADR nasazení pro mounty, oprávnění, upgrade, zálohu a obnovu.

Kritéria přijetí:

- Běžné `docker compose up` nemůže měnit knihovnu médií.
- Nepodporované platformy selžou běžně bez skryté emulace.
- Databáze a artefakty workspace přežijí upgrade s otestovaným postupem migrace a zálohy.

### P0.8 Dokončit dokumentaci operátora a end-to-end ověření

Cíl:

- Zajistit použitelnost podporovaného workflow bez nezdokumentovaných znalostí.

Výstupy:

- Compose-first quick start, nastavení, kontrola, provedení, rollback, záloha, upgrade a řešení potíží.
- Oddělené příklady aplikace jen pro čtení a explicitně zapisujícího executoru.
- Reprezentativní fixture velké knihovny a ověření výkonu.
- Aktualizované dvojice anglických a českých README a dokumentace podle skutečného chování.

Kritéria přijetí:

- Nový operátor dokončí bezpečné workflow bez přímé editace stavových souborů nebo hádání příkazů.
- Dokumentace nevydává plánované chování, nepodporované platformy ani veřejné vystavení za podporované.
- Projdou kontroly kvality repozitáře a end-to-end testy workflow.

## P1 - Důležité navazující práce

### P1.1 Přidat potvrzení názvy epizod

- Nejprve změřit kontrolní frontu seriálů bez roku.
- Pokud to data odůvodní, implementovat přijaté vzorkování dvou nebo tří epizod a skórování 75/25.
- Důkazy epizod cachovat opakovatelně a nikdy nevytvářet ID poskytovatele na úrovni epizody.

### P1.2 Dokončit exporty CSV a provedení

- Přidat kontrolní a nevyřešené exporty CSV ze stejné trvalé datové sady.
- Přidat JSON souhrn provedení; CSV jen tehdy, pokud má konkrétní hodnotu pro operátora.

### P1.3 Zlepšit sledování dlouhých běhů

- Přidat korelační ID, strukturované události začátku a konce, dobu, průběh a volitelné trvalé logy.
- Nezapisovat do diagnostiky tajné hodnoty ani URL s přihlašovacími údaji.

### P1.4 Zlepšit ergonomii CLI

- Přidat konzistentní příklady, zdokumentované návratové kódy, přepínače sestav a použitelné souhrny.
- Bezpečnostní přepínače ponechat explicitní a nezavádět pohodlné výchozí hodnoty umožňující změny.

## P2 - Údržba a volitelné zpevnění

### P2.1 Sladit názvy struktury testů

- Sladit existující nesoulad `tests/parses` se `src/parsers` bez regresí sběru testů.

### P2.2 Postupně zpřísnit typovou kontrolu

- Nejprve zpřísnit nové kritické moduly a doplnit cílené anotace tam, kde zůstanou užitečné a bez šumu.

### P2.3 Přidat autentizovaný vzdálený přístup

- Autentizaci, session, CSRF, práci s důvěryhodnou proxy a návod k HTTPS reverse proxy řešit jako nadstavbu.
- Integraci Synology účtu ponechat volitelnou a nezávislou na provozu v důvěryhodné privátní síti.

## P3 - Seznam budoucích možností (neblokuje vydání)

### P3.1 Přidat další profily názvů pro mediální servery

- Před implementací prozkoumat a určit profil Plex včetně tagů poskytovatele a názvů epizod.
- Emby považovat za alias profilu Jellyfin jen tehdy, pokud testy kompatibility prokážou shodný požadovaný výstup;
  jinak přidat samostatnou implementaci.
- Další profily zvažovat jen tehdy, když zapadnou do základního modelu a zachovají všechna bezpečnostní pravidla.
- Vyloučit workflow Kodi vyžadující `.nfo` spravované aplikací.

### P3.2 Zobecnit logiku jazyků a lokalizace

- Oddělit jazyk metadat, fallback zobrazovaného názvu, značky zvuku a značky titulků.
- Ponechat češtinu a `CZ` jako výchozí hodnoty prvního vydání a navrhnout ověřené jazykové tagy a mapování názvů.
- Předat tyto volby do `OutputScheme` místo větvení parserů nebo serverových profilů podle jazyka.

### P3.3 Přidat omezené šablony názvů

- Rozšířit `OutputScheme` o pojmenované předvolby a typované tokeny, například
  `{{year}} - {{movie_title}} - {{provider_tag}} - {{language}}`, s náhledem a ověřením.
- Odmítnout libovolný kód, neplatné cesty, kolize, nejednoznačný výstup a šablony obcházející profil nebo bezpečnost.

## Doporučené pořadí implementace

1. Opravit seskupování entit a přidat SQLite pro stav workflow.
2. Implementovat základní kontrolovatelný výběr poskytovatele.
3. Implementovat minimální trvalé kontrolní UI.
4. Přidat sdílené schéma manifestu, planner a náhled v UI.
5. Přidat bezpečný dry-run, provedení, audit a rollback.
6. Integrovat operace CLI a UI přes sdílené služby.
7. Zabalit a ověřit podporované nasazení Compose.
8. Dokončit dokumentaci operátora a end-to-end ověření.
9. Před výběrem prací P1, P2 nebo wishlistu změřit skutečné provozní potíže.

## Průřezová strategie testování

- Seskupování domény, role složek, limit hloubky, titulky, vícedílná média, verze, smíšený obsah a symlinky.
- Migrace SQLite, trvalost po restartu, platné přechody stavů, audit a souběžné změny.
- Hranice poskytovatele, konflikty roku, fallback, nejednoznačnost, původ mezipaměti a explicitní ruční změny.
- Filtrování a stránkování UI, opravy, schválení, hlídané hromadné akce a nepřítomnost skutečného provedení.
- Determinismus manifestu a stromového digestu, změny zdrojů, kolize a odmítnutí symbolických odkazů.
- Dry-run bez změn, explicitní provedení, globální lock, zastavení při chybě a trvalé stavy auditu.
- Pořadí rollbacku ve sdíleném schématu, integrita, odmítnutí změněného zdroje a existujícího cíle a samostatný audit.
- End-to-end workflow CLI a UI nad reprezentativními fixtures bez živých API a externích souborových systémů.

## Definice dokončení pro připravenost operátora

- Podporovaná aplikace Compose se spustí bez Pythonu na hostiteli a ve výchozím stavu připojí média jen pro čtení.
- Entity, kandidáti, opravy, schválení, poznámky a stav auditu přežijí restart.
- Minimální UI umožní praktickou kontrolu a nemá endpoint skutečného provedení.
- Před provedením je povinný schválený, ověřený a neměnný manifest a úspěšný dry-run.
- Skutečné provedení je explicitní, pouze v CLI, zamčené, auditované, zastaví se při chybě a má popsaný rollback.
- Anglická a česká dokumentace operátora popisuje nastavení až obnovu a odpovídá otestovanému chování.

## Rutina aktualizace

Při zahájení práce označte související položku backlogu v issue trackeru jako rozpracovanou a propojte implementační
PR a testy. Po dokončení zaznamenejte ověření a pro zbývající dluh vytvořte samostatná navazující issues. Datované
důkazy ověření udržujte oddělené od tvrzení o produktové úplnosti.
