# Zadání vývoje produktu

[English](../en/PRODUCT_DEVELOPMENT_BRIEF.md) | [Čeština](PRODUCT_DEVELOPMENT_BRIEF.md)

## Účel dokumentu

Tento dokument vymezuje ucelený směr produktu `jellyfin-media-normalizer` před implementací plánování a provádění
přejmenování a interaktivního uživatelského rozhraní.

Slouží jako podklad pro pozdější sladění dokumentace. Po přijetí rozhodnutí v tomto dokumentu se mají příslušné
části promítnout do:

- [Popisu projektu](PROJECT-DESCRIPTION.md) pro stabilní rozsah produktu a doménová pravidla;
- [Plánu vývoje](DEVELOPMENT_PLAN.md) pro implementační frontu a aktuální stav;
- [README](../../README.cs.md) pro instalaci a operátorské workflow;
- architektonických rozhodnutí o perzistenci, nasazení UI a bezpečnosti přejmenování.

Toto zadání popisuje cílový produkt. Netvrdí, že všechny uvedené schopnosti jsou již implementovány.

## Shrnutí produktu

`jellyfin-media-normalizer` má být aplikace s účastí člověka pro analýzu, kontrolu, plánování a bezpečnou normalizaci
knihovny filmů a televizních seriálů pro Jellyfin.

Aplikace má operátorovi pomoci převést nekonzistentní knihovnu na čistou a předvídatelnou strukturu bez ručních úprav
JSON, YAML, souborů mezipaměti nebo vytvořených manifestů.

Produkt je úspěšný, pokud operátor dokáže:

1. vybrat knihovnu médií;
2. prohledat ji beze změn mediálních souborů;
3. zkontrolovat rozpoznané filmy, seriály, epizody a související soubory;
4. opravit parsování a shody poskytovatelů v uživatelském rozhraní;
5. schválit navržené změny;
6. vytvořit a zkontrolovat neměnný manifest přejmenování;
7. ověřit manifest v režimu dry-run;
8. explicitně provést schválené změny;
9. prohlédnout auditní protokol a zotavit se z částečně neúspěšné dávky.

## Primární uživatel

Primárním uživatelem je vlastník nebo správce rozsáhlé osobní knihovny Jellyfin uložené na NAS. Umí spustit místní
aplikaci, ale neměl by potřebovat rozumět internímu datovému schématu ani upravovat strojově generované soubory.

Aplikace má zůstat skriptovatelná pro pokročilé uživatele, znalost CLI však nesmí být nutná pro běžnou kontrolu a
schvalování. Hlavní instalační cesta nesmí vyžadovat instalaci Pythonu na hostiteli ani ruční správu závislostí.

## Hranice produktu

### V rozsahu

- inventář podporovaných médií a souvisejících souborů;
- klasifikace na filmy, seriály, epizody, bonusy a nevyřešené položky;
- parsování a normalizace názvů souborů a složek;
- ověřování na úrovni položky, složky, filmu, seriálu a skupiny epizod;
- vyhledání kandidátů poskytovatele a jejich výběr;
- trvalé uložení ručních oprav a schválení;
- deterministické generování manifestu přejmenování;
- ověření dry-run;
- řízené dávkové provedení, auditní protokol a pomoc s vrácením změn;
- automatizace přes CLI a místní webové rozhraní pro kontrolu člověkem;
- reprodukovatelné obrazy kontejnerů a konfigurace Docker Compose pro běžný provoz.

### Mimo rozsah

- vytváření nebo správa souborů `.nfo`;
- změny mediálních streamů nebo vložených metadat;
- stahování obrázků, titulků nebo jiných metadat;
- ID poskytovatelů na úrovni epizod v názvech souborů;
- bezobslužné přijímání nejednoznačných shod poskytovatelů;
- přejmenování přímo ze surového výstupu parseru nebo poskytovatele;
- role obecného mediálního serveru nebo náhrady Jellyfinu.

## Neměnná bezpečnostní pravidla

