"""
THIS IS NOT HOW THINGS SHOULD BE DONE, and I acknowledge that.
But I'm new to this corner of web development, am hoping to avoid using Webpack, and would currently rather spend my time creating the game than continuing to troubleshoot this odd error.

Basically, VSCode and tsc want me to "import" React, but tsc transforms that into a require(), which the browser doesn't like.
Because I'm using <script> to include React on each page on which I use it, I do not need to do any sort of importing at all from the browser's point of view.
But when I use "import" in the Typescript files to satisfy VSCode and tsc, it transforms all references to React to use the one that it require()'d.
So instead of just deleting the require()s, we have to do a hacky replacement.

Usage: TODO
"""

import json
import os
import re

DEBUG = False
remove = ":transform_import.remove:"
replace = ":transform_import.replace:"
replacement = 'var react_1 = {default: React}; var react_dom_1 = {default: ReactDOM};'
success_comment = "//:transformed_import:"

def dp(s):
    if DEBUG: print(s)

config_file = open("tsconfig.json", "r")
config = json.load(config_file)
out_dir = config["compilerOptions"]["outDir"]
config_file.close()

dp("Output dir: "+out_dir)
for fname in os.listdir(out_dir):
    fpath = os.path.join(out_dir, fname)
    if not os.path.isfile(fpath): continue
    if not fname[-3:] == ".js": continue

    dp("Found JS file: "+fname)
    n = 0
    f = open(fpath, "r+")
    lines = f.readlines()

    for (i, line) in enumerate(lines):
        if (re.search(remove, line)) is not None:
            lines[i] = success_comment+"\n"
            n += 1
        if (re.search(replace, line)) is not None:
            lines[i] = replacement+"  "+success_comment+"\n"
            n += 1

    f.seek(0)
    f.truncate(0)
    f.writelines(lines)
    f.close()
    dp(f"Stripped {n} requires")
print("Tranformed imports!")