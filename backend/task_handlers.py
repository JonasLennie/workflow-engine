def detect_outliers(input_data):
    outliers = []
    for reading in input_data.get("sensor_readings", []):
        values = reading["values"]
        if len(values) < 2:
            continue
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        flagged = [v for v in values if std > 0 and abs(v - mean) > 2 * std]
        if flagged:
            outliers.append({
                "sensor_id": reading["sensor_id"],
                "outliers": flagged,
                "mean": round(mean, 4),
                "std": round(std, 4),
            })

    for m in input_data.get("measurements", []):
        values = m["values"]
        if len(values) < 2:
            continue
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        flagged = [v for v in values if std > 0 and abs(v - mean) > 2 * std]
        if flagged:
            outliers.append({
                "part_id": m["part_id"],
                "dimension": m["dimension"],
                "outliers": flagged,
                "mean": round(mean, 4),
                "std": round(std, 4),
            })

    return {"outliers": outliers, "total_flagged": len(outliers)}


def analyze_trends(input_data):
    trends = []
    for reading in input_data.get("sensor_readings", []):
        values = reading["values"]
        n = len(values)
        if n < 2:
            continue
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / max(denominator, 1e-9)
        direction = "increasing" if slope > 0.01 else "decreasing" if slope < -0.01 else "stable"
        trends.append({
            "sensor_id": reading["sensor_id"],
            "slope": round(slope, 4),
            "direction": direction,
        })
    return {"trends": trends}


def synthesize(input_data):
    outlier_data = input_data["upstream"]["detect_outliers"]
    trend_data = input_data["upstream"]["analyze_trends"]
    return {
        "outliers": outlier_data["outliers"],
        "trends": trend_data["trends"],
        "has_critical_outliers": outlier_data["total_flagged"] > 0,
        "unstable_sensors": [t["sensor_id"] for t in trend_data["trends"] if t["direction"] != "stable"],
    }


def verdict(input_data):
    synthesis = input_data["upstream"]["synthesize"]
    if synthesis["has_critical_outliers"] and synthesis["unstable_sensors"]:
        v = "FAIL"
    elif synthesis["has_critical_outliers"] or synthesis["unstable_sensors"]:
        v = "WARNING"
    else:
        v = "PASS"
    return {
        "verdict": v,
        "summary": f"Outliers: {len(synthesis['outliers'])}, Unstable sensors: {len(synthesis['unstable_sensors'])}",
        **synthesis,
    }


HANDLERS = {
    "detect_outliers": detect_outliers,
    "analyze_trends": analyze_trends,
    "synthesize": synthesize,
    "verdict": verdict,
}
