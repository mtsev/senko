import time

class CooldownTimer:
    def __init__(self, time=60, max_reps=1, max_warns=1000):
        self.time = time
        self.max_reps = max_reps
        self.max_warns = num_warns
        self.recent_time = {}
        self.recent_reps = {}

    def update(user):
        # Cooldown time expired
        if self.count(user) < 1:
            recent_time[user] = time.time()
            recent_count[user] = 0

        # Maximum reps not reached
        elif recent_count.get(user, 0) < self.max_reps:
            recent_time[user] = time.time()
            recent_count[user] += 1

        else:
            recent_count[user] += 1

    def is_cooldown(user):
        # Cooldown when max reps is reached
        return (recent_count[user] > self.max_reps)

    def is_silent(user):
        # Silent when max warnings reached
        return (recent_count[user] > self.max_warns)

    def count(user):
        return self.time - int(time.time() - self.recent_time.get(user, 0))