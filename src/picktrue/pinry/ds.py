import csv
import os
from collections import namedtuple
from dataclasses import dataclass
from typing import List


@dataclass
class Pin2Import:
    referer: str
    tags: list
    description: str
    board: str

    # only one of following item should exist and another one should be None
    file_abs_path: str
    image_url2download: str

    @classmethod
    def get_fields(cls) -> List[str]:
        return list(cls.__annotations__.keys())

    def as_dict(self) -> dict:
        out = {}
        fields = self.get_fields()
        for field in fields:
            value = getattr(self, field)
            if not value:
                value = ''
            else:
                value = str(value)
            out[field] = value
        return out


def from_csv(path='pins2import.csv') -> List[Pin2Import]:
    with open(path, 'r', encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter="|")
        rows = list(reader)
        for row in rows:
            row['tags'] = eval(row['tags'])
            row['file_abs_path'] = row['file_abs_path'] or None
            row['image_url2download'] = row['file_abs_path'] or None
        return [Pin2Import(**row) for row in rows]


def to_csv(pins2export: List[Pin2Import], base_path, filename='pins2import.csv'):
    fields_names = Pin2Import.get_fields()
    path = os.path.join(base_path, filename)
    with open(path, 'w', encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields_names, delimiter="|")
        writer.writeheader()
        for row in pins2export:
            writer.writerow(
                row.as_dict(),
            )


def write_to_csv(pin2export: Pin2Import, base_path, filename='pins2import.csv'):
    fields_names = Pin2Import.get_fields()
    path = os.path.join(base_path, filename)
    if os.path.exists(path):
        mode = "a"
    else:
        mode = "w"
    with open(path, mode, encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields_names, delimiter="|")
        if mode == "w":
            writer.writeheader()
        writer.writerow(
            pin2export.as_dict(),
        )
        csv_file.flush()
