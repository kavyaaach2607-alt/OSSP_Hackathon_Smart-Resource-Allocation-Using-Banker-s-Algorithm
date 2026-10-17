"""Banker's Algorithm resource manager (standard library only)."""


class Bankers:
    def __init__(self, available, maximum, allocation):
        self.validate(available, maximum, allocation)
        self.available = list(available)
        self.maximum = [list(r) for r in maximum]
        self.allocation = [list(r) for r in allocation]
        self.n = len(maximum)
        self.m = len(available)

    # ---------- input validation ----------
    @staticmethod
    def validate(available, maximum, allocation):
        if not available or not maximum:
            raise ValueError("Available and Max must not be empty")
        m = len(available)
        if len(maximum) != len(allocation):
            raise ValueError("Max and Allocation must have the same number of processes")
        if any(v < 0 for v in available):
            raise ValueError("Negative value in Available")
        for i, (mx, al) in enumerate(zip(maximum, allocation)):
            if len(mx) != m or len(al) != m:
                raise ValueError(f"P{i}: row length must be {m}")
            if any(v < 0 for v in mx) or any(v < 0 for v in al):
                raise ValueError(f"P{i}: negative value")
            if any(a > x for a, x in zip(al, mx)):
                raise ValueError(f"P{i}: Allocation exceeds Max")

    # ---------- need matrix ----------
    def need(self, i=None):
        full = [[self.maximum[p][j] - self.allocation[p][j] for j in range(self.m)]
                for p in range(self.n)]
        return full if i is None else full[i]

    # ---------- safety algorithm ----------
    def is_safe(self):
        """Returns (safe: bool, sequence: list[int], steps: list[dict])."""
        work = list(self.available)
        finish = [False] * self.n
        need = self.need()
        sequence, steps = [], []
        progress = True
        while progress:
            progress = False
            for i in range(self.n):
                if not finish[i] and all(need[i][j] <= work[j] for j in range(self.m)):
                    before = list(work)
                    work = [work[j] + self.allocation[i][j] for j in range(self.m)]
                    finish[i] = True
                    sequence.append(i)
                    steps.append({"process": i, "need": need[i], "work_before": before,
                                  "work_after": list(work)})
                    progress = True
        return all(finish), sequence, steps

    # ---------- request algorithm ----------
    def request(self, pid, req):
        if not 0 <= pid < self.n:
            raise ValueError("Unknown process")
        if len(req) != self.m or any(v < 0 for v in req):
            raise ValueError("Invalid request vector")
        need = self.need(pid)
        if any(req[j] > need[j] for j in range(self.m)):
            return {"granted": False, "code": "EXCEEDS_MAX",
                    "message": "Denied: request exceeds the process's maximum claim"}
        if any(req[j] > self.available[j] for j in range(self.m)):
            return {"granted": False, "code": "NOT_AVAILABLE",
                    "message": "Denied: resources not available, process must wait"}
        # trial allocation
        for j in range(self.m):
            self.available[j] -= req[j]
            self.allocation[pid][j] += req[j]
        safe, seq, _ = self.is_safe()
        if safe:
            return {"granted": True, "code": "GRANTED",
                    "message": "Granted: system stays safe", "sequence": seq}
        # rollback
        for j in range(self.m):
            self.available[j] += req[j]
            self.allocation[pid][j] -= req[j]
        return {"granted": False, "code": "UNSAFE",
                "message": "Denied: would lead to an UNSAFE state (rolled back)"}

    def snapshot(self):
        safe, seq, steps = self.is_safe()
        return {"n": self.n, "m": self.m, "available": self.available,
                "max": self.maximum, "allocation": self.allocation, "need": self.need(),
                "safe": safe, "sequence": seq, "steps": steps}


SAMPLE = {
    "available": [3, 3, 2],
    "max": [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
    "allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
}


def sample_manager():
    return Bankers(SAMPLE["available"], SAMPLE["max"], SAMPLE["allocation"])