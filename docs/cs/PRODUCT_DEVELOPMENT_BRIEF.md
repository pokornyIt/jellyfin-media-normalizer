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

- Nikdy samostatně nečíst, neparsovat, nevytvářet, neměnit, nemazat ani necílit na soubory `.nfo`. Soubor `.nfo` se
  smí přesunout pouze jako ignorovaný obsah přejmenované nadřazené složky a nikdy nedostane vlastní položku manifestu.
- U entity filmu nebo seriálu uložit nejvýše jedno vybrané ID poskytovatele.
- Nikdy neukládat ID poskytovatelů do entit epizod ani jejich názvů souborů.
- Nikdy nepřejmenovávat přímo z výstupu skenování, parsování, ověření nebo vyhledání poskytovatele.
- Každá změna souborového systému musí pocházet z ověřeného, schváleného a trvale uloženého manifestu.
- Dry-run musí být výchozím režimem workflow CLI i webu.
- Skutečné provedení musí vyžadovat explicitní potvrzení oddělené od schválení manifestu.
- Před provedením se musí kontrolovat kolize cílů, chybějící a změněné zdroje i přesuny mezi souborovými systémy.
- Každý pokus o operaci se musí zapsat do auditního protokolu použitelného pro ruční obnovu.
- Výsledky s nízkou jistotou, konfliktní nebo nejednoznačné výsledky musí projít kontrolou člověkem.
- Symbolické odkazy se vždy odmítnou. Aplikace je nikdy nenásleduje, nemodeluje, neplánuje ani nepřejmenovává.
  Symbolický odkaz uvnitř složky, která by se jinak přejmenovala, tuto složku z plánování vyloučí.

## Požadovaný doménový model

Současný model zaměřený na soubory stačí ke skenování, ale plánování přejmenování vyžaduje explicitní mediální
entity. Před vytvořením planneru má implementace zavést následující pojmy.

### Položka knihovny

Nalezený běžný soubor nebo složka s původní cestou, typem, příslušnou velikostí, časem změny a povinným otiskem stavu
zdroje. Zahrnuje podporovaná videa a související soubory, které může být nutné přesunout spolu s videem. Symbolické
odkazy jsou neplatnými položkami knihovny a nikdy se nenásledují.

### Film

Entita filmu sdružuje jednu nebo více fyzických částí hlavní verze, volitelné alternativní verze, související soubory,
nadřazenou složku, parsované názvy, rok a jedno vybrané ID poskytovatele. Bonus nebo extra se k filmu nepřipojí
automaticky; vyžaduje klasifikaci operátorem.

### Televizní seriál

Entita seriálu vlastní identitu na úrovni seriálu, zobrazovaný název, zdrojovou složku, řady, epizody a jedno vybrané
ID poskytovatele. Vyhledávání musí používat identitu seriálu, nikoli název epizody.

### Epizoda

Entita epizody obsahuje číslo řady a epizody, název epizody, jazykové informace, hlavní video a související soubory.
Nikdy nevlastní ID poskytovatele.

### Související soubor

Podporované soubory titulků musí být propojeny se svým videem, aby po přejmenování nezůstaly osiřelé. První vydání
podporuje soubory `.srt`, `.ass`, `.ssa`, `.vtt` a `.sub`. Vlastnictví vyžaduje stejný základ názvu jako video nebo
tento základ následovaný pouze rozpoznanými jazykovými a titulkovými příznaky, například `cs`, `en`, `forced`, `sdh`,
`cc` nebo `default`. Příznaky se při přejmenování videa a titulků zachovají. Osiřelé titulky nebo kolize cílového
názvu vyžadují kontrolu.

Ostatní typy souborů se ignorují a nedostanou samostatnou operaci parsování, ověření, plánování ani provedení. Při
přejmenování nadřazené složky v ní zůstanou. Soubory `.nfo` se chovají stejně jako ignorovaný obsah, ale nikdy se
nečtou, nemodelují ani nezahrnují jako samostatné položky manifestu.

### Pole názvů

Model nesmí používat jediný řetězec pro všechny účely názvu. Minimálně musí rozlišovat:

