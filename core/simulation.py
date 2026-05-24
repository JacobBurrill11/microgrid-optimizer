import json
from datetime import datetime, date
from pathlib import Path
from typing import Generator
from core.graph import microgrid_graph
from data.weather import fetch_hourly_weather, get_simulated_weather
from data.pricing import get_grid_price

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

BATTERY_CAPACITY_KWH = 500.0
INITIAL_BATTERY_KWH = 250.0  # start at 50% SOC
FOSSIL_FUEL_COST_PER_KWH = 0.35


def _update_battery(battery_kwh: float, command: dict) -> float:
    """Apply the broker's command to update battery state."""
    charge = command.get("charge_battery_kw", 0)
    discharge = command.get("discharge_battery_kw", 0)
    new_level = battery_kwh + charge - discharge
    return max(BATTERY_CAPACITY_KWH * 0.10, min(BATTERY_CAPACITY_KWH * 0.95, new_level))


def _compute_financials(command: dict, price: float) -> dict:
    """Calculate revenue, cost, and net profit for the hour."""
    revenue = command.get("sell_grid_kw", 0) * price
    grid_cost = command.get("buy_grid_kw", 0) * price
    fossil_cost = command.get("fossil_fuel_kw", 0) * FOSSIL_FUEL_COST_PER_KWH
    total_cost = grid_cost + fossil_cost
    return {
        "revenue_usd":     round(revenue, 4),
        "cost_usd":        round(total_cost, 4),
        "grid_cost_usd":   round(grid_cost, 4),
        "fossil_cost_usd": round(fossil_cost, 4),
        "net_usd":         round(revenue - total_cost, 4),
    }


def run_simulation(use_real_weather: bool = True, hours: int = 24) -> list[dict]:
    """
    Run the full 24-hour microgrid simulation.

    Args:
        use_real_weather: Fetch live data from Open-Meteo. Falls back to simulated if fetch fails.
        hours: Number of hours to simulate (default: 24).

    Returns:
        List of hourly result dicts, also saved to output/simulation_results.json.
    """
    today = date.today().isoformat()

    # Attempt live weather fetch
    weather_by_hour = None
    if use_real_weather:
        try:
            weather_by_hour = fetch_hourly_weather()
            print("Weather source: Open-Meteo API (live)")
        except Exception as e:
            print(f"Weather fetch failed ({e}), falling back to simulated data.")

    battery_kwh = INITIAL_BATTERY_KWH
    results = []

    for hour in range(hours):
        timestamp = f"{today}T{hour:02d}:00"

        weather = weather_by_hour[hour] if weather_by_hour else get_simulated_weather(hour)
        price = get_grid_price(hour)

        initial_state = {
            "timestamp": timestamp,
            "hour": hour,
            "weather_data": weather,
            "battery_level_kwh": battery_kwh,
            "battery_capacity_kwh": BATTERY_CAPACITY_KWH,
            "grid_price_per_kwh": price,
            # Fields populated by agents
            "solar_forecast_kw": 0.0,
            "wind_forecast_kw": 0.0,
            "forecaster_analysis": "",
            "demand_forecast_kw": 0.0,
            "peak_risk": "low",
            "demand_analysis": "",
            "storage_action": "hold",
            "storage_amount_kw": 0.0,
            "storage_reasoning": "",
            "broker_reasoning": "",
            "fossil_fuel_kw": 0.0,
            "final_command": {},
            "agent_logs": [],
        }

        print(f"\n{'=' * 60}")
        print(f"Hour {hour:02d}:00 | Price: ${price:.3f}/kWh | Battery: {battery_kwh:.1f} kWh")
        print("=" * 60)

        final_state = microgrid_graph.invoke(initial_state)

        for log in final_state["agent_logs"]:
            print(f"  {log}")

        battery_kwh = _update_battery(battery_kwh, final_state["final_command"])
        financials = _compute_financials(final_state["final_command"], price)

        hour_result = {
            "hour": hour,
            "timestamp": timestamp,
            "weather": weather,
            "grid_price_per_kwh": price,
            "solar_forecast_kw": final_state["solar_forecast_kw"],
            "wind_forecast_kw": final_state["wind_forecast_kw"],
            "demand_forecast_kw": final_state["demand_forecast_kw"],
            "peak_risk": final_state["peak_risk"],
            "battery_level_kwh": battery_kwh,
            "storage_action": final_state["storage_action"],
            "final_command": final_state["final_command"],
            "financials": financials,
            "agent_logs": final_state["agent_logs"],
        }
        results.append(hour_result)

    output_path = OUTPUT_DIR / "simulation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    total_revenue = sum(r["financials"]["revenue_usd"] for r in results)
    total_cost = sum(r["financials"]["cost_usd"] for r in results)
    print(f"\n{'=' * 60}")
    print(f"Simulation complete. Results saved to {output_path}")
    print(f"Total revenue: ${total_revenue:.2f} | Total cost: ${total_cost:.2f} | Net: ${total_revenue - total_cost:.2f}")

    return results


