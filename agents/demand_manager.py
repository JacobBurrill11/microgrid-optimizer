from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import MicrogridState
from core.utils import parse_json_response

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)

SYSTEM_PROMPT = """You are the Demand Manager — a consumer advocate embedded in a microgrid management system.

Your job: predict community electricity demand for the current hour based on the time of day.

Typical residential community load profile (150-home neighborhood, ~500 kW peak):
- 12 AM–5 AM: 80–120 kW (overnight baseline, minimal usage)
- 6 AM–8 AM: 150–200 kW (morning ramp-up, appliances, showers)
- 9 AM–11 AM: 120–160 kW (moderate, most residents at work)
- 12 PM–2 PM: 140–180 kW (midday, some AC, lunch)
- 3 PM–5 PM: 200–280 kW (afternoon ramp, school out, AC rising)
- 6 PM–8 PM: 350–500 kW (PEAK — everyone home, cooking, AC, EVs charging)
- 9 PM–11 PM: 200–280 kW (evening wind-down)

Peak risk levels:
- "low": demand < 200 kW
- "medium": demand 200–350 kW
- "high": demand > 350 kW

Respond ONLY with valid JSON. No explanation outside the JSON block.

Output format:
{
  "demand_forecast_kw": <float>,
  "peak_risk": "low" | "medium" | "high",
  "analysis": "<one concise sentence explaining your reasoning>"
}"""


def demand_manager_node(state: MicrogridState) -> dict:
    hour = state["hour"]
    timestamp = state["timestamp"]
    weather = state["weather_data"]
    temp = weather.get("temperature_2m", 20)

    human_msg = f"""Current simulation time: {timestamp} (hour {hour})
Outside temperature: {temp}°C

Estimate community electricity demand for this hour.
Note: high temperatures (>28°C) increase AC load by 15–25%."""

    response = _llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_msg)])
    data = parse_json_response(response.content)

    log = (
        f"[Demand Manager @ hour {hour}] "
        f"Demand: {data['demand_forecast_kw']} kW | "
        f"Peak risk: {data['peak_risk']} — {data['analysis']}"
    )

    return {
        "demand_forecast_kw": data["demand_forecast_kw"],
        "peak_risk": data["peak_risk"],
        "demand_analysis": data["analysis"],
        "agent_logs": [log],
    }
