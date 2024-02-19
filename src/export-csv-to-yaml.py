"""
Convert the extracted CSV file to a YAML file.

The csv is extracted from https://docs.google.com/spreadsheets/d/18GuctcI7bFuW34A1s8jX5FXvYc0YZVxVcF3i17RLq48/edit#gid=994067023
"""
import collections
import csv

import yaml
from pydantic import BaseModel

# Path to your CSV file
csv_file_path = "../docs/guitares - export.csv"
yaml_file_path = "../docs/generated_guitars.yml"
classic_antique_yaml_file_path = (
    "../docs/blog/posts/generated_guitars_classic_antique.yml"
)


class Entry(BaseModel):
    model: str
    starting: str
    ending: str
    webpage: str
    reverb: str

    def to_dict(self) -> dict[str, str]:
        d = self.model_dump(exclude={"webpage", "reverb"})
        d["link"] = self.to_link()
        ordered = collections.OrderedDict(d)
        ordered.move_to_end("model", last=False)
        return dict(ordered)

    def to_link(self) -> str:
        link = ""
        if self.webpage:
            link += f'<a href="{self.webpage}"target="_blank">:material-folder-wrench: Specs</a>'
        if self.webpage and self.reverb:
            link += "<br />"
        if self.reverb:
            link += f'<a href="{self.reverb}"target="_blank">:fontawesome-solid-magnifying-glass-dollar: reverb</a>'
        return link


# Open the CSV file
def main():
    with open(csv_file_path, mode="r", encoding="utf-8") as file:
        # Create a CSV reader object
        csv_reader = csv.DictReader(file)

        entries = (Entry(**entry) for entry in list(csv_reader))
        dicts = [entry.to_dict() for entry in entries]

    # Write the YAML string to a file
    with open(yaml_file_path, "w") as file:
        yaml.dump(dicts, file, sort_keys=False)

    with open(classic_antique_yaml_file_path, "w") as file:
        antiques = [d for d in dicts if "antique" in d["model"].lower()]
        yaml.dump(antiques, file, sort_keys=False)


if __name__ == "__main__":
    main()
