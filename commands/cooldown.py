import time

class CooldownTimer:
    def __init__(self, time=60, max_reps=1, max_warns=1000):
        self.time = time
        self.max_reps = max_reps
        self.max_warns = max_warns + max_reps
        self.recent_time = {}
        self.recent_reps = {}

    def update(self, user):
        # Cooldown time expired
        if self.count(user) < 1:
            self.recent_time[user] = time.time()
            self.recent_reps[user] = 1

        # Maximum reps not reached
        elif self.recent_reps.get(user, 0) < self.max_reps:
            self.recent_time[user] = time.time()
            self.recent_reps[user] += 1

        else:
            self.recent_reps[user] += 1

    def is_cooldown(self, user):
        # Cooldown when max reps is reached
        return (self.recent_reps[user] > self.max_reps)

    def is_silent(self, user):
        # Silent when max warnings reached
        return (self.recent_reps[user] > self.max_warns)

    def count(self, user):
        return self.time - int(time.time() - self.recent_time.get(user, 0))
