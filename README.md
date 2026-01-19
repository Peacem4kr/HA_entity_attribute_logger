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
During the setup, you can select which entities you want to track. The logger will automatically start recording state changes to `/config/www/entity_and_attribute_logger/`.
Files are organized per "Entry". Even when multiple entities are used in one entry, they are logged into a single file to allow for better cross-entity analysis.

---

## 💡 Example Use Case: AI-Driven Car Pre-heating

**The Problem:**
I wanted to track when we leave home to automate our car's pre-heating. Managing this manually in a calendar was too time-consuming, especially since multiple people use the car.

**The Solution:**
By using this integration to log the `device_tracker` status over a long period, we created a dataset that reveals our natural departure patterns. A local AI model (Gemma3) analyzes this data and proposes a departure time. Using **Home Assistant Assist**, the system then asks for verbal confirmation before setting the car's "alarm".

### 🚀 Step-by-Step Implementation

#### 1. Create the Helper (The Alarm)
Before setting up the automation, you need a place to store the final time.
1. Go to **Settings** -> **Devices & Services** -> **Helpers**.
2. Click **Create Helper** -> **Date and/or time**.
3. Name it `Car Heating AI Time` (Entity ID: `input_datetime.car_heating_ai_time`).
4. Select **Date and Time**.

#### 2. Create a Shell Command
To allow the AI to read the generated log file, add this to your `configuration.yaml`:
```yaml
shell_command:
  get_location_history: "cat /config/www/entity_and_attribute_logger/location_tracking.json"
```

#### 3. Add automation
This automation triggers the AI analysis (e.g., when you put your phone on the charger in the evening), asks for confirmation via your Voice Satellite, and sets the helper.

**The Workflow:**
* **Trigger:** Phone starts charging after 19:00.
* **AI Task 1:** Read history file -> Predict departure time.
* **Voice Question 1:** *"Shall I pre-heat the car tomorrow at [AI Time]?"*
    * **IF YES:** Save [AI Time] to helper. **Done.**
    * **IF NO:** Ask Question 2.
* **Voice Question 2:** *"Would you like to set a different time?"*
    * **IF YES:** Ask Question 3.
    * **IF NO:** Do nothing. **Done.**
* **Voice Question 3:** *"At what time are you leaving?"*
    * **User Answer:** Speaks a time (e.g., "Seven hours five" or "Quarter past eight").
    * **AI Task 2:** Converts speech to strict `HH:MM` format.
    * **Final Action:** Save formatted time to helper. **Done.**

Action: Save user's time to the helper. Done.
```yaml
alias: "Car Pre-heating via AI Pattern Analysis"
description: "Analyzes patterns and plans car climate via Gemma3"
triggers:
  - trigger: state
    entity_id: sensor.phone_battery_state
    to: "charging"
conditions:
  - condition: time
    after: "19:00:00"
actions:
  - action: shell_command.get_location_history
    response_variable: log_data
    data: {}
  - action: ai_task.generate_data
    metadata: {}
    data:
      entity_id: ai_task.gemma3_12b_task
      task_name: "Predict Departure"
      instructions: >
        Je bent een patroon-analist. Je krijgt JSON data van de locatie van Bjorn.
        Voorspel de meest waarschijnlijke VERTREKTIJD voor morgenochtend {{ (now() + timedelta(days=1)).strftime('%A %d %B') }}
        Antwoord ENKEL met de tijd in HH:MM formaat (bijv. 07:15). Geen extra tekst!
        Hier is de data die je moet analyseren: {{ log_data.stdout }}
    response_variable: opwarmen_ai_output
  - action: assist_satellite.ask_question
    data:
      question: >-
        Zal ik de auto morgen voorverwarmen voor {{ opwarmen_ai_output.data | trim }}?
      entity_id: assist_satellite.home_assistant_voice_091c68_assist_satellite
      answers:
        - id: "yes"
          sentences: ["ja", "oke", "doe maar"]
        - id: "no"
          sentences: ["nee", "ander tijdstip", "liever niet"]
    response_variable: first_answer
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ first_answer.id == 'yes' }}"
        sequence:
          - action: input_datetime.set_datetime
            target:
              entity_id: input_datetime.volvo_opwarmen_ai_antwoord
            data:
              time: "{{ opwarmen_ai_output.data | trim }}"
              date: "{{ (now() + timedelta(days=1)).strftime('%Y-%m-%d') }}"
      - conditions:
          - condition: template
            value_template: "{{ first_answer.id == 'no' }}"
        sequence:
          - action: assist_satellite.ask_question
            data:
              question: "Wil je een ander tijdstip voor morgen instellen?"
              entity_id: assist_satellite.home_assistant_voice_091c68_assist_satellite
              answers:
                - id: "new_time"
                  sentences: ["ja", "stel in"]
                - id: "cancel"
                  sentences: ["nee", "laat maar"]
            response_variable: second_answer
          - choose:
              - conditions:
                  - condition: template
                    value_template: "{{ second_answer.id == 'new_time' }}"
                sequence:
                  - action: assist_satellite.ask_question
                    data:
                      question: "Welk uur vertrek je?"
                      entity_id: assist_satellite.home_assistant_voice_091c68_assist_satellite
                    # Listen for the vague voice command
                    response_variable: manual_voice_response
                  
                  # --- NEW STEP: AI Formats the voice input ---
                  - action: ai_task.generate_data
                    data:
                      entity_id: ai_task.gemma3_12b_task
                      task_name: "Tijd formatteren"
                      instructions: >
                        De gebruiker zei: "{{ manual_voice_response.sentences[0] }}".
                        Zet dit om naar een tijdformaat HH:MM. 
                        Antwoord ALLEEN met de tijd (bijv. 08:30). 
                        Als het onduidelijk is, gok dan op basis van de meest logische ochtendtijd.
                    response_variable: formatted_time_output

                  - action: input_datetime.set_datetime
                    target:
                      entity_id: input_datetime.volvo_opwarmen_ai_antwoord
                    data:
                      # Uses the AI formatted time
                      time: "{{ formatted_time_output.data | trim }}"
                      date: "{{ (now() + timedelta(days=1)).strftime('%Y-%m-%d') }}"
mode: single
```
#### 4. The final trigger
Finally, create a simple automation that triggers when the time in your helper is reached:
```yaml
alias: "Start Car Heating"
triggers:
  - trigger: time
    at: input_datetime.car_heating_ai_time
actions:
  - action: climate.set_hvac_mode
    target:
      entity_id: climate.your_car_climate
    data:
      hvac_mode: "heat"
```
#### 5. 📂 Directory Structure
```yaml
config/custom_components/entity_attribute_logger/
├── __init__.py          # Core integration logic
├── config_flow.py       # UI configuration flow
├── const.py             # Constant definitions
├── manifest.json        # Metadata and domain definition
├── services.yaml        # Service definitions
└── translations/
    └── en.json          # UI text strings


config/www/entity_and_attribute_logger/
└── filename.json        # Unique logfile per entry
```
