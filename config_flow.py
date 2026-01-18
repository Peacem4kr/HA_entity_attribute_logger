import voluptuous as vol
import logging
from homeassistant.core import callback
from homeassistant import config_entries
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt as dt_util

# CONF_IMPORT_HISTORY toegevoegd aan imports
from .const import DOMAIN, CONF_ENTITIES, CONF_RETENTION_DAYS, CONF_ATTRIBUTES, CONF_IMPORT_HISTORY

_LOGGER = logging.getLogger(__name__)

VIRTUAL_ATTRS = [
    "meta_day_of_week",
    "meta_is_weekend",
    "meta_hour_of_day",
    "meta_minute_of_hour",
    "meta_month",    
]

class OllamaPatternFinderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ollama Pattern Finder."""

    VERSION = 1

    def __init__(self):
        """Initialize flow."""
        self.data = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Start the options flow."""
        return OllamaOptionsFlowHandler(config_entry)

    def _get_display_title(self, user_input):
        """Genereer een titel op basis van entiteiten EN geselecteerde attributen."""
        entity_ids = user_input.get(CONF_ENTITIES, [])
        selected_attrs = user_input.get(CONF_ATTRIBUTES, [])
        
        if not entity_ids:
            return "Ollama Pattern Finder"
        
        eid = entity_ids[0]
        state = self.hass.states.get(eid)
        name = state.attributes.get("friendly_name", eid) if state else eid
        
        current_entity_attrs = []
        for attr_path in selected_attrs:
            if attr_path.startswith(f"{eid}#attr#"):
                attr_name = attr_path.split("#attr#")[1]
                current_entity_attrs.append(attr_name)
        
        title = name
        if current_entity_attrs:
            attr_string = ", ".join(current_entity_attrs[:2])
            if len(current_entity_attrs) > 2:
                attr_string += "..."
            title = f"{name} ({attr_string})"
        
        if len(entity_ids) > 1:
            title += f" +{len(entity_ids) - 1} extra"
            
        return title

    async def async_step_user(self, user_input=None):
        """Eerste stap: selecteer entiteiten en retentie."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_attributes()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ENTITIES): selector.EntitySelector(
                    selector.EntitySelectorConfig(multiple=True)
                ),
                vol.Optional(CONF_RETENTION_DAYS, default=30): vol.Coerce(int),
                # EXTRA CHECKBOX BIJ INSTALLATIE
                vol.Optional(CONF_IMPORT_HISTORY, default=False): bool,
            })
        )

    async def async_step_attributes(self, user_input=None):
        """Tweede stap: selecteer specifieke attributen."""
        if user_input is not None:
            full_data = {**self.data, **user_input}
            title = self._get_display_title(full_data)
            
            return self.async_create_entry(
                title=title,
                data=full_data
            )
        
        entities = self.data.get(CONF_ENTITIES, [])
        options = self._get_attribute_options(entities)

        return self.async_show_form(
            step_id="attributes",
            data_schema=vol.Schema({
                vol.Required(CONF_ATTRIBUTES): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode="list"
                    )
                ),
            })
        )

    def _get_attribute_options(self, entity_ids):
        """Generate the list of attributes with current values for the UI."""
        options = []
        now = dt_util.now()
        
        meta_labels = {
            "meta_state": "📝 Current State",
            "meta_day_of_week": f"📅 Day: {now.strftime('%A')}",
            "meta_is_weekend": f"🏖️ Weekend: {'Yes' if now.weekday() >= 5 else 'No'}",
            "meta_hour_of_day": f"🕒 Hour: {now.hour}h",
            "meta_minute_of_hour": f"⏱️ Minute: {now.minute}m",
            "meta_month": f"🗓️ Month: {now.strftime('%B')}",
            "meta_previous_state_duration": "⏳ Last State Duration"
        }

        for attr in VIRTUAL_ATTRS:
            options.append(selector.SelectOptionDict(value=attr, label=meta_labels[attr]))

        for eid in entity_ids:
            state_obj = self.hass.states.get(eid)
            if not state_obj:
                continue

            name = state_obj.attributes.get("friendly_name", eid)
            options.append(selector.SelectOptionDict(
                value=f"{eid}#state",
                label=f"⭐ {name}: State ({state_obj.state})"
            ))

            for attr, val in state_obj.attributes.items():
                if attr in ["friendly_name", "icon", "supported_features", "entity_picture"]:
                    continue

                display_val = str(val)[:22] + "..." if len(str(val)) > 25 else str(val)
                options.append(selector.SelectOptionDict(
                    value=f"{eid}#attr#{attr}",
                    label=f"🔹 {name}: {attr} ({display_val})"
                ))

        return options

class OllamaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the 'Configure' button."""

    def __init__(self, config_entry):
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            title_input = {
                CONF_ENTITIES: self._entry.data.get(CONF_ENTITIES, []),
                CONF_ATTRIBUTES: user_input.get(CONF_ATTRIBUTES, [])
            }
            
            flow_instance = OllamaPatternFinderConfigFlow()
            flow_instance.hass = self.hass
            new_title = flow_instance._get_display_title(title_input)
            
            self.hass.config_entries.async_update_entry(self._entry, title=new_title)
            return self.async_create_entry(title="", data=user_input)

        entities = self._entry.data.get(CONF_ENTITIES, [])
        flow_instance = OllamaPatternFinderConfigFlow()
        flow_instance.hass = self.hass
        options = flow_instance._get_attribute_options(entities)

        current_selection = (
            self._entry.options.get(CONF_ATTRIBUTES)
            or self._entry.data.get(CONF_ATTRIBUTES, [])
        )
        
        # Haal huidige import history status op
        current_import_history = self._entry.options.get(
            CONF_IMPORT_HISTORY, 
            self._entry.data.get(CONF_IMPORT_HISTORY, False)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_ATTRIBUTES,
                    default=list(current_selection)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode="list"
                    )
                ),
                # EXTRA CHECKBOX IN CONFIGURATIE MENU
                vol.Optional(CONF_IMPORT_HISTORY, default=current_import_history): bool,
            })
        )