- zdrojový název: text získaný ze stávajícího souborového systému;
- zobrazovaný název: čitelný návrh konečného názvu souboru se zachovanou diakritikou;
- vyhledávací název: normalizovaný text používaný pouze pro hledání a porovnání;
- název seriálu a název epizody: samostatná pole s odděleným vlastnictvím.

Normalizace pro vyhledávání se nikdy nesmí bez upozornění stát konečným názvem souboru.

Závazné pořadí zdrojů zobrazovaného názvu je:

1. název explicitně upravený nebo schválený operátorem;
2. český lokalizovaný název vybraného kandidáta poskytovatele;
3. existující název ze souborového systému, pokud vybraný poskytovatel nemá český název;
4. původní název poskytovatele pouze jako poslední možnost s povinnou kontrolou.

Zobrazovaný název zachovává diakritiku, členy, interpunkci a pořadí slov z vybraného zdroje. Normalizace pro
vyhledávání jej nikdy nepřepisuje. Významný rozdíl mezi existujícím názvem a názvem poskytovatele je viditelný při
kontrole. Jednou ručně schválený zobrazovaný název zůstává závazný i při dalších skenech. Změna vybraného
poskytovatele toto schválení zneplatní a znovu otevře kontrolu zobrazovaného názvu.

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

Jistota kandidáta je oddělená od jistoty parseru a skupiny entity. Automatický výběr poskytovatele vyžaduje
strukturálně platnou entitu s vysokou jistotou, kompatibilní typ média, ID platné pro poskytovatele a žádný konflikt
s vloženým nebo ručně schváleným výběrem poskytovatele. Platné vložené ID a ručně schválený výběr mají před
skórováním kandidátů přednost.

Podobnost normalizovaného názvu je nejlepší porovnání s lokalizovaným nebo původním názvem kandidáta. Pokud je
dostupný spolehlivý zdrojový rok, běžné skóre kandidáta je:

```text
candidate score = 0.80 * title similarity + 0.20 * year agreement
```

Přesný rok má shodu `1.0`, rozdíl jednoho roku má `0.5` a větší rozdíl nebo chybějící rok kandidáta má `0.0`. Film
pro automatický výběr vyžaduje přesný rok. Televizní seriál také vyžaduje přesný rok, pokud vstup obsahoval
spolehlivě parsovaný koncový rok. Bez porovnatelného roku seriálu odpovídá běžné skóre podobnosti názvu.

Běžný automatický výběr vyžaduje všechny následující podmínky:

- skóre kandidáta alespoň `0.92`;
- podobnost názvu alespoň `0.90`;
- náskok skóre alespoň `0.08` před druhým kandidátem stejného poskytovatele;
- všechny výše popsané brány struktury, typu média, roku, ID a konfliktů.

Jediný vrácený kandidát vyžaduje skóre i podobnost názvu alespoň `0.97`. Pro filmy se vyhodnocuje TMDb. U seriálů
se nejprve vyhodnotí TMDb TV a TVDB slouží jako záloha, pokud TMDb nemá kandidáta splňujícího pravidla. Pořadí
výsledků API, popularita, grafika, dostupnost přehledu a úplnost metadat nikdy nezvyšují skóre identity.

Seriál bez roku, který neprojde běžnou cestou založenou pouze na názvu, může použít názvy epizod jako další důkaz.
Aplikace deterministicky vybere až tři vzorky: první, prostřední a poslední vhodnou epizodu, pokud možno z různých
řad. Vynechá `Season 00`, speciály, vícedílné soubory, soubory s více epizodami, nerozpoznatelné epizody a názvy
souborů bez použitelného názvu epizody. Jsou potřeba alespoň dva použitelné názvy epizod.

Každá vybraná kombinace řady a epizody musí u kandidáta existovat a každý název musí dosáhnout podobnosti `0.85`
s lokalizovaným nebo původním názvem epizody od poskytovatele. Chybějící kombinace je konfliktním důkazem. Samotná
existence kombinace může kandidáta vyřadit, ale není pozitivním důkazem identity. Důkaz epizod je průměr podobností
použitelných názvů a potvrzené skóre je:

```text
corroborated TV score = 0.75 * series title similarity + 0.25 * episode evidence
```