- Nikdy nezpracovávat, nevytvářet, nepřejmenovávat ani nemazat soubory `.nfo`.
- U entity filmu nebo seriálu uložit nejvýše jedno vybrané ID poskytovatele.
- Nikdy neukládat ID poskytovatelů do entit epizod ani jejich názvů souborů.
- Nikdy nepřejmenovávat přímo z výstupu skenování, parsování, ověření nebo vyhledání poskytovatele.
- Každá změna souborového systému musí pocházet z ověřeného, schváleného a trvale uloženého manifestu.
- Dry-run musí být výchozím režimem workflow CLI i webu.
- Skutečné provedení musí vyžadovat explicitní potvrzení oddělené od schválení manifestu.
- Před provedením se musí kontrolovat kolize cílů, chybějící a změněné zdroje i přesuny mezi souborovými systémy.
- Každý pokus o operaci se musí zapsat do auditního protokolu použitelného pro ruční obnovu.
- Výsledky s nízkou jistotou, konfliktní nebo nejednoznačné výsledky musí projít kontrolou člověkem.

## Požadovaný doménový model

Současný model zaměřený na soubory stačí ke skenování, ale plánování přejmenování vyžaduje explicitní mediální
entity. Před vytvořením planneru má implementace zavést následující pojmy.

### Položka knihovny

Nalezená položka souborového systému s původní cestou, typem, velikostí, časovými údaji a volitelným otiskem obsahu.
Zahrnuje podporovaná videa a související soubory, které může být nutné přesunout spolu s videem.

### Film

Entita filmu sdružuje hlavní video, volitelné alternativní verze nebo bonusy, související soubory, nadřazenou složku,
parsované názvy, rok a jedno vybrané ID poskytovatele.

### Televizní seriál

Entita seriálu vlastní identitu na úrovni seriálu, zobrazovaný název, zdrojovou složku, řady, epizody a jedno vybrané
ID poskytovatele. Vyhledávání musí používat identitu seriálu, nikoli název epizody.

### Epizoda

Entita epizody obsahuje číslo řady a epizody, název epizody, jazykové informace, hlavní video a související soubory.
Nikdy nevlastní ID poskytovatele.

### Související soubor

Titulky a jiné explicitně podporované doprovodné soubory musí být propojeny se svým videem, aby po přejmenování
nezůstaly osiřelé. Soubory `.nfo` zůstávají vyloučené, i když jsou přítomné.

První implementace musí explicitně určit podporované přípony souvisejících souborů. Minimální kategorií mají být
titulky.

### Pole názvů

Model nesmí používat jediný řetězec pro všechny účely názvu. Minimálně musí rozlišovat:

- zdrojový název: text získaný ze stávajícího souborového systému;
- zobrazovaný název: čitelný návrh konečného názvu souboru se zachovanou diakritikou;
- vyhledávací název: normalizovaný text používaný pouze pro hledání a porovnání;
- název seriálu a název epizody: samostatná pole s odděleným vlastnictvím.

Normalizace pro vyhledávání se nikdy nesmí bez upozornění stát konečným názvem souboru.

### Kandidát a výběr poskytovatele

Online hledání má vracet kandidáty poskytovatele místo okamžitého vytvoření konečné shody. Kandidát musí obsahovat
dostatek údajů pro hodnocení a kontrolu člověkem: poskytovatele, ID, název, původní název, rok nebo datum první
premiéry, typ média, přehled a dostupnou adresu plakátu.

Vybraná shoda poskytovatele musí zaznamenat:

- zvoleného kandidáta;
- jistotu a vysvětlení skóre;
- zda byla vložená, načtená z mezipaměti, automaticky přijatá nebo ručně vybraná;
- kdo nebo co ji vybralo a kdy;
- entitu, ke které výběr patří.

## Zásady párování poskytovatelů

Výsledek poskytovatele se nesmí přijmout pouze proto, že je první odpovědí API.

Automatické přijetí má vyžadovat konfigurovatelná a zdokumentovaná kritéria, například:

- kompatibilní typ média;
- podobnost normalizovaného názvu nad určeným prahem;
- přesnou nebo přijatelnou shodu roku filmu;
- dostatečný rozdíl skóre mezi nejlepším a druhým kandidátem;
- žádný konflikt s vloženým nebo dříve schváleným ID poskytovatele.

Pokud kritéria nejsou splněna, entita musí přejít ke kontrole místo získání konečného výběru poskytovatele.

