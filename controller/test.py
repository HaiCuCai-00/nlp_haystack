
a={
    "id": "123"
}

try:
    if a["index"] is None:
        print("a")
except Exception as e:
    print("b")