def run_simulation_stream(
    use_real_weather: bool = True,
    hours: int = 24,
    city_name: str = "San Francisco, CA",
    latitude: float = 37.7749,
    longitude: float = -122.4194,
) -> Generator[dict, None, None]:
    """Streaming version of run_simulation(). Yields one hourly result dict per hour.

    Battery state persists across yields via generator local scope.
    JSON is written to output/simulation_results.json after all hours complete.
    """
    today = date.today().isoformat()

    weather_by_hour = None
    if use_real_weather:
        try:
            weather_by_hour = fetch_hourly_weather(lat=latitude, lon=longitude)
        except Exception:
            pass  # fall through to simulated

    battery_kwh = INITIAL_BATTERY_KWH
    results = []

    for hour in range(hours):
        timestamp = f"{today}T{hour:02d}:00"
        weather = weather_by_hour[hour] if weather_by_hour else get_simulated_weather(hour)
        price = get_grid_price(hour)

        initial_state = {
            "timestamp": timestamp,
            "hour": hour,
            "weather_data": weather,
            "battery_level_kwh": battery_kwh,
            "battery_capacity_kwh": BATTERY_CAPACITY_KWH,
            "grid_price_per_kwh": price,
            "solar_forecast_kw": 0.0,
            "wind_forecast_kw": 0.0,
            "forecaster_analysis": "",
            "demand_forecast_kw": 0.0,
            "peak_risk": "low",
            "demand_analysis": "",
            "storage_action": "hold",
            "storage_amount_kw": 0.0,
            "storage_reasoning": "",
            "broker_reasoning": "",
            "fossil_fuel_kw": 0.0,
            "final_command": {},
            "agent_logs": [],
        }

        final_state = microgrid_graph.invoke(initial_state)
        battery_kwh = _update_battery(battery_kwh, final_state["final_command"])
        financials = _compute_financials(final_state["final_command"], price)

        hour_result = {
            "hour": hour,
            "timestamp": timestamp,
            "city": city_name,
            "weather": weather,
            "grid_price_per_kwh": price,
            "solar_forecast_kw": final_state["solar_forecast_kw"],
            "wind_forecast_kw": final_state["wind_forecast_kw"],
            "demand_forecast_kw": final_state["demand_forecast_kw"],
            "peak_risk": final_state["peak_risk"],
            "battery_level_kwh": battery_kwh,
            "storage_action": final_state["storage_action"],
            "fossil_fuel_kw": final_state["final_command"].get("fossil_fuel_kw", 0.0),
            "final_command": final_state["final_command"],
            "financials": financials,
            "agent_logs": final_state["agent_logs"],
        }
        results.append(hour_result)
        yield hour_result

    output_path = OUTPUT_DIR / "simulation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