Tato cesta vyžaduje podobnost názvu seriálu alespoň `0.85`, konečné skóre alespoň `0.92`, běžný náskok `0.08` a žádný
konflikt ve vzorku. Pro jediného kandidáta nadále platí hranice `0.97`. Metadata epizod se načtou pouze pro nejlepší
kandidáty, kteří potřebují potvrzení, čímž se omezí požadavky poskytovateli a zachová opakovatelnost výsledku.

Automaticky vybrané ID vyřeší identitu poskytovatele a přesune entitu do `ready_for_approval`; nikdy neschválí
přejmenování. Ruční výběr může překonat nevyhovující skóre, musí však být explicitní a auditovatelný. Při nesplnění
kteréhokoli automatického kritéria entita přechází ke kontrole.

První vydání používá pro tyto prahy pojmenované a verzované konstanty zásad. Operátor je nemůže snižovat konfigurací,
dokud výsledky na skutečné knihovně neodůvodní samostatně schválenou změnu zásad. Kandidát není důvěryhodný jen proto,
že je v mezipaměti. Automatické opětovné použití vyžaduje dříve schválený výběr, nezměněné vstupy identity a stejnou
verzi zásad; staré nebo neprokazatelné záznamy mezipaměti vyžadují nové skórování nebo kontrolu.

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

Každý běžný zdrojový soubor zaznamenává relativní cestu, typ položky, velikost a čas změny s nejvyšší přesností
poskytnutou souborovým systémem. Hash celého obsahu média, čísla inode, čas vytvoření, vlastník a oprávnění nejsou
součástí otisku zdroje v prvním vydání.

Přejmenování složky zaznamenává stromový SHA-256 digest nad kanonicky seřazenou inventurou. Každý potomek přispívá
relativní cestou a typem položky. Spravované běžné soubory navíc přispívají velikostí a časem změny. Ignorovaní
potomci včetně `.nfo` přispívají pouze neprůhledným členstvím v adresáři a nikdy se neotevírají, neparsují, nemodelují
ani nedostávají samostatný záznam manifestu. Přidání, odebrání, přejmenování nebo změna spravovaného potomka digest
zneplatní.

Neměnný manifest také získá SHA-256 digest své kanonické serializace. Výsledky dry-run platí pouze pro tento přesný
digest manifestu.

### 6. Dry-run

Dry-run ověří současný stav zdrojů, cílové cesty, oprávnění, kolize, pořadí dávek a údaje pro vrácení změn. Knihovnu
nesmí změnit.

Manifest lze provést pouze po úspěšném dry-run nad stejnými otisky zdrojů a přesným digestem manifestu. Dry-run
nezávisle znovu vypočítá otisky zdrojů. Rozdíl se nikdy nepřijme aktualizací manifestu na místě; operátor musí
zopakovat skenování, analýzu, schválení, plánování a dry-run.

### 7. Provedení a audit

Skutečné provedení vyžaduje explicitní potvrzení a pracuje pouze s jedním schváleným manifestem. Otisky zdrojů znovu
vypočítá bezprostředně před každou dávkou a znovu před každou operací. Rozdíl zastaví celý běh provádění před dalšími
operacemi a oznámí stabilní důvod, například `SOURCE_MISSING`, `SOURCE_SIZE_CHANGED`, `SOURCE_MTIME_CHANGED` nebo
`DIRECTORY_CONTENT_CHANGED`. Existence cílů a kolize se kontrolují samostatně při plánování, dry-run a bezprostředně
před každou operací. Aplikace zaznamená každý pokus o operaci a jeho výsledek.

Při prvním selhání operace se zastaví celý běh provádění. Aplikace se nepokusí o automatické vrácení změn. Ohlásí
dokončené, čekající, neúspěšné a obnovitelné operace a vytvoří neměnný JSON manifest rollbacku pouze z operací, které
trvalý audit potvrzuje jako úspěšně dokončené.

Položky rollbacku obracejí úspěšné operace v opačném pořadí provedení: dokončený cíl se stane zdrojem rollbacku a
původní zdroj jeho cílem. Každá položka zaznamenává ID původní operace, současný otisk zdroje, očekávanou nepřítomnost
cíle, pořadí a důvod obnovy. Manifest rollbacku zaznamenává verzi schématu, druh manifestu, ID původního běhu, digest
původního manifestu, čas vytvoření a vlastní SHA-256 digest. Obsahuje strukturované cesty a metadata, nikdy shellové
příkazy.