Vloženým ID lze ve výchozím stavu důvěřovat, stále se však musí ověřit syntaxe, kompatibilita poskytovatele a pravidlo
jediného ID na entitu. UI musí operátorovi před plánováním umožnit nesprávný vložený výběr nahradit.

## Zásady ověřování

Ověřování musí fungovat nad rámec jednotlivého souboru.

Produkční proces má zahrnovat:

- ověření polí a syntaxe;
- ověření seskupení složek a entit;
- konzistenci názvu seriálu;
- detekci duplicitních řad a epizod;
- detekci duplicitních filmů a alternativních verzí;
- ověření výběru poskytovatele;
- ověření cílových cest a kolizí;
- kontrolu úplnosti souvisejících souborů.

Vyhledání poskytovatele může shromažďovat kandidáty ke kontrole, neplatná entita se však nikdy nesmí automaticky
schválit ani stát spustitelnou.

Výsledky ověření mají vedle čitelných zpráv používat stabilní strojově čitelné kódy. To umožní spolehlivě filtrovat,
dokumentovat a provádět akce UI bez parsování anglického textu.

## Cílové operátorské workflow

### 1. Počáteční nastavení

Operátor vybere cestu knihovny a pracovního prostoru, nastaví přihlašovací údaje poskytovatelů a ověří oprávnění ke
čtení a zápisu. Tajné údaje se po uložení nesmí zobrazovat.

Aplikace má nabídnout obrazovku nastavení a odpovídající volby CLI. Ruční export proměnných v shellu může zůstat pro
automatizaci, nesmí však být jedinou podporovanou metodou nastavení.

Pro běžnou instalaci má operátor potřebovat pouze Docker s podporou Compose, checkout vydání nebo balíček vydání,
malý soubor prostředí s nastavením nasazení a přístup ke knihovně. Instalace Pythonu, `uv` nebo závislostí projektu
na hostiteli nesmí být nutná.

### 2. Skenování

Skenování vytvoří trvalý běh s identifikátorem, časovými údaji, snímkem nastavení, souhrnem a nalezenými položkami.
UI zobrazuje průběh a dovolí operátorovi odejít a vrátit se bez ztráty běhu.

Skenování je pouze ke čtení.

### 3. Analýza

Aplikace parsuje, seskupuje, ověřuje a hledá kandidáty poskytovatelů. Výsledky trvale ukládá, takže kontrola není
závislá na úpravách vytvořených sestav.

### 4. Kontrola a opravy

Operátor může výsledky hledat, filtrovat, řadit a stránkovat. Pro každou entitu může:

- upravit parsovaný název, rok, řadu, epizodu a jazyk;
- vybrat kandidáta poskytovatele nebo explicitně zadat jeho ID;
- navrženou interpretaci schválit, zamítnout nebo odložit;
- přidat poznámku;
- použít bezpečné hromadné akce na ekvivalentní položky.

Každá oprava znovu spustí příslušné ověření.

### 5. Plánování

Do manifestu přejmenování mohou vstoupit pouze schválené a platné entity. Planner generuje deterministické zdrojové
a cílové cesty seskupené do logických dávek.

Operátor zkontroluje náhled před a po změně. Vygenerované manifesty jsou strojové artefakty a nejsou hlavním
rozhraním pro úpravy.

### 6. Dry-run

Dry-run ověří současný stav zdrojů, cílové cesty, oprávnění, kolize, pořadí dávek a údaje pro vrácení změn. Knihovnu
nesmí změnit.

Manifest lze provést pouze po úspěšném dry-run nad stejným relevantním stavem zdrojů. Pokud se knihovna změní, musí
se manifest znovu ověřit.

### 7. Provedení a audit

Skutečné provedení vyžaduje explicitní potvrzení a pracuje pouze s jedním schváleným manifestem. Aplikace zaznamená
každý pokus o operaci a jeho výsledek.

Při částečném selhání se provádění zastaví na bezpečné hranici a ohlásí dokončené, čekající, neúspěšné a obnovitelné
operace. Vrácení změn má použít auditní protokol a samo se musí zaprotokolovat.

## Směr uživatelského rozhraní

Doporučeným rozhraním je lehká místní webová aplikace s HTML vykreslovaným na serveru. CLI a webové UI musí být
adaptéry nad stejnými aplikačními službami; nesmí duplikovat logiku planneru nebo executoru.

