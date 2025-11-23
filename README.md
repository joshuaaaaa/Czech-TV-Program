# Czech TV Program 2.0 - Home Assistant Integrace

Integrace pro stahování TV programu České televize, TV Prima, TV Nova a dalších stanic do Home Assistant s týdenním programem a custom kartou pro dashboard.

<img width="425" height="473" alt="image" src="https://github.com/user-attachments/assets/f52fb0e3-cb15-417f-ad42-a4d8963f06e9" />

## 🎉 Novinky ve verzi 2.0

- 🌟 **Podpora více zdrojů** - České televize a XMLTV (Prima, Nova, a další)
- 📊 **Více typů senzorů** - Aktuální program, Nadcházející programy, Denní program
- 💾 **JSON úložiště** - Data se ukládají do souborů pro snížení velikosti v paměti
- 🔌 **Modulární architektura** - Snadné přidání dalších zdrojů v budoucnu
- ⚡ **Lepší výkon** - Optimalizace načítání a ukládání dat

## ✨ Funkce

- 📺 **Více zdrojů TV programu:**
  - **Česká televize** (ČT1, ČT2, ČT24, ČT sport, ČT :D, ČT art, ČT3)
  - **XMLTV** (Prima, Prima COOL, Prima ZOOM, Prima MAX, Prima LOVE, Prima KRIMI, Prima STAR, Prima SHOW, CNN Prima, TV Nova, Nova Cinema, Nova Action, Nova Gold, Nova Sport 1, Nova Sport 2)
- 📅 Týdenní program dopředu
- 📊 **Tři typy senzorů** pro každý kanál:
  - Aktuální program
  - Nadcházející programy (10 nejbližších)
  - Denní program (dnes + zítra)
- 💾 Úsporné ukládání dat do JSON souborů
- 🎨 Custom Lovelace karta s možností výběru počtu dní
- 🔄 Automatická aktualizace každých 6 hodin

## 📦 Instalace

### HACS (Doporučeno)
1. Přidejte tento repozitář do HACS jako vlastní repozitář
2. Vyhledejte "Czech TV Program" v HACS a dejte stáhnout
3. Restartujte
4. Nainstalujte integraci


### Manuální instalace

1. **Zkopírujte složku integrace** do vašeho Home Assistant:
   ```
   custom_components/cz_tv_program/
   ```
   Do adresáře: `/config/custom_components/`

2. **Restartujte Home Assistant**

3. **Přidejte integraci:**
   - Jděte do **Nastavení** → **Zařízení a služby**
   - Klikněte na **+ Přidat integraci**
   - Vyhledejte "Czech TV Program"
   - **Krok 1:** Vyberte zdroj dat:
     - **Česká televize (ČT)** - oficiální API České televize
     - **XMLTV** - Prima, Nova a další stanice
   - **Krok 2:** Vyberte kanály, které chcete sledovat
   - Klikněte na **Odeslat**

### Custom Karta

1. **Zkopírujte soubor karty:**
   ```
   www/tv-program-card.js
   ```
   Do adresáře: `/config/www/`

2. **Přidejte kartu jako resource** v Lovelace:
   - Jděte do **Nastavení** → **Dashboardy**
   - Klikněte na tři tečky → **Resources**
   - Klikněte **+ Add Resource**
   - URL: `/local/tv-program-card.js`
   - Resource type: **JavaScript Module**
   - Klikněte **Create**

3. **Přidejte kartu do dashboardu:**
   - Upravte váš dashboard
   - Klikněte **+ Add Card**
   - Vyhledejte "TV Program Card"
   - Nebo použijte manuální konfiguraci (viz níže)

## 🔧 Konfigurace Karty

### Základní konfigurace
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_ct1
title: TV Program ČT1
days: 3
```

### Pokročilá konfigurace
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_ct24
title: ČT24 Program
days: 5
show_genre: true
show_duration: true
show_description: true
max_programs: 50
```

### Parametry karty

| Parametr | Typ | Výchozí | Popis |
|----------|-----|---------|-------|
| `entity` | string | **povinné** | Entity ID TV program sensoru |
| `title` | string | "TV Program" | Nadpis karty |
| `days` | number | 3 | Počet dní programu k zobrazení (1-7) |
| `show_genre` | boolean | true | Zobrazit žánr pořadu |
| `show_duration` | boolean | true | Zobrazit délku pořadu |
| `show_description` | boolean | true | Zobrazit popis pořadu |
| `max_programs` | number | 50 | Maximální počet zobrazených pořadů |

## 📱 Použití

### Dostupné senzory

**Verze 2.0** vytváří **tři typy senzorů** pro každý vybraný kanál:

#### Příklad pro ČT1:
- `sensor.ct1_aktualni_program` - Aktuálně běžící pořad
- `sensor.ct1_nadchazejici` - Nadcházející programy (10 nejbližších)
- `sensor.ct1_denni_program` - Denní program (dnes + zítra)

#### Příklad pro TV Nova:
- `sensor.nova_aktualni_program` - Aktuálně běžící pořad
- `sensor.nova_nadchazejici` - Nadcházející programy
- `sensor.nova_denni_program` - Denní program

### Atributy senzorů