Rollback používá stejný bezpečný executor manifestu. Vyžaduje ověření integrity a stavu zdroje, nepřítomný cíl,
úspěšný dry-run a samostatné explicitní potvrzení. Existující položku nikdy nepřepíše. Výsledky provedení se zapisují
do samostatného auditu místo změny manifestu rollbacku. Pokud se stav pro rollback změnil, operace se odmítne.
Operátor může manifest rollbacku provést, nebo ponechat dokončenou práci a pro zbývající položky vytvořit nové
workflow od skenování po dry-run.

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
- historii auditu.

Statické sestavy HTML a CSV zůstávají užitečnými exporty, nejsou však hlavním kontrolním workflow.

První UI předpokládá jediného operátora na důvěryhodném počítači nebo privátní síti. Adresa naslouchání je
konfigurovatelná a výchozí hodnota pro vývoj a kontejner je `0.0.0.0`, což umožňuje přístup z prohlížeče Windows při
běhu aplikace ve WSL a volitelně z privátní LAN. Tato fáze nevyžaduje autentizaci, uživatelské účty, role, TLS
spravované aplikací ani integraci se Synology účtem.

Toto nasazení se nesmí vystavit veřejnému internetu ani nedůvěryhodné síti. Dostupnost řídí firewall hostitele a
publikování portu v Compose. Aplikace při naslouchání mimo loopback zobrazí upozornění, ale spuštění nezablokuje.
Změnové trasy nikdy nepoužívají metodu `GET`.

První UI podporuje nastavení, analýzu, kontrolu, opravy, schvalování, náhled manifestu a dry-run. Skutečné provedení
přejmenování zůstává pouze v CLI s běžnými branami manifestu, ověření, dry-run a explicitního potvrzení. Autentizace,
session, ochrana CSRF, návod k HTTPS reverse proxy a širší zabezpečení vzdáleného přístupu jsou pozdější nadstavbou.
Integrace se Synology účtem je volitelná a není nutná pro podporované nasazení.

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
- výchozí dlouhodobá služba `app` připojí knihovnu médií explicitně jako `:ro`;
- samostatná jednorázová služba `executor` patří do profilu `execution` a připojí stejnou knihovnu explicitně jako
  `:rw`;
- samotný zapisovatelný mount nikdy neobchází aplikační brány manifestu, dry-run, ověření a potvrzení;
- přihlašovací údaje poskytovatelů se předávají proměnnými prostředí nebo podporovanými tajnými soubory a nikdy se
  nezabudují do obrazu.

Běžné `docker compose up` spustí pouze `app` a nikdy neaktivuje profil `execution`. Služba `executor` nemá webový port
ani dlouhodobý proces, používá `restart: "no"` a `network_mode: "none"`. Spouští se explicitně pomocí
`docker compose --profile execution run --rm executor ...` a po dokončení se odstraní. Stejná služba zpracovává
manifesty skutečného přejmenování i rollbacku.

Režim mountu musí být v Compose uvedený přímo. Proměnná jako `${MEDIA_MODE}` nikdy nesmí přepínat běžnou službu mezi
`:ro` a `:rw` a webová služba nikdy nesmí dostat zapisovatelný mount médií. Executor navíc vyžaduje explicitní
přepínač skutečného provedení v CLI a globální execution lock v trvalém workspace. Lock zabraňuje souběžným
executorům přejmenování nebo rollbacku, ale nenahrazuje kontroly manifestu, otisků, cílů, dry-run, potvrzení ani auditu.

Oficiální obrazy se sestavují, kontrolují smoke testem a publikují pouze pro `linux/amd64`. To pokrývá vývojové
prostředí WSL `x86_64` a cílové systémy Synology DS925+ a DS723+. Projekt v prvním vydání nepublikuje `linux/arm64`,
`linux/arm/v7`, `linux/386` ani multi-platformní manifest obrazu.