První užitečné UI má poskytovat:

- nastavení a ověření připojení;
- vytvoření běhu a zobrazení průběhu;
- přehled s počty vyžadujícími akci;
- fronty chyb parsování, nejednoznačných poskytovatelů, duplicit a nevyřešených položek;
- úpravy na místě a výběr poskytovatele;
- hromadné schválení, zamítnutí a odložení;
- náhled manifestu;
- zahájení dry-run a jeho výsledky;
- potvrzení provedení a historii auditu.

Statické sestavy HTML a CSV zůstávají užitečnými exporty, nejsou však hlavním kontrolním workflow.

Výchozí nasazení má naslouchat na localhostu a předpokládat jediného místního operátora. Jakékoli podporované nasazení
v LAN musí nejprve definovat autentizaci, ochranu CSRF, zacházení s tajnými údaji a předpoklady důvěryhodné sítě.

## Nasazení v kontejneru

Docker Compose má být hlavní dokumentovanou metodou nasazení pro operátory. Nativní instalace přes `uv` má zůstat
dostupná pro vývoj, diagnostiku a pokročilou automatizaci CLI.

Repozitář má obsahovat:

- produkční `Dockerfile` s připnutou verzí Pythonu projektu;
- `.dockerignore` vylučující vývojové mezipaměti, přihlašovací údaje, pracovní data a mediální soubory;
- `compose.yaml` s bezpečnými výchozími hodnotami a dokumentovanými proměnnými prostředí;
- vzorový soubor prostředí pouze se zástupnými hodnotami;
- kontrolu stavu kontejneru;
- verzovaná metadata obrazu a značky vydání;
- návod ke spuštění, aktualizaci, zálohování a řešení potíží.

Produkční obraz má:

- obsahovat pouze běhové závislosti;
- běžet pod uživatelem bez oprávnění root;
- podle potřeby oprávnění NAS podporovat konfigurovatelné UID a GID;
- vystavovat pouze port webové aplikace;
- zapisovat měnitelná aplikační data pouze do deklarovaných pracovních nebo dočasných cest;
- nepoužívat privilegovaný režim, síť hostitele ani přístup k socketu Dockeru;
- mít jasný vstupní bod schopný spustit webovou aplikaci nebo podporované příkazy CLI.

Konfigurace Compose má oddělovat média od stavu aplikace:

- knihovna médií se připojí na stabilní cestu kontejneru, například `/media`;
- pracovní prostor se připojí například na `/workspace` a uchová SQLite, manifesty, sestavy, auditní záznamy a logy;
- výchozí nasazení pro analýzu a kontrolu připojí knihovnu médií pouze ke čtení;
- povolení zápisu do médií vyžaduje explicitní konfiguraci nebo profil určený k provádění;
- samotný zapisovatelný mount nikdy neobchází aplikační brány manifestu, dry-run, ověření a potvrzení;
- přihlašovací údaje poskytovatelů se předávají proměnnými prostředí nebo podporovanými tajnými soubory a nikdy se
  nezabudují do obrazu.

Přesný mechanismus aktivace zápisu má popsat architektonické rozhodnutí. Bezpečný výchozí stav musí být viditelný
v konfiguraci Compose i operátorské dokumentaci, nejen vynucený aplikačním kódem.

Publikované obrazy mají cílit na architektury vybraných vývojových strojů a zařízení NAS. Před prvním vydáním pro
operátory musí projekt explicitně rozhodnout minimálně o podpoře `linux/amd64` a `linux/arm64`.

Aktualizace kontejneru musí zachovat databázi a artefakty pracovního prostoru. Migrace databázového schématu musí
probíhat verzovaným a obnovitelným procesem s návodem k záloze před potenciálně nekompatibilní aktualizací.

## Strategie perzistence

Lidská rozhodnutí a stav workflow se mají ukládat do malé aplikační databáze; preferovanou první implementací je
SQLite. Tím se nevyžaduje samostatná databázová služba a současně je možné filtrovat, měnit stavy, pokračovat v
kontrole a uchovávat historii auditu.

Doporučené odpovědnosti úložišť:

- SQLite: běhy skenování, entity, kandidáti, opravy, schválení, poznámky, stav workflow a metadata auditu;
- JSON: verzované neměnné manifesty přejmenování a přenositelné strojové exporty;
- CSV a HTML: volitelné čitelné exporty;
- prostředí nebo chráněné úložiště nastavení: tajné údaje poskytovatelů;
- soubory protokolu: provozní diagnostika, pokud je nastavena.

Soubory JSON, YAML a SQLite nesmí být prezentovány jako běžná operátorská rozhraní pro úpravy.

## Stavy workflow

Aplikace má používat explicitní stavy místo odvozování schválení z absence chyb. Minimální životní cyklus entity a
manifestu je:

```text
discovered
  -> analyzed
  -> review_required | ready_for_approval
  -> approved | rejected | deferred
  -> planned
  -> dry_run_verified
  -> executed | execution_failed
  -> rolled_back
```

Ne každý stav platí pro každý objekt, povolené přechody však musí být definované a ověřované. Akce uživatele,
automatické pravidlo nebo událost provedení, která vyvolá přechod, musí být auditovatelná.

## Plán dodání

### Fáze 0: Sladit produktovou dokumentaci

- Přijmout nebo upravit rozhodnutí v tomto zadání.
- Vyřešit níže uvedená otevřená produktová rozhodnutí.
- Sladit terminologii a stav fází v `PROJECT-DESCRIPTION.md`, `DEVELOPMENT_PLAN.md` a obou README.
- Přidat architektonická rozhodnutí o perzistenci, nasazení UI, bezpečnosti kontejneru a provádění manifestu.

### Fáze 1: Opravit analytický model

- Zavést entity filmu, seriálu, epizody a souvisejícího souboru.
- Oddělit zdrojový, zobrazovaný, vyhledávací, seriálový a epizodní název.
- Seskupit nalezené soubory do entit.
- Zapojit ověřování konzistence do produkčního procesu.
- Zabránit automatickému schválení neúspěšných entit a entit s nízkou jistotou.

### Fáze 2: Umožnit kontrolu párování poskytovatelů

- Vracet více kandidátů poskytovatele.
- Přidat vysvětlitelné skóre a prahy nejednoznačnosti.
- Trvale ukládat vybrané shody a ruční opravy.
- Do doby vytvoření UI nabídnout příkazy CLI pro prohlížení a výběr kandidátů.

### Fáze 3: Implementovat plánování přejmenování

- Přidat verzované modely `RenameEntry` a `RenameManifest`.
- Generovat deterministické cílové cesty složek, videí a podporovaných souvisejících souborů.
- Odmítat nevyřešené, neschválené, neplatné nebo konfliktní položky.
- Ukládat neměnné manifesty a čitelné náhledy.

### Fáze 4: Implementovat bezpečné provádění

- Přidat výchozí dry-run.
- Ověřovat stav zdroje a bezpečnost cíle.
- Vyžadovat explicitní potvrzení skutečného provedení.
- Přidat hranice dávek, auditní záznamy, zpracování částečných selhání a pomoc s vrácením změn.

### Fáze 5: Implementovat UI pro kontrolu člověkem

- Přidat nastavení, přehled, kontrolu, výběr poskytovatele a hromadné akce.
- Přidat náhled manifestu, výsledky dry-run, potvrzení provedení a historii auditu.
- Všechny změny stavů vést přes stejné služby a ověřovací brány jako CLI.

### Fáze 6: Zabalit produkt pro kontejnerové nasazení

- Přidat produkční Dockerfile, `.dockerignore`, konfiguraci Compose a vzorový soubor prostředí.
- Spouštět produkční proces bez uživatele root s trvalým pracovním úložištěm.
- Ve výchozím stavu připojit média jen ke čtení a pro zápis vyžadovat explicitní konfiguraci.
- Přidat kontroly stavu, metadata obrazu, cílové architektury a reprodukovatelná sestavení vydání.
- Zdokumentovat spuštění, CLI v kontejneru, aktualizace, zálohy, oprávnění a obnovu.

### Fáze 7: Provozně zpevnit produkt

- Přidat obnovitelné dlouhé úlohy a jasné zobrazení průběhu.
- Přidat korelační ID běhu a trvalé provozní protokoly.
- Přidat koncovou dokumentaci, řešení potíží, zálohování a cvičení obnovy.
- Ověřit výkon na reprezentativní velké knihovně.

