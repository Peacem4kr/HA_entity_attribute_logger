import os
import json
import hashlib
import logging
import re
from datetime import timedelta
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.util import dt as dt_util
from homeassistant.components import recorder

# Voeg CONF_IMPORT_HISTORY toe aan je imports uit .const
from .const import DOMAIN, CONF_ENTITIES, CONF_RETENTION_DAYS, CONF_ATTRIBUTES, CONF_IMPORT_HISTORY

_LOGGER = logging.getLogger(__name__)

def slugify(text):
    """Maak een tekst veilig voor gebruik in een bestandsnaam."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Entity Attribute Logger."""
    
    # STAP 1: IDENTITEIT EN PADEN
    entry_title = slugify(entry.title)
    short_id = hashlib.md5(entry.entry_id.encode()).hexdigest()[:5]
    
    storage_path = hass.config.path("www", "entity_and_attribute_logger")
    
    if not os.path.exists(storage_path):
        await hass.async_add_executor_job(os.makedirs, storage_path)

    file_name = f"{entry_title}_{short_id}.json"
    file_path = os.path.join(storage_path, file_name)

    _LOGGER.warning("--- LOGGER START (Bestand: %s) ---", file_name)

    # CENTRALE FUNCTIE: Verwerk en bewaar een state
    def process_state(eid, state_obj, timestamp, is_history=False):
        if not state_obj or state_obj.state in ["unknown", "unavailable"]:
            return

        selected_attrs = entry.options.get(CONF_ATTRIBUTES, entry.data.get(CONF_ATTRIBUTES, []))
        retention = entry.options.get(CONF_RETENTION_DAYS, entry.data.get(CONF_RETENTION_DAYS, 30))
        state_key = f"{eid}#state"
        
        context_data = {"entity_id": eid}
        
        if state_key in selected_attrs:
            context_data["state"] = state_obj.state
        
        for item in selected_attrs:
            if item.startswith(f"{eid}#attr#"):
                attr_name = item.split("#attr#")[1]
                val = state_obj.attributes.get(attr_name)
                if val is not None:
                    context_data[attr_name] = val
        
        if len(context_data) <= 1:
            return

        local_time = dt_util.as_local(timestamp)
        if "meta_day_of_week" in selected_attrs:
            context_data["day"] = local_time.strftime("%A")
        if "meta_hour_of_day" in selected_attrs:
            context_data["hour"] = local_time.hour
        if "meta_minute_of_hour" in selected_attrs:
            context_data["minute"] = local_time.minute
        if "meta_month" in selected_attrs:
            context_data["month"] = local_time.strftime("%B")
        if "meta_is_weekend" in selected_attrs:
            context_data["is_weekend"] = local_time.weekday() >= 5

        history_list = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    history_list = json.load(f)
            except:
                history_list = []

        ts_iso = local_time.isoformat()
        existing_record = next(
            (d for d in history_list if d["ts"] == ts_iso and d["data"].get("entity_id") == eid), 
            None
        )

        if existing_record:
            needs_save = False
            for key, val in context_data.items():
                if key not in existing_record["data"]:
                    existing_record["data"][key] = val
                    needs_save = True
            if not needs_save:
                return
        else:
            history_list.append({"ts": ts_iso, "data": context_data})
            history_list.sort(key=lambda x: x["ts"])

        cutoff = dt_util.utcnow() - timedelta(days=retention)
        history_list = [d for d in history_list if dt_util.parse_datetime(d["ts"]) > cutoff]

        with open(file_path, 'w') as f:
            json.dump(history_list, f, indent=2)

    # LIVE HANDLER
    async def handle_state_change(event: Event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        eid = event.data.get("entity_id")
        
        selected_attrs = entry.options.get(CONF_ATTRIBUTES, entry.data.get(CONF_ATTRIBUTES, []))
        
        state_changed = old_state and old_state.state != new_state.state
        attr_changed = False
        for item in selected_attrs:
            if item.startswith(f"{eid}#attr#"):
                attr_name = item.split("#attr#")[1]
                if new_state.attributes.get(attr_name) != (old_state.attributes.get(attr_name) if old_state else None):
                    attr_changed = True
                    break
        
        if (f"{eid}#state" in selected_attrs and state_changed) or attr_changed:
            await hass.async_add_executor_job(process_state, eid, new_state, dt_util.utcnow())

    # HISTORISCHE IMPORT
    async def import_historical_data():
        entities = entry.data.get(CONF_ENTITIES, [])
        retention = entry.options.get(CONF_RETENTION_DAYS, entry.data.get(CONF_RETENTION_DAYS, 30))
        start_time = dt_util.utcnow() - timedelta(days=retention)

        _LOGGER.warning("[%s] Start geschiedenis import naar %s", entry_title, file_name)
        
        history_data = await hass.async_add_executor_job(
            recorder.history.get_significant_states, hass, start_time, None, entities
        )

        if history_data:
            for eid, states in history_data.items():
                for s in states:
                    await hass.async_add_executor_job(process_state, eid, s, s.last_changed, True)
        
        _LOGGER.warning("[%s] Import voltooid", entry_title)

    # SETUP LISTENERS
    entities = entry.data.get(CONF_ENTITIES, [])
    entry.async_on_unload(async_track_state_change_event(hass, entities, handle_state_change))
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # STAP 4: CHECK OF HISTORY GEÏMPORTEERD MOET WORDEN
    # We kijken in opties (als gewijzigd) of data (bij eerste installatie)
    should_import = entry.options.get(CONF_IMPORT_HISTORY, entry.data.get(CONF_IMPORT_HISTORY, False))

    if should_import:
        hass.async_create_task(import_historical_data())
    else:
        _LOGGER.info("[%s] Geschiedenis import overgeslagen (uitgeschakeld in instellingen)", entry_title)

    return True

async def async_reload_entry(hass: HomeAssistant, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry):

    return await hass.config_entries.async_unload_platforms(entry, [])