Dockerfile má zůstat přenositelný, pokud to nepřináší složitost specifickou pro architekturu, přenositelnost ale
nevytváří závazek podpory. Pokročilá dokumentace má ukázat místní nativní sestavení ze zdrojů a volitelný příklad
jediné platformy přes `docker buildx build`. Obrazy vytvořené pro jiné architektury jsou best-effort, projekt je v
release netestuje ani nepublikuje a mohou selhat, pokud není dostupný připnutý obraz Pythonu nebo binární závislosti.

Compose nesmí vynucovat hodnotu `platform`. Oficiální jednoplatformní tag na nepodporovaném hostiteli jasně selže,
místo aby skrytě spouštěl obraz AMD64 přes emulaci. Běžný rychlý začátek pro operátory dokumentuje pouze podporovaný
obraz AMD64; nepodporované sestavení ze zdrojů patří do pokročilé nebo vývojové dokumentace.

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
- Přidat hranice dávek, trvalé stavy auditu, zastavení při chybě a neměnné manifesty rollbacku.

### Fáze 5: Implementovat UI pro kontrolu člověkem

- Přidat nastavení, přehled, kontrolu, výběr poskytovatele a hromadné akce.
- Přidat náhled manifestu, výsledky dry-run a historii auditu. Pro první vydání UI ponechat skutečné provedení v CLI.
- Všechny změny stavů vést přes stejné služby a ověřovací brány jako CLI.

### Fáze 6: Zabalit produkt pro kontejnerové nasazení

- Přidat produkční Dockerfile, `.dockerignore`, konfiguraci Compose a vzorový soubor prostředí.
- Spouštět produkční proces bez uživatele root s trvalým pracovním úložištěm.
- Ve výchozím stavu připojit média jen ke čtení a pro zápis vyžadovat explicitní konfiguraci.
- Přidat kontroly stavu, metadata obrazu, cíl vydání `linux/amd64`, smoke testy a reprodukovatelná sestavení vydání.
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

## Přijatá produktová rozhodnutí

### Rozložení a klasifikace knihovny

- Aplikace skenuje jeden nakonfigurovaný kořen knihovny obsahující filmy i televizní seriály. Kořen je neutrální
  kontejner; složky pod ním se klasifikují podle svého obsahu a struktury.
- Role složek jsou filmová kolekce, kolekce seriálů, televizní seriál, sezóna a nekompatibilní složka. Po klasifikaci
  musí podstromy filmových a seriálových kolekcí zůstat homogenní.
- Skenování sestupuje nejvýše pět adresářových úrovní pod kořen. Obsah za limitem se oznámí jako nekompatibilní,
  místo aby se tiše vynechal.
- Film je videosoubor a nevyžaduje vlastní složku. Jeho jediné ID poskytovatele patří do názvu souboru filmu. Složky
  žánrů a kolekcí zůstávají organizační a nedostávají ID poskytovatele.
- Televizní seriál vlastní složku seriálu s jedním ID poskytovatele a bez roku. Normalizovaná struktura pod ní je
  striktně `Season XX`, následovaná soubory epizod a jejich podporovanými souvisejícími soubory bez další úrovně.
- Soubory epizod přímo ve vstupní složce seriálu lze opravit. Jednoznačné `SxxExx` určí sezónu. Číslo epizody bez
  sezóny navrhne `Season 01` a vyžádá kontrolu. Nejednoznačné číslování vyžaduje kontrolu bez automatického plánu.
- Vnořené složky sezón a smíšený obsah filmů a seriálů jsou nekompatibilní a obdrží doporučení k nápravě.
- Soubor filmu nebo složka seriálu přímo v kořeni knihovny zůstává zpracovatelná a může být připravena k plánování,
  ale obdrží neblokující varování, protože smíšený kořen není vhodným cílovým rozložením Jellyfinu.
- Položka s bezpečně určeným strukturálním vlastnictvím, ale nejistými metadaty směřuje ke kontrole. Položka, jejíž
  vlastnictví nebo roli složky nelze určit, je nekompatibilní a nesmí vstoupit do výběru poskytovatele, schválení ani
  manifestu přejmenování.
- Soubory `.nfo` se vždy ignorují a nikdy nevstupují do doménového modelu ani samostatné operace se souborovým
  systémem. Smí se přesunout pouze jako obsah přejmenované nadřazené složky.
