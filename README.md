# Entity & Attribute Logger for Home Assistant
This custom component allows you to log specific entity states and their attributes to a JSON format. It is specifically designed to feed historical data into AI models (like Google Gemma or OpenAI) to perform pattern analysis, such as predicting departure times or home occupancy.

🚀 Features
JSON Output: Generates clean, structured JSON data.

Attribute Support: Not only logs the state but also all metadata (attributes) of an entity.

AI-Ready: Optimized to be used with the ai_task integration in Home Assistant.

Lightweight: Runs via a simple shell command or service call.

🛠 Installation
Manual Installation
Copy the entity_attribute_logger folder to your custom_components directory in Home Assistant.

Ensure your file structure looks like this:
