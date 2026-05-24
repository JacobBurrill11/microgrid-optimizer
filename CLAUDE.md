# Project Context

I would like to build a localized simulation where multiple specialized AI agents collaborate to manage a microgrid (solar arrays, wind turbines, battery storage, and a local community's power demand) to maximize profit and grid stability while minimizing reliance on fossil-fuel backup power. 

# About Me

I am a recently graduated college student with a math major and a double minor in Computer Science and Data science. I am looking to get a job as a data analyst/scientist. I would like to build a portfolio of different projects to demonstrate my abilities. My audience would be either future employers or people with some background knowledge about the subject. I prefer clear professional output. 

# Rules

- Always ask clarifying questions before starting a complex task
- Allow all URL web fetches unless otherwise stated
- Show your plan and steps before executing
- keep reports and summaries concise - bullet points over paragraphs
- Use free, historical weather data (like Open-Meteo API) and simulated grid pricing data (or real public data from ISOs like CAISO or ERCOT if you want to be fancy).
- Save all output files to the output folder
- Cite all sources when doing research

# Project Structure

Instead of one massive prompt, you break the problem down into a team of virtual "employees" (agents) with specific personas and goals:

- The Forecaster: Data-driven analyst that analyzes live (or simulated) weather APIs to predict solar/wind yield for the next 4–12 hours.
- The Demand Manager:	Consumer advocate that	monitors community power usage patterns and predicts "peak load" times (e.g., everyone turning on AC at 5 PM).
- The Storage Strategist:	Battery operator that decides when to charge the battery bank (when energy is cheap/abundant) and when to discharge it (during peaks).
- The Grid Broker:	Financial negotiator that checks current market electricity prices and decides whether to sell excess green energy back to the main grid or buy cheap grid power.

The Workflow (How They Collaborate)

- Environment Trigger: A simulated hourly update occurs (e.g., "It's 3:00 PM, partly cloudy, grid price is $0.15/kWh, community demand is spiking").

- Analysis: The Forecaster and Demand Manager pass their predictions to a shared state or memory buffer.

- Conflict Resolution: If demand is higher than generation, The Storage Strategist and The Grid Brokermust "negotiate." For example: 
Should we drain the battery now, or save it for 6:00 PM when prices double?

- Action execution: The agents output a unified, structured JSON command (e.g., {"charge_battery": 0, "buy_grid_power": 20, "curtail_solar": false}).

The Output: 
- Build a simple dashboard showing the agents "talking" to each other in real-time, alongside a live graph of battery levels, energy generation, and money saved. 

- Feature it on my github