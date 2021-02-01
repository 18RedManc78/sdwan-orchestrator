from controller.models import Template, NEGroup, NE
from controller.serializers import TemplateSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
import jinja2
import json


class TemplateViewSet(viewsets.ModelViewSet):

    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

    @action(detail=True, methods=['post'])
    def run(self, request, pk):
        data_dict = json.loads(request.data)
        params = data_dict['params']
        template = Template.objects.get(pk=pk)
        commands = jinja2.Template(template.text).render(**params.split('\n'))
        if 'ne_names' in data_dict and 'group' in data_dict:
            return Response('Invalid query. "Hosts" and "group"'
                            ' cannot be specified at the same time',
                            400)
        if (ne_names := data_dict.get('ne_names')):
            nes = NE.objects.filter(name__in=ne_names)
        elif (group := data_dict.get('group')):
            nes = NEGroup.objects.get(name=group).members
        else:
            return Response('Invalid query. '
                            '"Hosts" or "group" must be specified', 400)
        responce = []
        for activator in (activators := Template.get_activators(nes=nes)):
            # TODO: threads
            responce += activator.run_ssh(
                nes=activators[activator], commands=commands)
        return Response(responce, 200)
