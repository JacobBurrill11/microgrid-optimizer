import operator
from typing import Annotated
from typing_extensions import TypedDict


class MicrogridState(TypedDict):
    # Simulation context
    timestamp: str
    hour: int

    # Raw inputs
    weather_data: dict
    battery_level_kwh: float
    battery_capacity_kwh: float
    grid_price_per_kwh: float

    # Forecaster outputs
    solar_forecast_kw: float
    wind_forecast_kw: float
    forecaster_analysis: str

    # Demand Manager outputs
    demand_forecast_kw: float
    peak_risk: str
    demand_analysis: str

    # Storage Strategist outputs
    storage_action: str        # "charge" | "discharge" | "hold"
    storage_amount_kw: float
    storage_reasoning: str

    # Grid Broker outputs
    broker_reasoning: str
    fossil_fuel_kw: float

    # Final unified command
    final_command: dict

    # Append-only log — each agent appends its message
    agent_logs: Annotated[list[str], operator.add]