- Právě jedno syntakticky platné ID poskytovatele slučitelné s typem média, které již je v názvu souboru filmu nebo
  složky seriálu, vyřeší entitu bez mezipaměti či online vyhledávání. ID jinde, více ID a ID na úrovni epizody entitu
  nevyřeší a vyžadují ověření. Pozdější explicitní oprava operátorem zůstává auditovatelná.

### Související soubory

- První vydání podporuje přípony titulků `.srt`, `.ass`, `.ssa`, `.vtt` a `.sub`.
- Titulky patří k videu, pokud mají stejný základ názvu nebo přidávají pouze rozpoznané jazykové a titulkové příznaky.
  Tyto příznaky se při přejmenování zachovají.
- Osiřelé titulky a kolize cílových názvů titulků vyžadují kontrolu a nesmějí vstoupit do spustitelného manifestu.
- Nepodporované typy souborů se jako samostatné položky ignorují a zůstávají uvnitř přejmenované nadřazené složky.
- Soubor `.nfo` se nikdy nečte, nemodeluje, nemění, nemaže ani nezahrnuje jako samostatná operace manifestu. Smí se
  přesunout pouze jako ignorovaný obsah přejmenované nadřazené složky.

### Vícedílná média, verze, speciály a bonusy

- `Part 1`, `Part 2` nebo ekvivalentní výraz v oficiálním názvu filmu označuje samostatné filmové entity, pokud mají
  části odlišné identity poskytovatele. Výraz zůstává v zobrazovaném názvu, aby bylo zachováno přehledné řazení na
  souborovém systému.
- Jeden film fyzicky rozdělený do více souborů je jedna entita s uspořádanými částmi. Podporované koncové značky jsou
  `CD1`, `CD2`, `Disc 1`, `Disc 2`, `Part 1` a `Part 2`, podle potřeby rozšířené o další kladná celá čísla. Číslování
  musí začínat jedničkou, být souvislé a části se musí shodovat v názvu, roku, poskytovateli a jazyku. Stejné vybrané
  ID poskytovatele se zapíše do názvu každé části.
- Samotná značka `Part` nikdy nedokazuje příslušnost k vícedílnému filmu. Rozdělený soubor se od samostatně vydaných
  filmů musí odlišit identitou poskytovatele nebo explicitním potvrzením operátora. Chybějící, duplicitní nebo
  konfliktní části vyžadují kontrolu.
- Alternativní verze, například `Theatrical`, `Director's Cut`, `Extended`, `Unrated`, `Remastered` a `Alternate`,
  zůstávají samostatnými videosoubory pod jednou entitou filmu a jedním vybraným ID poskytovatele. Více souborů se
  stejným názvem, rokem a poskytovatelem vyžaduje kontrolu, která je označí jako verze, části, duplicity nebo různé
  filmy.
- Vícedílné seriálové příběhy se samostatnými čísly epizod zůstávají samostatnými epizodami; `Part 1` a `Part 2` jsou
  textem zobrazovaného názvu. Jeden soubor obsahující více epizod používá explicitní rozsah, například `S01E01-E02`,
  a vyžaduje jednoznačné parsování nebo potvrzení operátorem.
- Seriálové speciály používají `Season 00` a `S00E##`, patří svému seriálu a nikdy nedostávají ID poskytovatele. Pokud
  je dostupné pořadí poskytovatele, použije se; jinak speciál vyžaduje kontrolu.
- Video rozpoznané jako bonus nebo extra vyžaduje kontrolu. Operátor je může klasifikovat jako film, seriálový speciál
  nebo ignorovaný obsah. Ignorované bonusy zůstanou na místě, nedostanou ID poskytovatele ani samostatnou operaci
  manifestu a smějí se přesunout pouze jako obsah přejmenované nadřazené složky.

### Autorita zobrazovaného názvu

- Závazný je operátorem schválený název, následovaný českým lokalizovaným názvem vybraného poskytovatele, existujícím
  názvem ze souborového systému a nakonec původním názvem poskytovatele.
- Použití původního názvu poskytovatele jako poslední možnosti vyžaduje kontrolu.
- Zobrazovaný název zachovává diakritiku, členy, interpunkci a pořadí slov vybraného zdroje. Normalizace pro
  vyhledávání se nikdy nestane zobrazovaným textem.