#### Aktuální program (`*_aktualni_program`)
- `title` - název pořadu
- `supertitle` - nadtitul pořadu
- `episode_title` - název dílu
- `time` - čas začátku
- `date` - datum
- `genre` - žánr
- `duration` - délka
- `description` - popis
- `episode` - číslo epizody
- `link` - odkaz na detail
- `live` - živé vysílání (true/false)
- `premiere` - premiéra (true/false)

#### Nadcházející programy (`*_nadchazejici`)
- `programs` - seznam 10 nadcházejících programů s detaily

#### Denní program (`*_denni_program`)
- `today` - seznam programů na dnes
- `tomorrow` - seznam programů na zítra

### Příklad použití v automatizaci
```yaml
automation:
  - alias: "Upozornění na oblíbený pořad"
    trigger:
      - platform: state
        entity_id: sensor.tv_program_ct1
    condition:
      - condition: template
        value_template: "{{ 'Zprávy' in state_attr('sensor.tv_program_ct1', 'current_title') }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Začínají Zprávy na ČT1!"
```

#### Zapni TV 5 minut před oblíbeným filmem
```yaml
automation:
  - alias: "Zapni TV před filmem"
    trigger:
      - platform: time_pattern
        minutes: "/1"
    condition:
      - condition: template
        value_template: >
          {% set upcoming = state_attr('sensor.tv_program_ct1', 'upcoming_programs') %}
          {% if upcoming and upcoming|length > 0 %}
            {% set next_program = upcoming[0] %}
            {% set now = now() %}
            {% set program_time = strptime(next_program.date ~ ' ' ~ next_program.time, '%Y-%m-%d %H:%M') %}
            {% set time_diff = (program_time - now).total_seconds() / 60 %}
            {{ time_diff <= 5 and time_diff > 4 and 'Film' in next_program.title }}
          {% else %}
            false
          {% endif %}
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.tv_obyvak
```

### Použití v šablonách
```yaml
# Zobrazení aktuálního pořadu
{{ state_attr('sensor.tv_program_ct1', 'current_title') }}

# Zobrazení času dalšího pořadu
{{ state_attr('sensor.tv_program_ct1', 'upcoming_programs')[0].time }}
```

## 📊 Příklad dashboardu

```yaml
type: vertical-stack
cards:
  - type: custom:tv-program-card
    entity: sensor.tv_program_ct1
    title: ČT1
    days: 3
    
  - type: custom:tv-program-card
    entity: sensor.tv_program_ct24
    title: ČT24 Zpravodajství
    days: 1
    show_description: false
    
  - type: entities
    title: Přehled kanálů
    entities:
      - sensor.tv_program_ct1
      - sensor.tv_program_ct2
      - sensor.tv_program_ct24
```

## 🔄 Aktualizace dat

- Data se automaticky aktualizují každých **6 hodin**
- Program je dostupný na **7 dní dopředu**
- Data jsou uložena v JSON souborech v `/config/tv_program_data/`
- Integraci můžete ručně aktualizovat z karty integrace
- V případě chyby načítání se použijí uložená data z cache

## 📝 Poznámky

### Česká televize (ČT)
- Používá **oficiální API České televize**
- API vyžaduje parametr `user`, výchozí hodnota je `test`
- Pro vlastní registraci navštivte: https://www.ceskatelevize.cz/xml/tv-program/registrace/
- API umožňuje **max. 1 požadavek za minutu** - integrace toto respektuje

### XMLTV (Prima, Nova)
- Používá agregovaný XMLTV zdroj: http://xmltv.tvpc.cz/xmltv.xml
- Data se cachují na 1 hodinu
- Podporuje vlastní XMLTV URL v pokročilém nastavení
- Obsahuje program z DVB-T vysílání

## 🐛 Řešení problémů

### Integrace se nenačte
- Zkontrolujte, zda je složka `custom_components/cz_tv_program/` správně zkopírována
- Restartujte Home Assistant
- Zkontrolujte logy v **Nastavení** → **Systém** → **Logy**

### Karta se nezobrazuje
- Zkontrolujte, zda je soubor `tv-program-card.js` ve složce `www/`
- Ověřte, že je karta přidána jako resource
- Vymažte cache prohlížeče (Ctrl+F5)

### Data se neaktualizují
- Zkontrolujte připojení k internetu
- Zkontrolujte logy pro chyby API
- České televize API může být dočasně nedostupné

## 🎯 Plánované funkce

- [x] Podpora dalších TV stanic (Prima, Nova) ✅ **Nové ve v2.0**
- [x] Podpora XMLTV formátu ✅ **Nové ve v2.0**
- [x] Více typů senzorů ✅ **Nové ve v2.0**
- [x] JSON úložiště pro úsporu paměti ✅ **Nové ve v2.0**
- [ ] Filtrování pořadů podle žánru
- [ ] Oblíbené pořady
- [ ] Notifikace před začátkem vybraných pořadů
- [ ] Vyhledávání v programu
- [ ] Podpora dalších zdrojů (další XMLTV zdroje)

## 📄 Licence

Tento projekt je poskytován "tak jak je" bez záruky.

## 🤝 Přispívání

Příspěvky jsou vítány! Vytvořte issue nebo pull request.

## http://buymeacoffee.com/jakubhruby


<img width="150" height="150" alt="qr-code" src="https://github.com/user-attachments/assets/2581bf36-7f7d-4745-b792-d1abaca6e57d" />

