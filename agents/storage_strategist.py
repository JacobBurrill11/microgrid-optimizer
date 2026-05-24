from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import MicrogridState
from core.utils import parse_json_response

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)

SYSTEM_PROMPT = """You are the Storage Strategist — the battery operator for a microgrid management system.

Your job: decide whether to charge, discharge, or hold the battery bank this hour.

Battery rules:
- Never discharge below 10% state of charge (reserve for emergencies)
- Never charge above 95% (protects battery longevity)
- Max charge/discharge rate: 150 kW
- Think ahead: if peak demand is coming in 1–2 hours, preserve battery charge
- You cannot directly activate the fossil fuel generator — that is the Grid Broker's decision. Flag in your reasoning if battery + grid may be insufficient so the Broker can consider backup power.

Decision logic:
- If generation > demand AND battery < 95%: consider CHARGING
- If demand > generation AND battery > 10%: consider DISCHARGING
- If grid price is very high (>$0.20/kWh): prioritize using stored energy over buying grid power
- If grid price is very low (<$0.08/kWh): consider charging from grid (buy low, sell high later)

Respond ONLY with valid JSON. No explanation outside the JSON block.

Output format:
{
  "action": "charge" | "discharge" | "hold",
  "amount_kw": <float between 0 and 150>,
  "reasoning": "<one concise sentence explaining your decision>"
}"""


def storage_strategist_node(state: MicrogridState) -> dict:
    hour = state["hour"]
    battery_kwh = state["battery_level_kwh"]
    capacity_kwh = state["battery_capacity_kwh"]
    soc_pct = round((battery_kwh / capacity_kwh) * 100, 1)
    solar = state["solar_forecast_kw"]
    wind = state["wind_forecast_kw"]
    demand = state["demand_forecast_kw"]
    price = state["grid_price_per_kwh"]
    peak_risk = state["peak_risk"]
    net_generation = solar + wind - demand

    human_msg = f"""Hour {hour} energy snapshot:
- Solar generation: {solar} kW
- Wind generation: {wind} kW
- Community demand: {demand} kW
- Net generation (gen - demand): {net_generation:.1f} kW
- Battery: {battery_kwh:.1f} kWh / {capacity_kwh} kWh ({soc_pct}% SOC)
- Grid price: ${price:.3f}/kWh
- Peak risk (Demand Manager): {peak_risk}

Decide the battery action for this hour."""

    response = _llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_msg)])
    data = parse_json_response(response.content)

    log = (
        f"[Storage Strategist @ hour {hour}] "
        f"Battery: {soc_pct}% SOC | "
        f"Action: {data['action'].upper()} {data['amount_kw']} kW — {data['reasoning']}"
    )

    return {
        "storage_action": data["action"],
        "storage_amount_kw": data["amount_kw"],
        "storage_reasoning": data["reasoning"],
        "agent_logs": [log],
    }
