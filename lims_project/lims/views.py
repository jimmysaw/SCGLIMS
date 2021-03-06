from __future__ import print_function

import sys

import json

from django.shortcuts import render
from django.http import Http404
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.text import capfirst

from lims.models import Amplicon, Container, DNALibrary, Sample, SAGPlate, SAGPlateDilution, ExtractedCell, ExtractedDNA


def index(request):
    return render(request, 'lims/index.html')


def browse(request):
    return render(request, 'lims/browse.html')


def get_attr_list(obj):
    """Returns a [(key, value), ...] list for given object. The object should
    implement a preffered_ordering function that returns a list of attribute
    names."""
    return [(k, getattr(obj, k)) for k in obj.preferred_ordering()]


def default_object_table(obj):
    def func(request, obj_id):
        o = obj.objects.get(pk=obj_id)
        verbose_name = unicode(capfirst(obj._meta.verbose_name))
        verbose_name_plural = unicode(capfirst(obj._meta.verbose_name_plural))
        return render(request, 'lims/object.html',
                      {'objectname': obj.__name__, 'verbose_name':
                       verbose_name, 'verbose_name_plural':
                       verbose_name_plural, 'object': o})
    return func


def default_object_list(obj):
    def func(request):
        verbose_name = unicode(capfirst(obj._meta.verbose_name))
        verbose_name_plural = unicode(capfirst(obj._meta.verbose_name_plural))
        return render(request, 'lims/object_list.html',
                      {'objectname': obj.__name__, 'verbose_name':
                       verbose_name, 'verbose_name_plural':
                       verbose_name_plural, 'objects':
                       list(obj.objects.all())})
    return func


def generate_related_objects_tree(obj):
    rv = {"url": reverse('lims.views.browse.' + slugify(type(obj).__name__),
                                                 args=[obj.id])}

    for ro in obj._meta.get_all_related_objects():
        for o in getattr(obj, ro.get_accessor_name()).all():
            rv.setdefault(type(o).__name__, {})[str(o)] = generate_related_objects_tree(o)

    return rv


def sample_tree_json(request, sample_id):
    sample = Sample.objects.get(pk=sample_id)

    response_data = {'Sample': {}}
    response_data['Sample'][str(sample)] = generate_related_objects_tree(sample)

    return render(request, 'lims/sampletree.html',
                  {'json': json.dumps(response_data)})


def barcode_index(request):
    return render(request, 'lims/barcode_index.html')


def barcode_search(request, barcode):
    #try:
    barcode_model = {
        "AM": Amplicon,
        "SA": Sample,
        "CO": Container,
        "EC": ExtractedCell,
        "ED": ExtractedDNA,
        "SP": SAGPlate,
        "SD": SAGPlateDilution,
        "DL": DNALibrary,
    }[barcode[:2]]
    #except KeyError:
    #    raise Http404

    if barcode.startswith("CO:"):
        c = Container.objects.get(pk=int(barcode[3:]))
        return default_object_table(barcode_model)(request, c.id)
    else:
        o = barcode_model.objects.get(uid=barcode[3:])
        return default_object_table(barcode_model)(request, o.id)
