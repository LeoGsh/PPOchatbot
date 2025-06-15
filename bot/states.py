class StateManager:

    def __init__(self):
        self.user_states = {}

    def get_step(self, user_id):
        return self.user_states.get(user_id, {}).get("step")

    def get_user_data(self, user_id):
        return self.user_states.get(user_id, {}).get("data", {})

    def set_state(self, user_id, step, **data):
        if user_id not in self.user_states:
            self.user_states[user_id] = {"step": step, "data": {}}
        self.user_states[user_id]["step"] = step
        if data:
            self.user_states[user_id]["data"].update(data)

    def clear_state(self, user_id):
        if user_id in self.user_states:
            del self.user_states[user_id]