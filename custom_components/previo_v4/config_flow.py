from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from typing import Any, Dict, Optional

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({
    vol.Required("login"): str,
    vol.Required("password"): str,
    vol.Required("hotel_id"): str,
})

class PrevioV4ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow pro Previo v4."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Zpracuj uživatelský vstup."""
        errors = {}
        
        if user_input is not None:
            # Základní validace
            if not user_input.get("login", "").strip():
                errors["login"] = "Přihlašovací jméno je povinné"
            if not user_input.get("password", "").strip():
                errors["password"] = "Heslo je povinné"
            if not user_input.get("hotel_id", "").strip():
                errors["hotel_id"] = "ID hotelu je povinné"
            
            if not errors:
                # Můžeme přidat testovací připojení k API
                # test_result = await self._test_connection(user_input)
                # if not test_result:
                #     errors["base"] = "Nepodařilo se připojit k Previo API"
                
                return self.async_create_entry(
                    title=f"Previo v4 - Hotel {user_input['hotel_id']}", 
                    data=user_input
                )
        
        return self.async_show_form(
            step_id="user", 
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "login": "Vaše Previo přihlašovací jméno",
                "password": "Vaše Previo heslo", 
                "hotel_id": "ID vašeho hotelu v systému Previo"
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Vytvoř options flow."""
        return PrevioV4OptionsFlow(config_entry)

class PrevioV4OptionsFlow(config_entries.OptionsFlow):
    """Options flow pro Previo v4."""
    
    def __init__(self, config_entry):
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input=None):
        """Správa možností integrace."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        options_schema = vol.Schema({
            vol.Optional(
                "update_interval", 
                default=self.config_entry.options.get("update_interval", 15)
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
            vol.Optional(
                "days_ahead", 
                default=self.config_entry.options.get("days_ahead", 30)
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=90)),
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "update_interval": "Interval aktualizace v minutách (5-60)",
                "days_ahead": "Počet dní dopředu pro načítání rezervací (1-90)"
            }
        )