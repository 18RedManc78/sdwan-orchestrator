from django.db import models
from typing import List
import jinja2
import requests
import json
from collections import defaultdict
from typing import Iterator, Iterable, Dict, Set
from django.core.exceptions import ValidationError


class Customer(models.Model):
    name = models.CharField(max_length=128)


class AdminDomain(models.Model):
    name = models.CharField(max_length=128)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)


class Role(models.Model):
    name = models.CharField(max_length=128)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)


class NEGroup(models.Model):
    name = models.CharField(max_length=128)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    filter_string = models.TextField(default='')

    def set_filters(self, **filters):
        self.filter_string = json.dumps(filters)

    @property
    def members(self) -> Iterator[NE]:
        yield from NE.objects.filter(**json.loads(self.filter_string))


class Activator(models.Model):
    hostname = models.CharField(max_length=128, unique=True, db_index=True)
    port = models.IntegerField(default=8080)
    ssh_path = models.CharField(max_length=255)
    api_path = models.CharField(max_length=255)
    method = models.CharField(max_length=16, default='https')

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def make_url(self, path):
        return f'{self.method}://{self.hostname}:{self.port}/{path}'

    @property
    def ssh_url(self):
        return self.make_url(self.ssh_path)

    @property
    def api_url(self):
        return self.make_url(self.api_path)

    def run_ssh(self, commands: List[str], nes: List[NE]):
        hosts = tuple(ne.hostname for ne in nes)
        r = requests.post(self.ssh_url, data={
                          'hosts': hosts, 'commands': commands})
        return r.text


class NE(models.Model):
    name = models.CharField(unique=True, db_index=True)
    hostname = models.CharField(max_length=128)
    admin_domain = models.ForeignKey(AdminDomain, on_delete=models.CASCADE)
    role = models.ManyToManyField(Role)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sn = models.CharField(unique=True, db_index=True, max_length=128)
    activator = models.ForeignKey(Activator, on_delete=models.CASCADE)


class Template(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    code = models.TextField()

    def run(self, nes: List[NE], vars: List):
        pass

    @staticmethod
    def get_activators(nes: Iterable[NE]) -> Dict[Activator, Set[NE]]:
        activators = defaultdict(set)
        for ne in nes:
            activators[ne.activator].add(ne)
        return activators


def validate_type(value):
    datatypes = {
        'character',
        'text',
        'integer',
        'float',
        'boolean',
        'date'
    }
    if value not in datatypes:
        raise ValidationError(
            f"Invalid type: {value}"
        )


class TemplateVar(models.Model):
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    type = models.CharField(max_length=32, name='type',
                            validators=[validate_type])



class Service(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    


class ServiceTemplate(models.Model):
    template = models.ForeignKey(Template, on_delete=models.SET_NULL)
    group = models.ForeignKey(NEGroup, on_delete=models.SET_NULL)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)