# Czech TV Program Integration - OPRAVY

## KRITICKÉ problémy, které způsobily zamrznutí HA:

### 1. ⚠️ BLOKOVÁNÍ STARTUPU (nejzávažnější!)
**Problém:** 
- `async_config_entry_first_refresh()` blokoval startup HA
- Muselo se načíst 7 kanálů × 7 dní = 49 HTTP requestů
- S 1s pauzou mezi requesty = 49+ sekund čekání
- Při problémech s API zamrzl celý Home Assistant!

**Oprava:**
- Startup je nyní neblokující
- Data se načítají na pozadí
- HA startuje okamžitě i bez dat

### 2. 🐌 SEKVENČNÍ REQUESTY
**Problém:**
- Všechny requesty běžely sekvenčně (jeden po druhém)
- 49 requestů trvalo 49+ sekund

**Oprava:**
- Requesty běží paralelně (asyncio.gather)
- Všech 49 requestů se dokončí za ~10-15 sekund
- Timeout 120s pro celý update

### 3. 💾 OBROVSKÁ DATA V ATRIBUTECH
**Problém:**
- `all_programs` obsahoval ~200 programů (7 dní)
- Způsobovalo vysoké CPU při každém renderu entity
- Obrovská velikost state

**Oprava:**
- `all_programs` nyní pouze dnes + zítra (~50 programů)
- Snížení velikosti dat o 75%
- Cache pro aktuální program (aktualizace max 1x za minutu)

### 4. 🔄 FULL RELOAD PŘI ZMĚNĚ OPTIONS
**Problém:**
- Každá změna kanálů = reload celé integrace
- Opakované blokování

**Oprava:**
- Pouze aktualizace channelů v API
- Refresh dat místo reload

### 5. ❌ CONFIG FLOW CHYBA
**Problém:**
- Chybějící `username` field v schema
- Způsobovalo chybu při setupu

**Oprava:**
- Přidán `username` field s defaultem "test"

## Výsledky optimalizace:

| Metrika | Před | Po |
|---------|------|-----|
| Startup blokování | 49+ sekund | 0 sekund |
| Update doba | 49+ sekund | 10-15 sekund |
| Velikost atributů | ~200 programů | ~50 programů |
| CPU zátěž | vysoká | nízká |
| Timeout handling | žádný | 120s global |

## Instalace:

1. Zálohuj původní integraci
2. Nahraď soubory v `custom_components/cz_tv_program/`
3. Restartuj Home Assistant
4. Integrace by měla startovat okamžitě
5. Data se načtou během pár sekund na pozadí

## Poznámky:

- Integrace nyní startuje vždy, i když API nereaguje
- Paralelní requesty jsou rychlejší a efektivnější
- Cache snižuje CPU zátěž
- Timeout chrání před zamrznutím
- Všechny chyby jsou logované, ale neblokují ostatní kanály