## Milník připravenosti pro operátory

Projekt se nesmí označit za připravený pro operátory, dokud neplatí vše následující:

- operátor spustí podporovanou aplikaci přes Docker Compose bez instalace závislostí Pythonu;
- výchozí kontejner připojuje knihovnu pouze ke čtení;
- operátor dokončí nastavení bez úpravy generovaných datových souborů;
- filmy, seriály, epizody a podporované související soubory jsou správně reprezentovány;
- nejednoznačné shody poskytovatelů vyžadují kontrolu;
- opravy a schválení přetrvají restart;
- ověřený manifest přejmenování je povinný;
- dry-run prokazuje, že nedochází ke změnám souborového systému;
- skutečné provedení vyžaduje explicitní potvrzení;
- jsou vynucené kontroly kolizí a změněných zdrojů;
- každá operace je auditovaná;
- částečná selhání mají zdokumentovanou cestu obnovy;
- úplné workflow je zdokumentované a otestované na reprezentativních knihovních fixturech.

## Kontrolní seznam sladění dokumentace

Po přijetí tohoto zadání aktualizujte stávající dokumenty následovně.

### `PROJECT-DESCRIPTION.md`

- Zařadit mediální entity a související soubory do stabilního popisu domény.
- Vyjasnit název seriálu vůči názvu epizody.
- Vyjasnit zachování zobrazovaného názvu vůči normalizaci pro vyhledávání.
- Nahradit okamžité spárování poskytovatele kandidáty, skórováním, výběrem a schválením.
- Popsat trvalé workflow s účastí člověka.
- Aktualizovat strom architektury a popis fází.

### `DEVELOPMENT_PLAN.md`

- Opravit stav ověřování: strukturální ověření existuje, skupinová konzistence ale není integrovaná.
- Označit vyhledání poskytovatele za implementované, kvalitu jeho výběru však za neúplnou.
- Nahradit současnou plochou frontu fázemi dodání z tohoto zadání.
- Stanovit milník připravenosti pro operátory jako cíl vydání.
- Oddělit datované výsledky ověření od tvrzení o úplnosti produktu.

### `README.md` a `README.cs.md`

- Až do existence plánování a provádění jasně označit současné vydání jako pouze analytické.
- Po vytvoření podpory nastavení nahradit ruční export `.env` jako hlavní uživatelskou metodu.
- Nastavit workflow Docker Compose jako hlavní rychlý začátek pro operátory.
- Samostatně popsat bezpečnou analýzu pouze ke čtení a explicitní konfiguraci zápisu pro provádění.
- Po implementaci příkazů přidat jeden úplný operátorský workflow.
- Vysvětlit, které soubory se skenují, ignorují, přesouvají společně a kterých se aplikace nikdy nedotkne.
- Přidat řešení potíží s cestami, přihlašovacími údaji, nevyřešenými kandidáty a dry-run.

## Otevřená produktová rozhodnutí

Před zahájením implementace fáze 1 je třeba rozhodnout:

1. Která stávající rozložení adresářů filmů a seriálů budou oficiálně podporována?
2. Které typy souvisejících souborů se v prvním vydání přesouvají spolu s videem?
3. Jak se reprezentují alternativní verze a vícedílné filmy, speciály a bonusy?
4. Jaký je závazný zdroj konečného českého zobrazovaného názvu při rozdílu mezi souborem a poskytovatelem?
5. Mají složky seriálů rok vynechávat vždy, nebo jej smí operátor povolit u nejednoznačných remaků?
6. Jaké prahy skóre umožní automatické přijetí poskytovatele?
7. Má první UI podporovat pouze localhost, nebo i autentizovaný přístup z NAS či LAN?
8. Jaký otisk stavu zdroje je vyžadován mezi plánováním, dry-run a provedením?
9. Vyžaduje první vydání automatické vrácení změn, nebo stačí deterministická pomoc s jejich vrácením?
10. Které architektury kontejnerů se musí publikovat, zejména pro cílový Synology NAS?
11. Jaký explicitní mechanismus Compose povolí zápis a současně zachová běžný provoz pouze ke čtení?

Dokud tato rozhodnutí nebudou vyřešena, má implementace upřednostňovat zachování dat, explicitní kontrolu a vratné
operace před automatizací.
