# Entity & Attribute Logger for Home Assistant

## Overview

The **Entity & Attribute Logger** is a custom integration for Home Assistant designed to solve a specific problem: keeping a detailed, long-term history of state changes and attributes for a single entity in a format that is easy to process.

While Home Assistant's internal database (Recorder) eventually purges old data, this integration allows you to build an indefinite, human-readable (JSON) log of an entity's behavior. This makes it the perfect bridge for deep-data analysis and feeding historical patterns into Local LLMs (like Google Gemma or OpenAI).

---

## 🚀 Key Features

- **Persistent Long-Term History**: Unlike the standard Recorder, this integration focuses on creating a permanent log for specific entities.
- **Deep Attribute Logging**: Every state change triggers a log entry containing the state AND all associated attributes (e.g., GPS coordinates, battery level, or climate presets).
- **AI-Ready JSON**: Data is stored in a clean, chronological JSON structure, making it "plug-and-play" for AI pattern analysis.
- **Minimal Footprint**: Lightweight logic that only triggers when the specified entity actually changes.

## 🛠 How it Works

The integration monitors a specific entity. Every time that entity updates, the integration appends the new data to a local file. This results in a "time-series" dataset that survives Home Assistant restarts and database purges.



## 📋 Requirements

- Home Assistant (Supervised or OS recommended)
- [HACS](https://hacs.xyz/) installed
- Access to your local file system (via File Editor or Samba)

## 📥 Installation

1. Open Home Assistant UI and go to **HACS** → **Integrations**.  
2. Click the three dots menu (top right), then **Custom repositories**.  
3. Add this repository URL: `https://github.com/YOUR_USERNAME/entity_attribute_logger`
4. Select **Integration** as the category and click **Add**.
5. **Download** the integration and **Restart** Home Assistant.

## ⚙️ Configuration

### Step 1: Initialize the Integration
Go to **Settings** → **Devices & Services** → **Add Integration** and search for **Entity & Attribute Logger**.

### Step 2: Set up the Logger script
The integration uses a Python script to handle the file writing. Ensure the script is located in your custom components folder:
`/config/custom_components/entity_attribute_logger/log_script.py`

### Step 3: Usage via Shell Command
Add the following to your `configuration.yaml` to enable the logging trigger:

```yaml
shell_command:
  log_my_tracker: "python3 /config/custom_components/entity_attribute_logger/log_script.py device_tracker.my_phone"
