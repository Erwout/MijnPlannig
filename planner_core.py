"""Core logic for LIFE OS. Pure functions are kept separate for easy testing."""
from dataclasses import dataclass
from typing import List, Dict, Any
import itertools
import requests


@dataclass
class Task:
    name: str
    duration: int
    importance: int       # 1-5
    urgency: int          # 1-5
    energy: int           # 1-5 required focus/energy
    category: str
    deadline_days: int    # 0 = today
    flexible: bool = True


def task_score(task: Task, available_energy: int, remaining_minutes: int) -> float:
    """Transparent heuristic score; not an objective truth."""
    if task.duration > remaining_minutes:
        return -100.0
    deadline_factor = 1.0 + max(0, 3 - task.deadline_days) * 0.18
    energy_fit = max(-1.0, 1.0 - abs(task.energy - available_energy) / 4)
    fit_factor = 0.65 + 0.35 * max(0, energy_fit)
    time_fit = min(1.0, remaining_minutes / max(task.duration, 1))
    flexibility_penalty = 0.94 if task.flexible else 1.08
    base = (task.importance * 0.9 + task.urgency * 1.15)
    return round(base * deadline_factor * fit_factor * time_fit * flexibility_penalty, 3)


def greedy_plan(tasks: List[Task], total_minutes: int, energy: int) -> List[Dict[str, Any]]:
    """Choose the highest-scoring currently feasible task repeatedly."""
    remaining = total_minutes
    pending = list(tasks)
    result = []
    while pending and remaining > 0:
        scored = [(task_score(t, energy, remaining), t) for t in pending if t.duration <= remaining]
        if not scored:
            break
        score, chosen = max(scored, key=lambda item: item[0])
        result.append({"task": chosen, "score": score, "start_minute": total_minutes - remaining})
        remaining -= chosen.duration
        pending.remove(chosen)
    return result


def weighted_plan(tasks: List[Task], total_minutes: int, energy: int) -> List[Dict[str, Any]]:
    """Alternative baseline: prioritize importance + urgency per minute."""
    pending = list(tasks)
    remaining = total_minutes
    result = []
    while pending and remaining > 0:
        feasible = [t for t in pending if t.duration <= remaining]
        if not feasible:
            break
        def baseline(t):
            deadline_boost = 1 + max(0, 3 - t.deadline_days) * .18
            return ((t.importance * 1.2 + t.urgency * deadline_boost) / max(t.duration, 5))
        chosen = max(feasible, key=baseline)
        score = round(baseline(chosen), 3)
        result.append({"task": chosen, "score": score, "start_minute": total_minutes - remaining})
        remaining -= chosen.duration
        pending.remove(chosen)
    return result


def summarize(plan: List[Dict[str, Any]], total_minutes: int) -> Dict[str, Any]:
    minutes = sum(item["task"].duration for item in plan)
    return {
        "planned_minutes": minutes,
        "free_minutes": max(0, total_minutes - minutes),
        "tasks_done": len(plan),
        "importance_points": sum(item["task"].importance for item in plan),
        "urgency_points": sum(item["task"].urgency for item in plan),
        "names": [item["task"].name for item in plan],
    }


def sensitivity_analysis(tasks: List[Task], total_minutes: int, energy: int) -> List[Dict[str, Any]]:
    """Change one input at a time and show how the selected task order changes."""
    scenarios = []
    baseline = greedy_plan(tasks, total_minutes, energy)
    base_names = [x["task"].name for x in baseline]
    scenarios.append({"scenario": "Basisplanning", "change": "Geen wijziging", "order": base_names,
                      "changed": False})
    for new_energy in sorted(set([1, 3, 5])):
        if new_energy == energy:
            continue
        plan = greedy_plan(tasks, total_minutes, new_energy)
        names = [x["task"].name for x in plan]
        scenarios.append({"scenario": f"Energie = {new_energy}/5", "change": f"Energie van {energy} naar {new_energy}",
                          "order": names, "changed": names != base_names})
    for extra in [30, -30]:
        new_time = max(15, total_minutes + extra)
        if new_time == total_minutes:
            continue
        plan = greedy_plan(tasks, new_time, energy)
        names = [x["task"].name for x in plan]
        scenarios.append({"scenario": f"Beschikbare tijd = {new_time} min",
                          "change": f"Tijd met {extra:+d} minuten aangepast",
                          "order": names, "changed": names != base_names})
    return scenarios


