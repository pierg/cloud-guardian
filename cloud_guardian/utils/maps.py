class BiMap:
    def __init__(self):
        self.map = {}
        self.reverse_map = {}

    def add(self, key, value):
        if not (
            isinstance(key, (int, str, float, tuple))
            and isinstance(value, (int, str, float, tuple))
        ):
            raise ValueError(
                "Keys and values must be hashable types (int, str, float, tuple)"
            )
        self.map[key] = value
        self.reverse_map[value] = key

    def remove(self, key):
        if not isinstance(key, (int, str, float, tuple)):
            raise ValueError("Key must be a hashable type")
        if key in self.map:
            value = self.map.pop(key)
            self.reverse_map.pop(value, None)
        elif key in self.reverse_map:
            value = self.reverse_map.pop(key)
            self.map.pop(value, None)

    def get(self, key):
        if not isinstance(key, (int, str, float, tuple)):
            print(key, type(key))
            raise ValueError("Key must be a hashable type")
        return self.map.get(key) or self.reverse_map.get(key)

    def print_table(self):
        print(f"{'Key'.ljust(30)} | {'Value'.ljust(30)}")
        print("-" * 63)
        for key, value in self.map.items():
            print(f"{key.ljust(30)} | {value.ljust(30)}")


