"""Apply the shared example rules to this library's minimal example."""
from usdaeco_check import Result
from usdaeco_check.structure import Context, RULES, check_structure as upstream_structure


def check_structure(root, *, deps=()):
    # Toolchain skips library examples and assumes examples/datacentre.
    # Run its unmodified rules against our explicit minimal example instead.
    example_rules = {21, 22, 23, 24, 27, 28, 29}
    ordinary = [f"S{i:02d}" for i in sorted(RULES) if i not in example_rules]
    results = upstream_structure(root, deps=deps, only=ordinary)
    context = Context(root, deps, [])
    context.example = context.root / "examples/minimal"
    context.story = True
    for number in sorted(example_rules):
        try:
            detail = RULES[number](context)
            results.append(Result(f"S{number:02d}", True, detail or RULES[number].__name__.replace("_", " ")))
        except Exception as exc:
            results.append(Result(f"S{number:02d}", False, str(exc).replace(str(context.root), "<repo>")))
    return sorted(results, key=lambda result: result.name)
