from rest_framework import serializers
from controller.models import TemplateVar, Template


class TemplateVarSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateVar
        fields = ['name', 'type']


class TemplateSerializer(serializers.ModelSerializer):
    vars = TemplateVarSerializer(many=True)

    class Meta:
        model = Template
        fields = ['id', 'name', 'code', 'vars']

    def create(self, validated_data):
        vars_data = validated_data.pop('vars')
        template = Template.objects.create(**validated_data)
        for var in vars_data:
            TemplateVar.objects.create(template=template, **var)
        return template

    def validate_name(self, value):
        if value.isdigit():
            raise serializers.ValidationError(
                'Template name must not be a digit'
            )
        return value
