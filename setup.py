import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="uzoncalc",
    version="1.0.1",
    author="uyoufu",
    url="https://github.com/uyoufu/UzonCalc",
    author_email="uyoufu@uzoncloud.com",
    description="UzonCalc is a tool for writing engineering calculation documents using Python. With it, you can write calculation reports as smoothly as writing Python, and benefit from the full Python ecosystem and AI assistance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"uzoncalc": "core"},
    packages=["uzoncalc"]
    + ["uzoncalc." + p for p in setuptools.find_packages(where="core")],
    package_data={
        "uzoncalc.template": ["*.html", "*.css"],
    },
    python_requires=">=3.9",
    install_requires=["pint", "numpy"],
)