- Významný rozdíl mezi názvem ze souborového systému a názvem poskytovatele se zobrazí při kontrole.
- Ručně schválený název přetrvá další skeny. Změna vybraného poskytovatele znovu otevře kontrolu názvu.

### Rok televizního seriálu

- Normalizovaná složka seriálu nikdy neobsahuje rok vydání ani první premiéry. Vybrané ID poskytovatele rozlišuje
  seriály se stejným zobrazovaným názvem včetně remaků.
- Koncový rok ve vstupní složce se zachová jako metadata pro vyhledávání a kontrolu a z plánovaného názvu složky se
  odstraní až po výběru a schválení identity poskytovatele.
- Čísla, která jsou součástí skutečného názvu seriálu, například `1899`, `1923`, `11.22.63` nebo `Catch-22`, zůstávají
  zachována. Nejednoznačné číslo vyžaduje kontrolu místo automatického odstranění.
- Seriál bez vybraného ID poskytovatele nelze schválit pro plánování přejmenování. Změna nebo odstranění vstupního
  roku nepřepíše ručně schválený výběr poskytovatele.
- Roky se nikdy nepřidávají do složek sezón ani názvů souborů epizod.

### Výběr kandidáta poskytovatele

- Jistota kandidáta poskytovatele je nezávislá na jistotě parseru a skupiny entity. Automatický výběr vyžaduje
  strukturálně platnou entitu s vysokou jistotou a všechny brány typu média, ID, roku a konfliktů.
- Běžné skóre používá 80 % podobnosti názvu a 20 % shody roku, pokud je dostupný spolehlivý zdrojový rok. Bez
  porovnatelného roku seriálu odpovídá skóre podobnosti názvu.
- Automatický výběr vyžaduje skóre `0.92`, podobnost názvu `0.90` a náskok `0.08` před druhým kandidátem stejného
  poskytovatele. Jediný kandidát vyžaduje skóre i podobnost názvu `0.97`.
- Filmy vyžadují přesný rok. Seriály vyžadují přesný spolehlivě parsovaný vstupní rok, pokud je přítomen; seriál bez
  roku lze vybrat na základě dostatečně silného důkazu názvu.
- Seriál bez roku může jako potvrzení použít dva nebo tři deterministicky vybrané názvy epizod. Potvrzené skóre
  používá 75 % podobnosti názvu seriálu a 25 % průměrné podobnosti názvů epizod. Každý název epizody i název seriálu
  musí dosáhnout `0.85`, konečné skóre musí dosáhnout `0.92` a každá vybraná kombinace řady a epizody musí existovat.
- Automatický výběr poskytovatele pouze vytvoří stav `ready_for_approval`; nikdy neschválí přejmenování. Ruční změny
  jsou explicitní a auditovatelné.
- Prahy jsou pojmenované a verzované konstanty zásad, které operátor v prvním vydání nemůže snížit. Výběry z
  mezipaměti se automaticky použijí jen tehdy, pokud byly dříve schváleny podle stejné verze zásad a vstupy se
  nezměnily.

### Počáteční nasazení webového UI

- První UI je neautentizovaná aplikace pro jediného operátora na důvěryhodném počítači nebo privátní LAN. Není
  podporované na veřejném internetu ani nedůvěryhodné síti.
- Adresa naslouchání je konfigurovatelná a pro přístup z WSL, kontejneru, prohlížeče Windows a volitelně privátní LAN
  má výchozí hodnotu `0.0.0.0`. Naslouchání mimo loopback zobrazí upozornění, ale je povolené.
- Autentizace, účty, role, TLS spravované aplikací a integrace se Synology účtem nejsou požadavky prvního vydání.
  Integrace se Synology účtem zůstává volitelná.
- UI podporuje kontrolu, opravy, schvalování, náhled manifestu a dry-run, ale nemá endpoint skutečného přejmenování.
  Skutečné provedení zůstává v CLI za všemi existujícími bezpečnostními branami.
- Autentizace, session, ochrana CSRF, návod k HTTPS reverse proxy a zabezpečení vzdáleného přístupu jsou pozdější
  nadstavbou, nikoli překážkou funkčního UI.

### Otisk stavu zdroje

