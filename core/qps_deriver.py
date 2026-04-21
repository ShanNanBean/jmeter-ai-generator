"""QPS Deriver — derives thread group parameters from target QPS."""

from typing import Dict, List, Optional


class QPSDeriver:
    """Derives thread group parameters from a target QPS value."""

    RT_ESTIMATES = {
        "login": 200, "query": 100, "search": 150,
        "create": 300, "upload": 500, "payment": 400,
        "order": 300, "pay": 400, "browse": 100,
        "list": 100, "get": 100, "post": 200,
        "default": 200,
    }

    def derive(
        self,
        target_qps: int,
        scenario_steps: Optional[List] = None,
        think_time_range: Optional[List[int]] = None,
    ) -> Dict:
        """Calculate threads, rampUp, duration from target QPS."""

        # Estimate total RT per cycle
        total_rt_ms = 0
        if scenario_steps:
            for step in scenario_steps:
                name_lower = (step.name or "").lower()
                estimated = self.RT_ESTIMATES["default"]
                for key, rt in self.RT_ESTIMATES.items():
                    if key in name_lower:
                        estimated = rt
                        break
                total_rt_ms += estimated
        else:
            total_rt_ms = 200

        # Think time
        if think_time_range and len(think_time_range) == 2:
            think_avg = (think_time_range[0] + think_time_range[1]) / 2
        else:
            think_avg = 1250  # 0.5-2s random, average 1.25s

        cycle_time_s = total_rt_ms / 1000 + think_avg / 1000

        # QPS = threads / cycle_time => threads = QPS * cycle_time
        threads = max(int(target_qps * cycle_time_s), 10)
        ramp_up = max(int(threads * 0.2), 5)
        duration = 600  # Default 10 minutes

        return {
            "threads": threads,
            "rampUp": ramp_up,
            "duration": duration,
            "loop": -1,
            "qpsNote": (
                f"Target QPS={target_qps}, estimated cycle={cycle_time_s:.1f}s, "
                f"requires {threads} threads"
            ),
        }