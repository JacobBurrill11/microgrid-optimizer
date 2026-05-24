from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from core.state import MicrogridState
from core.utils import parse_json_response

_llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0.2)

SYSTEM_PROMPT = """You are the Grid Broker — the financial negotiator for a microgrid management system.

Your job: given all upstream agent recommendations, produce the final unified action command for this hour.

You settle any conflicts between agents and make the final call on grid interactions.

Priorities (in order):
1. Meet community demand — never leave the community without power
2. Protect battery health — honor Storage Strategist's SOC constraints
3. Maximize profit — sell surplus at high prices, buy at low prices
4. Minimize fossil fuel — use ONLY when renewable + battery + grid cannot cover demand. Fossil fuel is never profitable; it exists solely to prevent blackouts.

The final command controls six levers:
- charge_battery_kw: kW to charge the battery from renewables (0 if not charging)
- discharge_battery_kw: kW to pull from battery (0 if not discharging)
- buy_grid_kw: kW to purchase from the main grid (use sparingly)
- sell_grid_kw: kW to sell back to the main grid (profit opportunity)
- curtail_solar_kw: kW of solar to curtail (last resort — waste of free energy)
- fossil_fuel_kw: kW from the on-site diesel/gas peaker generator. LAST RESORT ONLY — costs $0.35/kWh (more than grid), produces CO2 emissions. Default to 0 unless grid + battery cannot meet demand.

Respond ONLY with valid JSON. No explanation outside the JSON block.

Output format:
{
  "charge_battery_kw": <float>,
  "discharge_battery_kw": <float>,
  "buy_grid_kw": <float>,
  "sell_grid_kw": <float>,
  "curtail_solar_kw": <float>,
  "fossil_fuel_kw": <float>,
  "reasoning": "<one concise sentence explaining the final decision>"
}"""


def grid_broker_node(state: MicrogridState) -> dict:
    hour = state["hour"]
    solar = state["solar_forecast_kw"]
    wind = state["wind_forecast_kw"]
    demand = state["demand_forecast_kw"]
    battery_kwh = state["battery_level_kwh"]
    capacity_kwh = state["battery_capacity_kwh"]
    soc_pct = round((battery_kwh / capacity_kwh) * 100, 1)
    price = state["grid_price_per_kwh"]
    storage_action = state["storage_action"]
    storage_amount = state["storage_amount_kw"]

    human_msg = f"""Hour {hour} — Final negotiation:

Agent summaries:
- Forecaster: Solar {solar} kW + Wind {wind} kW = {solar + wind} kW total generation
- Demand Manager: Community needs {demand} kW
- Storage Strategist: {storage_action.upper()} {storage_amount} kW (battery at {soc_pct}% SOC)

Grid price: ${price:.3f}/kWh
Net generation before battery/grid: {solar + wind - demand:.1f} kW

Produce the final command. Ensure demand is fully met."""

    response = _llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=human_msg)])
    data = parse_json_response(response.content)

    reasoning = data.pop("reasoning", "")

    fossil = data.get("fossil_fuel_kw", 0)
    fossil_str = f" | ⚠ Fossil: {fossil} kW" if fossil > 0 else ""
    log = (
        f"[Grid Broker @ hour {hour}] "
        f"Buy: {data.get('buy_grid_kw', 0)} kW | Sell: {data.get('sell_grid_kw', 0)} kW | "
        f"Charge: {data.get('charge_battery_kw', 0)} kW | Discharge: {data.get('discharge_battery_kw', 0)} kW"
        f"{fossil_str} — {reasoning}"
    )

    return {
        "broker_reasoning": reasoning,
        "final_command": data,
        "agent_logs": [log],
    }
