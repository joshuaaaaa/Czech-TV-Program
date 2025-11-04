class TvProgramCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
    this._days = 3; // Inicializace defaultního počtu dní
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Prosím, definujte entitu');
    }

    this._config = {
      entity: config.entity,
      title: config.title || 'TV Program',
      show_genre: config.show_genre !== false,
      show_duration: config.show_duration !== false,
      show_description: config.show_description !== false,
      max_programs: config.max_programs || 50,
    };
    
    // Nastaví počet dní z konfigurace, pokud existuje. Používá privátní proměnnou.
    this._days = config.days || 3; 

    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    // Optimalizované renderování: rendrujeme jen když se změní data entity
    const oldState = this._lastState;
    const newState = hass.states[this._config.entity];

    if (!oldState || !newState || oldState.state !== newState.state || JSON.stringify(oldState.attributes) !== JSON.stringify(newState.attributes)) {
      this._lastState = newState;
      this.render();
    }
  }

  // Přidání metody pro parsování data/času pro správné porovnávání
  _parseProgramDatetime(program) {
    if (!program.date || !program.time) return null;
    // Předpokládá formát YYYY-MM-DD HH:MM z Python kódu
    const datetimeStr = `${program.date}T${program.time}:00`;
    const programDate = new Date(datetimeStr);
    
    // Kontrola, zda je datum platné
    if (isNaN(programDate)) {
        console.error(`Chyba při parsování data pro program: ${program.title} s datem ${program.date} a časem ${program.time}`);
        return null;
    }
    return programDate;
  }

  render() {
    if (!this._hass || !this._config.entity) return;

    const entity = this._hass.states[this._config.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <p>Entita "${this._config.entity}" nebyla nalezena</p>
          </div>
        </ha-card>
      `;
      return;
    }

    const allPrograms = entity.attributes.all_programs || [];
    const channelName = entity.attributes.channel || 'TV';
    
    // 1. Získej aktuální čas
    const now = new Date();
    
    // 2. Vypočítej konečné datum (poslední den, který chceme zobrazit)
    const endDate = new Date(now);
    endDate.setDate(now.getDate() + this._days);
    // Nastav čas na 23:59:59 pro daný den, abychom zahrnuli celý den
    endDate.setHours(23, 59, 59, 999); 
    
    // 3. Filtruj programy
    const filteredPrograms = allPrograms
      .map(program => ({ ...program, datetime: this._parseProgramDatetime(program) })) // Přidej parsované datum
      .filter(program => {
        if (!program.datetime) return false;
        // Zobraz programy, které již začaly A NEBO jsou v rozsahu (now až endDate)
        // Programy, které začaly, ale neskončily, by měly být zobrazeny, ale náš filtr je založen pouze na čase začátku.
        // Pro správné zobrazení nadcházejících ignorujeme ty, které už začaly, a zaměřujeme se na budoucí.
        // Protože ale entita již zobrazuje CURRENT program, zaměříme se na budoucí programy.
        return program.datetime >= now && program.datetime <= endDate;
      })
      .slice(0, this._config.max_programs);

    const currentProgram = {
      title: entity.attributes.current_title || '',
      time: entity.attributes.current_time || '',
      genre: entity.attributes.current_genre || '',
      duration: entity.attributes.current_duration || '',
      description: entity.attributes.current_description || '',
    };

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .card-header {
          font-size: 24px;
          font-weight: 500;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--divider-color);
        }
        .current-program {
          /* Barvy pro lepší kontrast */
          background: var(--primary-color, #03a9f4); 
          color: var(--ha-card-background, #fff); 
          padding: 12px;
          border-radius: 8px;
          margin: 16px 0;
        }
        .current-program .title {
          font-size: 18px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        .current-program .info {
          font-size: 14px;
          opacity: 0.9;
        }
        .days-selector {
          display: flex;
          gap: 8px;
          margin: 16px 0;
          flex-wrap: wrap;
        }
        .day-button {
          padding: 8px 16px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          color: var(--primary-text-color); /* Zajištění viditelnosti textu */
          cursor: pointer;
          transition: all 0.3s;
        }
        .day-button:hover {
          background: var(--light-primary-color, #67daff); 
          color: var(--text-primary-color, #000); /* Barva pro hover */
        }
        .day-button.active {
          background: var(--primary-color, #03a9f4);
          color: var(--text-primary-color, #fff); 
          border-color: var(--primary-color, #03a9f4);
        }
        .program-list {
          margin-top: 16px;
        }
        .program-item {
          padding: 12px;
          border-bottom: 1px solid var(--divider-color);
          display: flex;
          gap: 12px;
        }
        .program-item:last-child {
            border-bottom: none;
        }
        .program-item:hover {
          background: var(--secondary-background-color, #f0f0f0);
        }
        .program-time {
          font-weight: 500;
          min-width: 60px;
          color: var(--primary-text-color);
        }
        .program-details {
          flex: 1;
        }
        .program-title {
          font-weight: 500;
          margin-bottom: 4px;
        }
        .program-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-right: 4px;
          /* Použití accent barvy pro lepší viditelnost */
          background: var(--label-badge-background-color, #41aea9); 
          color: var(--label-badge-text-color, #fff); 
        }
        .program-info {
          font-size: 14px;
          color: var(--secondary-text-color);
          margin-top: 4px;
        }
        .program-description {
          font-size: 13px;
          color: var(--secondary-text-color);
          margin-top: 8px;
          line-height: 1.4;
        }
        .date-separator {
          font-weight: 500;
          padding: 12px 8px;
          background: var(--card-background-color); /* Použijeme barvu pozadí karty */
          margin-top: 8px;
          border-radius: 4px;
          border-bottom: 1px solid var(--divider-color);
          color: var(--primary-color);
        }
        .no-programs {
          padding: 20px;
          text-align: center;
          color: var(--secondary-text-color);
        }
      </style>
      
      <ha-card>
        <div class="card-header">
          ${this._config.title} - ${this.escapeHtml(channelName)}
        </div>
        
        ${currentProgram.title ? `
          <div class="current-program">
            <div class="title">▶ Nyní: ${this.escapeHtml(currentProgram.title)}</div>
            <div class="info">
              ${currentProgram.time} 
              ${this._config.show_genre && currentProgram.genre ? `• ${this.escapeHtml(currentProgram.genre)}` : ''}
              ${this._config.show_duration && currentProgram.duration ? `• ${currentProgram.duration}` : ''}
            </div>
          </div>
        ` : ''}
        
        <div class="days-selector">
          ${[1, 2, 3, 5, 7].map(days => `
            <button class="day-button ${this._days === days ? 'active' : ''}" 
                    onclick="this.getRootNode().host.updateDays(${days})">
              ${days} ${days === 1 ? 'den' : days < 5 ? 'dny' : 'dní'}
            </button>
          `).join('')}
        </div>
        
        <div class="program-list">
          ${filteredPrograms.length > 0 ? this.renderPrograms(filteredPrograms) : `
            <div class="no-programs">Žádné nadcházející pořady v následujících ${this._days} dnech.</div>
          `}
        </div>
      </ha-card>
    `;
  }

  renderPrograms(programs) {
    let html = '';
    let lastDate = '';

    programs.forEach(program => {
      // Add date separator if date changes
      if (program.date && program.date !== lastDate) {
        // Použijeme program.datetime pro správné formátování dne v týdnu
        const date = program.datetime || this._parseProgramDatetime(program);
        const dateStr = date ? this.formatDate(date) : program.date;
        html += `<div class="date-separator">${dateStr}</div>`;
        lastDate = program.date;
      }

      html += `
        <div class="program-item">
          <div class="program-time">${program.time || ''}</div>
          <div class="program-details">
            <div class="program-title">
              ${program.supertitle ? `${this.escapeHtml(program.supertitle)}: ` : ''}
              ${this.escapeHtml(program.title || 'Neznámý pořad')}
              ${program.episode_title ? ` - ${this.escapeHtml(program.episode_title)}` : ''}
            </div>
            ${program.live || program.premiere || program.episode ? `
              <div>
                ${program.live ? '<span class="program-badge">ŽIVĚ</span>' : ''}
                ${program.premiere ? '<span class="program-badge">PREMIÉRA</span>' : ''}
                ${program.episode ? `<span class="program-badge">${this.escapeHtml(program.episode)}</span>` : ''}
              </div>
            ` : ''}
            ${this._config.show_genre || this._config.show_duration ? `
              <div class="program-info">
                ${this._config.show_genre && program.genre ? this.escapeHtml(program.genre) : ''}
                ${this._config.show_genre && program.genre && this._config.show_duration && program.duration ? ' • ' : ''}
                ${this._config.show_duration && program.duration ? program.duration : ''}
              </div>
            ` : ''}
            ${this._config.show_description && program.description ? `
              <div class="program-description">${this.escapeHtml(program.description)}</div>
            ` : ''}
          </div>
        </div>
      `;
    });

    return html;
  }

  formatDate(date) {
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Pro porovnání ignorujeme čas

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const programDate = new Date(date);
    programDate.setHours(0, 0, 0, 0);

    if (programDate.getTime() === today.getTime()) {
      return 'Dnes';
    } else if (programDate.getTime() === tomorrow.getTime()) {
      return 'Zítra';
    } else {
      const days = ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'];
      return `${days[date.getDay()]} ${date.getDate()}.${date.getMonth() + 1}.`;
    }
  }

  escapeHtml(text) {
    if (typeof text !== 'string') return text;
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  updateDays(days) {
    this._days = days; // Aktualizujeme _days
    this.render();
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('tv-program-card', TvProgramCard);

// Register the card
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'tv-program-card',
  name: 'TV Program Card',
  description: 'Karta pro zobrazení TV programu z České televize',
  preview: true,
});

// Add to card picker
console.info(
  '%c TV-PROGRAM-CARD %c Version 1.0.0 ',
  'color: orange; font-weight: bold; background: black',
  'color: white; font-weight: bold; background: dimgray',
);
