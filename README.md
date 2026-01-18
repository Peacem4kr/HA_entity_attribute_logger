# Entity & Attribute Logger for Home Assistant

## Overview

The **Entity & Attribute Logger** is a custom integration for Home Assistant designed to solve a specific problem: keeping a detailed, long-term history of state changes for one or more entities or attributes in a format that is easy to process.

While Home Assistant's internal database (Recorder) eventually purges old data, this integration allows you to build an indefinite, human-readable (JSON) log of an entity's behavior. This makes it the perfect bridge for deep-data analysis and feeding historical patterns into Local LLMs (like Google Gemma or OpenAI).

---

## 🚀 Key Features

- **Persistent Long-Term History**: Create a permanent log for specific entities or attribute(s) that survives Home Assistant database purges.
- **Deep Attribute Logging**: Every state change triggers a log entry containing the state AND all associated attributes (e.g., GPS coordinates, battery level, or climate presets).
- **Customizable Retention**: You decide how long the data stays. Choose between keeping everything forever or setting a specific number of days to keep your storage clean.
- **AI-Ready JSON**: Data is stored in a chronological JSON structure, making it "plug-and-play" for AI pattern analysis.
- **Minimal Footprint**: Lightweight logic that only triggers when the specified entity actually changes.

## 🛠 How it Works

The integration monitors your selected entities. Every time an entity updates, the integration appends the new data to a local JSON file. This results in a "time-series" dataset that is independent of the Home Assistant Recorder.



## 📅 Retention Policy

One of the core features is the **Retention Policy**. In the configuration menu, you can set how many days of history you want to keep:
- **0 (Default)**: Keep all data forever.
- **X Days**: Automatically remove entries older than X days to save disk space.

## 📥 Installation

1. Open Home Assistant UI and go to **HACS** → **Integrations**.  
2. Click the three dots menu (top right), then **Custom repositories**.  
3. Add this repository URL: `https://github.com/Peacem4kr/HA_entity_attribute_logger`
4. Select **Integration** as the category and click **Add**.
5. **Download** the integration and **Restart** Home Assistant.

## ⚙️ Configuration

### Step 1: Initialize the Integration
Go to **Settings** → **Devices & Services** → **Add Integration** and search for **Entity & Attribute Logger**.

### Step 2: Select Entities
During the setup, you can select which entities you want to track. The logger will automatically start recording state changes to `/config/entity_attribute_logger/`.
1 file per "Entry", even when multiple entities are used, this way you can combine logging for better analysis.

### Step 3: Usage in Automations (Optional)
If you want to feed the logged data into an AI model (like Gemma), you can use a `shell_command` to pass the file content to your automation:

```yaml
# configuration.yaml example
shell_command:
  get_ai_history: "cat /config/entity_attribute_logger/device_tracker_bjorn.json"
