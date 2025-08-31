import requests, pickle, db

discord_id = 0
id = 1
week_score = 2
total_score = 3
day_score = 4

def user_calculate_total_score():
    users = db.user_read_all()
    ranked_users = get_ranked_users(users, score_type=2)  # 2: week_score (예시)

    for user in ranked_users:
        rank = user[5]
        user_id = user[1]
        total_score = int(100 * (0.93 ** (rank - 1))) + user[3]
        db.user_update_total_score(user_id, total_score)

def get_ranked_users(users, score_type: int):
    filtered_users = sorted(
        (u for u in users if u[score_type] > 0),
        key=lambda x: x[score_type],
        reverse=True
    )

    ranked_users = []
    current_rank = 1
    prev_score = None
    same_count = 0

    for user in filtered_users:
        score = user[score_type]
        if score != prev_score:
            current_rank += same_count
            same_count = 1
            prev_score = score
        else:
            same_count += 1

        ranked_users.append(list(user) + [current_rank])

    return ranked_users
    
def crawling(user):
    url = "https://solved.ac/api/v3/user/problem_stats"
    querystring = {"handle":user}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36', "Accept": "application/json"}
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()