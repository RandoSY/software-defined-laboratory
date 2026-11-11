def register(registry, lab):
    def add(args):
        a = float(args.get("A", 0))
        b = float(args.get("B", 0))
        return {"name":"demo_add", "a":a, "b":b, "result":a+b}

    def scale(args):
        x = float(args.get("X", 0))
        k = float(args.get("K", 1))
        return {"name":"demo_scale", "x":x, "k":k, "result":x*k}

    registry.register("demo_add", add)
    registry.register("demo_scale", scale)
