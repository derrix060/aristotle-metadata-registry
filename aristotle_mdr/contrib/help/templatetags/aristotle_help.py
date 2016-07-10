from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, resolve
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from aristotle_mdr import perms
import aristotle_mdr.models as MDR
from aristotle_mdr.contrib.help.models import ConceptHelp, HelpPage
from aristotle_mdr.templatetags.aristotle_tags import doc
from django.conf import settings

register = template.Library()


@register.simple_tag
def help_doc(item, field='brief', request=None):
    """Gets the appropriate help text for a model.
    """

    from aristotle_mdr.utils.doc_parse import parse_rst, parse_docstring
    app_label = item._meta.app_label
    model_name = item._meta.model_name

    _help = ConceptHelp.objects.filter(app_label=app_label, concept_type=model_name).first()

    if _help:
        help_text = getattr(_help, field)
        if help_text:
            return relink(_help, field)
    return doc(item)


@register.simple_tag
def relink(help_item, field):
    text = getattr(help_item, field)
    if not text:
        return ""

    import re
    text = re.sub(
        r'\{static\}',
        "%s/aristotle_help/" % settings.STATIC_URL, text
    )

    def make_concept_link(match):
        from django.core.urlresolvers import reverse_lazy
        try:
            flags = match.group(2) or ""
            model_details = match.group(1)

            m = model_details.lower().replace(' ', '').split('.', 1)
            if len(m) == 1:
                app = help_item.app_label
                model = m[0]
            else:
                app, model = m
            if app:
                ct = ContentType.objects.get(app_label=app, model=model)
            else:
                ct = ContentType.objects.get(model=model)
                app = ct.app_label
            help_url = reverse_lazy("aristotle_help:concept_help", args=[app, model])

            if 's' not in flags:
                name = ct.model_class().get_verbose_name()
            else:
                name = ct.model_class().get_verbose_name_plural()

            if 'u' in flags:
                return help_url
            else:
                return "<a class='help_link' href='{url}'>{name}</a>".format(
                    name=name,
                    url=help_url
                    )
        except:
            return "unknown model - %s" % match.group(0)

    def make_helppage_link(match):
        from django.core.urlresolvers import reverse_lazy
        try:
            flags = match.group(2) or ""

            help_page = HelpPage.objects.get(slug=match.group(1))
            name = help_page.title
            help_url = reverse("aristotle_help:help_page", args=[help_page.slug])

            if 'u' in flags:
                return help_url
            else:
                return "<a class='help_link' href='{url}'>{name}</a>".format(
                    name=name,
                    url=help_url
                    )
        except:
            return "unknown help page - %s" % match.group(0)

    text = re.sub(
        r"\[\[(?:h\|)([[a-zA-Z0-9 _\-.]+)(\|[a-z]+)?\]\]",
        make_helppage_link, text
    )
    text = re.sub(
        r"\[\[(?:c\|)?([[a-zA-Z _.]+)(\|[a-z]+)?\]\]",
        make_concept_link, text
    )
    return text
