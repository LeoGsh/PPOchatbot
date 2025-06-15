def get_user_id_by_nickname(self, nickname):
    try:
        user_data = self.vk.users.get(user_ids=nickname)
        if user_data:
            user_id = user_data[0]['id']
            return user_id
    except Exception as e:
        print(f"[ERROR] Ошибка в get_user_id_by_nickname: {str(e)}")
    return None