import io
import pathlib
from ruamel.yaml import YAML
from jinja2 import Environment, FileSystemLoader

class Config:
    def __init__(self, filename):
        self.filename = filename
        jinja = Environment(loader=FileSystemLoader('.'), trim_blocks=True, lstrip_blocks=True)
        template = jinja.get_template(self.filename)
        yaml=YAML()
        yaml.allow_duplicate_keys = True
        yaml.explicit_start = True
        self.config = yaml.load(template.render())

    @property
    def general(self):
        return self.config["general"]
    @property
    def cve(self):
        return self.config["cve"]