- Běžné soubory používají otisk z relativní cesty, typu položky, velikosti a času změny souborového systému. Hash
  celého obsahu, čísla inode, čas vytvoření, vlastník a oprávnění jsou z prvního vydání vyloučené.
- Přejmenovávané složky používají stromový SHA-256 digest nad seřazenou inventurou. Ignorovaní potomci přispívají jen
  neprůhlednou cestou a typem; nikdy se neotevírají ani nedostávají samostatné záznamy manifestu.
- Symbolické odkazy se vždy odmítnou a nikdy se nenásledují. Jejich přítomnost ve složce tuto složku vyloučí z
  plánování i provedení.
- Manifest má samostatný SHA-256 digest kanonické serializace. Úspěšný dry-run platí pouze pro přesný digest manifestu
  a shodné otisky zdrojů.
- Dry-run, začátek dávky a každá operace nezávisle ověřují stav zdroje. Každý rozdíl zastaví celý běh provádění a
  vyžaduje nové workflow od skenování po dry-run; otisky se nikdy neobnovují na místě.
- Existence cílů a kolize se samostatně kontrolují při plánování, dry-run i provedení.

### Částečné selhání a rollback

- První neúspěšná operace zastaví celý běh provádění. Aplikace nikdy automaticky nespustí rollback.
- Trvalý audit rozlišuje dokončené, neúspěšné, čekající a nejisté operace. Do neměnného JSON manifestu rollbacku
  vstoupí v opačném pořadí provedení pouze potvrzené úspěšné operace.
- Každá obrácená položka odkazuje na původní operaci a ukládá zdroj a cíl rollbacku, otisk zdroje, očekávanou
  nepřítomnost cíle, pořadí a důvod. Manifest odkazuje na původní běh a digest manifestu a má vlastní verzi schématu
  a SHA-256 digest. Nikdy neobsahuje shellové příkazy.
- Rollback používá běžný executor a vyžaduje ověření, dry-run, explicitní potvrzení a audit. Nikdy nepřepisuje
  existující cestu ani nemění vstupní manifest.
- Operátor volí mezi provedením rollbacku a zachováním dokončených operací s vytvořením nového workflow pro zbývající
  položky.

### Podpora architektur kontejneru

- Jediná oficiálně sestavovaná, testovaná a publikovaná platforma je `linux/amd64`, která pokrývá vývojové prostředí
  a cílová zařízení Synology DS925+ a DS723+.
- Projekt v prvním vydání nepublikuje obrazy ARM, 32bitové ani multi-platformní obrazy.
- Compose nenastavuje `platform`; nepodporovaný hostitel dostane běžnou chybu nekompatibilního obrazu místo skryté
  emulace.
- Dockerfile zůstává přiměřeně přenositelný a pokročilá dokumentace poskytuje příklady nativního a volitelného
  cross-buildu pro nepodporované platformy. Takové obrazy jsou best-effort bez release testování a podpory.

### Přístup Compose pro zápis

- Běžné `docker compose up` spouští dlouhodobou službu `app` s `/media:ro` a trvalým zapisovatelným workspace.
- Skutečné přejmenování a rollback používají samostatnou jednorázovou službu `executor` v explicitním profilu
  `execution`. Má `/media:rw`, žádnou síť, žádný webový port ani restart a po dokončení příkazu se odstraní.
- Dokumentované spuštění vyžaduje zároveň `--profile execution` a explicitní přepínač skutečného provedení v CLI.
  Executor před každou změnou získá globální execution lock ve workspace.
- Compose uvádí `:ro` a `:rw` přímo. Proměnné režimy mountu a zapisovatelná média webové služby jsou zakázané.
- Zapisovatelný mount poskytuje pouze schopnost zápisu; všechny brány integrity manifestu, otisků zdrojů,
  bezpečnosti cílů, úspěšného dry-run, potvrzení, zastavení při chybě, rollbacku a auditu zůstávají povinné.

## Vyřešená produktová rozhodnutí

Všechna produktová rozhodnutí určená pro toto sladění dokumentace jsou výše vyřešená. Implementace se jimi musí řídit
a nadále upřednostňovat zachování dat, explicitní kontrolu a vratné operace před automatizací.
