"""Print the resolved requirements that the image does not already hold.

Usage: missing_packages.py <image package list> <resolved requirements>

Both files hold ``name==version`` lines. A package the image has at another
version is an error: the image wins, so the bundle cannot bring its own.
"""
import re
import sys


def read(path):
    """The ``name==version`` lines of a file, by normalised name."""
    pins = {}
    for line in open(path):
        line = line.strip()
        if "==" in line and not line.startswith("#"):
            name, version = line.split("==", 1)
            version = version.split(";")[0].strip()
            pins[re.sub(r"[-_.]+", "-", name.split("[")[0]).lower()] = (name, version)
    return pins


image = read(sys.argv[1])
resolved = read(sys.argv[2])
conflicts = [
    f"{name}: image {image[name][1]}, bundle {resolved[name][1]}"
    for name in sorted(set(image) & set(resolved))
    if image[name][1] != resolved[name][1]
]
if conflicts:
    sys.exit("the bundle asks for a version the image does not have:\n  " + "\n  ".join(conflicts))
for name in sorted(set(resolved) - set(image)):
    print("==".join(resolved[name]))
