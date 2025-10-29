import requests

topics = ["a unicorn", "pirates", "flying sailboats", "the fae", "cats and dogs", "whales and giraffes"]

for topic in topics:

    response = requests.post("http://localhost:8000/queue/add", json={
        "client_id": "darrin_tests",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": f"Please write the longest story you possibly can about {topic}. It should take 10 minutes to read aloud."}
        ],
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "temperature": 0.7,
        "stream": "True"
    }
    )

    print(response)

    data = response.json()
    print(data)