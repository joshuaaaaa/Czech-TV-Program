# Czech TV Program - Home Assistant Integrace

Integrace pro stahování TV programu České televize do Home Assistant s týdenním programem a custom kartou pro dashboard.

<img width="425" height="473" alt="image" src="https://github.com/user-attachments/assets/f52fb0e3-cb15-417f-ad42-a4d8963f06e9" />


## ✨ Funkce

- 📺 Stahování TV programu z oficiálního API České televize
- 📅 Týdenní program dopředu
- 🎯 Výběr kanálů: ČT1, ČT2, ČT24, ČT sport, ČT :D, ČT art, ČT3
- 📊 Detailní informace o pořadech (název, čas, žánr, popis, délka)
- 🎨 Custom Lovelace karta s možností výběru počtu dní
- 🔄 Automatická aktualizace každých 6 hodin

## 📦 Instalace

### HACS (Doporučeno)
1. Přidejte tento repozitář do HACS jako vlastní repozitář
2. Vyhledejte "Czech TV Program" v HACS
3. Nainstalujte kartu
4. Přidejte kartu do vaší Lovelace konfigurace

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
   - Vyberte kanály, které chcete sledovat
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
Po instalaci budou vytvořeny senzory pro každý vybraný kanál:
- `sensor.tv_program_ct1` - ČT1
- `sensor.tv_program_ct2` - ČT2
- `sensor.tv_program_ct24` - ČT24
- `sensor.tv_program_ct4` - ČT sport
- `sensor.tv_program_ct5` - ČT :D
- `sensor.tv_program_ct6` - ČT art
- `sensor.tv_program_ct7` - ČT3

### Atributy senzoru
Každý senzor obsahuje následující atributy:

- **current_*** - informace o aktuálním pořadu
- **upcoming_programs** - seznam nadcházejících 10 pořadů
- **all_programs** - kompletní týdenní program

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
- Integraci můžete ručně aktualizovat z karty integrace

## 📝 Poznámky

- Integrace používá **oficiální API České televize**
- API vyžaduje parametr `user`, výchozí hodnota je `test`
- Pro vlastní registraci navštivte: https://www.ceskatelevize.cz/xml/tv-program/registrace/
- API umožňuje **max. 1 požadavek za minutu** - integrace toto respektuje

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

- [ ] Podpora dalších TV stanic (Prima, Nova)
- [ ] Podpora XMLTV formátu
- [ ] Filtrování pořadů podle žánru
- [ ] Oblíbené pořady
- [ ] Notifikace před začátkem vybraných pořadů
- [ ] Vyhledávání v programu

## 📄 Licence

Tento projekt je poskytován "tak jak je" bez záruky.

## 🤝 Přispívání

Příspěvky jsou vítány! Vytvořte issue nebo pull request.

## http://buymeacoffee.com/jakubhruby


<img width="150" height="150" alt="qr-code" src="https://github.com/user-attachments/assets/2581bf36-7f7d-4745-b792-d1abaca6e57d" />