def sample_tasks():
    return [
        Task("Wiskunde oefenen", 45, 5, 4, 5, "School", 1, False),
        Task("Was ophangen", 10, 3, 4, 1, "Thuis", 0, False),
        Task("Boodschappen halen", 25, 4, 3, 2, "Thuis", 0, True),
        Task("Presentatie voorbereiden", 35, 5, 3, 4, "School", 2, True),
        Task("Sporten", 40, 3, 2, 4, "Gezondheid", 1, True),
        Task("Bericht sturen aan oma", 5, 3, 2, 1, "Sociaal", 0, True),
    ]

# --- Kledingadvies op basis van weer en temperatuur ---
def clothing_advice(weather_cond, temp):
    """Geef kledingadvies op basis van weer en temperatuur."""
    temp = float(temp)
    
    # Temperatuur advisering
    if temp >= 30:
        temp_advice = "Lichtgewicht, ademende kleding. Hoed en zonnebril niet vergeten!"
    elif temp >= 25:
        temp_advice = "Lichte kleding is prima."
    elif temp >= 20:
        temp_advice = "Een T-shirt met eventueel een licht jack."
    elif temp >= 15:
        temp_advice = "Lange broek en een shirt of trui."
    elif temp >= 10:
        temp_advice = "Een sweater of fleece met een jas."
    elif temp >= 0:
        temp_advice = "Dikke jas, sjaal en handschoenen."
    else:
        temp_advice = "Echte winterkleding: dikke jas, muts en laarzen!"
        
    # Weer-specifiek advies
    if "regen" in weather_cond.lower() or "motregen" in weather_cond.lower():
        temp_advice += " *Verpak een regenjas of paraplu!* 🌧️"
    elif "sneeuw" in weather_cond.lower():
        temp_advice += " *Waterdichte schoenen en een warme muts zijn essentieel.* ❄️"
    elif "onweer" in weather_cond.lower():
        temp_advice += " *Blijf liever binnen, maar pak een regenjack mee als je moet.* ⛈️"
    elif "mist" in weather_cond.lower():
        temp_advice += " *Lichtere kleding, maar wel goed zichtbare kleding.* 🌫️"
    else:
        temp_advice += " *Zonnetje! * 😎"
        
    return temp_advice


# --- Live weer via Open-Meteo (geen API-sleutel nodig) ---
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LAT, DEFAULT_LON = 52.3670, 5.7397  # Fallback: Ermelo

_WMO = {
    0: ("Zonnig", "✨ Zonnetje! Prima voor buitenactiviteiten."),
    1: ("Grotendeels zonnig", "Licht bewolkt, goed weer voor buiten."),
    2: ("Half bewolkt", "Weer wisselt tussen zon en wolken."),
    3: ("Bewolkt", "Geen zon, maar wel droog."),
    45: ("Mistig", "Mist kan het zicht beïnvloeden."),
    48: ("Ijsmist", "Koud en glad."),
    51: ("Lichte motregen", "Lichte neerslag, neem een regenjas mee."),
    53: ("Motregen", "Neerslag, houd het droog."),
    55: ("Motregen", "Aanhoudende motregen."),
    61: ("Lichte regen", "Regen: korte wandeling of binnen blijven."),
    63: ("Regen", "Aanhoudende regen: kies taken die binnenshuis kunnen."),
    65: ("Hevige regen", "Zware regenval: focus op indoor taken."),
    71: ("Lichte sneeuw", "Sneeuw: pas op voor gladde wegen."),
    73: ("Sneeuw", "Sneeuwval."),
    75: ("Hevige sneeuw", "Zware sneeuwval."),
    95: ("Onweer", "Onweer: blijf binnen."),
    96: ("Onweer met hagel", "Gevaarlijk weer: binnenshuis blijven."),
}

def _map_wmo(code):
    return _WMO.get(code, ("Ander weer", "Weertype niet herkend; planning blijft werken."))

def get_weather():
    """Geeft (omschrijving, temperatuur, windsnelheid, advies). Breekt nooit af."""
    lat, lon = DEFAULT_LAT, DEFAULT_LON
    try:
        ip = requests.get("https://ipapi.co/json/", timeout=3)
        if ip.status_code == 200:
            d = ip.json()
            if d.get("latitude") and d.get("longitude"):
                lat, lon = d["latitude"], d["longitude"]
    except Exception:
        pass
    try:
        res = requests.get(
            f"{WEATHER_URL}?latitude={lat}&longitude={lon}&current_weather=true", timeout=4
        )
        if res.status_code == 200:
            w = res.json()["current_weather"]
            cond, vibe = _map_wmo(w["weathercode"])
            return cond, w["temperature"], w["windspeed"], vibe
    except Exception:
        pass
    return "Onbekend", 0, 0, "Geen internetverbinding: weer voor Ermelo."