# Entity & Attribute Logger for Home Assistant

## Overview

This repository contains a custom integration for Home Assistant called **"Entity & Attribute Logger"**. 

This integration is designed to bridge the gap between Home Assistant's state machine and AI analysis. It allows users to export the full state and all attributes of any entity into a clean JSON format. This data can then be used by Local LLMs (like Google Gemma or OpenAI) to perform advanced pattern analysis, such as predicting your next departure time or analyzing household habits.

---

## Features

- **Full Attribute Logging**: Captures not just the state, but every single attribute of an entity, free to choose.
- **AI-Ready Output**: Generates a clean JSON string optimized for LLM tokenization.
- **Shell Integration**: Can be triggered via a shell command for use in complex automations.

## Requirements

- Home Assistant (Supervised or OS recommended)
- [HACS](https://hacs.xyz/) installed (for easy management)
- Access to `configuration.yaml`

## Installation

1. Open Home Assistant UI and go to **HACS** → **Integrations**.  
2. Click the three dots menu (top right), then **Custom repositories**.  
3. Add this repository URL: `https://github.com/YOUR_USERNAME/entity_attribute_logger`
4. Select **Integration** as the category and click **Add**.
5. **Download** the integration.
6. **Restart** Home Assistant.

## Configuration

### Step 1: Add the Integration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.  
2. Search for **Entity & Attribute Logger** and select it.  
3. Follow the setup wizard to initialize the component.

### Step 2: Add Shell Command to `configuration.yaml`

To use the logger in your automations, add a shell command that points to the logger script. Replace `sensor.your_entity` with the entity you want to track:

```yaml
shell_command:
  log_person_name: "python3 /config/custom_components/entity_attribute_logger/log_script.py device_tracker.name"
