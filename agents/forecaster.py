from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import MicrogridState
from core.utils import parse_json_response

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)

SYSTEM_PROMPT = """You are the Forecaster — a data-driven energy analyst embedded in a microgrid management system.

Your job: analyze current weather data and estimate solar and wind power generation for the next hour.

Solar generation rules of thumb:
- Clear sky at peak sun (10 AM–2 PM): up to 100% of rated capacity
- Cloud cover reduces solar linearly (50% cloud cover → ~50% output)
- Early morning / late evening: reduce by 70–90%
- Night hours (8 PM–5 AM): 0 kW solar

Wind generation rules of thumb:
- Wind speed < 3 m/s: 0 kW (below cut-in speed)
- 3–12 m/s: scales linearly with speed
- > 25 m/s: 0 kW (turbine shuts down for safety)
- Rated capacity assumed at 12 m/s

Respond ONLY with valid JSON. No explanation outside the JSON block.

Output format:
{
  "solar_forecast_kw": <float>,
  "wind_forecast_kw": <float>,
  "confidence": "high" | "medium" | "low",
  "analysis": "<one concise sentence explaining your reasoning>"
}"""


def forecaster_node(state: MicrogridState) -> dict:
    weather = state["weather_data"]
    hour = state["hour"]

    human_msg = f"""Current conditions at hour {hour}:
- Cloud cover: {weather.get('cloudcover', 'N/A')}%
- Wind speed: {weather.get('windspeed_10m', 'N/A')} m/s
- Solar radiation: {weather.get('direct_radiation', 'N/A')} W/m²
- Temperature: {weather.get('temperature_2m', 'N/A')}°C

Assumed system capacities:
- Solar array: 500 kW rated
- Wind turbines: 100 kW rated

Forecast solar and wind generation for this hour."""

    response = _llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_msg)])
    data = parse_json_response(response.content)

    log = (
        f"[Forecaster @ hour {hour}] "
        f"Solar: {data['solar_forecast_kw']} kW | "
        f"Wind: {data['wind_forecast_kw']} kW | "
        f"Confidence: {data['confidence']} — {data['analysis']}"
    )

    return {
        "solar_forecast_kw": data["solar_forecast_kw"],
        "wind_forecast_kw": data["wind_forecast_kw"],
        "forecaster_analysis": data["analysis"],
        "agent_logs": [log],
    }
